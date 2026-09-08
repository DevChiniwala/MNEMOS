# -*- coding: utf-8 -*-
"""Mnemos — Temporal Memory Infrastructure for Autonomous AI.

This module provides the main :class:`Mnemos` facade, bringing together
memory storage, temporal reasoning, contradiction resolution, and retrieval
into a clean public API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mnemos.core.config import MnemosConfig
from mnemos.core.interfaces import Generator, MemoryStore, ProvenanceStore
from mnemos.evolution.resolver import ConflictResolver, ConflictOutcome
from mnemos.memory.models import MemoryEntry, Page
from mnemos.memory.page_store import InMemoryPageStore
from mnemos.memory.store import InMemoryStore
from mnemos.provenance.models import ProvenanceRecord, ProvenanceChain
from mnemos.provenance.store import InMemoryProvenanceStore
from mnemos.retrieval.engine import RetrievalEngine, Retriever
from mnemos.temporal.model import _utcnow_iso
from mnemos.temporal.validity import temporal_filter


class Mnemos:
    """The central interface for the memory infrastructure.
    
    Coordinates the memory store, provenance, retrieval, and conflict resolution.
    """

    def __init__(
        self,
        config: Optional[MnemosConfig] = None,
        generator: Optional[Generator] = None,
        memory_store: Optional[MemoryStore] = None,
        provenance_store: Optional[ProvenanceStore] = None,
    ) -> None:
        self.config = config or MnemosConfig()
        
        # Core components
        self.generator = generator
        self.memory = memory_store or InMemoryStore(
            config=self.config.memory,
            dir_path=self.config.storage_dir,
        )
        self.pages = InMemoryPageStore(dir_path=self.config.storage_dir)
        self.provenance = provenance_store or InMemoryProvenanceStore()
        
        # Subsystems
        self.resolver = ConflictResolver(generator=self.generator)
        self.retrieval = RetrievalEngine(config=self.config.retrieval)
        
        if self.config.retrieval.enable_temporal_filter:
            self.retrieval.set_temporal_filter(temporal_filter)

    def register_retriever(self, name: str, retriever: Retriever) -> None:
        """Register a retrieval channel (e.g., Sparse, Dense, Graph)."""
        self.retrieval.register_channel(name, retriever)

    def remember(
        self,
        content: str,
        *,
        observed_at: Optional[str] = None,
        valid_from: Optional[str] = None,
        entities: Optional[List[Dict[str, str]]] = None,
        source_content: Optional[str] = None,
    ) -> str:
        """Store a new fact, automatically resolving contradictions."""
        # 1. Create page for provenance
        page_id = str(self.pages.add(Page(header="Observation", content=source_content or content)))
        
        # 2. Build candidate entry
        entry = MemoryEntry(
            content=content,
        )
        if observed_at:
            entry.temporal.observed_at = observed_at
        if valid_from:
            entry.temporal.valid_from = valid_from
        entry.source_page_id = page_id
        if entities:
            entry.meta["entities"] = entities

        # 3. Resolve conflicts
        active = self.memory.get_active_entries()
        resolutions = self.resolver.resolve(entry, active)
        
        # Handle resolutions
        superseded_ids = []
        for res in resolutions:
            if res.outcome == ConflictOutcome.SUPERSEDE:
                self.memory.supersede_entry(res.existing_id, valid_until=entry.temporal.valid_from or _utcnow_iso())
                superseded_ids.append(res.existing_id)
            elif res.outcome == ConflictOutcome.DUPLICATE:
                # Discard duplicate, but touch existing
                self.memory.touch([res.existing_id])
                return res.existing_id

        # 4. Commit to memory
        new_id = self.memory.add_entry(entry)
        
        # 5. Record provenance
        self.provenance.record(
            new_id,
            ProvenanceRecord(
                memory_id=new_id,
                source_page_id=page_id,
                source_content=source_content or content,
                supersedes=superseded_ids[0] if superseded_ids else None,
                timestamp=_utcnow_iso(),
            )
        )
        
        return new_id

    def recall(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """Retrieve relevant memories for a query."""
        res = self.retrieval.search(query, top_k=top_k)
        
        entries = []
        for h in res.hits:
            if h.memory_id:
                entry = self.memory.get_entry(h.memory_id)
                if entry:
                    entries.append(entry)
        
        # Touch accessed entries
        self.memory.touch([e.id for e in entries])
        return entries

    def explain(self, memory_id: str) -> ProvenanceChain:
        """Return the full provenance and lineage of a memory."""
        return self.provenance.explain(memory_id, self.memory)

    def history(self) -> List[MemoryEntry]:
        """Return all active entries in the store."""
        return self.memory.get_active_entries()
