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


import http
import requests
import json
import os
import sys

import jsonschema



from mock_providers import get_test_credentials
from file_paths import (
    DATA_PATH_PREFIX,
    FILE_GENERIC_WRONG_DATE_TIME,
    SCHEMA_FILE_VALID_PATH,
    SCHEMA_FILE_GENERIC,
    SCHEMA_GENERIC_MASTERDATA_PATH,
    SCHEMA_SEISMIC_TRACE_DATA_VALID_PATH,
    SCHEMA_WORK_PRODUCT_VALID_PATH,
    SCHEMA_WORK_PRODUCT,
    SCHEMA_WPC_DATA_QUALITY,
    SCHEMA_TEST_MASTERDATA_PATH,
    SURROGATE_WPC_DATA_QUALITY,
    SURROGATE_WORK_PRODUCT,
    MANIFEST_WELLBORE_VALID_PATH,
    MANIFEST_GENERIC_PATH,
    MANIFEST_NEW_GENERIC_SCHEMA_PATH,
    SCHEMA_WELLBORE_VALID_PATH,
    TRAVERSAL_WELLBORE_VALID_PATH,
)
from mock_responses import MockSchemaResponse
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.linearize_manifest import ManifestEntity
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.exceptions import EmptyManifestError, NotOSDUSchemaFormatError
import pytest

from osdu_ingestion.libs.validation.validate_schema import SchemaValidator

TENANT = "opendes"


class TestSchemaValidator:

    @pytest.fixture
    def schema_validator(
        self,
        monkeypatch,
        schema_file: str
    ):
        context = Context(app_key="", data_partition_id="")
        validator = SchemaValidator(
            "",
            BaseTokenRefresher(get_test_credentials()),
            context
        )
        if schema_file:
            monkeypatch.setattr(requests, "get",
                                lambda *args, **kwargs: MockSchemaResponse(schema_file))
        return validator

    @pytest.fixture
    def surrogate_fields_paths(self):
        return [
            ("definitions", "{{data-partition-id}}:wks:AbstractWPCGroupType:1.0.0", "properties",
             "Datasets",
             "items"),
            ("definitions", "osdu:wks:AbstractWPCGroupType:1.0.0", "properties", "Artefacts",
             "items", "properties", "ResourceID"),
            ("properties", "data", "allOf", 1, "properties", "Components", "items"),
        ]

    @staticmethod
    def mock_get_schema(uri: str):
        if "WorkProduct" in uri:
            schema_path = SCHEMA_WORK_PRODUCT_VALID_PATH
        elif "SeismicTraceData" in uri:
            schema_path = SCHEMA_SEISMIC_TRACE_DATA_VALID_PATH
        elif "File" in uri:
            schema_path = SCHEMA_FILE_VALID_PATH
        elif "GenericMasterData" in uri:
            schema_path = SCHEMA_GENERIC_MASTERDATA_PATH
        elif "TestMaster" in uri:
            schema_path = SCHEMA_TEST_MASTERDATA_PATH
        else:
            print(uri)
            raise Exception(f"Can't get such a schema {uri} in data files of tests")
        with open(schema_path) as f:
            schema_content = json.load(f)
        return schema_content

    @pytest.mark.parametrize(
        "traversal_manifest_file_path,schema_file",
        [
            pytest.param(
                TRAVERSAL_WELLBORE_VALID_PATH,
                None,
                id="Valid manifest_file"
            )
        ]
    )
    def test_schema_validator_master_manifest(
        self,
        monkeypatch,
        schema_validator,
        traversal_manifest_file_path: str,
        schema_file
    ):
        monkeypatch.setattr(schema_validator, "get_schema", self.mock_get_schema)
        with open(traversal_manifest_file_path) as f:
            manifest_file = json.load(f)

        manifest_file = [ManifestEntity(**e) for e in
                         manifest_file]
        validated_records, skipped_records = schema_validator.validate_manifest(manifest_file)
        assert len(manifest_file) == len(validated_records)

    @pytest.mark.parametrize(
        "traversal_manifest_file,schema_file",
        [
            pytest.param(
                f"{DATA_PATH_PREFIX}/invalid/TraversalNotOSDUFormatManifest.json",
                None,
                id="Not OSDU FORMAT"),
        ]
    )
    def test_schema_validator_not_osdu_format(self,
                                              monkeypatch,
                                              schema_validator: SchemaValidator,
                                              traversal_manifest_file: str,
                                              schema_file: str):
        with open(traversal_manifest_file) as f:
            manifest_file = json.load(f)
        manifest_file = [ManifestEntity(entity_data=e["entity"], manifest_path=e["schema"]) for e in
                         manifest_file]
        valid_entities, skipped_entities = schema_validator.validate_manifest(manifest_file)
        assert not valid_entities
        assert len(skipped_entities)

    @pytest.mark.parametrize(
        "manifest_file,traversal_manifest_file,schema_file,kind",
        [
            pytest.param(
                MANIFEST_WELLBORE_VALID_PATH,
                TRAVERSAL_WELLBORE_VALID_PATH,
                SCHEMA_WELLBORE_VALID_PATH,
                "opendes:osdu:Wellbore:0.3.0",
                id="Valid manifest Wellore"),
        ]
    )
    def test_get_schema_request(self,
                                schema_validator: SchemaValidator,
                                manifest_file: str,
                                traversal_manifest_file: str,
                                schema_file: str,
                                kind: str):
        schema_validator.get_schema_request(kind)

    @pytest.mark.parametrize(
        "manifest_file,traversal_manifest_file,schema_file,kind",
        [
            pytest.param(
                MANIFEST_WELLBORE_VALID_PATH,
                TRAVERSAL_WELLBORE_VALID_PATH,
                SCHEMA_WELLBORE_VALID_PATH,
                "opendes:osdu:Wellbore:0.3.0",
                id="Valid manifest Wellore"),
        ]
    )
    def test_get_schema_error(self,
                              monkeypatch,
                              schema_validator: SchemaValidator,
                              manifest_file: str,
                              traversal_manifest_file: str,
                              schema_file: str,
                              kind: str):
        monkeypatch.setattr(requests,
                            "get",
                            lambda *args, **kwargs: MockSchemaResponse("{}",
                                                                       http.HTTPStatus.INTERNAL_SERVER_ERROR))
        assert not schema_validator.get_schema(kind)

    @pytest.mark.parametrize(
        "manifest_file,schema_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                MANIFEST_NEW_GENERIC_SCHEMA_PATH,
                id="Valid generic manifest"),
        ]
    )
    def test_generic_manifest_validation(
        self,
        monkeypatch,
        schema_validator: SchemaValidator,
        manifest_file: str,
        schema_file
    ):
        def mock_get_schema(uri: str):
            with open(schema_file) as f:
                schema_content = json.load(f)
            return schema_content

        with open(manifest_file) as f:
            manifest_content = json.load(f)
        monkeypatch.setattr(schema_validator, "get_schema", mock_get_schema)
        schema_validator.validate_common_schema(manifest_content)

    @pytest.mark.parametrize(
        "manifest_file,schema_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                MANIFEST_NEW_GENERIC_SCHEMA_PATH,
                id="Valid generic manifest"),
        ]
    )
    def test_manifest_ensure_manifest_validity(
        self,
        monkeypatch,
        schema_validator: SchemaValidator,
        manifest_file: str,
        schema_file
    ):
        def mock_get_schema(uri: str):
            with open(schema_file) as f:
                schema_content = json.load(f)
            return schema_content

        with open(manifest_file) as f:
            manifest_content = json.load(f)
        monkeypatch.setattr(schema_validator, "get_schema", mock_get_schema)
        schema_validator.ensure_manifest_validity(manifest_content)

    @pytest.mark.parametrize(
        "manifest_file,schema_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                MANIFEST_NEW_GENERIC_SCHEMA_PATH,
                id="Valid generic manifest"),
        ]
    )
    def test_manifest_schema_not_present_ensure_validity(
        self,
        monkeypatch,
        schema_validator: SchemaValidator,
        manifest_file: str,
        schema_file
    ):
        def mock_get_schema(uri: str):
            return None

        with open(manifest_file) as f:
            manifest_content = json.load(f)
        monkeypatch.setattr(schema_validator, "get_schema", mock_get_schema)
        manifest, skipped_entities = schema_validator.ensure_manifest_validity(manifest_content)
        assert skipped_entities

    @pytest.mark.parametrize(
        "manifest_file,schema_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                MANIFEST_NEW_GENERIC_SCHEMA_PATH,
                id="Valid generic manifest"),
        ]
    )
    def test_manifest_entity_invalid_against_schema(
        self,
        monkeypatch,
        schema_validator: SchemaValidator,
        manifest_file: str,
        schema_file
    ):
        def mock_validate_against_schema(*args, **kwargs):
            raise jsonschema.exceptions.ValidationError("Something wrong")

        with open(manifest_file) as f:
            manifest_content = json.load(f)
        monkeypatch.setattr(schema_validator, "_validate_against_schema", mock_validate_against_schema)
        manifest, skipped_entities = schema_validator.ensure_manifest_validity(manifest_content)
        assert skipped_entities

    def test_delete_refs(self):
        context = Context(app_key="", data_partition_id="")
        validator = SchemaValidator(
            "",
            BaseTokenRefresher(get_test_credentials()),
            context
        )
        manifest = {
            'manifest': {'ReferenceData': [], 'MasterData': [], 'kind': 'osdu:wks:Manifest:1.0.0',
                         'Data': {}}}
        schema = {
            "x-osdu-license": "Copyright 2021, The Open Group \\nLicensed under the Apache License, Version 2.0 (the \"License\"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 . Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an \"AS IS\" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.",
            "$id": "https://schema.osdu.opengroup.org/json/manifest/Manifest.1.0.0.json",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "x-osdu-schema-source": "osdu:wks:Manifest:1.0.0", "title": "Load Manifest Schema",
            "description": "Load manifest applicable for all types defined as 'kind', i.e. registered as schemas with the Schema Service. It supports loading of individual 'records' of any group-type or combinations. The load sequence follows a well-defined sequence. The 'ReferenceData' array is processed first (if populated). The 'MasterData' array is processed second (if populated) second. The 'Data' structure is processed last (if populated). Inside the 'Data' property the 'Datasets' array is processed first, followed by the 'WorkProductComponents' array, the 'WorkProduct' is processed last. Any arrays are ordered. should there be interdependencies, the dependent items must be placed behind their relationship targets, e.g. a master-data Well record must placed in the 'MasterData' array before its Wellbores.",
            "type": "object", "properties": {"kind": {
                "description": "The schema identification for the manifest record following the pattern {Namespace}:{Source}:{Type}:{VersionMajor}.{VersionMinor}.{VersionPatch}. The versioning scheme follows the semantic versioning, https://semver.org/.",
                "title": "Manifest  Kind", "type": "string",
                "pattern": "^[\\w\\-\\.]+:[\\w\\-\\.]+:[\\w\\-\\.]+:[0-9]+.[0-9]+.[0-9]+$",
                "example": "osdu:wks:Manifest:1.0.0"}, "ReferenceData": {
                "description": "Reference-data are submitted as an array of records.",
                "type": "array", "items": {"$ref": "GenericReferenceData.1.0.0.json"}},
                "MasterData": {
                    "description": "Master-data are submitted as an array of records.",
                    "type": "array",
                    "items": {"$ref": "GenericMasterData.1.0.0.json"}},
                "Data": {
                    "description": "Manifest schema for work-product, work-product-component, dataset ensembles. The items in 'Datasets' are processed first since they are referenced by 'WorkProductComponents' ('data.DatasetIDs[]' and 'data.Artefacts[].ResourceID'). The WorkProduct is processed last collecting the WorkProductComponents.",
                    "type": "object", "properties": {"WorkProduct": {
                        "description": "The work-product component capturing the work-product-component records belonging to this loading/ingestion transaction.",
                        "$ref": "GenericWorkProduct.1.0.0.json"},
                        "WorkProductComponents": {
                            "description": "The list of work-product-components records. The record ids are internal surrogate keys enabling the association of work-product-component records with the work-product records.",
                            "type": "array",
                            "items": {
                                "$ref": "GenericWorkProductComponent.1.0.0.json"}},
                        "Datasets": {
                            "description": "The list of 'Datasets' or data containers holding the actual data. The record ids are usually internal surrogate keys enabling the association of dataset records with work-product-component records, namely via 'DatasetIDs' and 'Artefacts.ResourceID' (both referring to 'dataset' group-type entity types).",
                            "type": "array",
                            "items": {
                                "$ref": "GenericDataset.1.0.0.json"}}}}},
            "x-osdu-inheriting-from-kind": []}
        validator._clear_data_fields(schema)
        validator._validate_against_schema(schema, manifest)

    @pytest.mark.parametrize(
        "schema_file, manifest_file",
        [
            pytest.param(
                SCHEMA_WPC_DATA_QUALITY,
                SURROGATE_WPC_DATA_QUALITY,
                id="Extend with surrogate keys. WPC"
            ),
            pytest.param(
                SCHEMA_WORK_PRODUCT,
                SURROGATE_WORK_PRODUCT,
                id="Extend with surrogate keys. WP"
            ),
        ]
    )
    def test_extend_patterns_with_surrogate_keys(self, surrogate_fields_paths, schema_file: str,
                                                 manifest_file: str):
        with open(schema_file) as f:
            schema = json.load(f)
        with open(manifest_file) as f:
            manifest = json.load(f)

        context = Context(app_key="", data_partition_id="osdu")
        validator = SchemaValidator(
            "",
            BaseTokenRefresher(get_test_credentials()),
            context,
            surrogate_key_fields_paths=surrogate_fields_paths,
            data_types_with_surrogate_ids=("dataset", "work-product", "work-product-component")
        )
        schema = validator._add_surrogate_keys_to_patterns(schema)
        validator._validate_against_schema(schema, manifest)

    @pytest.mark.parametrize(
        "schema, data",
        [
            pytest.param(
                SCHEMA_FILE_GENERIC,
                FILE_GENERIC_WRONG_DATE_TIME,
                id="Wrong date-time"
            )
        ]
    )
    def test_validate_against_schema_raises_wrong_date_time_format(self, schema, data):
        with open(schema) as f:
            schema = json.load(f)
        with open(data) as f:
            data = json.load(f)
        context = Context(app_key="", data_partition_id="")
        schema_validator = SchemaValidator(
            "",
            BaseTokenRefresher(get_test_credentials()),
            context
        )
        with pytest.raises(jsonschema.exceptions.ValidationError) as err:
            schema_validator._validate_against_schema(schema, data)
        assert "is not a \'date-time\'" in str(err)
