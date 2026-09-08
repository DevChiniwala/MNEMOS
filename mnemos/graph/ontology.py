# -*- coding: utf-8 -*-
"""Graph ontology for Mnemos knowledge graph.

Defines node types and relation types that structure the graph layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field


class RelationType(str, Enum):
    MENTIONS = "MENTIONS"
    RELATES_TO = "RELATES_TO"
    DERIVED_FROM = "DERIVED_FROM"
    SUPERSEDES = "SUPERSEDES"
    UPDATES = "UPDATES"
    EXTENDS = "EXTENDS"
    WORKS_AT = "WORKS_AT"
    LOCATED_IN = "LOCATED_IN"
    PART_OF = "PART_OF"
    HAS_ROLE = "HAS_ROLE"


class NodeType(str, Enum):
    MEMORY = "Memory"
    ENTITY = "Entity"
    EPISODE = "Episode"
    SEMANTIC = "Semantic"
    COMMUNITY = "Community"
    SOURCE = "Source"


class GraphOntology(BaseModel):
    """Schema for the Mnemos knowledge graph.

    Defines which node types and relation types are recognized,
    and configurable constraints.
    """

    node_types: Set[str] = Field(
        default_factory=lambda: {t.value for t in NodeType}
    )
    relation_types: Set[str] = Field(
        default_factory=lambda: {r.value for r in RelationType}
    )
    entity_types: Set[str] = Field(
        default_factory=lambda: {
            "person", "organization", "location", "concept",
            "event", "product", "technology",
        }
    )
    max_traversal_depth: int = 3

    def is_valid_relation(self, rel: str) -> bool:
        return rel.upper() in self.relation_types

    def is_valid_entity_type(self, etype: str) -> bool:
        return etype.lower() in self.entity_types
