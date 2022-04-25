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
"""Module for validation of WorkProduct, WorkProductComponents and Datasets."""

import functools
import logging
from typing import Any, Dict, Iterable, List, Set, Tuple

from osdu_ingestion.libs.search_client import SearchClient
from osdu_ingestion.libs.utils import create_skipped_entity_info
from osdu_ingestion.libs.validation.validate_file_source import \
    FileSourceValidator

logger = logging.getLogger(__name__)


class DataIntegrityValidator:
    """Provides functions to validate Manifest["Data"]."""

    def __init__(self, search_client: SearchClient, file_source_validator: FileSourceValidator):
        """Initialize validator with dependencies."""
        super().__init__()
        self._search_client = search_client
        self._file_source_validator = file_source_validator

    @staticmethod
    def _collect_ids_from_object_array(object_array: Iterable[Dict[str, Any]]) -> Set[str]:
        """Collects ids from an object array."""
        ids_set = set(map(lambda obj: obj.get("id"), object_array))
        ids_set.discard(None)
        return ids_set

    @staticmethod
    def _create_search_ids_query_str(ids_list) -> str:
        """Create an Apache Lucene compliant query."""
        ids_list_str = " OR ".join(f"\"{_id}\"" for _id in ids_list)
        query = f"id:({ids_list_str})"
        logger.debug(query)
        return query

    def _search_for_entities(self, ids_list: Iterable[str]) -> Iterable[str]:
        """Returns entities ids found in OSDU system."""
        query_str = self._create_search_ids_query_str(ids_list)
        all_kinds = "*:*:*:*"
        search_response = self._search_client.query_records(kind=all_kinds,
                                                            query_str=query_str,
                                                            limit=len(ids_list),
                                                            returned_fields=["id"])
        return [result.get("id") for result in search_response.results]

    def _update_ids_from_search(self, expected_ids_set, all_ids_set):
        """Updates all_ids_set with a query to OSDU system."""
        ids_to_search = list(filter(lambda _id: "surrogate" not in _id, expected_ids_set))
        if ids_to_search:
            logger.debug(f"ids_to_search {ids_to_search}")
            ids_found = self._search_for_entities(ids_to_search)
            logger.debug(f"ids_found: {ids_found}")
            all_ids_set.update(ids_found)

    def _remove_redundant_colon(self, ids: Iterable[str]) -> Iterable[str]:
        """
        Remove symbol ':' from ids without versions
        """
        cleaned_ids = []
        for elem in ids:
            if elem.endswith(":"):
                cleaned_ids.append(elem[:-1])
            else:
                cleaned_ids.append(elem)
        return set(cleaned_ids)

    def _validate_wpcs_to_datasets(
        self, work_product_components: Iterable[dict],
        datasets: Iterable[dict]) -> Tuple[Iterable[dict], Iterable[dict], List[dict]]:
        """Validate that all Datasets referenced from any WorkProductComponent
        exist and validate there are no orphan Datasets.

        :param work_product_components: A list of WorkProductComponents
        :type work_product_components: Iterable[dict]
        :param datasets: A list of Datasets
        :type datasets: Iterable[dict]
        :return: A tuple containing (valid_work_product_components, valid_datasets)
        :rtype: Tuple[Iterable[dict], Iterable[dict], List[dict]]
        """
        skipped_entities = []
        all_datasets_ids = self._collect_ids_from_object_array(datasets)
        all_expected_datasets_ids = set(
            functools.reduce(lambda a, b: a + b,
                             (wpc["data"]["Datasets"] for wpc in work_product_components)))
        self._update_ids_from_search(all_expected_datasets_ids, all_datasets_ids)

        all_valid_datasets_ids = set()
        filtered_wpcs = []
        for wpc in work_product_components:
            expected_datasets_ids = set(wpc["data"]["Datasets"])
            expected_datasets_ids = self._remove_redundant_colon(expected_datasets_ids)
            logger.debug(f"Expected datasets ids: {expected_datasets_ids}")
            valid_datasets_ids = expected_datasets_ids.intersection(all_datasets_ids)
            all_valid_datasets_ids.update(valid_datasets_ids)
            diffs = expected_datasets_ids.symmetric_difference(valid_datasets_ids)
            if not diffs:
                filtered_wpcs.append(wpc)
            else:
                wpc_id = wpc.get("id")
                logger.error(f"Rejecting WorkProductComponent with id: {wpc_id}.\n"
                             f"Reason: following datasets ids don't match: {diffs}")
                skipped_entities.append(
                    create_skipped_entity_info(wpc, f"The following datasets are missing: {diffs}")
                )

        filtered_datasets = []
        for dataset in datasets:
            dataset_id = dataset.get("id")
            if dataset_id in all_valid_datasets_ids:
                filtered_datasets.append(dataset)
            else:
                logger.error(f"Rejecting orphan dataset with id: {dataset_id}")
                skipped_entities.append(
                    create_skipped_entity_info(dataset, "It is orphaned.")
                )

        return filtered_wpcs, filtered_datasets, skipped_entities

    def _validate_wp_to_wpcs(
        self,
        work_product: Dict[str, Any],
        work_product_components: Iterable[dict]
    ) -> Tuple[Dict[str, Any], List[dict]]:
        """Validate all WorkProductComponents referenced from WorkProduct exist.

        :param work_product: The WorkProduct metadata object
        :type work_product: Dict[str, Any]
        :param work_product_components: A list of WorkProductComponents
        :type work_product_components: Iterable[dict]
        :return: Validated WorkProduct or empty if invalid.
        :rtype: Tuple[Dict[str, Any], List[dict]]
        """
        skipped_entities = []
        if not work_product:
            return {}, []
        all_wpcs_ids = self._collect_ids_from_object_array(work_product_components)
        expected_wpc_ids = set(work_product["data"]["Components"])
        expected_wpc_ids = self._remove_redundant_colon(expected_wpc_ids)
        self._update_ids_from_search(expected_wpc_ids, all_wpcs_ids)
        diffs = expected_wpc_ids.symmetric_difference(all_wpcs_ids)
        if not diffs:
            return work_product, skipped_entities
        else:
            logger.error(f"Rejecting WorkProduct and all its entities: WPC and Datasets.\n"
                         f"Reason: following work_product_components ids are inconsistent: {diffs}")
            skipped_entities.append(
                create_skipped_entity_info(work_product, f"The WP misses: {diffs}")
            )
            return {}, skipped_entities

    def _validate_manifest_data_datasets(
        self,
        manifest_data: Dict[str, Any]
    ) -> Tuple[List[dict], List[dict]]:
        """Delegate call to FileSource validator to validate datasets.

        :param manifest_data: `Data` fragment in Manifest 1.0.0
        :type manifest_data: Dict[str, Any]
        :return: List of valid datasets and list of skipped ones
        """
        manifest_data_datasets = manifest_data.get("Datasets")
        if not manifest_data_datasets:
            logger.debug("No datasets found. Skipping validation.")
            return [], []
        valid_datasets, skipped_datasets = \
            self._file_source_validator.filter_valid_datasets(manifest_data_datasets)
        return valid_datasets, skipped_datasets

    def validate_manifest_data_integrity(self, manifest: Dict[str, Any]) -> Tuple[dict, List[dict]]:
        """Validate `Data` field in Manifest.

        :param manifest: Manifest 1.0.0
        :type manifest: Dict[str: Any]
        """
        manifest_data = manifest.get("Data")
        skipped_entities = []
        if not manifest_data:
            logger.debug("No Data found, skipping validation")
            return manifest, []

        valid_datasets, not_valid_datasets = self._validate_manifest_data_datasets(manifest_data)
        manifest_data["Datasets"] = valid_datasets
        skipped_entities.extend(not_valid_datasets)

        if manifest_data.get("WorkProductComponents") and manifest_data.get("Datasets"):
            valid_wpcs, valid_datasets, not_valid_entities = self._validate_wpcs_to_datasets(
                manifest_data["WorkProductComponents"], manifest_data["Datasets"])
            skipped_entities.extend(not_valid_entities)
            valid_wp, not_valid_wp = \
                self._validate_wp_to_wpcs(manifest_data["WorkProduct"], valid_wpcs)
            skipped_entities.extend(not_valid_wp)

            if valid_wp:
                manifest_data["WorkProduct"] = valid_wp
                manifest_data["WorkProductComponents"] = valid_wpcs
                manifest_data["Datasets"] = valid_datasets
            else:
                manifest["Data"] = {}
        else:
            manifest["Data"] = {}
        return manifest, skipped_entities
