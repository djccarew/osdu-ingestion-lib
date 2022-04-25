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
"""OSDU Search client."""

import dataclasses
import json
import logging

import requests
import tenacity
from osdu_api.auth.authorization import TokenRefresher, authorize

from osdu_ingestion.libs.constants import RETRIES, WAIT
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.mixins import HeadersMixin

logger = logging.getLogger(__name__)

TIMEOUT = 60  # seconds to wait for OSDU API response
TENACITY_RETRY_SETTINGS = {
    "stop": tenacity.stop_after_attempt(RETRIES),
    "wait": tenacity.wait_fixed(WAIT),
    "reraise": True,
}


@dataclasses.dataclass
class SearchResponse:
    """Simple class to store search results."""
    results: list
    total_count: int


class SearchClient(HeadersMixin):
    """OSDU Search Client."""

    def __init__(self, search_url: str, token_refresher: TokenRefresher, context: Context):
        """Initialize Search Client.

        :param search_url: The base search url
            (Please note that airflow var points already to the endpoint /query)
        :type search_url: str
        :param token_refresher: An instance of TokenRefresher
        :type token_refresher: TokenRefresher
        :param context: Tenant context
        :type context: Context
        """
        super().__init__(context)
        self.search_url = search_url
        self.token_refresher = token_refresher

    @tenacity.retry(**TENACITY_RETRY_SETTINGS)
    @authorize()
    def _send_post_request(self, headers: dict, url: str, request_body: str) -> requests.Response:
        logger.debug(request_body)
        response = requests.post(url, request_body, headers=headers, timeout=TIMEOUT)
        logger.debug(response.content)
        return response

    def _create_query_request_body(self,
                                   kind: str,
                                   query_str: str,
                                   limit: int,
                                   offset: int = 0,
                                   returned_fields: list = None,
                                   filter_opt: dict = None) -> str:
        """Create request body to send to Search service."""
        request_body = {
            "kind": kind,
            "query": query_str,
            "limit": limit,
            "offset": offset,
        }
        if returned_fields:
            request_body.update({"returnedFields": returned_fields})
        if filter_opt:
            request_body.update({"filter": filter_opt})
        return json.dumps(request_body)

    def query_records(self,
                      kind: str,
                      query_str: str,
                      limit: int,
                      offset: int = 0,
                      returned_fields: list = None,
                      filter_opt: dict = None) -> SearchResponse:
        """Query records in OSDU System given parameters.

        :param kind: The kind of entitities to retrieve if query matches
        :type kind: str
        :param query_str: An Apache Lucene compliant query string
        :type query_str: str
        :param limit: Number of results to return in request,
            limit + offset < 9999
        :type limit: int
        :param offset: Combine with limit to paginate results, defaults to 0
            limit + offset < 9999
        :type offset: int, optional
        :param returned_fields: The entity fields to return in the result list,
            defaults to None
        :type returned_fields: list, optional
        :param filter_opt: An optional filter dict, defaults to None
        :type filter_opt: dict, optional
        :return: SearchResponse with result list and total count
        :rtype: SearchResponse
        """
        request_body = self._create_query_request_body(kind, query_str, limit, offset,
                                                       returned_fields, filter_opt)
        response_dict = self._send_post_request(self.request_headers, self.search_url,
                                                request_body).json()
        return SearchResponse(results=response_dict.get("results", []),
                              total_count=response_dict.get("totalCount", 0))
