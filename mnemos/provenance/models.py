# -*- coding: utf-8 -*-
"""Provenance data models.

Every important memory should be able to answer:
- Where did this come from?
- When was it observed?
- What evidence supports it?
- What replaced it?  What does it replace?
- What other memories depend on it?
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from mnemos.temporal.model import _utcnow_iso


class ProvenanceRecord(BaseModel):
    """A single provenance record for a memory entry."""

    memory_id: str
    source_page_id: Optional[str] = None
    source_content: Optional[str] = None
    mutation_type: str = "add"
    timestamp: str = Field(default_factory=_utcnow_iso)
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    merged_from: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)
    related_entities: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ProvenanceChain(BaseModel):
    """Complete provenance chain for a memory entry — the full explanation."""

    memory_id: str
    current_content: str
    current_status: str
    temporal_state: Dict[str, Optional[str]] = Field(default_factory=dict)
    confidence: float = 1.0
    lineage: List[ProvenanceRecord] = Field(default_factory=list)
    related_entities: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)

    def summary(self) -> str:
        """Human-readable provenance summary."""
        lines = [
            f"Memory: {self.memory_id}",
            f"Content: {self.current_content}",
            f"Status: {self.current_status}",
            f"Confidence: {self.confidence:.2f}",
            f"Versions: {len(self.lineage)}",
        ]
        if self.related_entities:
            lines.append(f"Entities: {', '.join(self.related_entities)}")
        return "\n".join(lines)
