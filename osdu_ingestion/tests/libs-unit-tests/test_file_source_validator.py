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

import json



import pytest

from file_paths import (FILES_SOURCE_VALID, FILES_SOURCE_INVALID, FILE_COLLECTIONS_VALID,
                        FILE_COLLECTIONS_INVALID)
from osdu_ingestion.libs.validation.validate_file_source import FileSourceValidator


class TestFileSourceValidator:
    """Test validation of file source in datasets File and FileCollection."""
    @pytest.fixture
    def provide_datasets(self, input_datasets_path) -> list:
        """Read data from files."""
        with open(input_datasets_path) as f:
            return json.load(f)

    @pytest.mark.parametrize("input_datasets_path", [
        pytest.param(FILES_SOURCE_VALID),
        pytest.param(FILE_COLLECTIONS_VALID),
    ])
    def test_valid_datasets(self, provide_datasets: list, input_datasets_path: str):
        """Test valid inputs."""
        file_source_validator = FileSourceValidator()
        expected_datasets = sorted(provide_datasets, key=lambda k: k["id"])

        filtered_datasets, skipped = file_source_validator.filter_valid_datasets(provide_datasets)
        filtered_datasets = sorted(filtered_datasets, key=lambda k: k["id"])

        assert len(expected_datasets) == len(filtered_datasets)
        for i in range(len(expected_datasets)):
            assert expected_datasets[i] == filtered_datasets[i]

    @pytest.mark.parametrize("input_datasets_path,wrong_file_source", [
        pytest.param(FILES_SOURCE_VALID, " "),
        pytest.param(FILES_SOURCE_VALID, "  "),
        pytest.param(FILES_SOURCE_VALID, "\t"),
    ])
    def test_FileSource_space_chars(self, provide_datasets: list, input_datasets_path: str, wrong_file_source: str):
        """Test invalid inputs with spaces."""
        file_source_validator = FileSourceValidator()
        for ds in provide_datasets:
            ds["data"]["DatasetProperties"]["FileSourceInfo"]["FileSource"] = wrong_file_source

        filtered_datasets, skipped = file_source_validator.filter_valid_datasets(provide_datasets)
        filtered_datasets = sorted(filtered_datasets, key=lambda k: k["id"])
        assert not filtered_datasets


    @pytest.mark.parametrize("input_datasets_path", [
        pytest.param(FILES_SOURCE_INVALID),
        pytest.param(FILE_COLLECTIONS_INVALID),
    ])
    def test_invalid_datasets(self, provide_datasets: list, input_datasets_path: str):
        file_source_validator = FileSourceValidator()

        expected_datasets = []
        filtered_datasets, skipped = file_source_validator.filter_valid_datasets(provide_datasets)

        assert expected_datasets == filtered_datasets
