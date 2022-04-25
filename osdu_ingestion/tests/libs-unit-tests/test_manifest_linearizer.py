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

import pytest
from file_paths import MANIFEST_WELLBORE_VALID_PATH, TRAVERSAL_WELLBORE_VALID_PATH, \
    MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH, TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH, MANIFEST_EMPTY_PATH, \
    TRAVERSAL_MANIFEST_EMPTY_PATH, MANIFEST_GENERIC_SCHEMA_PATH
from osdu_ingestion.libs.exceptions import EmptyManifestError
from osdu_ingestion.libs.linearize_manifest import ManifestLinearizer, ManifestEntity


class TestManifestTraversal:

    @pytest.mark.parametrize(
        "manifest_file,manifest_schema_file,traversal_manifest_file",
        [
            pytest.param(
                MANIFEST_WELLBORE_VALID_PATH,
                MANIFEST_GENERIC_SCHEMA_PATH,
                TRAVERSAL_WELLBORE_VALID_PATH,
                id="Valid manifest Wellore"),
            pytest.param(
                MANIFEST_SEISMIC_TRACE_DATA_VALID_PATH,
                MANIFEST_GENERIC_SCHEMA_PATH,
                TRAVERSAL_SEISMIC_TRACE_DATA_VALID_PATH,
                id="Valid manifest WPC"),
        ]
    )
    def test_traversal_manifest(self, monkeypatch, manifest_file: str,
                                manifest_schema_file: str, traversal_manifest_file: str):
        manifest_traversal = ManifestLinearizer()
        with open(traversal_manifest_file) as f:
            traversal_manifest = json.load(f)
        with open(manifest_file) as f:
            manifest_file = json.load(f)
        traversal_manifest = [
            ManifestEntity(**e) for e in traversal_manifest
        ]
        manifest_records = manifest_traversal.linearize_manifest(manifest_file)
        for m in manifest_records:
            assert m in traversal_manifest, f"Expected {traversal_manifest}\nGot    {manifest_records}"

    @pytest.mark.parametrize(
        "manifest_file,traversal_manifest_file",
        [
            pytest.param(
                MANIFEST_EMPTY_PATH,
                TRAVERSAL_MANIFEST_EMPTY_PATH,
                id="Empty manifest"),
        ]
    )
    def test_traversal_empty_manifest(self, monkeypatch,
                                      manifest_file: str,
                                      traversal_manifest_file: str):
        manifest_traversal = ManifestLinearizer()
        with open(manifest_file) as f:
            conf_manifest_file = json.load(f)

        with pytest.raises(EmptyManifestError):
            manifest_traversal.linearize_manifest(conf_manifest_file["execution_context"].get("manifest", []), )
