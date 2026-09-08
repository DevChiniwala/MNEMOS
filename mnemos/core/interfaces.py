# -*- coding: utf-8 -*-
"""Mnemos core interfaces (protocols).

These define the contracts that concrete implementations must satisfy.
Using :class:`typing.Protocol` so implementations do *not* need to inherit
from these — structural subtyping (duck typing with type-checker support).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Forward references — avoid circular imports
# ---------------------------------------------------------------------------
# Concrete types live in mnemos.memory, mnemos.temporal etc.  The protocols
# only reference them by string annotation or generic dicts so that
# ``mnemos.core`` has zero intra-package dependencies.
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryStore(Protocol):
    """Persistent store for versioned memory entries."""

    def add_entry(self, entry: Any) -> str:
        """Persist a new memory entry.  Returns its id."""
        ...

    def update_entry(self, entry_id: str, new_entry: Any) -> None:
        """Supersede *entry_id* with *new_entry*."""
        ...

    def delete_entry(self, entry_id: str) -> None:
        """Soft-delete *entry_id*."""
        ...

    def get_entry(self, entry_id: str) -> Optional[Any]:
        """Return a single entry by id, or ``None``."""
        ...

    def get_active_entries(self) -> List[Any]:
        """Return all entries with ``status == 'active'``."""
        ...

    def query_as_of(
        self,
        valid_at: Any,
        *,
        transaction_at: Any | None = None,
    ) -> List[Any]:
        """Bi-temporal point-in-time query."""
        ...

    def get_version_history(self, entry_id: str) -> List[Any]:
        """Return the full version chain for *entry_id*."""
        ...


@runtime_checkable
class PageStore(Protocol):
    """Append-only store for provenance pages (source evidence)."""

    def add(self, page: Any) -> int:
        """Append a page and return its index."""
        ...

    def load(self) -> List[Any]:
        """Return all stored pages."""
        ...

    def get(self, index: int) -> Optional[Any]:
        """Return a page by index."""
        ...


@runtime_checkable
class GraphStore(Protocol):
    """Optional graph backend for entity/relation storage."""

    def upsert_memory(self, memory_id: str, props: Dict[str, Any]) -> None: ...
    def add_entities_relations(
        self,
        memory_id: str,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> None: ...
    def query_memories(
        self,
        entity_names: List[str],
        *,
        depth: int = 1,
        limit: int = 10,
    ) -> List[Dict[str, Any]]: ...
    def mark_memory_status(self, memory_id: str, status: str) -> None: ...


@runtime_checkable
class ProvenanceStore(Protocol):
    """Store for provenance / explanation records."""

    def record(self, memory_id: str, provenance: Dict[str, Any]) -> None: ...
    def explain(self, memory_id: str) -> Dict[str, Any]: ...


@runtime_checkable
class Generator(Protocol):
    """LLM text generation provider."""

    def generate(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        """Return ``{"text": str, "json": dict | None}``."""
        ...


@runtime_checkable
class Embedder(Protocol):
    """Embedding provider."""

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embedding vectors."""
        ...


@runtime_checkable
class Reranker(Protocol):
    """Cross-encoder reranker."""

    def rerank(
        self,
        query: str,
        documents: List[str],
        *,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return ``[{"index": int, "score": float}, ...]``."""
        ...
