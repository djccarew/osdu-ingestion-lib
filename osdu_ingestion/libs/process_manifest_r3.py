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

"""Provides Manifest Processor."""

import json
import logging
from typing import List

import requests
import tenacity
from osdu_api.auth.authorization import TokenRefresher, authorize

from osdu_ingestion.libs.constants import RETRIES, WAIT
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import EmptyManifestError
from osdu_ingestion.libs.handle_file import FileHandler
from osdu_ingestion.libs.linearize_manifest import ManifestEntity
from osdu_ingestion.libs.mixins import HeadersMixin
from osdu_ingestion.libs.source_file_check import SourceFileChecker
from osdu_ingestion.libs.utils import is_surrogate_key

RETRY_SETTINGS = {
    "stop": tenacity.stop_after_attempt(RETRIES),
    "wait": tenacity.wait_fixed(WAIT),
    "reraise": True
}
logger = logging.getLogger()

RETRIES = 3
TIMEOUT = 1


class ManifestProcessor(HeadersMixin):
    """Class to process WP, Master and Reference data."""

    def __init__(
        self,
        storage_url: str,
        file_handler: FileHandler,
        source_file_checker: SourceFileChecker,
        token_refresher: TokenRefresher,
        context: Context
    ):
        """Manifest processor.

        :param file_handler: An instance of a file handler
        :type file_handler: FileHandler
        :param source_file_checker: An instance of file checker
        :type source_file_checker: SourceFileChecker
        :param storage_url: The OSDU Storage base url
        :type storage_url: str
        :param context: The tenant context
        :type context: Context
        :param token_refresher: An instance of token refresher
        :type token_refresher: TokenRefresher
        """
        super().__init__(context)
        self.file_handler = file_handler
        self.source_file_checker = source_file_checker
        self.storage_url = storage_url
        self.context = context
        self.token_refresher = token_refresher

    @staticmethod
    def _get_kind_name(kind: str) -> str:
        """Get and return kind name. Ex., osdu:osdu:Well:1.0.0 -> Well."""
        kind_name = kind.split(":")[2]
        return kind_name

    def upload_source_file(self, file_record: dict) -> dict:
        """Upload files from preloadfile path.

        :param file_record: The file record
        :type file_record: dict
        :return: file record updated if file was properly uploaded
        :rtype: dict
        """
        file_path = file_record["data"]["DatasetProperties"]["FileSourceInfo"]["PreloadFilePath"]
        try:
            file_source = self.file_handler.upload_file(file_path)
            file_record["data"]["DatasetProperties"]["FileSourceInfo"]["FileSource"] = file_source
        except Exception as e:
            logger.error(f"Unhandled exception while uploading {file_path}: {e}")
        return file_record

    def _delete_surrogate_key(self, entity: dict) -> dict:
        if is_surrogate_key(entity.get("id", "")):
            del entity["id"]
        return entity

    @staticmethod
    def _validate_storage_response(response_dict: dict):
        """Validate Storage service response."""
        if not (
            isinstance(response_dict, dict) and
            isinstance(response_dict.get("recordIds"), list)
        ):
            raise ValueError(f"Invalid answer from Storage server: {response_dict}")

    @tenacity.retry(**RETRY_SETTINGS)
    @authorize()
    def save_record_to_storage(self, headers: dict, request_data: List[dict]) -> requests.Response:
        """
        Send request to record storage API.
        """
        request_data = json.dumps(request_data)
        logger.info("Sending records to Storage service")
        logger.debug(f"{request_data}")
        response = requests.put(self.storage_url, request_data, headers=headers)
        if response.ok:
            response_dict = response.json()
            self._validate_storage_response(response_dict)
            record_ids = ", ".join(map(str, response_dict["recordIds"]))
            logger.debug(f"Response: {response_dict}")
            logger.info(f"Records '{record_ids}' were saved using Storage service.")
        else:
            reason = response.text[:250]
            logger.error(f"Request error.")
            logger.error(f"Response status: {response.status_code}. "
                         f"Response content: {reason}.")
        return response

    def save_record_to_file_service(self, file_records: List[dict]) -> List[str]:
        """
        Send request to file service API
        """
        file_record_ids = []
        for file_record in file_records:
            # TODO(python-team) implement concurrent request in File Handler service.
            record_id = self.file_handler.save_file_record(file_record)
            file_location = self.file_handler.get_file_permanent_location(record_id)
            # TODO(python-team) implement rollback strategy in case file validation fails.
            self.source_file_checker.does_file_exist(file_location)
            file_record_ids.append(record_id)
        return file_record_ids

    def process_work_product_files(self, file_records: List[dict]) -> List[dict]:
        """
        Process list of file records.
        """
        records = []
        for file_record in file_records:
            if not file_record["data"]["DatasetProperties"]["FileSourceInfo"]["FileSource"]:
                file_record = self.upload_source_file(file_record)
            else:
                file_source = file_record["data"]["DatasetProperties"]["FileSourceInfo"][
                    "FileSource"]
                file_location = self.file_handler.get_file_staging_location(file_source)
                self.source_file_checker.does_file_exist(file_location)

            record = self._delete_surrogate_key(file_record)
            records.append(record)
        return records

    def process_manifest_records(self, manifest_records: List[ManifestEntity]) -> List[str]:
        """Process manifests and save them into Storage service.

        :manifest_records: List of ManifestEntities to be ingested.
        :raises EmptyManifestError: When manifest is empty
        :return: List of ids of saved records
        :rtype: List[str]
        """
        record_ids = []
        populated_manifest_records = []
        if not manifest_records:
            raise EmptyManifestError
        for manifest_record in manifest_records:
            populated_manifest_records.append(
                self._delete_surrogate_key(manifest_record.entity_data))
        save_manifests_response = self.save_record_to_storage(
            self.request_headers, request_data=populated_manifest_records)
        record_ids.extend(save_manifests_response.json()["recordIds"])

        return record_ids
