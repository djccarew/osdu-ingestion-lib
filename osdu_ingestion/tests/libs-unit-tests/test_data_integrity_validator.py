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
import os
import sys



import pytest
import pytest_mock

from file_paths import (DATA_INTEGRITY_VALID_DATA, DATA_INTEGRITY_ORPHAN_DATASETS,
                        DATA_INTEGRITY_VALID_WP_INVALID_WPC, DATA_INTEGRITY_INVALID_WP,
                        DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_VALID_REAL_IDS,
                        DATA_INTEGRITY_EMPTY_DATA_CASE_2, DATA_INTEGRITY_EMPTY_WP,
                        DATA_INTEGRITY_VALID_DATA_IDS_WITH_COLON)
from osdu_ingestion.libs.search_client import SearchClient, SearchResponse
from osdu_ingestion.libs.validation.validate_data_integrity import DataIntegrityValidator
from osdu_ingestion.libs.validation.validate_file_source import FileSourceValidator


class TestDataIntegrityValidator:
    """Test data integrity validator."""
    @pytest.fixture
    def provide_manifests(self, expected_manifest_path, input_manifest_path):
        """Read manifest from files."""
        with open(expected_manifest_path) as f:
            expected_manifest = json.load(f)
        with open(input_manifest_path) as f:
            input_manifest = json.load(f)
        return expected_manifest, input_manifest

    @pytest.fixture
    def file_source_validator(self):
        file_source_validator = FileSourceValidator()
        return file_source_validator

    @pytest.mark.parametrize("expected_manifest_path, input_manifest_path", [
        pytest.param(DATA_INTEGRITY_VALID_DATA, DATA_INTEGRITY_VALID_DATA),
        pytest.param(DATA_INTEGRITY_VALID_DATA, DATA_INTEGRITY_ORPHAN_DATASETS),
        pytest.param(DATA_INTEGRITY_VALID_DATA, DATA_INTEGRITY_VALID_WP_INVALID_WPC),
        pytest.param(DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_INVALID_WP),
        pytest.param(DATA_INTEGRITY_VALID_DATA_IDS_WITH_COLON, DATA_INTEGRITY_VALID_DATA_IDS_WITH_COLON),
    ])
    def test_validate_data_integrity(self, mocker: pytest_mock.MockerFixture, provide_manifests,
                                     file_source_validator, expected_manifest_path: str,
                                     input_manifest_path: str):
        """Test validation of datasets dependencies."""
        search_client = mocker.Mock(spec=SearchClient)
        data_integrity_validator = DataIntegrityValidator(search_client, file_source_validator)

        expected_manifest, input_manifest = provide_manifests

        data_integrity_validator.validate_manifest_data_integrity(input_manifest)

        assert expected_manifest == input_manifest

    @pytest.mark.parametrize("expected_manifest_path, input_manifest_path", [
        pytest.param(DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_EMPTY_DATA),
        pytest.param(DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_EMPTY_DATA_CASE_2),
        pytest.param(DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_EMPTY_WP)
    ])
    def test_validate_empty_data_integrity(self, mocker: pytest_mock.MockerFixture,
                                           provide_manifests, file_source_validator,
                                           expected_manifest_path: str, input_manifest_path: str):
        """Test validation of datasets dependencies."""
        search_client = mocker.Mock(spec=SearchClient)
        data_integrity_validator = DataIntegrityValidator(search_client, file_source_validator)

        expected_manifest, input_manifest = provide_manifests

        data_integrity_validator.validate_manifest_data_integrity(input_manifest)

        assert expected_manifest == input_manifest

    @pytest.mark.parametrize("expected_manifest_path, input_manifest_path, wpc_ids, datasets_ids", [
        pytest.param(DATA_INTEGRITY_VALID_REAL_IDS, DATA_INTEGRITY_VALID_REAL_IDS,
                     ["opendes:work-product-component--GenericWorkProductComponent:1234"],
                     ["opendes:dataset--GenericDataset:1234"]),
        pytest.param(DATA_INTEGRITY_EMPTY_DATA, DATA_INTEGRITY_VALID_REAL_IDS, [], []),
    ])
    def test_validate_data_integrity_real_ids(self, mocker: pytest_mock.MockerFixture,
                                              provide_manifests, file_source_validator,
                                              expected_manifest_path: str, input_manifest_path: str,
                                              wpc_ids: list, datasets_ids: list):
        """Test validation of datasets dependencies simulating search api call."""
        search_client = mocker.Mock(spec=SearchClient)
        data_integrity_validator = DataIntegrityValidator(search_client, file_source_validator)
        mocker.patch(
            "osdu_ingestion.libs.validation.validate_data_integrity.DataIntegrityValidator._search_for_entities",
            side_effect=[datasets_ids, wpc_ids])
        expected_manifest, input_manifest = provide_manifests

        data_integrity_validator.validate_manifest_data_integrity(input_manifest)

        assert expected_manifest == input_manifest

    @pytest.mark.parametrize("expected_manifest_path, input_manifest_path, wpc_ids, datasets_ids", [
        pytest.param(DATA_INTEGRITY_VALID_REAL_IDS, DATA_INTEGRITY_VALID_REAL_IDS,
                     [{
                         "id": "opendes:work-product-component--GenericWorkProductComponent:1234"
                     }], [{
                         "id": "opendes:dataset--GenericDataset:1234"
                     }])
    ])
    def test_validate_expected_search_calls(self, mocker: pytest_mock.MockerFixture,
                                            provide_manifests, file_source_validator,
                                            expected_manifest_path: str, input_manifest_path: str,
                                            wpc_ids: list, datasets_ids: list):
        """Test validation of datasets dependencies simulating search api call."""
        datasets_response = SearchResponse(results=datasets_ids, total_count=1)
        wpcs_response = SearchResponse(results=wpc_ids, total_count=1)

        search_client = mocker.Mock(spec=SearchClient)
        query_records_mock = mocker.Mock(side_effect=[datasets_response, wpcs_response])
        search_client.query_records = query_records_mock
        data_integrity_validator = DataIntegrityValidator(search_client, file_source_validator)
        expected_manifest, input_manifest = provide_manifests

        data_integrity_validator.validate_manifest_data_integrity(input_manifest)

        assert expected_manifest == input_manifest
        datasets_call = mocker.call(kind='*:*:*:*',
                                    query_str='id:("opendes:dataset--GenericDataset:1234")',
                                    limit=1,
                                    returned_fields=['id'])
        wpcs_call = mocker.call(
            kind='*:*:*:*',
            query_str='id:("opendes:work-product-component--GenericWorkProductComponent:1234")',
            limit=1,
            returned_fields=['id'])
        query_records_mock.assert_has_calls([datasets_call, wpcs_call])
