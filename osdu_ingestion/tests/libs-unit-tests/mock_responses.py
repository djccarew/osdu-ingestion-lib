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


class MockResponse(requests.Response):
    """
    Mock response is used for monkey patching requests' methods.
    Example usage: monkeypatch.setattr(
                        requests, "get", lambda *args, **kwargs: MockResponse(http.HTTPStatus.OK)
                   )
    """

    def __init__(self, status_code: http.HTTPStatus):
        super(MockResponse, self).__init__()
        self.status_code = status_code
        self.url = "Test"
        self.reason = "Test"

    @property
    def text(self):
        return None


class MockWorkflowResponse(MockResponse):

    def __init__(self, json: str = "", status_code: http.HTTPStatus = http.HTTPStatus.OK):
        super().__init__(status_code)
        self._json = json

    def json(self):
        return self._json


class MockSearchResponse(MockResponse):

    def __init__(self, body_path: str, status_code: http.HTTPStatus = 200, total_count: int = 0,
                 cursor: str = None, *args, **kwargs):
        super().__init__(status_code)
        self.body_path = body_path
        self.total_count = total_count
        self.cursor = cursor

    def json(self):
        with open(self.body_path) as f:
            response_dict = json.load(f)

            if "totalCount" in response_dict:
                response_dict["totalCount"] = self.total_count

            if self.cursor:
                response_dict["cursor"] = self.cursor

            return response_dict


class MockSearchResponseForRecords(MockResponse):
    def __init__(self, records: list, status_code: http.HTTPStatus = 200, total_count: int = 0, *args, **kwargs):
        super().__init__(status_code)
        self.records = records
        self.total_count = total_count

    def json(self):
        body = {
            "results": self.records,
            "totalCount": self.total_count
        }

        return body


class MockSchemaResponse(MockResponse):

    def __init__(self, schema_path: str, status_code=200, *args, **kwargs):
        super().__init__(status_code)
        self.schema_path = schema_path

    def json(self):
        with open(self.schema_path) as f:
            return json.load(f)
