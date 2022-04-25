#  Copyright 2020 Google LLC
#  Copyright 2020 EPAM Systems
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Provides SchemaValidator."""

import copy
import logging
from functools import lru_cache
from typing import Any, List, Tuple, Union

import jsonschema
import requests
import tenacity
from jsonschema import FormatChecker, exceptions
from osdu_api.auth.authorization import TokenRefresher, authorize

from osdu_ingestion.libs.constants import (DATA_SECTION, DATASETS_SECTION,
                                           MASTER_DATA_SECTION,
                                           REFERENCE_DATA_SECTION,
                                           WORK_PRODUCT_COMPONENTS_SECTION,
                                           WORK_PRODUCT_SECTION)
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import (EntitySchemaValidationError,
                                            GenericManifestSchemaError)
from osdu_ingestion.libs.linearize_manifest import ManifestEntity
from osdu_ingestion.libs.mixins import HeadersMixin

logger = logging.getLogger()

RETRIES = 3
TIMEOUT = 1

# Fields' patterns of schemas must be extended with surrogate-keys.
# Inside a list we specify paths to any field, which value we want to extend.
# Example: [
#   ("id"),
#   "definitions", "osdu:wks:AbstractWPCGroupType:1.0.0", "properties", "Datasets", "items")
# ]
SurrogateKeysPaths = List[Tuple[Union[str, int]]]


class OSDURefResolver(jsonschema.RefResolver):
    """Extends base jsonschema resolver for OSDU."""

    def __init__(self, schema_service: str, *args, **kwargs):
        """Implements the schema validatoe

        :param schema_service: The base url for schema service
        :type schema_service: str
        """
        super(OSDURefResolver, self).__init__(*args, **kwargs)
        self.schema_service = schema_service

    def resolve_fragment(self, document: dict, fragment: str) -> dict:
        """
        Add deleting $id field, as long as RefResolver uses the "$id" for resolving references
        instead of searching for these references in "definitions" field.

        :param document: The schema document
        :type document: dict
        :param fragment: schema fragment
        :type fragment: str
        :return: The updated schema document
        :rtype: dict
        """
        document = super().resolve_fragment(document, fragment)
        # /definitions/<OsduID> -> [..., <OsduID>]
        fragment_parts = fragment.split("/")
        if len(fragment_parts) > 1:
            document.pop("$id", None)
        return document


class SchemaValidator(HeadersMixin):
    """Class to validate schema of Manifests."""

    SURROGATE_KEY_ID_PARTS = ("dataset", "work-product", "work-product-component")

    def __init__(
        self,
        schema_service: str,
        token_refresher: TokenRefresher,
        context: Context,
        surrogate_key_fields_paths: SurrogateKeysPaths = None,
        data_types_with_surrogate_ids: List[str] = None
    ):
        """Init SchemaValidator.

        :param schema_service: The base OSDU Schema service url
        :param token_refresher: An instance of token refresher
        :param context: The tenant context
        """
        super().__init__(context)
        self.schema_service = schema_service
        self.context = context
        self.token_refresher = token_refresher
        self.resolver_handlers = {
            "osdu": self.get_schema_request,
            "https": self.get_schema_request,
            self.context.data_partition_id: self.get_schema_request
        }
        self.surrogate_key_fields_paths = surrogate_key_fields_paths or []
        self.data_types_with_surrogate_ids = data_types_with_surrogate_ids or []

    @tenacity.retry(
        wait=tenacity.wait_fixed(TIMEOUT),
        stop=tenacity.stop_after_attempt(RETRIES),
        reraise=True
    )
    @authorize()
    def _get_schema_from_schema_service(self, headers: dict, uri: str) -> requests.Response:
        """Send request to Schema service to retrieve schema."""
        response = requests.get(uri, headers=headers, timeout=60)
        return response

    def _clear_data_fields(self, schema_part: Union[dict, list]):
        """
        Clear a schema's ReferenceData, Data and MasterData fields".
        This method is used by generic manifest validation, deleting these fields make such a
        validation.more generic.
        :param schema_part:
        """
        if schema_part.get("ReferenceData"):
            schema_part["ReferenceData"] = {}
        if schema_part.get("Data"):
            schema_part["Data"] = {}
        if schema_part.get("MasterData"):
            schema_part["MasterData"] = {}

    def get_schema_request(self, uri: str) -> dict:
        """Get schema from Schema service. Change $id field to url.

        :param uri: The URI to fetch the schema
        :type uri: str
        :return: The Schema service response
        :rtype: dict
        """
        if uri.startswith("osdu") or uri.startswith(self.context.data_partition_id):
            uri = f"{self.schema_service}/{uri}"
        response = self._get_schema_from_schema_service(self.request_headers, uri).json()
        response["$id"] = uri
        return response

    @lru_cache()
    def get_schema(self, kind: str) -> Union[dict, None]:
        """Fetch schema from Schema service.

        Implies that the cache is a one-off.

        @TODO lru_cache should be replaced by generic cache mechanism to work with providers
        solutions

        :param kind: The kind of the scheema to fetch
        :type kind: str
        :raises e: Generic exception
        :return: Schema server response
        :rtype: dict
        """
        manifest_schema_uri = f"{self.schema_service}/{kind}"
        try:
            response = self.get_schema_request(manifest_schema_uri)
        except requests.HTTPError as e:
            logger.error(f"Error on getting schema of kind '{kind}'")
            logger.error(e)
            return None
        return response

    @staticmethod
    def _extend_pattern_with_surrogate_key(pattern: str) -> str:
        """
        Extend pattern value with 'surrogate-key:.+'.

        :param pattern: Pattern of any field.
        :return: Extended pattern.
        """
        if "surrogate-key" in pattern:
            return pattern
        if pattern.startswith("^"):
            pattern = pattern[1:]
        if pattern.endswith("$"):
            pattern = pattern[:-1]
        pattern = f"^(surrogate-key:.+|{pattern})$"
        return pattern

    def _get_next_schema_scope(self, schema_scope: Union[dict, list], field: Union[str, int]):
        """
        Get new schema scope, which can be either dict or list, by accessing to it with the next
        element of field

        :param schema_scope: previous schema scope.
        :param field: A field-name by which next schema scopes are accessed.
        :return: Next Schema Scope.
        """
        if isinstance(field, int):
            try:
                schema_scope = schema_scope[field]
            except IndexError:
                schema_scope = None
        elif isinstance(field, str):
            field = field.replace("{{data-partition-id}}", self.context.data_partition_id)
            schema_scope = schema_scope.get(field)
        else:
            schema_scope = None
        return schema_scope

    def _extend_id_patterns_with_surrogate_keys(self, schema: dict):
        """
        Extend Schema's ID pattern with surrogate-key, if this schema can have surrogate keys
        (e.g. WP, Dataset, WPC).
        :param schema:
        :return: Schema with extended id-pattern.
        """
        pattern = schema.get("properties", {}).get("id", {}).get("pattern", "")
        pattern_can_be_surrogate = any(
            data_type in pattern for data_type in self.data_types_with_surrogate_ids
        )
        if pattern_can_be_surrogate:
            schema["properties"]["id"]["pattern"] = self._extend_pattern_with_surrogate_key(
                pattern
            )
        return schema

    def _extend_referential_patterns_with_surrogate_keys(self, schema: dict) -> dict:
        """
        Extend Schema's referential patterns with surrogate-keys, paths to those patterns specified
        in self.surrogate_key_fields_paths
        (e.g. WP -> Components, WPC -> Datasets).

        :param schema: Schema
        :return: Schema with extended id-patterns.
        """
        for path in self.surrogate_key_fields_paths:
            schema_scope = schema
            for field in path:
                schema_scope = self._get_next_schema_scope(schema_scope, field)
                if not schema_scope:
                    break
            else:
                schema_scope["pattern"] = self._extend_pattern_with_surrogate_key(
                    schema_scope["pattern"])
        return schema

    def _add_surrogate_keys_to_patterns(self, schema: dict) -> dict:
        """
        Add 'surrogate-key:.+' to patterns of specific fields.

        :param schema: Original schema.
        :return: Extended schema.
        """
        schema = self._extend_id_patterns_with_surrogate_keys(schema)
        schema = self._extend_referential_patterns_with_surrogate_keys(schema)
        return schema

    def _validate_entity(self, entity: dict, schema: dict = None) -> None:
        """
        Validate an entity against a schema.
        If the entity is valid, then return True, otherwise, False.
        If the schema isn't passed, get it from Schema service.

        :param entity: A manifest's entity.
        :param schema: The schema to validate an entity against.
        """
        if not isinstance(entity, dict):
            raise EntitySchemaValidationError(entity, "Entity must be type of dict.")

        if not entity.get("kind"):
            raise EntitySchemaValidationError(entity, "Kind field is absent")

        if not schema:
            schema = self.get_schema(entity["kind"])
            if not schema:
                logger.warning(f"{entity['kind']} is not present in Schema service.")
                raise EntitySchemaValidationError(entity, "Kind is not present in Schema service")

        try:
            schema = self._add_surrogate_keys_to_patterns(schema)
            self._validate_against_schema(schema, entity)
            logger.debug(f"Record successfully validated")
        except exceptions.ValidationError as exc:
            logger.error("Schema validation error. Data field.")
            logger.error(f"Manifest kind: {entity['kind']}")
            logger.error(f"Error: {exc}")
            raise EntitySchemaValidationError(entity, "Entity doesn't pass the schema validation.")

    def _validate_against_schema(self, schema: dict, data: Any):
        """
        Validate any data against schema. If the data is not valid, raises ValidationError.

        :param schema: The schema to validate an entity against.
        :param data: Any data to validate against schema.
        :return:
        """
        resolver = OSDURefResolver(
            schema_service=self.schema_service,
            base_uri=schema.get("$id", ""),
            referrer=schema,
            handlers=self.resolver_handlers,
            cache_remote=True
        )
        jsonschema.validate(
            schema=schema,
            instance=data,
            resolver=resolver,
            format_checker=FormatChecker(
                formats=("date-time", "time", "date")
            )
        )

    @staticmethod
    def get_manifest_kind(manifest: dict) -> str:
        """
        Utility method to extract kind value
        Raises GenericManifestSchemaError exception in case of absent `kind` property

        :param manifest: Manifest data
        :return: Manifest's kind
        """
        try:
            return manifest["kind"]
        except KeyError:
            raise GenericManifestSchemaError("There is no kind in the Manifest.")

    def validate_common_schema(self, manifest: dict) -> dict:
        """
        This is a preliminary validation of a manifest that verifies that a manifest corresponds
        the OSDU schemes at the highest level.
        This validation skips verifying each concrete entity by removing references to their schemas.
        :param manifest:
        :return: Manifest schema
        """
        kind = self.get_manifest_kind(manifest)
        schema = self.get_schema(kind)
        if not schema:
            raise GenericManifestSchemaError(
                f"There is no schema for Manifest kind {kind}")

        schema_without_refs = copy.deepcopy(schema)
        if schema_without_refs.get("properties"):
            self._clear_data_fields(schema_without_refs["properties"])
        else:
            self._clear_data_fields(schema_without_refs)
        logger.debug("Schema without refs")
        logger.debug(f"{schema_without_refs}")

        try:
            self._validate_against_schema(schema_without_refs, manifest)
        except jsonschema.ValidationError as err:
            raise GenericManifestSchemaError(f"Manifest failed generic schema validation.\n {err}")

        return schema

    def _validate_work_product(self, entity: dict) -> dict:
        """
        Validate a single entity. If the entity is valid, then return it,.

        :param entity: A single entity
        :return: Entity or empty dict.
        """
        try:
            self._validate_entity(entity)
        except EntitySchemaValidationError as error:
            logger.warning(f"Resource with kind {entity.get('kind')} was rejected")
        return entity

    def _validate_manifest_section(self, manifest_section: List[dict]) -> Tuple[
        List[dict], List[dict]]:
        """
        Validate each entity in the Manifest's section.
        If an entity is valid, add to the list of valid entities.

        :param manifest_section: A Manifest section (e.g. ReferenceData, Data.WorkProductComponents etc.)
        :return: List of valid entities
        """
        valid_entities = []
        skipped_entities = []
        for entity in manifest_section:
            try:
                self._validate_entity(entity)
            except EntitySchemaValidationError as error:
                skipped_entities.append(error.skipped_entity)
            else:
                valid_entities.append(entity)
        return valid_entities, skipped_entities

    def validate_manifest(
        self,
        manifest_records: List[ManifestEntity]
    ) -> Tuple[List[ManifestEntity], List[dict]]:
        """
        Validate manifest's entities one-by-one. Return list of
        :param manifest_records: List of manifest's records
        :return: List of entities passed the validation
        """
        validated_records = []
        skipped_entities = []
        for manifest_record in manifest_records:
            entity = manifest_record.entity_data
            try:
                self._validate_entity(entity)
            except EntitySchemaValidationError as error:
                skipped_entities.append(error.skipped_entity)
            else:
                validated_records.append(manifest_record)
        return validated_records, skipped_entities

    def ensure_manifest_validity(self, manifest: dict) -> Tuple[dict, List[dict]]:
        """
        Validate manifest entities inside manifest and return only valid entities with saved structure

        """
        skipped_entities = []
        for data_type in (REFERENCE_DATA_SECTION, MASTER_DATA_SECTION):
            if manifest.get(data_type):
                valid_entities, not_valid_entities = self._validate_manifest_section(
                    manifest[data_type]
                )
                manifest[data_type] = valid_entities
                skipped_entities.extend(not_valid_entities)

        if manifest.get(DATA_SECTION):
            if manifest[DATA_SECTION].get(WORK_PRODUCT_SECTION):
                try:
                    self._validate_work_product(manifest[DATA_SECTION][WORK_PRODUCT_SECTION])
                except EntitySchemaValidationError as error:
                    manifest[DATA_SECTION][WORK_PRODUCT_SECTION] = {}
                    skipped_entities.append(error.skipped_entity)

            for data_type in (WORK_PRODUCT_COMPONENTS_SECTION, DATASETS_SECTION):
                if manifest[DATA_SECTION].get(data_type):
                    valid_entities, not_valid_entities = self._validate_manifest_section(
                        manifest[DATA_SECTION][data_type]
                    )
                    manifest[DATA_SECTION][data_type] = valid_entities
                    skipped_entities.extend(not_valid_entities)

        return manifest, skipped_entities
