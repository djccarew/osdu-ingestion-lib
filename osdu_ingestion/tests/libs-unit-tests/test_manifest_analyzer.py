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
import logging
import uuid

from functools import partial
from typing import List

import pytest
from file_paths import SURROGATE_MANIFEST_WELLBORE, REF_RESULT_WHITELIST_WELLLOG_PATH, \
    MANIFEST_WELLLOG_PATH, MANIFEST_REFERENCE_PATTERNS_WHITELIST
from osdu_ingestion.libs.manifest_analyzer import ManifestAnalyzer, EntityNode
from osdu_ingestion.libs.linearize_manifest import ManifestEntity, ManifestLinearizer
from osdu_ingestion.libs.utils import EntityId, split_id

logger = logging.getLogger()

TEST_FAKE_DATA = [
        {
            "id": "1",
            "parents": [],
        },
        {
            "id": "2",
            "parents": ["1"],
        },
        {
            "id": "3",
            "parents": ["1"],
        },
        {
            "id": "4",
            "parents": ["2"],
        },
        {
            "id": "5",
            "parents": ["1", "3"],
        },
        {
            "id": "7",
            "parents": ["1", "6"],
        },
        {
            "id": "9",
            "parents": ["7"]
        }
    ]

TEST_FAKE_DATA = [ManifestEntity(entity_data=i, manifest_path="") for i in TEST_FAKE_DATA]

class TestManifestAnalyzer(object):

    @pytest.fixture()
    def manifest_analyzer(self):
        with open(SURROGATE_MANIFEST_WELLBORE) as f:
            data = json.load(f)
        return ManifestAnalyzer(data)

    @pytest.fixture
    def whitelist_ref_patterns_str(self) -> List:
        with open(MANIFEST_REFERENCE_PATTERNS_WHITELIST) as f:
            whitelist_ref_patterns = f.read()
        return whitelist_ref_patterns

    @pytest.fixture()
    def fake_data_manifest_analyzer(self, monkeypatch, data):
        monkeypatch.setattr(EntityNode, "get_parent_entity_ids", self.mock_get_parent_srns)
        manifest_analyzer = ManifestAnalyzer(data)
        return manifest_analyzer

    def process_entity(self, entity: EntityNode) -> str:
        if "surrogate-key" in entity.srn:
            return f"system_srn: {entity.srn}"
        else:
            return entity.srn

    def index_in_queue_by_srn(
        self,
        manifest_analyzer: ManifestAnalyzer,
        queue: list,
        srn: str
    ):
        entity_node = manifest_analyzer.entity_id_node_table[split_id(srn)]
        return queue.index(entity_node)

    @staticmethod
    def mock_get_parent_srns(obj: EntityNode):
        parent_srns = set(split_id(p) for p in obj.data.get("parents", []))
        return parent_srns

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param(TEST_FAKE_DATA, id="Fake data")
        ]
    )
    def test_queue_order(
        self,
        monkeypatch,
        data: dict
    ):
        """
        Here we use array with simple objects where it's immediately seen who depends on whom.
        Check if queue return parents, then and only then their children.
        Check if there is no orphaned and their children in the queue (SRN 7 and SRN 9).
        """
        monkeypatch.setattr(EntityNode, "get_parent_entity_ids", self.mock_get_parent_srns)
        manifest_analyzer = ManifestAnalyzer(data, {"6"})
        queue = list(manifest_analyzer.entity_queue())
        index_in_queue = partial(self.index_in_queue_by_srn, manifest_analyzer, queue)

        # check if child goes after all its parents in queue.
        assert index_in_queue("5") > index_in_queue("1") \
               and index_in_queue("5") > index_in_queue("3"), \
            "SRN 5 must follow parents: SRN 1 and 3"

        # check if orphans and their dependants are not in ingestion queue.
        for unprocessed_srn in ("7", "9"):
            unprocessed_entity = manifest_analyzer.entity_id_node_table[split_id(unprocessed_srn)]
            assert unprocessed_entity not in queue, \
                f"{unprocessed_entity} expected not to be in queue: {queue}"

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param(TEST_FAKE_DATA, id="Fake data")
        ]
    )
    def test_add_new_unporcessed(
        self,
        monkeypatch,
        fake_data_manifest_analyzer: ManifestAnalyzer,
        data: dict
    ):
        """
        Here we use array with simple objects where it's immediately seen who depends on whom.
        Imagine we can't process entity (e.g. Storage service can't save this entity).
        Then we must add this entity to unprocessed ones and traverse all the children of
        this entity marking them as unprocessed.
        They must disappear from the ingestion queue.
        """

        queue = fake_data_manifest_analyzer.entity_queue()
        unprocessed_node = fake_data_manifest_analyzer.entity_id_node_table[split_id("3")]
        expected_unprocessed_entities = {"7", "9", "3", "5"}
        fake_data_manifest_analyzer.add_invalid_node(unprocessed_node)
        for entity in queue:
            assert entity not in expected_unprocessed_entities, \
                f"{entity} must be excluded from queue."

    def test_real_data(self):
        with open(SURROGATE_MANIFEST_WELLBORE) as f:
            data = json.load(f)
        data = [ManifestEntity(entity_data=e, manifest_path="") for e in data]
        manifest_analyzer = ManifestAnalyzer(data)

        for entity in manifest_analyzer.entity_queue():
            entity.replace_parents_surrogate_srns()
            entity.system_srn = self.process_entity(entity)

    def test_real_data_with_orphaned(self):
        """
        Test if entity is added to invalid entities if it has reference to already skipped entity.
        :return:
        """
        with open(SURROGATE_MANIFEST_WELLBORE) as f:
            data = json.load(f)
        data = [ManifestEntity(entity_data=e, manifest_path="") for e in data]
        manifest_analyzer = ManifestAnalyzer(
            data,
            {"osdu:master-data--Wellbore:7587"}
        )

        for entity in manifest_analyzer.entity_queue():
            entity.replace_parents_surrogate_srns()
            entity.system_srn = self.process_entity(entity)
            logger.info(f"Processed entity {json.dumps(entity.data, indent=2)}")
        invalid_entities = [e.entity_data.get("id") for e in manifest_analyzer.invalid_entities_info]
        assert "surrogate-key:wpc-1" in invalid_entities

    @pytest.mark.parametrize(
        "manifest,system_srn,expected_replaced_srns",
        [
            pytest.param(
                [
                    {
                        "id": "surrogate-key:wpc",
                        "ref": "surrogate-key:wpc2"
                    },
                    {
                        "id": "surrogate-key:wpc2"
                    }

                ],
                "test:work-product--WorkProduct:7b37ff0e13ac40a0ac35b7e5ca60e5a7",
                "test:work-product--WorkProduct:7b37ff0e13ac40a0ac35b7e5ca60e5a7:",
                id="Surrogate key"
            ),
            pytest.param(
                [
                    {
                        "id": "surrogate-key:wpc",
                        "ref": "osdu:reference-data--ResourceSecurityClassification:RESTRICTED:test:"
                    },
                    {
                        "id": "osdu:reference-data--ResourceSecurityClassification:RESTRICTED:test"
                    }

                ],
                "osdu:reference-data--ResourceSecurityClassification:RESTRICTED:test",
                "osdu:reference-data--ResourceSecurityClassification:RESTRICTED:test:",
                id="Real Ids"
            )
        ]
    )
    def test_update_parent_entity_id_with_system_srn(self, manifest, system_srn, expected_replaced_srns):
        data = [ManifestEntity(entity_data=e, manifest_path="") for e in manifest]
        manifest_analyzer = ManifestAnalyzer(
            data,
        )

        for entity in manifest_analyzer.entity_queue():
            entity.replace_parents_surrogate_srns()
            entity.system_srn = system_srn
            if entity.data.get("ref"):
                assert entity.data["ref"] == expected_replaced_srns

    @pytest.mark.parametrize(
        "conf_path,ref_result_file",
        [
            pytest.param(
                MANIFEST_WELLLOG_PATH,
                REF_RESULT_WHITELIST_WELLLOG_PATH,
                id="Validate manifest WPC"
            )
        ]
    )
    def test_extract_references_with_applied_ref_patterns_whitelist(self, monkeypatch,
                                                                     whitelist_ref_patterns_str: str,
                                                                     conf_path: str,
                                                                     ref_result_file: str):
        with open(ref_result_file) as f:
            expected_result = json.load(f)
        with open(conf_path) as f:
            conf = json.load(f)
        test_data = conf["Data"]["WorkProductComponents"][0]
        entity_info = ManifestEntity(
            entity_data=test_data,
            manifest_path="Data.WorkProductComponents"
        )
        entity_node = EntityNode(
            split_id(test_data.get("id", str(uuid.uuid4()))),
            entity_info,
            whitelist_ref_patterns=whitelist_ref_patterns_str
        )
        entity_node_parents = entity_node.get_parent_entity_ids()
        parent_srns = set(i.srn for i in entity_node_parents)
        assert parent_srns == set(expected_result), parent_srns.difference(set(expected_result))

    @pytest.mark.parametrize(
        "conf_path,ref_result_file",
        [
            pytest.param(
                MANIFEST_WELLLOG_PATH,
                REF_RESULT_WHITELIST_WELLLOG_PATH,
                id="Validate manifest WPC"
            )
        ]
    )
    def test_no_entity_nodes_from_ref_patterns_whitelist(self, monkeypatch,
                                                                     whitelist_ref_patterns_str: str,
                                                                     conf_path: str,
                                                                     ref_result_file: str):
        with open(ref_result_file) as f:
            expected_result = json.load(f)
        with open(conf_path) as f:
            conf = json.load(f)
        tested_wpc = conf["Data"]["WorkProductComponents"][0]
        linearized_manifest = ManifestLinearizer().linearize_manifest(conf)
        manifest_analyzer = ManifestAnalyzer(
            linearized_manifest,
            whitelist_ref_patterns=whitelist_ref_patterns_str
        )
        tested_wpc_entity_id = split_id(tested_wpc["id"])
        wpc_parents = {p.srn for p in manifest_analyzer.entity_id_node_table[tested_wpc_entity_id].parents}
        assert wpc_parents == set(expected_result)

    @pytest.mark.parametrize(
        "manifest,expected_generations",
        [
            pytest.param(
                [
                    {
                        "id": "surrogate-key:wpc",
                        "ref": "surrogate-key:wpc2",
                        "ref2": "surrogate-key:wpc3",
                    },
                    {
                        "id": "surrogate-key:wpc2",
                        "ref": "surrogate-key:wpc4",
                    },
                    {
                        "id": "surrogate-key:wpc3",
                        "ref": "surrogate-key:wpc4"
                    },
                    {
                        "id": "surrogate-key:wpc4",
                    }
                ],
                [{"surrogate-key:wpc4"}, {"surrogate-key:wpc3", "surrogate-key:wpc2"}, {"surrogate-key:wpc"}],
                id="Surrogate key"
            )
        ]
    )
    def test_generation_queue(self, manifest, expected_generations):
        data = [ManifestEntity(entity_data=e, manifest_path="") for e in manifest]
        manifest_analyzer = ManifestAnalyzer(
            data
        )
        result = []
        for generation in manifest_analyzer.entity_generation_queue():
            result.append({e.data.get("id") for e in generation})
        assert result == expected_generations
        