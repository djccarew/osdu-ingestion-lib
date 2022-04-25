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

"""Provides SearchId validator."""

import json
import logging
from typing import Generator, Set

import requests
import tenacity
from osdu_api.auth.authorization import TokenRefresher, authorize
from requests import Response

from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.exceptions import RecordsNotSearchableError
from osdu_ingestion.libs.mixins import HeadersMixin

logger = logging.getLogger()

RETRIES = 5
WAIT = 5
TIMEOUT = 10

DEFAULT_LIMIT = 200


class SearchId(HeadersMixin):
    """Class for stored records search validation."""

    def __init__(self, search_url: str, record_ids: list, token_refresher: TokenRefresher,
                 context: Context, limit: int = DEFAULT_LIMIT):
        """Init search id validator.

        :param search_url: Base OSDU Search service url
        :type search_url: str
        :param record_ids: The list of records id to be searched
        :type record_ids: list
        :param token_refresher: An instance of token refresher
        :type token_refresher: Token Refresher
        :param context: The tenant context
        :type context: Context
        :param limit: Search request limit
        :type limit: int
        :raises ValueError: When a mismatch of record counts occur
        """
        super().__init__(context)
        if not record_ids:
            logger.error("There are no record ids")
            raise ValueError("There are no record id")
        self.record_ids = record_ids
        self.search_url = search_url
        self.expected_total_count = len(record_ids)
        self.token_refresher = token_refresher
        self.limit = limit
        self._create_request_body()

    def _create_search_query(self) -> str:
        """Create search query to send to Search service using recordIds need
        to be found.

        :return: An elastic search valid query
        :rtype: str
        """
        record_ids = " OR ".join(f"\"{id_}\"" for id_ in self.record_ids)
        logger.debug(f"Search query {record_ids}")
        query = f"id:({record_ids})"
        return query

    def _create_request_body(self):
        """Create request body to send to Search service."""
        query = self._create_search_query()
        request_body = {
            "kind": "*:*:*:*",
            "returnedFields": ["id", "version", "acl", "kind", "legal"],
            "query": query
        }
        self.request_body = json.dumps(request_body)

    def _is_record_searchable(self, response: requests.Response) -> bool:
        """Check if search service returns expected totalCount of records.

        :param response: The response returned from the Search service
        :type response: requests.Response
        :raises ValueError: When a mismatch of record counts occur
        :return: [description]
        :rtype: bool
        """
        logger.debug(response.text)
        data = response.json()
        total_count = data.get('totalCount')
        logger.debug(f"Got total count {total_count}")
        if total_count is None:
            raise ValueError(f"Got no totalCount field in Search service response. "
                             f"Response is {data}.")
        return total_count == self.expected_total_count

    @tenacity.retry(
        wait=tenacity.wait_exponential(WAIT),
        stop=tenacity.stop_after_attempt(RETRIES),
        reraise=True
    )
    @authorize()
    def search_files(self, headers: dict) -> requests.Response:
        """Send request with recordIds to Search service.

        :param headers: The request headers
        :type headers: dict
        :raises RecordsNotSearchableError: When any of the records is not
            searchable
        :return: The server response
        :rtype: requests.Response
        """
        if self.request_body:
            response = requests.post(
                self.search_url, self.request_body, headers=headers)
            if not self._is_record_searchable(response):
                logger.error("Expected amount (%s) of records not found." %
                             self.expected_total_count,
                             )
                raise RecordsNotSearchableError(
                    f"Can't find records {self.request_body}. "
                    f"Got response {response.json()} from Search service."
                )
            return response

    def check_records_searchable(self):
        """Check if every record in self.record_ids is searchable."""
        headers = self.request_headers
        self.search_files(headers)


class ExtendedSearchId(SearchId):

    def __init__(self, search_url: str, record_ids: list, token_refresher,
                 context: Context, limit: int = DEFAULT_LIMIT):
        super().__init__(search_url, record_ids, token_refresher, context, limit=limit)

    def _create_request_body(self):
        """
        Create request body to send to Search service.
        """
        query = self._create_search_query()
        request_body = {
            "kind": "*:*:*:*",
            "query": query,
            "returnedFields": ["id", "version", "acl", "kind", "legal"],
            "limit": self.limit
        }
        self._request_body = request_body
        self.request_body = json.dumps(request_body)

    def _extract_id_from_response(self, response: dict):
        results = response.get("results")
        record_ids = [
            ":".join([elem.get("id"), str(elem.get("version", ""))]) for elem in results]
        record_ids.extend([elem.get("id") for elem in results])
        logger.debug(f"response ids: {record_ids}")
        return record_ids

    @authorize()
    def _make_post_request(self, headers: dict, request_body: dict) -> Response:
        return requests.post(self.search_url, request_body, headers=headers)

    def search_records(self) -> Set[str]:
        """
        Send request with recordIds to Search service.
        """
        if self.request_body:
            response = self._make_post_request(
                self.request_headers, self.request_body)
            logger.debug(response.text)

            data = response.json()
            total_count = data.get("totalCount")

            logger.debug(f"Got total count {total_count}")

            if total_count is None:
                raise ValueError(f"Got no totalCount field in Search service response. "
                                 f"Response is {data}.")

            response_records_ids = set(self._extract_id_from_response(data))

            cursor = total_count > self.limit
            if cursor:
                logger.debug("Start cursor iteration")

                offset = self.limit
                for ids in self._iterate_cursor(offset, total_count):
                    response_records_ids.update(ids)

            return response_records_ids
        return set()

    def _iterate_cursor(self, offset: int, total_count: int) -> Generator:
        """
        Cursor iterator.
        Fetch all records using offest.
        """
        while offset <= total_count - self.limit:
            response = self._make_post_request(
                self.request_headers, json.dumps({"offset": offset, **self._request_body}))
            data = response.json()

            ids = set(self._extract_id_from_response(data))
            yield ids

            offset += self.limit
