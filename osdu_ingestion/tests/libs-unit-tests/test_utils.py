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

import os
import sys
from typing import Iterable, List
import pytest



from osdu_ingestion.libs.utils import split_id, remove_trailing_colon, split_into_batches, is_surrogate_key


class TestUtil:

    @pytest.mark.parametrize(
        "_id,expected_id_version",
        [
            pytest.param(
                "namespace:reference-data--UnitQuantity:1:",
                ("namespace:reference-data--UnitQuantity:1", ""),
                id="Trailing colon"),
            pytest.param(
                "namespace:reference-data--UnitQuantity:1a",
                ("namespace:reference-data--UnitQuantity:1a", ""),
                id="With no colon"),
            pytest.param(
                "namespace:reference-data--UnitQuantity:1:1",
                ("namespace:reference-data--UnitQuantity:1", "1"),
                id="With version")
        ]
    )
    def test_split_id_version(self, _id, expected_id_version):
        entity_id = split_id(_id)
        assert (entity_id.id, entity_id.version) == expected_id_version

    @pytest.mark.parametrize(
        "_id,expected_id",
        [
            pytest.param(
                "test:test:",
                "test:test",
                id="Trailing colon"),
            pytest.param(
                "test:test",
                "test:test",
                id="With no colon")
        ]
    )
    def test_delete_trailing_colon(self, _id, expected_id):
        assert remove_trailing_colon(_id) == expected_id

    @pytest.mark.parametrize(
        "element_list,batch_size,expected_result",
        [
            pytest.param(
                [1, 2, 3, 4, 5, 6, 7],
                3,
                [[1, 2, 3], [4, 5, 6], [7]],
                id="List"
            ),
            pytest.param(
                range(1, 8),
                3,
                [[1, 2, 3], [4, 5, 6], [7]],
                id="Range"
            ),
        ]
    )
    def test_split_into_batches(self, element_list: Iterable, batch_size: int, expected_result: List[List]):
        chunked_list = list(split_into_batches(element_list, batch_size))
        assert chunked_list == expected_result

    @pytest.mark.parametrize(
        "wrong_value,batch_size",
        [
            pytest.param(
                1,
                3,
                id="Int"
            ),
            pytest.param(
                None,
                3,
                id="None"
            ),
        ]
    )
    def test_split_into_batches_type_error(self, wrong_value, batch_size: int):
        with pytest.raises(TypeError):
            list(split_into_batches(wrong_value, batch_size))

    @pytest.mark.parametrize(
        "_id,result",
        [
            pytest.param(
                "surrogate-key: 1",
                True,
                id="Surrogate key"
            ),
            pytest.param(
                "namspace:Some:id",
                False,
                id="Not surrogate key"
            ),
        ]
    )
    def test_is_surrogate_key(self, _id: str, result: bool):
        assert is_surrogate_key(_id) == result
