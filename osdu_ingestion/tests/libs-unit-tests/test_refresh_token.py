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



import pytest


from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from mock_providers import get_test_credentials


class TestBaseTokenRefresher:

    @pytest.fixture()
    def token_refresher(self, access_token: str) -> BaseTokenRefresher:
        creds = get_test_credentials()
        creds.access_token = access_token
        token_refresher = BaseTokenRefresher(creds)
        return token_refresher

    @pytest.mark.parametrize(
        "access_token",
        [
            "test",
            "aaaa"
        ]
    )
    def test_authorization_header(self, token_refresher: BaseTokenRefresher, access_token: str):
        """
        Check if Authorization header is 'Bearer <access_token>'
        """
        token_refresher.refresh_token()
        assert token_refresher.authorization_header.get("Authorization") == f"Bearer {access_token}"


class TestBaseTokenRefresher:

    @pytest.fixture()
    def token_refresher(self, access_token: str) -> BaseTokenRefresher:
        creds = get_test_credentials()
        creds.access_token = access_token
        token_refresher = BaseTokenRefresher(creds)
        return token_refresher

    @pytest.mark.parametrize(
        "access_token",
        [
            "test",
            "aaaa"
        ]
    )
    def test_authorization_header(self, token_refresher: BaseTokenRefresher, access_token: str):
        """
        Check if Authorization header is 'Bearer <access_token>'
        """
        token_refresher.refresh_token()
        assert token_refresher.authorization_header.get("Authorization") == f"Bearer {access_token}"
