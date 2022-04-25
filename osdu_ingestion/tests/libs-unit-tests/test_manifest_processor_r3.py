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
import json
import os
import sys



from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.handle_file import FileHandler
from osdu_ingestion.libs.source_file_check import SourceFileChecker
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.linearize_manifest import ManifestEntity
from osdu_ingestion.libs.exceptions import EmptyManifestError
import pytest
import requests

import mock_providers
from file_paths import (
    MANIFEST_WELLBORE_VALID_PATH,
    MANIFEST_EMPTY_PATH,
    MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
    RECORD_WELLBORE_VALID_PATH,
    RECORD_SEISMIC_TRACE_DATA_VALID_PATH,
    TRAVERSAL_WELLBORE_VALID_PATH, TRAVERSAL_MANIFEST_EMPTY_PATH, TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH)
from osdu_ingestion.libs import process_manifest_r3

TENANT = "opendes"


class TestManifestProcessor:

    @staticmethod
    def monkeypatch_storage_response(
        monkeypatch,
        response_content: bytes = b"{\"recordIds\": [\"test\"]}"
    ):
        """
        Make storage service request return mock response.
        """

        def mockresponse(url, data=None, **kwargs):
            response = requests.Response()
            response.status_code = http.HTTPStatus.OK
            response._content = response_content
            return response

        monkeypatch.setattr(requests, "put", mockresponse)

    @staticmethod
    def monkeypatch_storage_response_error(monkeypatch, error_status: http.HTTPStatus):
        """
        Make storage request return HTTPError response.
        """

        def mockresponse(url, data=None, **kwargs):
            response = requests.Response()
            response.status_code = error_status
            response._content = b"{\"recordIds\": [\"test\"]}"
            return response

        monkeypatch.setattr(requests, "put", mockresponse)

    @pytest.fixture()
    def manifest_records(self, traversal_manifest_file: str) -> list:
        with open(traversal_manifest_file) as f:
            manifest_file = json.load(f)
        return manifest_file

    @pytest.fixture(autouse=True)
    def manifest_processor(self, monkeypatch, traversal_manifest_file, conf_path: str):
        with open(conf_path) as f:
            conf = json.load(f)
        with open(traversal_manifest_file) as f:
            manifest_file = json.load(f)
        manifest_records = manifest_file
        context = Context.populate(conf["execution_context"])
        token_refresher = BaseTokenRefresher()
        file_handler = FileHandler("test", token_refresher, context)
        source_file_checker = SourceFileChecker()
        manifest_processor = process_manifest_r3.ManifestProcessor(
            storage_url="",
            token_refresher=token_refresher,
            context=context,
            file_handler=file_handler,
            source_file_checker=source_file_checker,
        )

        monkeypatch.setattr(file_handler, "upload_file",
                            lambda *args, **kwargs: "/test/source_file")
        monkeypatch.setattr(file_handler, "save_file_record",
                            lambda *args, **kwars: "test_file_record_id")
        monkeypatch.setattr(file_handler, "get_file_staging_location",
                            lambda *args, **kwargs: "gs://staging/test/source_file")
        monkeypatch.setattr(file_handler, "get_file_permanent_location",
                            lambda *args, **kwargs: "gs://permanent/test/source_file")
        monkeypatch.setattr(source_file_checker, "does_file_exist",
                            lambda *args, **kwargs: None)
        return manifest_processor

    @pytest.fixture()
    def mock_records_list(self, records_file_path: str):
        """
        Mock records list from Storage service taken from file.
        """
        with open(records_file_path) as f:
            return json.load(f)

    @pytest.mark.parametrize(
        "conf_path,traversal_manifest_file,records_file_path",
        [
            pytest.param(
                MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
                TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH,
                RECORD_SEISMIC_TRACE_DATA_VALID_PATH,
                id="Valid WorkProduct"
            ),
        ]
    )
    def test_save_record(
        self,
        monkeypatch,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        manifest_records,
        mock_records_list: list,
        traversal_manifest_file: str,
        conf_path: str,
        records_file_path: str
    ):
        self.monkeypatch_storage_response(monkeypatch)
        manifest_processor.save_record_to_storage({}, records_file_path)

    @pytest.mark.parametrize(
        "conf_path,traversal_manifest_file",
        [
            pytest.param(MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
                         TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH)
        ]
    )
    def test_save_record_invalid_storage_response_value(
        self,
        monkeypatch,
        manifest_records,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        traversal_manifest_file: str,
        conf_path: str
    ):
        self.monkeypatch_storage_response(monkeypatch, b"{}")
        with pytest.raises(ValueError):
            manifest_processor.save_record_to_storage({}, [{}])

    @pytest.mark.parametrize(
        "conf_path,traversal_manifest_file",
        [
            pytest.param(MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
                         TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH,
                         id="Valid WorkProduct")
        ]
    )
    def test_save_record_storage_response_http_error(
        self,
        monkeypatch,
        manifest_records,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        traversal_manifest_file: str,
        conf_path: str
    ):
        self.monkeypatch_storage_response_error(monkeypatch, http.HTTPStatus.INTERNAL_SERVER_ERROR)
        with pytest.raises(requests.HTTPError):
            manifest_processor.save_record_to_storage({}, conf_path)

    @pytest.mark.parametrize(
        "conf_path,traversal_manifest_file",
        [
            pytest.param(MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
                         TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH,
                         id="WorkProduct"),
            pytest.param(MANIFEST_WELLBORE_VALID_PATH,
                         TRAVERSAL_WELLBORE_VALID_PATH,
                         id="Master"),
        ]
    )
    def test_process_manifest_valid(
        self,
        monkeypatch,
        manifest_records,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        traversal_manifest_file: str,
        conf_path: str
    ):
        self.monkeypatch_storage_response(monkeypatch)
        manifest_file = [ManifestEntity(**e) for e in manifest_records]
        manifest_processor.process_manifest_records(manifest_file)

    @pytest.mark.parametrize(
        "conf_path,traversal_manifest_file",
        [
            pytest.param(MANIFEST_EMPTY_PATH, TRAVERSAL_MANIFEST_EMPTY_PATH, id="Empty Manifest"),
        ]
    )
    def test_process_empty_manifest(
        self,
        monkeypatch,
        manifest_records,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        traversal_manifest_file: str,
        conf_path: str
    ):
        self.monkeypatch_storage_response(monkeypatch)
        with pytest.raises(EmptyManifestError):
            manifest_processor.process_manifest_records(manifest_records)

    @pytest.mark.parametrize(
        "conf_path,expected_kind_name,traversal_manifest_file",
        [
            pytest.param(MANIFEST_WELLBORE_VALID_PATH, "TestMaster", TRAVERSAL_WELLBORE_VALID_PATH, id="Valid Wellbore"),
        ]
    )
    def test_get_kind(
        self,
        monkeypatch,
        manifest_processor: process_manifest_r3.ManifestProcessor,
        manifest_records: list,
        conf_path: str,
        traversal_manifest_file: str,
        expected_kind_name: str
    ):
        for manifest_part in manifest_records:
            kind = manifest_part["entity_data"]["kind"]
            assert expected_kind_name == manifest_processor._get_kind_name(kind)
