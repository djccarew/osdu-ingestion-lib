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
import uuid
from unittest.mock import patch

import mock_providers
import pytest
from file_paths import MANIFEST_BATCH_SAVE_PATH, SURROGATE_MANIFEST_WELLBORE
from osdu_ingestion.libs.manifest_analyzer import ManifestAnalyzer
from osdu_ingestion.libs.processors.single_manifest_processor import SingleManifestProcessor
from osdu_ingestion.libs.refresh_token import BaseTokenRefresher
from osdu_ingestion.libs.linearize_manifest import ManifestEntity, ManifestLinearizer
from osdu_ingestion.libs.exceptions import EmptyManifestError, ProcessRecordBatchError, ProcessRecordError
from osdu_ingestion.libs.utils import is_surrogate_key, split_into_batches


TENANT = "opendes"


class MockManifestProcessor:

    def process_manifest_records(self, records):
        return [i.entity_data.get("id", str(uuid.uuid4())) for i in records]


class MockDataIntegrityValidator:

    def validate_manifest_data_integrity(self, manifest):
        return manifest, []


class MockSchemaValidator:

    def get_schema(self, manifest):
        return {"properties": {"items": "a"}}

    def get_manifest_kind(self, manifest):
        return ""


class TestSingleManifestProcessor:

    @pytest.fixture
    def single_manifest_processor(self):
        token_refresher = BaseTokenRefresher()
        return SingleManifestProcessor(
            storage_url="",
            manifest_processor=MockManifestProcessor(),
            token_refresher=token_refresher,
            schema_validator=MockSchemaValidator(),
            payload_context="",
            referential_integrity_validator=""
        )

    def test__process_valid_records(self, single_manifest_processor):
        with open(SURROGATE_MANIFEST_WELLBORE) as f:
            data = json.load(f)
        data = [ManifestEntity(e, "") for e in data]
        manifest_analyzer = ManifestAnalyzer(data)
        records, skipped = single_manifest_processor._process_records_by_one(manifest_analyzer)
        assert len(records) == len(data) and not skipped

    def test__process_records_by_one_bad_response_from_storage(self, monkeypatch,
                                                        single_manifest_processor):
        def mock_bad_response(*args, **kwargs):
            raise Exception("Dummy exception")

        with open(SURROGATE_MANIFEST_WELLBORE) as f:
            data = json.load(f)
        data = [ManifestEntity(entity_data=e, manifest_path="") for e in data]
        monkeypatch.setattr(MockManifestProcessor, "process_manifest_records", mock_bad_response)
        manifest_analyzer = ManifestAnalyzer(data)
        records, skipped = single_manifest_processor._process_records_by_one(manifest_analyzer)
        assert not records and skipped

    @pytest.mark.parametrize(
        "file_path",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
            )
        ]
    )
    def test_save_records_by_one_node(self, single_manifest_processor: SingleManifestProcessor, file_path: str): 
        with open(file_path) as f:
            manifest = json.load(f)

        single_manifest_processor.batch_save_enabled = False

        manifest_lineazer = ManifestLinearizer()
        linearized_manifest = manifest_lineazer.linearize_manifest(manifest)
        expected_process_count = len(linearized_manifest)

        with patch.object(SingleManifestProcessor, "_process_single_entity_node", return_value="none") as mock_process_single_node:
            single_manifest_processor.process_manifest(manifest, False)
            assert mock_process_single_node.call_count == expected_process_count

    @pytest.mark.parametrize(
        "file_path,batch_size",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
                10
            ),
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
                500
            )
        ]
    )
    def test_save_records_by_generations(self, single_manifest_processor: SingleManifestProcessor, file_path: str, batch_size: int): 
        with open(file_path) as f:
            manifest = json.load(f)

        single_manifest_processor.batch_save_enabled = True
        single_manifest_processor.save_records_batch_size = batch_size

        manifest_lineazer = ManifestLinearizer()
        linearized_manifest = manifest_lineazer.linearize_manifest(manifest)
        manifest_analyzer = ManifestAnalyzer(linearized_manifest)

        for generation in manifest_analyzer.entity_generation_queue():
            surrogate_key_number = len([e for e in generation if is_surrogate_key(e.data.get("id", ""))])

            not_surrogate_key = [e for e in generation if not is_surrogate_key(e.data.get("id", ""))]
            expected_batch_number = len(list(split_into_batches(not_surrogate_key, batch_size)))

            with patch.object(SingleManifestProcessor, "_process_entity_nodes_batch", return_value="none") as mock_process_nodes_batch, \
                patch.object(SingleManifestProcessor, "_process_single_entity_node", return_value="none") as mock_process_single_node:
                single_manifest_processor._save_entities_generation(manifest_analyzer, generation)

                assert mock_process_nodes_batch.call_count == expected_batch_number
                assert mock_process_single_node.call_count == surrogate_key_number

    @pytest.mark.parametrize(
        "file_path",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
            )
        ]
    )
    def test_save_records_by_one(self, single_manifest_processor: SingleManifestProcessor, file_path: str): 
        with open(file_path) as f:
            manifest = json.load(f)
        single_manifest_processor.batch_save_enabled = False
        with patch.object(SingleManifestProcessor, "_process_records_by_one", return_value=([], [])) as mock_process_single_node:
            single_manifest_processor.process_manifest(manifest, False)
            assert mock_process_single_node.call_count == 1

    @pytest.mark.parametrize(
        "file_path",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
            )
        ]
    )
    def test_save_records_by_one(self, single_manifest_processor: SingleManifestProcessor, file_path: str): 
        with open(file_path) as f:
            manifest = json.load(f)
        single_manifest_processor.batch_save_enabled = True
        with patch.object(SingleManifestProcessor, "_process_records_by_batches", return_value=([], [])) as mock_process_batch_process:
            single_manifest_processor.process_manifest(manifest, False)
            assert mock_process_batch_process.call_count == 1

    @pytest.mark.parametrize(
        "file_path",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
            )
        ]
    )
    def test_skip_records(self, single_manifest_processor: SingleManifestProcessor, file_path: str): 
        with open(file_path) as f:
            manifest = json.load(f)
        single_manifest_processor.batch_save_enabled = True
        linearize_manifest = ManifestLinearizer().linearize_manifest(manifest)
        with patch.object(
            single_manifest_processor.manifest_processor, "process_manifest_records", side_effect=Exception('a')
        ):
            saved_record_ids, skipped_ids = single_manifest_processor.process_manifest(manifest, False)
            assert set(_id.get("id", "") for _id in skipped_ids) == set(e.entity_data.get("id", "") for e in linearize_manifest)
            
    @pytest.mark.parametrize(
        "file_path,batch_size",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
                10
            ),
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH,
                500
            )
        ]
    )
    def test_save_records_by_generations_raise_error(
        self, 
        single_manifest_processor: SingleManifestProcessor, 
        file_path: str, 
        batch_size: int
    ): 
        with open(file_path) as f:
            manifest = json.load(f)

        single_manifest_processor.batch_save_enabled = True
        single_manifest_processor.save_records_batch_size = batch_size

        manifest_lineazer = ManifestLinearizer()
        linearized_manifest = manifest_lineazer.linearize_manifest(manifest)
        manifest_analyzer = ManifestAnalyzer(linearized_manifest)

        for generation in manifest_analyzer.entity_generation_queue():
            with patch.object(single_manifest_processor.manifest_processor, "process_manifest_records", side_effect=Exception('a')):
                with pytest.raises(ProcessRecordBatchError):
                    single_manifest_processor._process_entity_nodes_batch(manifest_analyzer, generation)


    @pytest.mark.parametrize(
        "file_path",
        [
            pytest.param(
                MANIFEST_BATCH_SAVE_PATH
            )
        ]
    )
    def test_save_records_single_one_raise_error(
        self, 
        single_manifest_processor: SingleManifestProcessor, 
        file_path: str 
    ): 
        with open(file_path) as f:
            manifest = json.load(f)

        single_manifest_processor.batch_save_enabled = False
        manifest_lineazer = ManifestLinearizer()
        linearized_manifest = manifest_lineazer.linearize_manifest(manifest)
        manifest_analyzer = ManifestAnalyzer(linearized_manifest)

        for entity in manifest_analyzer.entity_queue():
            with patch.object(
                single_manifest_processor.manifest_processor, "process_manifest_records", side_effect=Exception('a')
            ):
                with pytest.raises(ProcessRecordError):
                    single_manifest_processor._process_single_entity_node(manifest_analyzer, entity)