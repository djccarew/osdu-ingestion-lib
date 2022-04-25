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

import http
import json

import pytest
import responses

from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.search_client import SearchClient
from mock_providers import get_test_credentials


class TestSearchClient:

    BASE_TEST_URL = "http://search_service_url/query"
    PARTITION_ID = "test_partition_id"

    @pytest.fixture
    def search_client(self):
        context = Context(data_partition_id=self.PARTITION_ID, app_key="")
        search_client = SearchClient(self.BASE_TEST_URL,
                                     BaseTokenRefresher(get_test_credentials()), context)
        return search_client

    @pytest.mark.parametrize("kind, query_str, limit, results, total_count", [
        pytest.param("*:*:*:*", "some_query", 20, [], 10),
        pytest.param("opendes:osdu:File:1.0.0", "id:(test1 OR test2)", 10, [{}, {}], 5)
    ])
    @responses.activate
    def test_query_record_with_defaults(self, search_client, kind: str, query_str: str, limit: int,
                                        results: list, total_count: int):

        responses.add(responses.POST,
                      f"{self.BASE_TEST_URL}",
                      json={
                          "results": results,
                          "aggregations": None,
                          "totalCount": total_count
                      },
                      status=http.HTTPStatus.OK)

        search_response = search_client.query_records(kind, query_str, limit)

        expected_body = {
            "kind": kind,
            "query": query_str,
            "limit": limit,
            "offset": 0,
        }

        assert expected_body == json.loads(responses.calls[0].request.body)
        assert results == search_response.results
        assert total_count == search_response.total_count
