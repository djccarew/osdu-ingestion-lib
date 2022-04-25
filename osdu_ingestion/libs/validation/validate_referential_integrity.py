#  Copyright 2021 Google LLC
#  Copyright 2021 EPAM Systems
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

import logging
from typing import Any, Dict, Generator, Iterable, List, Set, Tuple

from osdu_ingestion.libs.constants import (DATA_SECTION, DATASETS_SECTION,
                                           SEARCH_ID_BATCH_SIZE,
                                           WORK_PRODUCT_COMPONENTS_SECTION)
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import (EmptyManifestError,
                                            ValidationIntegrityError)
from osdu_ingestion.libs.linearize_manifest import ManifestLinearizer
from osdu_ingestion.libs.manifest_analyzer import ManifestAnalyzer
from osdu_ingestion.libs.search_record_ids import ExtendedSearchId
from osdu_ingestion.libs.utils import (EntityId, create_skipped_entity_info,
                                       remove_trailing_colon, split_id,
                                       split_into_batches)
from osdu_ingestion.libs.validation.validate_file_source import \
    FileSourceValidator

logger = logging.getLogger()


class ManifestIntegrity:
    """Class to validate if parents reference and master data are exists and
    remove non-valid entities to provide integrity
    """

    def __init__(
        self,
        search_url: str,
        token_refresher,
        file_source_validator: FileSourceValidator,
        context: Context,
        whitelist_ref_patterns: str = None,
        search_id_batch_size: int = SEARCH_ID_BATCH_SIZE,

    ):
        self.search_url = search_url
        self.token_refresher = token_refresher
        self.file_source_validator = file_source_validator
        self.context = context
        self.search_id_batch_size = search_id_batch_size
        self.whitelist_ref_patterns = whitelist_ref_patterns
        super().__init__()

    def _filter_not_found_ids(
        self,
        external_references: Iterable[EntityId],
        found_ids: Set[str]
    ) -> Set[EntityId]:
        """
        Filter not found ids.

        :param external_references: External entity's references to be found in OSDU.
        :param found_ids: Set of found bare IDs and IDs with versions by ExtendedSearchId in OSDU.
        :return: Set of not found ids.
        """
        not_found_ids = set()

        for entity_id in external_references:
            # As found_ids contains ids with versions and bare ids, and if entity_id is an id
            # with no version (refers to the last version), we use just the bare id.
            entity_srn = entity_id.srn if entity_id.version else entity_id.id
            if entity_srn not in found_ids:
                not_found_ids.add(entity_id)

        return not_found_ids

    def _find_missing_external_ids(self, external_references: List[EntityId]) -> Set[str]:
        """
        Find absent external references in the system and searchable

        :param external_references: Records IDs are supposed to be found in Search.
        :return: Set of not found references via Search.
        """
        missing_ids = set()
        for ids_batch in split_into_batches(external_references, self.search_id_batch_size):
            # Search can't work with ids with versions. So get only ids without versions.
            external_references_without_version = [e.id for e in ids_batch]

            # TODO: Move ExtendedSearchId() to the class attribute.
            #  Refactor ExtendedSearchId().search_records() to take records to search
            search_handler = ExtendedSearchId(self.search_url, external_references_without_version,
                                              self.token_refresher, self.context)
            found_ids = search_handler.search_records()
            missing_ids.update(self._filter_not_found_ids(ids_batch, found_ids))

        return {missing_id.srn for missing_id in missing_ids}

    def _ensure_wpc_artefacts_integrity(self, wpc: dict):
        artefacts = wpc["data"].get("Artefacts")
        if not artefacts:
            logger.debug(
                f"WPC: {wpc.get('id')} doesn't have Artefacts field. Mark it as valid.")
            return
        artefacts_resource_ids = set(artefact["ResourceID"] for artefact in artefacts)
        datasets = set(wpc["data"].get(DATASETS_SECTION, []))
        duplicated_ids = artefacts_resource_ids.intersection(datasets)
        if duplicated_ids:
            logger.warning(
                f"Resource kind '{wpc.get('kind')}' and id '{wpc.get('id', '')}' was rejected. "
                f"The WPC's Artefacts field contains the same ids as in "
                f"the WPC's 'Datasets': {duplicated_ids}."
            )
            raise ValidationIntegrityError(wpc,
                                           reason=f"It has duplicated "
                                                  f"Datasets and Artefacts: {duplicated_ids}.")

    def _ensure_artefacts_integrity(self, work_product_components: list) -> Tuple[
        List[dict], List[dict]]:
        """
        Delete a WPC entity if it didn't passed artefacts integrity check.

        :param work_product_components:
        :return: List of valid wpcs.
        """
        valid_work_product_components = []
        skipped_ids = []
        for wpc in work_product_components:
            try:
                self._ensure_wpc_artefacts_integrity(wpc)
            except ValidationIntegrityError as error:
                skipped_ids.append(error.skipped_entity)
            else:
                valid_work_product_components.append(wpc)
        return valid_work_product_components, skipped_ids

    def _validate_datasets_file_sources(
        self,
        manifest_datasets: Dict[str, Any]
    ) -> Tuple[List[dict], List[dict]]:
        """Delegate call to FileSource validator to validate datasets.

        :param manifest_data: `Data` fragment in Manifest 1.0.0
        :type manifest_data: Dict[str, Any]
        :return: List of valid datasets and list of skipped ones
        """
        if not manifest_datasets:
            logger.debug("No datasets found. Skipping validation.")
            return [], []
        valid_datasets, skipped_datasets = \
            self.file_source_validator.filter_valid_datasets(manifest_datasets)
        return valid_datasets, skipped_datasets

    def _mark_dependant_entities_invalid(
        self,
        manifest_analyzer: ManifestAnalyzer,
        missing_external_ids: Set[str]
    ):
        """
        Mark entities dependant on missing external ids as invalid.

        :param manifest_analyzer: Manifest Analyzer
        :param missing_external_ids: Missing external ids
        :return:
        """
        for missing_id in missing_external_ids:
            missing_id = remove_trailing_colon(missing_id)
            missing_entity = manifest_analyzer.external_entity_id_node_table[missing_id]
            manifest_analyzer.add_invalid_node(missing_entity)

    def _ensure_external_references_integrity(self, manifest_analyzer: ManifestAnalyzer):
        """
        Collect all the external ids from Manifest Analyzer.
        Spilt this id list into batches.
        Check if these external ids are in OSDU. If they are not there mark entities
        dependant on them as invalid.

        :param manifest_analyzer: Manifest analyzer containing the Manifest as a tree
        """
        missing_external_ids = set()

        external_references_entity_id = [entity_node.entity_id for entity_node in
                               manifest_analyzer.external_entity_id_node_table.values()]
        if external_references_entity_id:
            missing_external_ids.update(self._find_missing_external_ids(external_references_entity_id))

        if missing_external_ids:
            self._mark_dependant_entities_invalid(manifest_analyzer, missing_external_ids)

    def _ensure_manifest_integrity(
        self,
        manifest,
        previously_skipped_entities_srns: Set[str]
    ) -> Tuple[dict, List[dict]]:
        """
        Create dependency graph using ManifestAnalyzer.
        Check if all entities has valid parent entities.
        Omit inconsistent records.

        :param manifest: Manifest
        :param previously_skipped_entities_srns: Skipped entities
        :return: Manifest, skipped entities
        """
        skipped_entities = []

        manifest_traversal = ManifestLinearizer()
        linearized_manifest = manifest_traversal.linearize_manifest(manifest)
        manifest_analyzer = ManifestAnalyzer(linearized_manifest, previously_skipped_entities_srns, self.whitelist_ref_patterns)

        self._ensure_external_references_integrity(manifest_analyzer)

        for entity_node in manifest_analyzer.invalid_entity_nodes:
            skipped_entities.append(
                create_skipped_entity_info(entity_node.data, f"Missing parents: {entity_node.invalid_parents}")
            )

        manifest = manifest_traversal.assemble_manifest(
            manifest_analyzer.valid_entities_info,
            manifest["kind"]
        )

        return manifest, skipped_entities

    def ensure_integrity(
        self,
        manifest: dict = None,
        previously_skipped_entities: List[dict] = None
    ) -> Tuple[dict, List[dict]]:

        """
        Check Manifest's integrity

        :param manifest: Manifest
        :param previously_skipped_entities: Skipped ids in previous step
        :return: Manifest, skipped_entities
        """

        skipped_entities = []
        previously_skipped_entities = previously_skipped_entities or []

        if manifest.get(DATA_SECTION):
            if manifest[DATA_SECTION].get(DATASETS_SECTION):
                datasets = manifest[DATA_SECTION].get(DATASETS_SECTION)
                valid_entities, not_valid_entities = self._validate_datasets_file_sources(datasets)
                manifest[DATA_SECTION][DATASETS_SECTION] = valid_entities
                skipped_entities.extend(not_valid_entities)

            if manifest[DATA_SECTION].get(WORK_PRODUCT_COMPONENTS_SECTION):
                work_product_components = manifest[DATA_SECTION][WORK_PRODUCT_COMPONENTS_SECTION]
                valid_entities, not_valid_entities = self._ensure_artefacts_integrity(
                    work_product_components
                )
                manifest[DATA_SECTION][WORK_PRODUCT_COMPONENTS_SECTION] = valid_entities
                skipped_entities.extend(not_valid_entities)

        skipped_entities_srns = {srn["id"] for srn in skipped_entities if srn.get("id")}
        skipped_entities_srns.update(
            {srn["id"] for srn in previously_skipped_entities if srn.get("id")})

        manifest, missing_entities = self._ensure_manifest_integrity(
            manifest,
            skipped_entities_srns
        )
        skipped_entities.extend(missing_entities)

        return manifest, skipped_entities
