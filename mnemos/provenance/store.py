# -*- coding: utf-8 -*-
"""In-memory provenance store."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from mnemos.memory.models import MemoryEntry, MemoryStatus
from mnemos.provenance.models import ProvenanceChain, ProvenanceRecord


class InMemoryProvenanceStore:
    """Builds provenance explanations from the memory store state.

    Implements :class:`mnemos.core.interfaces.ProvenanceStore`.
    """

    def __init__(self) -> None:
        self._records: Dict[str, List[ProvenanceRecord]] = {}
        self._lock = threading.Lock()

    def record(self, memory_id: str, record: ProvenanceRecord) -> None:
        with self._lock:
            self._records.setdefault(memory_id, []).append(record)

    def explain(self, memory_id: str, memory_store: object) -> ProvenanceChain:
        """Build a full provenance chain for *memory_id*."""
        from mnemos.memory.store import InMemoryStore

        if not isinstance(memory_store, InMemoryStore):
            return ProvenanceChain(
                memory_id=memory_id,
                current_content="",
                current_status="unknown",
            )

        entry = memory_store.get_entry(memory_id)
        if entry is None:
            return ProvenanceChain(
                memory_id=memory_id,
                current_content="[not found]",
                current_status="unknown",
            )

        history = memory_store.get_version_history(memory_id)
        lineage = []
        for h in history:
            rec = ProvenanceRecord(
                memory_id=h.id,
                source_page_id=h.source_page_id,
                source_content=h.content,
                mutation_type="update" if h.version_of else "add",
                timestamp=h.temporal.created_at,
                supersedes=h.version_of,
                confidence=h.confidence,
            )
            lineage.append(rec)

        # Add any explicit records
        with self._lock:
            extra = self._records.get(memory_id, [])
            lineage.extend(extra)

        return ProvenanceChain(
            memory_id=memory_id,
            current_content=entry.content,
            current_status=entry.status.value,
            temporal_state={
                "created_at": entry.temporal.created_at,
                "observed_at": entry.temporal.observed_at,
                "valid_from": entry.temporal.valid_from,
                "valid_until": entry.temporal.valid_until,
                "expired_at": entry.temporal.expired_at,
            },
            confidence=entry.confidence,
            lineage=lineage,
            related_entities=list(entry.meta.get("entities", [])),
            supporting_evidence=[entry.content] + [h.content for h in history if h.id != entry.id],
        )
