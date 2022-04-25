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

import dataclasses
import logging
from typing import List

from osdu_ingestion.libs.constants import (DATA_SECTION, DATASETS_SECTION,
                                           MASTER_DATA_SECTION,
                                           REFERENCE_DATA_SECTION,
                                           WORK_PRODUCT_COMPONENTS_SECTION,
                                           WORK_PRODUCT_SECTION)
from osdu_ingestion.libs.exceptions import EmptyManifestError

logger = logging.getLogger()


@dataclasses.dataclass()
class ManifestEntity:
    """
    This a dataclass class to represent entities of linearized Manifest

    Args:
        entity_data: Content of entity
        manifest_path: Path to the entity inside the manifest.
                       E.g. 'ReferenceData' or 'Data.WorkProduct'
    """
    entity_data: dict
    manifest_path: str

    def __eq__(self, other: "ManifestEntity"):
        return self.entity_data == other.entity_data \
               and self.manifest_path == other.manifest_path


class ManifestLinearizer:
    """Class to linearize manifest and extract all manifest records"""

    def _populate_manifest_entity(self, entity_data: dict, manifest_path: str):
        """
        Populate manifest entity for future processing

        :param entity_data: manifest entity instance (for future processing)
        :param manifest_path: corresponding generic schema (for future schema validation)
        :return:
        """
        return ManifestEntity(entity_data=entity_data, manifest_path=manifest_path)

    def _traverse_list(
        self,
        manifest_entities: List[dict],
        manifest_path: str
    ) -> List[ManifestEntity]:
        """
        Traverse list of entities and returned populated list of entities
        """
        entities = []
        for manifest_entity in manifest_entities:
            entities.append(
                self._populate_manifest_entity(manifest_entity, manifest_path)
            )
        return entities

    def linearize_manifest(self, manifest: dict) -> List[ManifestEntity]:
        """
        Traverse manifest structure and return the list of manifest records.

        :param manifest: Manifest
        :return: list of records
        """
        if not manifest:
            raise EmptyManifestError

        manifest_entities = []

        for section in (REFERENCE_DATA_SECTION, MASTER_DATA_SECTION):
            if manifest.get(section):
                manifest_entities.extend(
                    self._traverse_list(manifest[section], section)
                )

        if manifest.get(DATA_SECTION):

            if manifest[DATA_SECTION].get(WORK_PRODUCT_SECTION):
                manifest_entities.append(
                    self._populate_manifest_entity(
                        manifest[DATA_SECTION][WORK_PRODUCT_SECTION],
                        f"{DATA_SECTION}.{WORK_PRODUCT_SECTION}"
                    )
                )

            for section in (WORK_PRODUCT_COMPONENTS_SECTION, DATASETS_SECTION):
                if manifest[DATA_SECTION].get(section):
                    manifest_entities.extend(
                        self._traverse_list(
                            manifest[DATA_SECTION][section],
                            f"{DATA_SECTION}.{section}",
                        )
                    )

        return manifest_entities

    def assemble_manifest(self, linearized_manifest: List[ManifestEntity],
                          manifest_kind: str = None) -> dict:
        """
        Assemble Manifest from previously linearized one.


        :param linearized_manifest:
        :param manifest_kind:
        :return:
        """
        manifest = {
            REFERENCE_DATA_SECTION: [],
            MASTER_DATA_SECTION: [],
            DATA_SECTION: {
                DATASETS_SECTION: [],
                WORK_PRODUCT_COMPONENTS_SECTION: [],
                WORK_PRODUCT_SECTION: {}
            }
        }
        if manifest_kind:
            manifest["kind"] = manifest_kind

        for entity_info in linearized_manifest:
            manifest_path = entity_info.manifest_path.split(".")

            if len(manifest_path) == 1:
                manifest[manifest_path[0]].append(entity_info.entity_data)

            elif len(manifest_path) == 2:
                data_section, subsection = manifest_path
                if subsection == WORK_PRODUCT_SECTION:
                    manifest[data_section][subsection] = entity_info.entity_data
                else:
                    manifest[data_section][subsection].append(entity_info.entity_data)

            else:
                raise ValueError

        return manifest
