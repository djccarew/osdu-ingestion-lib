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

from osdu_api.providers import blob_storage
from osdu_api.providers.types import BlobStorageClient

from osdu_ingestion.libs.exceptions import FileSourceError


class SourceFileChecker:
    """Class to perform file validation."""

    def __init__(self, blob_storage_client: BlobStorageClient = None):
        """Initiliaze SourceFileChecker with provided BlobStorageClient.

        :param blob_storage_client: Optional storage client, if not provided,
            client will be obtained according to `CLOUD_PROVIDER` env var,
            defaults to None
        :type blob_storage_client: BlobStorageClient, optional
        """
        self._blob_storage_client = blob_storage_client or blob_storage.get_client()

    def does_file_exist(self, file_path: str):
        """Verifies if a file exist give file path.

        :param file_path: The full URI of the file
        :type file_path: str
        """
        if not self._blob_storage_client.does_file_exist(file_path):
            raise FileSourceError(f"File not found in {file_path}.")
