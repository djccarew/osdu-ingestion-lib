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

"""This module provides cloud specific File Handler implementations."""

import dataclasses
import io
import json
import logging
from typing import List, Tuple

import requests
import tenacity
from osdu_api.auth.authorization import TokenRefresher, authorize
from osdu_api.providers import blob_storage
from osdu_api.providers.types import BlobStorageClient, FileLikeObject

from osdu_ingestion.libs.constants import RETRIES, WAIT
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import InvalidFileRecordData
from osdu_ingestion.libs.mixins import HeadersMixin

logger = logging.getLogger()

RETRY_SETTINGS = {
    "stop": tenacity.stop_after_attempt(RETRIES),
    "wait": tenacity.wait_fixed(WAIT),
}


@dataclasses.dataclass
class FileUploadUrlResponse:
    """Simple class to store File service uploadURL response values."""
    file_id: str
    signed_url: str
    file_source: str


@dataclasses.dataclass
class FileDownloadUrlResponse:
    """Simple class to store File service downloadURL response values."""
    signed_url: str
    unsigned_url: str
    kind: str


class FileHandler(HeadersMixin):
    """Class to perform operations using OSDU File Service."""

    def __init__(self, file_service_host: str, token_refresher: TokenRefresher, context: Context,
                 blob_storage_client: BlobStorageClient = None):
        """File handler.

        :param file_service_host: Base OSDU File service url
        :type file_service_host: str
        :param token_refresher: Object to refresh tokens
        :type token_refresher: TokenRefresher
        :param context: The tenant context data
        :type context: Context
        """
        super().__init__(context)
        self._file_service_host = file_service_host
        self.token_refresher = token_refresher
        self._blob_storage_client = blob_storage_client or blob_storage.get_client()

    def _get_file_from_preload_path(self, preload_file_path: str,
                                    file: FileLikeObject) -> Tuple[FileLikeObject, str]:
        """Get file from a preloaded path.

        :param preload_file_path: Full URI of the file to obtain
        :type preload_file_path: str
        :return: Raw file data and content-type
        :rtype: Tuple[FileLikeObject, str]
        """
        return self._blob_storage_client.download_to_file(preload_file_path, file)

    @staticmethod
    def _verify_file_record_data(file_record_data: dict):
        """Perform simple verification of mandatory fields according to OSDU
        File Service.

        :param file_record_data: Data field of file_record
        :type file_record_data: dict
        :raises InvalidFileRecordData: When some of the mandatory fields is
            missing or empty
        """
        endian = file_record_data.get("Endian")
        file_source = file_record_data["DatasetProperties"]["FileSourceInfo"].get("FileSource")
        if not (endian and file_source):
            raise InvalidFileRecordData(f"Mandatory fields: Endian-{endian}"
                                        f"FileSource-{file_source}")

    @staticmethod
    def _handle_download_url_response(response: dict) -> FileDownloadUrlResponse:
        """
        Handle downloadURL according to file service version

        :param response: The response already load from json
        :type response: dict
        :return: FileDownloadUrlResponse filled properly
        :rtype: FileDownloadUrlResponse
        """
        try:
            # response got from latest version of File service
            return FileDownloadUrlResponse(signed_url=response["signedUrl"],
                                           unsigned_url=response["unsignedUrl"],
                                           kind=response["kind"])
        except KeyError:
            # response got from a legacy version of File service
            return FileDownloadUrlResponse(signed_url=response["SignedUrl"],
                                           unsigned_url=None,
                                           kind=None)

    @tenacity.retry(**RETRY_SETTINGS)
    @authorize()
    def _send_post_request(self, headers: dict, url: str, request_body: str) -> requests.Response:
        logger.debug(f"{request_body}")
        response = requests.post(url, request_body, headers=headers)
        logger.debug(response.content)
        return response

    @tenacity.retry(**RETRY_SETTINGS)
    @authorize()
    def _send_get_request(self, headers: dict, url: str) -> requests.Response:
        response = requests.get(url, headers=headers)
        logger.debug(response)
        return response

    def _get_upload_signed_url(self, headers: dict) -> FileUploadUrlResponse:
        """Get FileID, SignedURL and FileSource using File Service uploadURL
        endpoint.

        :param headers: Request headers to pass to the final request issuer
        :type headers: dict
        :return: FileUploadUrlResponse with data from service
        :rtype: FileUploadUrlResponse
        """
        logger.debug("Getting upload signed url.")
        endpoint = f"{self._file_service_host}/v2/files/uploadURL"
        response = self._send_get_request(headers, endpoint).json()
        logger.debug("Signed url got.")
        upload_url_response = FileUploadUrlResponse(file_id=response["FileID"],
                                                    signed_url=response["Location"]["SignedURL"],
                                                    file_source=response["Location"]["FileSource"])
        return upload_url_response

    def _get_download_signed_url(self, headers: dict, record_id: str) -> FileDownloadUrlResponse:
        """Get signedURL, unsignedURL and kind using File Service downloadURL
        endpoint.

        :param headers: Request headers to pass to the final request issuer
        :type headers: dict
        :param record_id: Unique id of the file record saved in the osdu system
        :type record_id: str
        :return: FileDownloadUrlResponse with signed and unsigned urls
        :rtype: FileDownloadUrlResponse
        """
        logger.debug("Getting download signed url.")
        endpoint = f"{self._file_service_host}/v2/files/{record_id}/downloadURL"
        response = self._send_get_request(headers, endpoint).json()
        logger.debug("Signed url got.")
        download_url_response = self._handle_download_url_response(response)
        return download_url_response

    @tenacity.retry(**RETRY_SETTINGS)
    def _upload_file_request(self, headers: dict, signed_url: str, buffer: FileLikeObject):
        """Upload file via File service using signed_url.

        :param headers: Request headers to pass to the final request issuer
        :type headers: dict
        :param signed_url: SignedURL to authenticate request
        :type signed_url: str
        :param buffer: Raw file data
        :type buffer: FileLikeObject
        """
        logger.debug("Uploading file.")
        buffer.seek(0)
        requests.put(signed_url, buffer.read(), headers=headers)
        logger.debug("File uploaded.")

    def _get_file_location_request(self, headers: dict, file_id: str) -> str:
        """Get file location using File Service.

        :param headers: Request headers to pass to the final request issuer
        :type headers: dict
        :param file_id: String identifier of the file
        :type file_id: str
        :return: Full URI of the located file
        :rtype: str
        """
        logger.debug("Getting file location.")
        request_body = json.dumps({"FileID": file_id})
        endpoint = f"{self._file_service_host}/getFileLocation"
        response = self._send_post_request(headers, endpoint, request_body)
        logger.debug("File location got.")
        return response.json()["Location"]

    def upload_file(self, preload_file_path: str) -> str:
        """Copy file from preload_file_path location to Landing Zone in OSDU
        platform using File service. Get Content-Type of this file, refresh
        Content-Type with this value in headers while this file is being
        uploaded onto OSDU platform.

        :param preload_file_path: The URI of the preloaded file
        :type preload_file_path: str
        :return: FileSource obtained via File service
        :rtype: str
        """
        with io.BytesIO() as buffer:
            buffer, content_type = self._get_file_from_preload_path(preload_file_path, buffer)
            upload_url_response = self._get_upload_signed_url(self.request_headers)

            headers = self.request_headers
            headers["Content-Type"] = content_type
            self._upload_file_request(headers, upload_url_response.signed_url, buffer)

        return upload_url_response.file_source

    def get_file_staging_location(self, file_source: str) -> str:
        """Retrieve location (full URI) of the file in staging area.

        :param file_source: The FileSource (relative URI) of the file of the form
            /{folder}/{file_id}
        :type file_source: str
        :return: Full URI of the location of the file in staging area
        :rtype: str
        """
        file_id = file_source.split("/")[-1]
        file_staging_location = self._get_file_location_request(self.request_headers, file_id)
        return file_staging_location

    def get_file_permanent_location(self, file_record_id: str) -> str:
        """Retrieve location (full URI) of the file in permanent area.

        :param file_record_id: The unique id of the file record (aka metadata
        :type file_record_id: str
        :return: Full URI of the location of the file in permanent area
        :rtype: str
        """
        download_url_response = self._get_download_signed_url(self.request_headers, file_record_id)
        permanent_location = download_url_response.unsigned_url
        return permanent_location

    def save_file_record(self, file_record: dict) -> str:
        """Send request to store record via file service API.

        :param file_record: The file record to save
        :type file_record: dict
        :return: OSDU system generated id of the saved record
        :rtype: str
        """
        self._verify_file_record_data(file_record["data"])
        # TODO fix 'name' field processing
        # Generate file entity name as workaround because file API required this field.
        if not file_record["data"].get("Name"):
            file_record["data"]["Name"] = \
                f"surrogate_name_{file_record['data']['DatasetProperties']['FileSourceInfo']['PreloadFilePath'].split('/')[-1]}"
            logger.info(f"Generated name: {file_record['data']['Name']}")
        logger.info("Sending file record metadata to File service")
        endpoint = f"{self._file_service_host}/v2/files/metadata"
        response = self._send_post_request(self.request_headers, endpoint, json.dumps(file_record))

        return response.json()["id"]

    def batch_save_file_records(self, file_records: List[str]) -> List[str]:
        """Perform concurrent save file record requests.

        :param file_records: List of file records to save
        :type file_records: List[str]
        :return: List of OSDU system generated ids of the saved records
        :rtype: List[str]
        """
        raise NotImplementedError("TODO(python-team) implementation.")
