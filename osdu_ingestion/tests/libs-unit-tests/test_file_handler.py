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
import io
import json
import os
import sys



from osdu_ingestion.libs.exceptions import InvalidFileRecordData
import pytest
import requests
import responses
import tenacity

from mock_providers import get_test_credentials

from file_paths import RECORD_SEISMIC_TRACE_DATA_VALID_PATH
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.handle_file import FileDownloadUrlResponse, FileUploadUrlResponse, FileHandler


class TestFileHandler:

    BASE_TEST_HOST = "http://file_service_url"
    PARTITION_ID = "test_partition_id"

    @pytest.fixture()
    def file_handler(self, monkeypatch):
        context = Context(data_partition_id=self.PARTITION_ID, app_key="")
        file_handler = FileHandler(self.BASE_TEST_HOST,
                                   BaseTokenRefresher(get_test_credentials()),
                                   context)
        monkeypatch.setattr(
                file_handler,
                "_get_upload_signed_url",
                lambda *args, **kwargs: FileUploadUrlResponse(
                        "test_id", "test_signed_url", "test_file_source"))
        monkeypatch.setattr(
                file_handler,
                "_upload_file_request",
                lambda *args, **kwargs: None)
        return file_handler

    @responses.activate
    def test_get_file_staging_location(self, file_handler: FileHandler):
        test_staging_location = "gs://staging/test/file_id"
        responses.add(responses.POST, f"{self.BASE_TEST_HOST}/getFileLocation",
                      json={"Location": test_staging_location}, status=http.HTTPStatus.OK)

        assert test_staging_location == file_handler.get_file_staging_location("/test/file_id")
        assert responses.calls[0].request.body == json.dumps({"FileID": "file_id"})

    @pytest.mark.parametrize(
        "http_status, reason",
        [
            pytest.param(http.HTTPStatus.NOT_FOUND, "Not Found."),
        ]
    )
    @responses.activate
    def test_get_file_staging_location_error(self, file_handler: FileHandler,
                                                 http_status: str, reason: str):
        responses.add(responses.POST, f"{self.BASE_TEST_HOST}/getFileLocation",
                      status=http_status, body=reason)

        with pytest.raises((tenacity.RetryError, requests.exceptions.HTTPError)):
            file_handler.get_file_staging_location("/test/file_id")

    @responses.activate
    def test_get_file_permanent_location(self, file_handler: FileHandler):
        test_record_id = "test_record_id"
        test_permanent_location = "gs://permanent/test/file_id"
        json_response = {
            "signedUrl": "test_signed",
            "unsignedUrl": test_permanent_location,
            "kind": "test_kind"
        }
        responses.add(responses.GET, f"{self.BASE_TEST_HOST}/v2/files/{test_record_id}/downloadURL",
                      json=json_response, status=http.HTTPStatus.OK)

        assert test_permanent_location == file_handler.get_file_permanent_location(test_record_id)

    @pytest.mark.parametrize(
        "http_status, reason",
        [
            pytest.param(http.HTTPStatus.NOT_FOUND, "Not Found."),
        ]
    )
    @responses.activate
    def test_get_file_permanent_location_error(self, file_handler: FileHandler,
                                               http_status: str, reason: str):
        test_record_id = "test_record_id"
        responses.add(responses.GET, f"{self.BASE_TEST_HOST}/v2/files/{test_record_id}/downloadURL",
                      status=http_status, body=reason)

        with pytest.raises((tenacity.RetryError, requests.exceptions.HTTPError)):
            file_handler.get_file_permanent_location(test_record_id)

    @pytest.mark.parametrize(
        "wp_records_file_path",
        [
            RECORD_SEISMIC_TRACE_DATA_VALID_PATH,
        ]
    )
    @responses.activate
    def test_save_file_record(self, file_handler: FileHandler, wp_records_file_path: str):
        with open(wp_records_file_path) as cf:
            file_record, unused_wpc_record, unused_wp_record = json.load(cf)

        test_record_id = "test_record_id"
        responses.add(responses.POST, f"{self.BASE_TEST_HOST}/v2/files/metadata",
                      json={"id": test_record_id}, status=http.HTTPStatus.OK)

        assert test_record_id == file_handler.save_file_record(file_record)

    @pytest.mark.parametrize(
        "wp_records_file_path",
        [
            RECORD_SEISMIC_TRACE_DATA_VALID_PATH,
        ]
    )
    def test_save_file_record_raises(self, file_handler: FileHandler, wp_records_file_path: str):
        with open(wp_records_file_path) as cf:
            file_record, unused_wpc_record, unused_wp_record = json.load(cf)

        file_record["data"]["DatasetProperties"]["FileSourceInfo"].pop("FileSource")

        with pytest.raises(InvalidFileRecordData):
            file_handler.save_file_record(file_record)
