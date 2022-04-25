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
"""Module for validation of File and FileCollection before ingesting."""

import logging
from typing import List, Tuple

from osdu_ingestion.libs.exceptions import DatasetValidationError

logger = logging.getLogger(__name__)


class DatasetType:
    FILE = ":dataset--File."
    FILE_COLLECTION = ":dataset--FileCollection."
    EDS_FILE = ":dataset--ConnectedSource."


class FileSourceValidator:
    """Validates FileSource or IndexFilePath according to the provided type."""

    def _validate_file_source_info(self, file_source_info: dict) -> bool:
        """Validates file source info is populated correctly.

        :param file_source_info: An instance of AbstractFileSourceInfo 1.0.0
        :type file_source_info: dict
        :return: True if validation succeed or field was populated.
        :rtype: bool
        """
        if file_source_info["FileSource"].strip():
            return True
        else:
            return False

    def _validate_eds_file_source_info(self, file_source_info: dict) -> bool:
        """Validates file source info is populated correctly.
        :param file_source_info: An instance of AbstractFileSourceInfo 1.0.0
        :type file_source_info: dict
        :return: True if validation succeed or field was populated.
        :rtype: bool
        """
        if file_source_info["SourceRecordID"].strip():
            return True
        else:
            return False

    def _validate_eds_file_record(self, file_record: dict) -> bool:
        """Validate file source info in file record.
        :param file_record: File record metadata
        :type file_record: dict
        :return: True if file record has FileSource info, False otherwise
        :rtype: bool
        """
        return self._validate_eds_file_source_info(
            file_record["data"]["DatasetProperties"])

    def _validate_file_record(self, file_record: dict) -> bool:
        """Validate file source info in file record.

        :param file_record: File record metadata
        :type file_record: dict
        :return: True if file record has FileSource info, False otherwise
        :rtype: bool
        """
        return self._validate_file_source_info(
            file_record["data"]["DatasetProperties"]["FileSourceInfo"])

    def _validate_file_collection_record(self, file_collection_record: dict) -> bool:
        """Validate file source info in file collection record

        :param file_collection_record: FileCollection record metadata
        :type file_collection_record: dict
        :return: True if file collection record has IndexFilePath info or all
            FileSourceInfo from inner elements, False otherwise
        :rtype: bool
        """
        index_file_path = file_collection_record["data"]["DatasetProperties"].get("IndexFilePath")
        if index_file_path:
            return True
        else:
            file_source_infos = []
            for file_source_info in file_collection_record["data"]["DatasetProperties"].get(
                    "FileSourceInfos", []):
                file_source_infos.append(self._validate_file_source_info(file_source_info))
            return bool(file_source_infos) and all(file_source_infos)

    def _validate_dataset(self, dataset: dict) -> dict:
        """
        :param dataset: A dataset to be validated
        :return: Dataset
        """
        is_file = DatasetType.FILE in dataset.get("kind", "")
        is_file_collection = DatasetType.FILE_COLLECTION in dataset.get("kind", "")
        is_eds_file = DatasetType.EDS_FILE in dataset.get("kind", "")
        is_valid_dataset = False

        if is_file:
            try:
                is_valid_dataset = self._validate_file_record(dataset)
            except KeyError as exc:
                logger.error(
                    f"Rejecting invalid dataset: {dataset.get('id')}, invalid structure. KeyError: {exc}"
                )
                raise DatasetValidationError(dataset, f"Invalid structure. KeyError: {exc}"[:128])
        elif is_eds_file:
            try:
                is_valid_dataset = self._validate_eds_file_record(dataset)
            except KeyError as exc:
                logger.error(
                    f"Rejecting invalid eds dataset: {dataset.get('id')}, invalid structure. KeyError: {exc}"
                )
                raise DatasetValidationError(dataset, f"Invalid structure. KeyError: {exc}"[:128])
        elif is_file_collection:
            try:
                is_valid_dataset = self._validate_file_collection_record(dataset)
            except KeyError as exc:
                logger.error(
                    f"Rejecting invalid dataset: {dataset.get('id')}, "
                    f"invalid structure. KeyError: {exc}"[:128]
                )
                raise DatasetValidationError(dataset, f"Invalid structure. KeyError: {exc}"[:128])
        else:
            logger.error(f"Unknown file type: {dataset.get('kind')}.")

        if is_valid_dataset:
            return dataset
        else:
            logger.error(
                f"Rejecting dataset: {dataset.get('id')}. Reason: No FileSource info found.")
            raise DatasetValidationError(dataset, f"No FileSource info found.")

    def filter_valid_datasets(self, datasets: List[dict]) -> Tuple[List[dict], List[dict]]:
        """Filter only valid (which contains FileSource info) datasets

        :param datasets: A list of {File, FileCollection} datasets
        :type datasets: List[dict]
        :return: The filtered list of valid {File, FileCollection} datasets
        :rtype: List[dict]
        """
        valid_datasets = []
        skipped_entities = []
        for dataset in datasets:
            try:
                self._validate_dataset(dataset)
            except DatasetValidationError as error:
                skipped_entities.append(error.skipped_entity)
            else:
                valid_datasets.append(dataset)
        return valid_datasets, skipped_entities
