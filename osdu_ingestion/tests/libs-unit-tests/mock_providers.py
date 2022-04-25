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
"""Mock providers module."""

import io
import logging
from typing import Tuple
from osdu_api.providers.blob_storage import get_client
from osdu_api.providers.credentials import get_credentials
from osdu_api.providers.factory import ProvidersFactory
from osdu_api.providers.types import BlobStorageClient, BaseCredentials

logger = logging.getLogger(__name__)


@ProvidersFactory.register("provider_test")
class MockCredentials(BaseCredentials):
    """Mock Credentials Provider."""

    def __init__(self):
        self._access_token = "test_token"

    def refresh_token(self) -> str:
        """Refresh token.

        :return: Refreshed token
        :rtype: str
        """
        logger.info("Refreshed token in test.")

    @property
    def access_token(self) -> str:
        """The access token.

        :return: Access token string.
        :rtype: str
        """
        return self._access_token

    @access_token.setter
    def access_token(self, token: str):
        """Set access token

        :param val: The access token
        :type val: str
        :return: [description]
        :rtype: [type]
        """
        self._access_token = token


@ProvidersFactory.register("provider_test")
class GoogleCloudStorageClient(BlobStorageClient):
    """Mock BlobStorage Provider."""

    def download_to_file(self, uri: str, file: io.BytesIO) -> Tuple[io.BytesIO, str]:
        """Download file from the given URI.

        :param uri: The full URI of the file.
        :type uri: str
        :param file: a file like object
        :type file: io.BytesIO
        :return: A tuple containing the file and its content-type
        :rtype: Tuple[io.BytesIO, str]
        """
        pass

    def download_file_as_bytes(self, uri: str) -> Tuple[bytes, str]:
        """Download file as bytes from the given URI.

        :param uri: The full URI of the file
        :type uri: str
        :return: The file as bytes and its content-type
        :rtype: Tuple[bytes, str]
        """
        pass

    def upload_file(self, uri: str, file: io.BytesIO, content_type: str):
        """Upload blob to given URI.

        :param uri: The full target URI of the resource to upload.
        :type uri: str
        :param file: The file to upload
        :type file: FileLikeObject
        :param content_type: The content-type of the file to uplaod
        :type content_type: str
        """
        pass

    def does_file_exist(self, uri: str):
        """Verify if a resource exists in the given URI.

        :param uri: The URI of the resource to verify
        :type uri: str
        """
        pass


def get_test_credentials():
    """Utiltiy to get the credentials to use in tests."""
    return get_credentials("provider_test")


def get_test_blob_storage_client():
    """Utility to get blob storage client to use in tests."""
    return get_client("provider_test")
