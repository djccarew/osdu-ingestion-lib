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

"""Auth and refresh token utility functions."""

import logging

from osdu_api.auth.authorization import TokenRefresher
from osdu_api.providers import credentials
from osdu_api.providers.types import BaseCredentials
from tenacity import retry, stop_after_attempt

logger = logging.getLogger(__name__)

RETRIES = 3


class BaseTokenRefresher(TokenRefresher):
    """Base Token refresher, that works with Credentials and has methods to refresh access tokens """

    def __init__(self, creds: BaseCredentials = None):
        super().__init__()
        self._credentials = creds or credentials.get_credentials()

    @retry(stop=stop_after_attempt(RETRIES))
    def refresh_token(self) -> str:
        """Refresh the token and cache token using airflow variables.

        :return: The refreshed token
        :rtype: str
        """
        self._credentials.refresh_token()
        self._access_token = self._credentials.access_token
        return self._access_token

    @property
    def access_token(self) -> str:
        """The access token.

        :return: The access token
        :rtype: str
        """
        return self._access_token

    @property
    def authorization_header(self) -> dict:
        """Authorization header with bearer token.

        :return: Auth header as dict
        :rtype: dict
        """
        return {"Authorization": f"Bearer {self.access_token}"}


class AirflowTokenRefresher(BaseTokenRefresher):
    """Simple wrapper for credentials to be used in refresh_token decorator within Airflow."""

    def __init__(self, creds: BaseCredentials = None):
        super().__init__(creds)
        from airflow.models import Variable
        self.airflow_variables = Variable
        self._access_token = None

    @retry(stop=stop_after_attempt(RETRIES))
    def refresh_token(self) -> str:
        """Refresh the token and cache token using airflow variables.

        :return: The refreshed token
        :rtype: str
        """
        super().refresh_token()
        self.airflow_variables.set("core__auth__access_token", self._access_token)
        return self._access_token

    @property
    def access_token(self) -> str:
        """The access token.

        :return: The access token
        :rtype: str
        """
        if not self._access_token:
            try:
                self._access_token = self.airflow_variables.get("core__auth__access_token")
            except KeyError:
                self.refresh_token()
        return self._access_token
