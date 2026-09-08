# -*- coding: utf-8 -*-
"""In-memory graph store for Mnemos.

Provides a graph backend that works without Neo4j for development/testing.
For production, a Neo4j-backed implementation can be swapped in via
the :class:`mnemos.core.interfaces.GraphStore` protocol.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from mnemos.graph.ontology import GraphOntology


@dataclass
class GraphNode:
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)


class InMemoryGraphStore:
    """Thread-safe in-memory graph store.

    Implements :class:`mnemos.core.interfaces.GraphStore`.
    """

    def __init__(self, ontology: Optional[GraphOntology] = None) -> None:
        self._ontology = ontology or GraphOntology()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._lock = threading.RLock()

    def upsert_memory(self, memory_id: str, props: Dict[str, Any]) -> None:
        with self._lock:
            self._nodes[memory_id] = GraphNode(
                id=memory_id, label="Memory", properties=props
            )

    def add_entity(self, name: str, entity_type: str = "Entity") -> str:
        with self._lock:
            node_id = f"entity:{name.lower()}"
            self._nodes[node_id] = GraphNode(
                id=node_id,
                label=entity_type,
                properties={"name": name, "type": entity_type},
            )
            return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._edges.append(
                GraphEdge(
                    source=source,
                    target=target,
                    relation=relation,
                    properties=properties or {},
                )
            )

    def add_entities_relations(
        self,
        memory_id: str,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        with self._lock:
            for ent in entities:
                name = ent.get("name", "")
                etype = ent.get("type", "Entity")
                if name:
                    eid = self.add_entity(name, etype)
                    self.add_edge(memory_id, eid, "MENTIONS")

            for rel in relations:
                head = rel.get("head", "")
                tail = rel.get("tail", "")
                rtype = rel.get("relation", "RELATES_TO")
                if head and tail:
                    hid = self.add_entity(head, "Entity")
                    tid = self.add_entity(tail, "Entity")
                    self.add_edge(hid, tid, rtype, rel)

    def query_memories(
        self,
        entity_names: List[str],
        *,
        depth: int = 1,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find memories related to the given entities via graph traversal."""
        with self._lock:
            target_ids = set()
            for name in entity_names:
                node_id = f"entity:{name.lower()}"
                if node_id in self._nodes:
                    target_ids.add(node_id)

            # BFS traversal
            visited: Set[str] = set()
            frontier = set(target_ids)
            memory_ids: Set[str] = set()

            for _ in range(depth):
                next_frontier: Set[str] = set()
                for node_id in frontier:
                    if node_id in visited:
                        continue
                    visited.add(node_id)
                    for edge in self._edges:
                        if edge.source == node_id:
                            next_frontier.add(edge.target)
                            if edge.target in self._nodes and self._nodes[edge.target].label == "Memory":
                                memory_ids.add(edge.target)
                        if edge.target == node_id:
                            next_frontier.add(edge.source)
                            if edge.source in self._nodes and self._nodes[edge.source].label == "Memory":
                                memory_ids.add(edge.source)
                frontier = next_frontier - visited

            results = []
            for mid in list(memory_ids)[:limit]:
                node = self._nodes.get(mid)
                if node:
                    results.append({"id": mid, **node.properties})
            return results

    def mark_memory_status(self, memory_id: str, status: str) -> None:
        with self._lock:
            node = self._nodes.get(memory_id)
            if node:
                node.properties["status"] = status

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            neighbors = []
            for edge in self._edges:
                if edge.source == node_id:
                    target = self._nodes.get(edge.target)
                    if target:
                        neighbors.append({
                            "id": target.id,
                            "label": target.label,
                            "relation": edge.relation,
                            **target.properties,
                        })
            return neighbors
