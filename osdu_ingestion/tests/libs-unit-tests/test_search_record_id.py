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
import json
import http
import requests
import pytest



from mock_providers import get_test_credentials
from file_paths import (
    SEARCH_INVALID_RESPONSE_PATH,
    SEARCH_VALID_RESPONSE_PATH,
    SEARCH_VALID_OFFSET_RESPONSE_PATH,
    SEARCH_EXTRACTED_IDS_PATH)
from utils import chunks
from osdu_ingestion.libs.exceptions import RecordsNotSearchableError
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from tenacity import stop_after_attempt
from osdu_ingestion.libs.search_record_ids import SearchId, ExtendedSearchId
from mock_responses import MockSearchResponse, MockSearchResponseForRecords


class TestManifestProcessor:

    def mock_storage_response(
        self,
        monkeypatch,
        body_path: str,
        status_code: http.HTTPStatus = http.HTTPStatus.OK,
        total_count: int = 0
    ):
        def mock_response(*args, **kwargs):
            return MockSearchResponse(body_path, status_code, total_count)

        monkeypatch.setattr(requests, "post", mock_response)
        # turn of retry for unit tests
        SearchId.search_files.retry.stop = stop_after_attempt(1)

    def mock_storage_response_with_chunks(
        self,
        monkeypatch,
        body_path: str,
        status_code: http.HTTPStatus = http.HTTPStatus.OK,
        total_count: int = None
    ):
        def response_generator():
            for records in chunks(body["results"], 20):
                yield MockSearchResponseForRecords(records, status_code=status_code, total_count=total_count)

        with open(body_path, "r") as f:
            body = json.load(f)
            total_count = total_count or body["totalCount"]

        responses = response_generator()

        def mock_response(*args, **kwargs):
            try:
                return next(responses)
            except StopIteration:
                return MockSearchResponseForRecords([], status_code=status_code, total_count=total_count, cursor=cursor)


        monkeypatch.setattr(requests, "post", mock_response)
        # turn of retry for unit tests
        SearchId.search_files.retry.stop = stop_after_attempt(1)

    @pytest.mark.parametrize(
        "record_ids,search_response_path",
        [
            pytest.param(
                ["test"],
                SEARCH_VALID_RESPONSE_PATH
            ),
            pytest.param(
                ["test", "test", "test"],
                SEARCH_VALID_RESPONSE_PATH
            )
        ]
    )
    def test_search_found_all_records(self, monkeypatch, record_ids: list,
                                      search_response_path: str):
        self.mock_storage_response(monkeypatch, search_response_path, total_count=len(record_ids))
        id_searcher = SearchId("http://test", record_ids,
                               BaseTokenRefresher(get_test_credentials()),
                               Context(app_key="", data_partition_id=""))
        id_searcher.check_records_searchable()

    @pytest.mark.parametrize(
        "record_ids,search_response_path",
        [
            pytest.param(
                ["test"],
                SEARCH_VALID_RESPONSE_PATH
            ),
            pytest.param(
                ["test", "test", "test"],
                SEARCH_VALID_RESPONSE_PATH
            )
        ]
    )
    def test_search_not_found_all_records(self, monkeypatch, record_ids: list,
                                          search_response_path: str):
        invalid_total_count = len(record_ids) - 1
        self.mock_storage_response(monkeypatch, search_response_path,
                                   total_count=invalid_total_count)
        id_searcher = SearchId("", record_ids, BaseTokenRefresher(get_test_credentials()),
                               Context(app_key="", data_partition_id=""))
        with pytest.raises(RecordsNotSearchableError):
            id_searcher.check_records_searchable()

    @pytest.mark.parametrize(
        "record_ids,search_response_path",
        [
            pytest.param(
                ["test"],
                SEARCH_INVALID_RESPONSE_PATH
            ),
            pytest.param(
                ["test", "test", "test"],
                SEARCH_INVALID_RESPONSE_PATH
            )
        ]
    )
    def test_search_got_wrong_response_value(self, monkeypatch, record_ids: list,
                                             search_response_path: str):
        self.mock_storage_response(monkeypatch, search_response_path)
        id_searcher = SearchId("http://test", record_ids,
                               BaseTokenRefresher(get_test_credentials()),
                               Context(app_key="", data_partition_id=""))
        with pytest.raises(ValueError):
            id_searcher.check_records_searchable()

    @pytest.mark.parametrize(
        "record_ids,search_response_path",
        [
            pytest.param(
                [],
                SEARCH_INVALID_RESPONSE_PATH
            )
        ]
    )
    def test_searcher_got_no_record_ids(self, monkeypatch, record_ids: list,
                                        search_response_path: str):
        self.mock_storage_response(monkeypatch, search_response_path)
        with pytest.raises(ValueError):
            SearchId("http://test", record_ids, BaseTokenRefresher(get_test_credentials()),
                     Context(app_key="", data_partition_id=""))

    @pytest.mark.parametrize(
        "record_ids,search_response_path,extracted_ids_path",
        [
            pytest.param(
                ["test"],
                SEARCH_VALID_RESPONSE_PATH,
                SEARCH_EXTRACTED_IDS_PATH
            )
        ]
    )
    def test_search_found_all_records(self, monkeypatch, record_ids: list,
                                      search_response_path: str,
                                      extracted_ids_path: str):
        self.mock_storage_response(monkeypatch, search_response_path, total_count=len(record_ids))
        with open(search_response_path) as f:
            response = json.load(f)
        id_searcher = ExtendedSearchId("http://test", record_ids,
                                       BaseTokenRefresher(get_test_credentials()),
                                       Context(app_key="", data_partition_id=""))
        record_ids = id_searcher._extract_id_from_response(response)
        with open(extracted_ids_path) as f:
            extracted_ids = json.load(f)
        assert set(record_ids) == set(extracted_ids)


    @pytest.mark.parametrize(
        "record_ids,search_response_path",
        [
            pytest.param(
                ["test"],
                SEARCH_VALID_OFFSET_RESPONSE_PATH
            )
        ]
    )
    def test_search_found_all_records_with_cursor(self, monkeypatch, record_ids: list,
                                      search_response_path: str):

        expected_length = 80
        self.mock_storage_response_with_chunks(monkeypatch, search_response_path)

        id_searcher = ExtendedSearchId("http://test", record_ids,
                                       BaseTokenRefresher(get_test_credentials()),
                                       Context(app_key="", data_partition_id=""),
                                       limit=20)
        record_ids = id_searcher.search_records()

        assert len(record_ids) == expected_length
