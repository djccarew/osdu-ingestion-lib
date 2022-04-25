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
import re
from collections import deque
from typing import Dict, Iterable, Iterator, List, Pattern, Set
from uuid import uuid4

import toposort

from osdu_ingestion.libs.linearize_manifest import ManifestEntity
from osdu_ingestion.libs.utils import (EntityId, is_surrogate_key,
                                       remove_trailing_colon, split_id)

logger = logging.getLogger()


class EntityNode:
    """
    This class represents entities and their links to parent and child ones.
    """
    __slots__ = [
        "entity_id",
        "system_srn",
        "entity_info",
        "children",
        "parents",
        "is_invalid",
        "is_external_srn",
        "_entity_id",
        "_whitelist_ref_patterns"
    ]

    SRN_REGEX = re.compile(
        r"(?<=\")surrogate-key:[\s\w\-\.\d]+(?=\")|(?<=\")[\w\-\.]+:[\w\-\.]+--[\w\-\.]+:.[^,;\"]+(?=\")")

    def __init__(
        self,
        entity_id: EntityId,
        entity_info: ManifestEntity,
        is_external_srn: bool = False,
        whitelist_ref_patterns: str = None
    ):
        self.entity_id = entity_id
        self.entity_info = entity_info
        self.system_srn = None
        self.children = set()
        self.parents = set()
        self.is_invalid = False
        self.is_external_srn = is_external_srn
        self._whitelist_ref_patterns = self._compile_whitelist_ref_patterns(whitelist_ref_patterns)

    @property
    def srn(self):
        return self.entity_id.srn

    def __repr__(self):
        return f"SRN: {self.srn}"

    @property
    def data(self) -> dict:
        if self.entity_info:
            return self.entity_info.entity_data
        else:
            return {}

    @data.setter
    def data(self, value: dict):
        self.entity_info.entity_data = value

    def add_child(self, child_node: "EntityNode"):
        self.children.add(child_node)

    def add_parent(self, parent_node: "EntityNode"):
        self.parents.add(parent_node)

    def _compile_whitelist_ref_patterns(self, whitelist_ref_patterns: str) -> List[Pattern]:
        """
        Trying to parse whitelist reference regexp patterns from string into list of regexp compiled patterns

        :param whitelist_ref_patterns: string containing various whitelist reference regexp patterns prepared for compilation
        :return: list of regexp compiled patterns or nothing
        """
        if not whitelist_ref_patterns:
            return []
        try:
            logger.debug(whitelist_ref_patterns)
            whitelist_ref_patterns = whitelist_ref_patterns.replace('\r\n', '\n').strip().split('\n')
            return [
                re.compile(r"{}".format(pattern), re.I + re.M)
                for pattern in whitelist_ref_patterns
            ]
        except Exception as e:
            logger.error(f"Unable to init whitelist reference patterns: {whitelist_ref_patterns}",
                         exc_info=e)
            return []

    def _extract_whitelist_references(self) -> Set[str]:
        """
        Extract whitelisted references from the entity.

        :return: Set of whitelisted ids to other entities or records.
        """
        manifest_str = json.dumps(self.data)
        whitelist_references = set()
        for pattern in self._whitelist_ref_patterns:
            whitelist_references.update(
                {match.get('value') for match in self._match_id_with_whitelist_pattern(pattern, manifest_str)}
            )
        logger.debug(f"Whitelist references of {self.data.get('id')}: {whitelist_references}")

        return whitelist_references

    def _match_id_with_whitelist_pattern(
        self,
        pattern: Pattern,
        source: str
    ) -> List[Dict[str, str]]:
        """
        Expects whitelist pattern containing (key) and (value) regexp groups

        :param pattern: compiled regexp whitelist pattern
        :param source: source to search with pattern
        :return: pattern matches filtered by groups
        """
        return [match.groupdict() for match in pattern.finditer(source)]

    def get_parent_entity_ids(self) -> Set[EntityId]:
        """
        Get list of parents' EnetityIds.
        """
        whitelist_references = set()
        entity_data = json.dumps(self.data, separators=(",", ":"))
        if self._whitelist_ref_patterns:
            whitelist_references = self._extract_whitelist_references()
        parent_entity_ids = set(
            split_id(reference) for reference in self.SRN_REGEX.findall(entity_data)
            if reference not in whitelist_references
        )
        parent_entity_ids.discard(self.entity_id)
        return parent_entity_ids

    def replace_parents_surrogate_srns(self):
        """
        Replace surrogate parents' keys with system-generated ones in child entity.
        """
        if not self.parents:
            return
        content = json.dumps(self.data)
        for parent in self.parents:
            if parent.system_srn:
                if is_surrogate_key(parent.srn):
                    # ':' at the end is for showing that it is reference if parent srn was surrogate-key.
                    content = content.replace(parent.srn, f"{parent.system_srn}:")
                else:
                    content = content.replace(parent.srn, f"{parent.system_srn}")
        self.data = json.loads(content)

    @property
    def invalid_parents(self) -> Set["EntityNode"]:
        return {parent for parent in self.parents if parent.is_invalid}


class ManifestAnalyzer:
    """
    This class is for creating a queue for ingesting set of data, each piece of data can depend on
    another one, so we must prioritize the order of ingesting. The idea is to create a dependency
    graph and traverse it to get the right order of ingestion.

    The Analyzer traverses each entity, each entity can contain references to other ones.

    The flow of prioritizing entities could be described as:
    1. Fill graph's nodes with entities (self._fill_entity_id_node_table())
    2. Create links between nodes (self._fill_nodes_edges())
    3. Mark unprocessed nodes if they are orphaned or dependant on orphaned nodes (self._find_invalid_nodes())
    4. Return prioritized queue for ingesting (self.entity_queue())
    """

    def __init__(
        self,
        entities: Iterable[ManifestEntity],
        previously_skipped_srns: Set[str] = None,
        whitelist_ref_patterns: str = None
    ):
        self.entities = entities
        self.entity_id_node_table = dict()
        self.external_entity_id_node_table = dict()
        self._invalid_entities_nodes = set()
        if previously_skipped_srns:
            self._previously_skipped_srns = set(split_id(_id) for _id in previously_skipped_srns)
        else:
            self._previously_skipped_srns = []
        self._whitelist_ref_patterns = whitelist_ref_patterns

        # used as a root for all orphan entities
        empty_entity_info = ManifestEntity({}, "")
        self._invalid_entities_parent = EntityNode(entity_id=split_id(str(uuid4())),
                                                   entity_info=empty_entity_info)

        self._fill_entity_id_node_table()
        self._fill_nodes_parents()

        self._find_invalid_nodes()

    def _create_entity_node(self, entity: ManifestEntity):
        _id = entity.entity_data.get("id", f"surrogate-key:{str(uuid4())}")
        entity_id = split_id(_id)
        self.entity_id_node_table[entity_id] = EntityNode(
            entity_id,
            entity,
            whitelist_ref_patterns=self._whitelist_ref_patterns
        )

    def _fill_entity_id_node_table(self):
        for entity in self.entities:
            self._create_entity_node(entity)

    def _fill_nodes_parents(self):
        """
        Find parents in every entity.
        """
        for entity_node in self.entity_id_node_table.values():
            self._set_entity_parents(entity_node)

    def _create_external_entity_node(self, parent_entity_id: EntityId) -> EntityNode:
        """
        Create a node with no content and mark it as external.

        :param parent_entity_id: Parent EntityId
        :return: EntityNode
        """
        return EntityNode(parent_entity_id, None, is_external_srn=True)

    def _set_entity_parents(self, entity_node: EntityNode):
        """
        Find all references parent in entity's content.
        If a parent is not presented in manifest, mark this entity as unprocessed.
        """
        parent_entity_ids = entity_node.get_parent_entity_ids()
        for parent_entity_id in parent_entity_ids:
            if self.entity_id_node_table.get(parent_entity_id):
                parent_node = self.entity_id_node_table[parent_entity_id]
                parent_node.add_child(entity_node)
                entity_node.add_parent(parent_node)
            elif parent_entity_id in self._previously_skipped_srns:
                # add to the common root for all invalid entity nodes. Will be marked as invalid
                # later in _find_invalid_nodes step in __init__.
                self._invalid_entities_parent.add_child(entity_node)
            else:
                # if entity srn has been never presented in manifest
                parent_node = self.external_entity_id_node_table.get(parent_entity_id)
                if not parent_node:
                    parent_node = self._create_external_entity_node(parent_entity_id)
                    self.external_entity_id_node_table[parent_entity_id] = parent_node
                parent_node.add_child(entity_node)
                entity_node.add_parent(parent_node)

    def _find_invalid_nodes(self, start_node: EntityNode = None):
        """
        Traverse entities dependant on orphaned or invalid ones.
        Add them to set of unprocessed nodes to exclude them from ingestion queue.
        """
        queue = deque()
        queue.append(start_node or self._invalid_entities_parent)
        while queue:
            node = queue.popleft()
            self._invalid_entities_nodes.add(node)
            node.is_invalid = True
            for child in node.children:
                if not child.is_invalid:
                    child.is_invalid = True
                    queue.append(child)
        if start_node is self._invalid_entities_parent:
            self._invalid_entities_nodes.discard(self._invalid_entities_parent)

    def entity_queue(self) -> Iterator[EntityNode]:
        """
        Create a queue, where a child entity goes after all its parents.
        If an entity is marked as unprocessed, then skip it.
        """
        entity_graph = {entity_node: entity_node.parents for entity_node in self.entity_id_node_table.values()}
        logger.debug(f"Entity graph {entity_graph}.")
        entity_queue = toposort.toposort_flatten(entity_graph, sort=False)
        for entity_node in entity_queue:
            if entity_node not in self._invalid_entities_nodes and not entity_node.is_external_srn:
                yield entity_node

        for entity_node in self._invalid_entities_nodes:
            entity_node.replace_parents_surrogate_srns()

    def entity_generation_queue(self) -> Iterator[Set[EntityNode]]:
        """
        Yield set of not dependant on each other entities (generation). 
        Generations of parents are followed by generations of children.

        """
        entity_graph = {entity: entity.parents for entity in self.entity_id_node_table.values()}
        logger.debug(f"Entity graph {entity_graph}.")
        toposorted_entities_nodes = toposort.toposort(entity_graph)
        for entity_set in toposorted_entities_nodes:
            valid_entities = {entity for entity in entity_set
                              if entity not in self._invalid_entities_nodes and not entity.is_external_srn}
            yield valid_entities

    def add_invalid_node(self, entity_node: EntityNode):
        """
        Use if there some problems with ingesting or finding entity.
        Mark it and its dependants as unprocessed.
        """
        self._invalid_entities_parent.add_child(entity_node)
        self._find_invalid_nodes(entity_node)

    @property
    def invalid_entities_info(self) -> List[ManifestEntity]:
        """
        :return: List of invalid entities info.
        """
        return [entity_node.entity_info for entity_node in self.entity_id_node_table.values()
                if entity_node.is_invalid]

    @property
    def invalid_entity_nodes(self) -> List[EntityNode]:
        return [entity_node for entity_node in self.entity_id_node_table.values() if entity_node.is_invalid]

    @property
    def valid_entities_info(self) -> List[ManifestEntity]:
        """
        :return: List of valid entities info.
        """
        return [entity_node.entity_info for entity_node in self.entity_id_node_table.values()
                if not entity_node.is_invalid]
