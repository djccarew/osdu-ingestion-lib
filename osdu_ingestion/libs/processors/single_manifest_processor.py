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


"""
R3 Process Single Manifest helper.
"""

import logging
from typing import Iterator, List, Set, Tuple

from osdu_ingestion.libs.constants import (FIRST_STORED_RECORD_INDEX,
                                           SAVE_RECORDS_BATCH_SIZE)
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import (ProcessRecordBatchError,
                                            ProcessRecordError)
from osdu_ingestion.libs.linearize_manifest import ManifestLinearizer
from osdu_ingestion.libs.manifest_analyzer import EntityNode, ManifestAnalyzer
from osdu_ingestion.libs.process_manifest_r3 import ManifestProcessor
from osdu_ingestion.libs.refresh_token import TokenRefresher
from osdu_ingestion.libs.utils import (create_skipped_entity_info,
                                       is_surrogate_key, split_into_batches)
from osdu_ingestion.libs.validation.validate_referential_integrity import \
    ManifestIntegrity
from osdu_ingestion.libs.validation.validate_schema import SchemaValidator

logger = logging.getLogger()


class SingleManifestProcessor:

    def __init__(
        self,
        storage_url: str,
        payload_context: Context,
        referential_integrity_validator: ManifestIntegrity,
        manifest_processor: ManifestProcessor,
        schema_validator: SchemaValidator,
        token_refresher: TokenRefresher,
        batch_save_enabled: bool = False,
        save_records_batch_size: int = SAVE_RECORDS_BATCH_SIZE
    ):
        """Init SingleManifestProcessor."""
        super().__init__()
        self.storage_url = storage_url
        self.payload_context = payload_context
        self.referential_integrity_validator = referential_integrity_validator
        self.manifest_processor = manifest_processor
        self.schema_validator = schema_validator
        self.token_refresher = token_refresher
        self.batch_save_enabled = batch_save_enabled
        self.save_records_batch_size = save_records_batch_size

    def _process_single_entity_node(self, manifest_analyzer: ManifestAnalyzer, entity_node: EntityNode):
        """
        Process single entity node. Try to save the entity's data in Storage service. 
        Replace surrogate keys of the entity and its children with the system generated one.

        :param manifest_analyzer: Object with proper queue of entities.
        :param entity_node: Entity node to be processed.
        :return: Saved record id.
        """
        try:
            logger.debug(f"Process entity {entity_node}")
            entity_node.replace_parents_surrogate_srns()
            record_id = self.manifest_processor.process_manifest_records(
                [entity_node.entity_info]
            )[FIRST_STORED_RECORD_INDEX]
            entity_node.system_srn = record_id
        except Exception as error:
            logger.warning(f"Can't process entity {entity_node}")
            manifest_analyzer.add_invalid_node(entity_node)
            raise ProcessRecordError(entity_node.entity_info.entity_data, f"{error}"[:128])
        return record_id

    def _process_entity_nodes_batch(
        self, 
        manifest_analyzer: ManifestAnalyzer, 
        entity_node_batch: List[EntityNode]   
    ) -> Tuple[List[str], List[dict]]:
        """
        Try to process batch of EntityNodes by saving their data in Storage Service.

        At the current implementation of Storage Service 
        the whole batch isn't saved in Storage Service if one or more entities are invalid.


        :param manifest_analyzer: Object with proper queue of entities.
        :param :
        :return: List of saved record ids. 
        """
        record_ids = []

        try:
            manifest_entities = [entity_node.entity_info for entity_node in entity_node_batch]
            record_ids.extend(self.manifest_processor.process_manifest_records(manifest_entities))
        except Exception as e:
            # TODO: Fix skipping saving the whole batch in Storage Service if some records in this batch are invalid.
            logger.warning(f"Can't process batch {entity_node_batch}. {str(e)[:128]}")
            for entity_node in entity_node_batch:
                manifest_analyzer.add_invalid_node(entity_node)

            raise ProcessRecordBatchError([node.data for node in entity_node_batch], f"{e}"[:128])

        return record_ids

    def _process_records_by_one(self, manifest_analyzer: ManifestAnalyzer) -> Tuple[List[str], List[dict]]:
        """
        Process each entity from entity queue created according to child-parent relationships
        between entities.
        Replace surrogate-keys of parents inside child entities with system-generated keys.

        :param manifest_analyzer: Object with proper queue of entities
        :return: List of saved ids and skipped ones.
        """
        record_ids = []
        skipped_ids = []
        for entity_node in manifest_analyzer.entity_queue():
            try:
                record_ids.append(self._process_single_entity_node(manifest_analyzer, entity_node))
            except ProcessRecordError as error:
                skipped_ids.append(error.skipped_entity)
        return record_ids, skipped_ids

    def _split_ids_by_type(
        self, 
        entity_node_batch: List[EntityNode]
    ) -> Tuple[List[EntityNode], List[EntityNode]]:
        """
        Split entity node batch into two lists with surrogate keys, and real ids.

        :param entity_node_batch: Batch of entity node
        :return: Two lists of surrogate-key entities and not-surrogate-key entities.
        """
        surrogate_key_id_nodes = []
        not_surrugate_key_id_nodes = []
        for entity_node in entity_node_batch:
            entity_node.replace_parents_surrogate_srns()
            if is_surrogate_key(entity_node.data.get("id", "")):
                surrogate_key_id_nodes.append(entity_node)
            else:
                not_surrugate_key_id_nodes.append(entity_node)
        return not_surrugate_key_id_nodes, surrogate_key_id_nodes

    def _save_entities_generation(
        self, 
        manifest_analyzer: ManifestAnalyzer, 
        entity_nodes_generation: Set[EntityNode]
    ) :
        """
        Save set of independent from each other entities in Storage Service by chunks.

        
        :param manifest_analyzer: Object with proper queue of entities.
        :param entity_nodes_generation: Set of independent from each other entity nodes.
        :return: List of saved ids and skipped ones.
        """
        record_ids = []
        skipped_ids = []
        for entity_node_batch in split_into_batches(entity_nodes_generation, self.save_records_batch_size):
            # surrogate-key entities and real-id entities must be treated in different ways.
            not_surrogate_key_nodes, surrogate_key_nodes = self._split_ids_by_type(entity_node_batch)

            if not_surrogate_key_nodes:
                try:
                    record_ids.extend(
                        self._process_entity_nodes_batch(manifest_analyzer, not_surrogate_key_nodes)
                    )
                except ProcessRecordBatchError as error:
                    skipped_ids.extend(error.skipped_entities)

            for entity_node in surrogate_key_nodes:
                try:
                    record_ids.append(self._process_single_entity_node(manifest_analyzer, entity_node))
                except ProcessRecordError as error:
                    skipped_ids.append(error.skipped_entity)

        return record_ids, skipped_ids

    def _process_records_by_batches(self, manifest_analyzer: ManifestAnalyzer) -> Tuple[List[str], List[dict]]:
        """
        Save batches of entities in Storage Service.
        
        :param manifest_analyzer: Object with proper queue of entities
        :return: List of saved ids and skipped ones.
        """
        record_ids = []
        skipped_ids = []
        for entity_nodes_generation in manifest_analyzer.entity_generation_queue():
            logger.info(f"Generation: {entity_nodes_generation}")
            generation_record_ids, generation_skipped_ids = self._save_entities_generation(manifest_analyzer, entity_nodes_generation)

            record_ids.extend(generation_record_ids)
            skipped_ids.extend(generation_skipped_ids)

        return record_ids, skipped_ids
            
    def process_manifest(self, manifest: dict, with_validation: bool) -> Tuple[
        List[str], List[dict]]:
        """Execute manifest validation then process it.

        Execution steps:
        1) validate referential manifest data integrity and remove invalid entities
        2) validate data integrity and prune to maintain dependency consistency
        3) initialize schema validator
        4) validate manifest file against common schema
        5) traverse manifest file and extract manifest entities
        6) validate extracted manifest entities
        7) create an ingestion queue according to child-parent relationships between entities
        8) process valid manifest entities one-by-one

        :param manifest: A single manifest
        :param with_validation: Flag for validation steps.
        :return: List of record ids and list of skipped entities.
        """
        skipped_ids = []

        if with_validation:
            manifest, not_valid_entities = \
                self.schema_validator.ensure_manifest_validity(manifest)

            manifest, orphaned_entities = \
                self.referential_integrity_validator.ensure_integrity(manifest)

            skipped_ids.extend(not_valid_entities)
            skipped_ids.extend(orphaned_entities)

        traversal = ManifestLinearizer()
        manifest_entities = traversal.linearize_manifest(manifest)

        manifest_analyzer = ManifestAnalyzer(
            manifest_entities,
            {entity["id"] for entity in skipped_ids if entity.get("id")}
        )

        if self.batch_save_enabled:
            record_ids, not_valid_ids = self._process_records_by_batches(manifest_analyzer)
        else:
            record_ids, not_valid_ids = self._process_records_by_one(manifest_analyzer)

        skipped_ids.extend(not_valid_ids)
        skipped_ids.extend(
            [create_skipped_entity_info(node.data, f"Missing parents {node.invalid_parents}")
             for node in manifest_analyzer.invalid_entity_nodes if node.invalid_parents]
        )

        logger.info(f"Processed ids {record_ids}")

        return record_ids, skipped_ids
