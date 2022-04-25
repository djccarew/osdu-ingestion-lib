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

"""Util functions to work with OSDU Manifests."""

import dataclasses
from itertools import islice
from typing import Any, Generator, Iterable, List, TypeVar

BatchElement = TypeVar("BatchElement")


@dataclasses.dataclass()
class EntityId:
    id: str
    raw_value: str
    version: str = ""

    @property
    def srn(self) -> str:
        if self.version:
            return f"{self.id}:{self.version}"
        else:
            return self.id

    def __hash__(self) -> int:
        return hash(self.srn)

    def __eq__(self, other: "EntityId") -> bool:
        return self.srn == self.srn


def remove_trailing_colon(id_value: str) -> str:
    """
    Remove a trailing colon of id. It is need, for example, to search the last version of record.

    :param id_value: Id value.
    :return: Id value with no trailing colon.
    """
    return id_value[:-1] if id_value.endswith(":") else id_value


def split_id(id_value: str) -> EntityId:
    """
    Get id without a version for searching later.

    :id_value: ID of some entity with or without versions.
    """
    version = ""
    if is_surrogate_key(id_value):
        _id = id_value
    elif id_value.endswith(":"):
        _id = id_value[:-1]
    elif id_value.split(":")[-1].isdigit():
        version = str(id_value.split(":")[-1])
        _id = id_value[:-len(version) - 1]
    else:
        _id = id_value

    return EntityId(_id, raw_value=id_value, version=version)


def create_skipped_entity_info(entity: Any, reason: str) -> dict:
    if isinstance(entity, dict):
        skipped_entity_info = {
            "id": entity.get("id", ""),
            "kind": entity.get("kind", ""),
            "reason": reason
        }
    else:
        skipped_entity_info = {
            "content": str(entity)[:128],
            "reason": reason[:128]
        }
    return skipped_entity_info


def split_into_batches(
    element_sequence: Iterable[BatchElement],
    batch_size: int
) -> Generator[List[BatchElement], None, None]:
    """
    Split external ids into batches of the same size

    :param element_seqeuence:
    :param batch_size:
    :return:
    """
    if not isinstance(element_sequence, Iterable):
        raise TypeError(
            f"Element sequence '{element_sequence}' is '{type(element_sequence)}'. " 
            "It must be either 'list' or 'tuple'."
        )

    element_sequence = iter(element_sequence)

    while True:
        batch = list(islice(element_sequence, batch_size))

        if not batch:
            return

        yield batch

def is_surrogate_key(entity_id: str):
    """
    Check if the entity's id is surrogate.

    :param entity_ids: Entitiy ID
    :return: bool
    """

    if "surrogate-key:" in entity_id:
        return True
    else:
        return False

