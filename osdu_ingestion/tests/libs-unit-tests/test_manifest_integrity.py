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

import copy
import json
from typing import List
from unittest.mock import patch

import pytest
from mock_providers import get_test_credentials
from file_paths import MANIFEST_WELLLOG_PATH, MANIFEST_WELL_PATH, \
    REF_RESULT_WELLLOG_PATH, MANIFEST_GENERIC_PATH, SURROGATE_MANIFEST_SEISMIC_NO_REFS_PATH
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.context import Context
from osdu_ingestion.libs.search_record_ids import ExtendedSearchId
from osdu_ingestion.libs.validation.validate_referential_integrity import ManifestIntegrity
from osdu_ingestion.libs.validation.validate_file_source import FileSourceValidator
from osdu_ingestion.libs.utils import EntityId, split_id, split_into_batches


class TestIntegrityProvider:

    @staticmethod
    def mock_valid_extended_search(monkeypatch, entity_references: List[EntityId]):
        search_response = set()
        for entity in entity_references:
            search_response.add(entity.id)
            search_response.add(entity.srn)
        monkeypatch.setattr(
            ExtendedSearchId,
            "search_records",
            lambda *args, **kwargs: search_response
        )

    @pytest.fixture
    def manifest_integrity(self) -> ManifestIntegrity:
        context = Context(app_key="", data_partition_id="test")
        manifest_integrity = ManifestIntegrity("", BaseTokenRefresher(get_test_credentials()),
                                               FileSourceValidator(),
                                               context)
        return manifest_integrity

    @pytest.mark.parametrize(
        "conf_path,ref_result_file",
        [
            pytest.param(
                MANIFEST_WELLLOG_PATH,
                REF_RESULT_WELLLOG_PATH,
                id="Validate manifest WPC")
        ]
    )
    def test_ensure_referential_integrity_valid(self, monkeypatch, manifest_integrity,
                                                conf_path: str, ref_result_file: str):
        with open(ref_result_file) as f:
            expected_result = json.load(f)
        with open(conf_path) as f:
            conf = json.load(f)
        monkeypatch.setattr(manifest_integrity, "_find_missing_external_ids",
                            lambda *args, **kwargs: {})
        manifest_integrity.ensure_integrity(conf)

    @pytest.mark.parametrize(
        "manifest,ref_result_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                REF_RESULT_WELLLOG_PATH,
                id="Validate manifest WPC")
        ]
    )
    def test_artefacts_manifest(self, monkeypatch, manifest_integrity, manifest: str,
                                ref_result_file: str):
        with open(manifest) as f:
            manifest = json.load(f)
        work_product_component = manifest["Data"]["WorkProductComponents"][0]
        monkeypatch.setattr(
            manifest_integrity,
            "_find_missing_external_ids",
            lambda *args, **kwargs: {}
        )
        monkeypatch.setattr(
            manifest_integrity,
            "_validate_datasets_file_sources",
            lambda datasets: (datasets, {})
        )
        expected_wpc_list = copy.deepcopy(manifest["Data"]["WorkProductComponents"])
        manifest_integrity.ensure_integrity(manifest)
        assert expected_wpc_list == manifest["Data"]["WorkProductComponents"]

    @pytest.mark.parametrize(
        "manifest,ref_result_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                REF_RESULT_WELLLOG_PATH,
                id="Validate manifest WPC")
        ]
    )
    def test_skip_valdiation_without_artefacts_wpc(self, monkeypatch, manifest_integrity,
                                                   manifest: str, ref_result_file: str):
        with open(manifest) as f:
            manifest = json.load(f)
        work_product_component = manifest["Data"]["WorkProductComponents"][0]
        work_product_component["data"].pop("Artefacts", None)
        monkeypatch.setattr(
            manifest_integrity,
            "_find_missing_external_ids",
            lambda *args, **kwargs: {}
        )
        monkeypatch.setattr(
            manifest_integrity,
            "_validate_datasets_file_sources",
            lambda datasets: (datasets, {})
        )
        expected_wpc_list = copy.deepcopy(manifest["Data"]["WorkProductComponents"])
        manifest_integrity.ensure_integrity(manifest)
        assert expected_wpc_list == manifest["Data"]["WorkProductComponents"]

    @pytest.mark.parametrize(
        "manifest,ref_result_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                REF_RESULT_WELLLOG_PATH,
                id="Validate manifest WPC")
        ]
    )
    def test_artefacts_absent_in_manifest_and_system_resourceId(self, monkeypatch,
                                                                manifest_integrity, manifest: str,
                                                                ref_result_file: str):
        wrong_resource_id = "namespace:reference-data--GenericReferenceData:Wrong1111"
        with open(manifest) as f:
            manifest = json.load(f)
        wrong_wpc = manifest["Data"]["WorkProductComponents"][0]
        wrong_wpc["data"]["Artefacts"][0]["ResourceID"] = f"{wrong_resource_id}:"
        monkeypatch.setattr(
            manifest_integrity,
            "_find_missing_external_ids",
            lambda *args, **kwargs: {wrong_resource_id}
        )
        monkeypatch.setattr(ExtendedSearchId, "search_records", lambda *args, **kwargs: [])
        expected_wpc_list = copy.deepcopy(manifest["Data"]["WorkProductComponents"])
        manifest, skipped_ids = manifest_integrity.ensure_integrity(manifest)
        assert wrong_wpc not in manifest["Data"]["WorkProductComponents"]

    @pytest.mark.parametrize(
        "manifest,ref_result_file",
        [
            pytest.param(
                MANIFEST_GENERIC_PATH,
                REF_RESULT_WELLLOG_PATH,
                id="Validate manifest WPC")
        ]
    )
    def test_artefacts_resourceId_duplicated_in_datasets(self, monkeypatch, manifest_integrity,
                                                         manifest: str,
                                                         ref_result_file: str):
        with open(manifest) as f:
            manifest = json.load(f)
        wrong_wpc = manifest["Data"]["WorkProductComponents"][0]
        wrong_wpc["data"]["Artefacts"][0]["ResourceID"] = \
            f'{wrong_wpc["data"]["Datasets"][0]}'
        monkeypatch.setattr(
            manifest_integrity,
            "_find_missing_external_ids",
            lambda *args, **kwargs: {}
        )
        manifest, skipped_ids = manifest_integrity.ensure_integrity(manifest)
        assert wrong_wpc not in manifest["Data"]["WorkProductComponents"]

    @pytest.mark.parametrize(
        "external_references,search_response,expected_missing_references",
        [
            pytest.param(
                [
                    "osdu:reference-data--ResourceSecurityClassification:Public:1",
                    "osdu:master-data--Organisation:HESS:1",
                ],
                set(),
                [
                    "osdu:reference-data--ResourceSecurityClassification:Public:1",
                    "osdu:master-data--Organisation:HESS:1",
                ],
                id="Empty search return"
            ),
            pytest.param(
                [
                    "osdu:reference-data--ResourceSecurityClassification:Public:",
                    "osdu:master-data--Organisation:123",
                ],
                {
                    "osdu:reference-data--ResourceSecurityClassification:Public",
                    "osdu:reference-data--ResourceSecurityClassification:Public:123",
                    "osdu:master-data--Organisation:123",
                    "osdu:master-data--Organisation:123:123",
                },
                set(),
                id="Full search return"
            ),
            pytest.param(
                [
                    "osdu:reference-data--ResourceSecurityClassification:Public:",
                    "osdu:master-data--Organisation:HESS:",
                ],
                {
                    "osdu:reference-data--ResourceSecurityClassification:Public:111",
                    "osdu:reference-data--ResourceSecurityClassification:Public",
                },
                [
                    "osdu:master-data--Organisation:HESS",
                ],
                id="Partial search return."
            )
        ]
    )
    def test_find_missing_external_ids(
        self,
        monkeypatch,
        manifest_integrity,
        external_references: List[str],
        search_response: set,
        expected_missing_references: set
    ):
        entity_ids = [split_id(r) for r in external_references]
        monkeypatch.setattr(
            ExtendedSearchId,
            "search_records",
            lambda *args, **kwargs: search_response
        )
        missing_ids = manifest_integrity._find_missing_external_ids(entity_ids)
        assert not missing_ids.symmetric_difference(expected_missing_references), \
            f'External references {external_references}\n' \
            f'Search response {search_response}\n' \
            f'Expected missing ids {expected_missing_references}'

    @pytest.mark.parametrize(
        "manifest_path,find_missing_external_ids_calls",
        [
            pytest.param(
                SURROGATE_MANIFEST_SEISMIC_NO_REFS_PATH,
                0,
                id="Surrogate keys with no refs"
            ),
            pytest.param(
                MANIFEST_WELL_PATH,
                1,
                id="Well with 1 ref"
            )
        ]
    )
    def test_ensure_external_integrity_found_all_records(
        self,
        manifest_integrity,
        manifest_path: str,
        find_missing_external_ids_calls: int
    ):
        with open(manifest_path) as f:
            manifest = json.load(f)
        with patch.object(manifest_integrity, "_find_missing_external_ids",
                          return_value=set()) as mock_search_records:
            manifest_integrity.ensure_integrity(manifest)
            assert mock_search_records.call_count == find_missing_external_ids_calls

    @pytest.mark.parametrize(
        "manifest_path,search_records_call",
        [
            pytest.param(
                MANIFEST_WELL_PATH,
                1,
                id="Well with 1 ref"
            )
        ]
    )
    def test_ensure_external_integrity_records_not_found(
        self,
        manifest_integrity,
        manifest_path: str,
        search_records_call: int
    ):
        """
        Check if search_records called if there are external references.
        """
        with open(manifest_path) as f:
            manifest = json.load(f)
        with patch.object(ExtendedSearchId, "search_records",
                          return_value=set()) as mock_search_records, \
            patch.object(ManifestIntegrity, "_mark_dependant_entities_invalid") \
                as mock_mark_invalid_children:

            manifest_integrity.ensure_integrity(manifest)
            assert mock_search_records.call_count == search_records_call
            assert mock_mark_invalid_children.call_count == search_records_call


    @pytest.mark.parametrize(
        "fake_refs_list,batch_size,expected_search_calls_number",
        [
            pytest.param(
                ["a:1", "a:2", "a:3"],
                2,
                2,
                id="2-element batch"
            ),
            pytest.param(
                ["a:1", "a:2", "a:3"],
                25,
                1,
                id="25-element batch"
            )
        ]
    )
    def test_find_missing_external_ids_search_batching(
        self,
        manifest_integrity,
        fake_refs_list,
        batch_size,
        expected_search_calls_number
    ):
        """
        Test if _find_missing_external_ids calls search records with batches
        """
        entities = [split_id(i) for i in fake_refs_list]
        manifest_integrity.search_id_batch_size = batch_size

        with patch.object(ExtendedSearchId, "search_records",
                     return_value=set()) as mock_search_records:
            manifest_integrity._find_missing_external_ids(entities)
            assert mock_search_records.call_count == expected_search_calls_number
