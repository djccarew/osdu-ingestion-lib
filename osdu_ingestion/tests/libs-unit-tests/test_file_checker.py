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


import os
import sys



import pytest
from osdu_ingestion.libs.source_file_check import SourceFileChecker
from mock_providers import get_test_blob_storage_client
from osdu_ingestion.libs.exceptions import FileSourceError


class TestSourceFileChecker:

    @pytest.fixture()
    def file_checker(self, monkeypatch, does_exist: bool):
        """Build fake blob storage client."""
        storage_client = get_test_blob_storage_client()
        monkeypatch.setattr(storage_client, "does_file_exist", lambda *args, **kwargs: does_exist)
        return SourceFileChecker(storage_client)

    @pytest.mark.parametrize(
        "does_exist",
        [
            pytest.param(True),
        ]
    )
    def test_does_exists(self, monkeypatch, file_checker: SourceFileChecker, does_exist: bool):
        assert file_checker.does_file_exist("gs://test/test") is None

    @pytest.mark.parametrize(
        "does_exist",
        [
            pytest.param(False),
        ]
    )
    def test_does_exists(self, monkeypatch, file_checker: SourceFileChecker, does_exist: bool):
        with pytest.raises(FileSourceError):
            file_checker.does_file_exist("gs://test/test")
