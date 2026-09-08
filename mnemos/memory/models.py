# -*- coding: utf-8 -*-
"""Core domain models for Mnemos memory entries.

Design decisions
----------------
* **MemoryEntry** is the atomic unit of knowledge.  It carries bi-temporal
  coordinates, lifecycle status, tier, strength/decay, provenance pointers,
  and a version chain via ``version_of``.
* **Page** is raw provenance: the source evidence that produced a memory.
* **MemoryMutation** captures an explicit operation (ADD, UPDATE, SUPERSEDE,
  MERGE, DELETE, NOOP) for audit logging.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from mnemos.temporal.model import TemporalCoordinates, _utcnow_iso


# ── Enums ──────────────────────────────────────────────────────────────


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    MERGED = "merged"


class MemoryTier(str, Enum):
    SHORT = "short"
    MID = "mid"
    LONG = "long"


class MutationType(str, Enum):
    ADD = "add"
    UPDATE = "update"
    SUPERSEDE = "supersede"
    MERGE = "merge"
    DELETE = "delete"
    NOOP = "noop"


# ── Core models ────────────────────────────────────────────────────────


class MemoryEntry(BaseModel):
    """A single versioned memory with bi-temporal coordinates.

    Every mutation creates a *new* entry; the old one is marked superseded.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="Memory abstract content")
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)
    tier: MemoryTier = Field(default=MemoryTier.SHORT)

    # Bi-temporal coordinates
    temporal: TemporalCoordinates = Field(default_factory=TemporalCoordinates)

    # Strength / decay
    last_accessed: Optional[str] = Field(default=None)
    strength: float = Field(default=1.0)
    confidence: float = Field(default=1.0)

    # Provenance
    source_page_id: Optional[str] = Field(default=None)
    version_of: Optional[str] = Field(default=None)
    merged_from: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class Page(BaseModel):
    """Source evidence page — the raw provenance for a memory entry."""

    header: str = Field(..., description="Page header / abstract")
    content: str = Field(..., description="Raw source content")
    meta: Dict[str, Any] = Field(default_factory=dict)


class MemoryMutation(BaseModel):
    """An auditable record of a memory operation.

    Stored alongside entries so the full mutation history is recoverable.
    """

    mutation_type: MutationType
    entry_id: str
    target_id: Optional[str] = None
    timestamp: str = Field(default_factory=_utcnow_iso)
    details: Dict[str, Any] = Field(default_factory=dict)
