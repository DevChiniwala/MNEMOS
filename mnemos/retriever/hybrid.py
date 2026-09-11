# -*- coding: utf-8 -*-
"""
HybridRetriever — Unified Multi-Signal Scoring Engine

Inspired by MemTier (arXiv:2605.03675) and Cognee's graph+vector unification.
Combines 6 retrieval signals into a single weighted score:

  S(q, m) = w_sem * phi_sem + w_bm25 * phi_bm25 + w_graph * phi_graph
           + w_decay * phi_decay + w_cw * phi_cw + w_tier * phi_tier

Wraps existing retrievers (BM25, Dense, Graph) and produces a unified ranked list.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mnemos.retriever.base import AbsRetriever
from mnemos.schemas import Hit, InMemoryPageStore
from mnemos.schemas.advanced_memory import AdvancedMemoryStore, MemoryEntry

logger = logging.getLogger(__name__)

TIER_BOOST = {"short": 1.0, "mid": 1.2, "long": 1.4}

DEFAULT_WEIGHTS = {
    "semantic": 0.20,
    "lexical": 0.30,
    "graph": 0.15,
    "time_decay": 0.15,
    "cognitive": 0.10,
    "tier": 0.10,
}


@dataclass
class HybridRetrieverConfig:
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    decay_lambda: float = 0.05
    decay_bypass_threshold: float = 2.0
    top_k: int = 10


class HybridRetriever(AbsRetriever):
    """
    Fans queries out to wrapped sub-retrievers, then scores every hit
    with 6 normalised signals and a learned weight vector.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        retrievers: Dict[str, AbsRetriever],
        memory_store: Optional[AdvancedMemoryStore] = None,
        page_store: Optional[InMemoryPageStore] = None,
    ) -> None:
        super().__init__(config)
        self.retrievers = retrievers
        self.memory_store = memory_store
        self.page_store = page_store

        hybrid_cfg = config.get("hybrid", {})
        self.weights = hybrid_cfg.get("weights", dict(DEFAULT_WEIGHTS))
        self.decay_lambda = hybrid_cfg.get("decay_lambda", 0.05)
        self.decay_bypass_threshold = hybrid_cfg.get("decay_bypass_threshold", 2.0)
        self._top_k = hybrid_cfg.get("top_k", 10)

    # ------------------------------------------------------------------
    # AbsRetriever interface
    # ------------------------------------------------------------------

    def build(self, page_store: InMemoryPageStore) -> None:
        self.page_store = page_store
        for r in self.retrievers.values():
            try:
                r.build(page_store)
            except Exception as exc:
                logger.warning("Failed to build %s: %s", type(r).__name__, exc)

    def load(self) -> None:
        for r in self.retrievers.values():
            try:
                r.load()
            except Exception as exc:
                logger.warning("Failed to load %s: %s", type(r).__name__, exc)

    def update(self, page_store: InMemoryPageStore) -> None:
        self.page_store = page_store
        for r in self.retrievers.values():
            try:
                r.update(page_store)
            except Exception as exc:
                logger.warning("Failed to update %s: %s", type(r).__name__, exc)

    def search(self, query_list: List[str], top_k: int = 10) -> List[List[Hit]]:
        effective_k = top_k or self._top_k

        raw: Dict[str, List[Hit]] = {}
        for name, retriever in self.retrievers.items():
            try:
                results = retriever.search(query_list, top_k=effective_k * 3)
                flat: List[Hit] = []
                for batch in results:
                    flat.extend(batch)
                raw[name] = flat
            except Exception as exc:
                logger.warning("Retriever %s failed: %s", name, exc)

        if not raw:
            return [[]]

        scored = self._score_and_rank(raw, effective_k)
        return [scored]

    # ------------------------------------------------------------------
    # Multi-signal scoring
    # ------------------------------------------------------------------

    def _score_and_rank(
        self,
        raw: Dict[str, List[Hit]],
        top_k: int,
    ) -> List[Hit]:
        by_key: Dict[str, _HitAccumulator] = {}

        for source_name, hits in raw.items():
            for rank, hit in enumerate(hits):
                key = hit.page_id or hit.snippet[:64]
                if key not in by_key:
                    by_key[key] = _HitAccumulator(hit)
                acc = by_key[key]
                score = hit.meta.get("score", 0.0) if hit.meta else 0.0
                acc.raw_scores[source_name] = max(
                    acc.raw_scores.get(source_name, 0.0), score
                )
                acc.ranks[source_name] = min(
                    acc.ranks.get(source_name, 9999), rank
                )

        sem_scores = [a.raw_scores.get("vector", 0.0) for a in by_key.values()]
        bm25_scores = [a.raw_scores.get("keyword", 0.0) for a in by_key.values()]
        graph_scores = [a.raw_scores.get("graph", 0.0) for a in by_key.values()]

        sem_norm = _Normalizer(sem_scores)
        bm25_norm = _Normalizer(bm25_scores)
        graph_norm = _Normalizer(graph_scores)

        now = datetime.now(timezone.utc)
        entry_cache: Dict[str, MemoryEntry] = {}

        for key, acc in by_key.items():
            entry = self._resolve_entry(acc.hit, entry_cache)

            phi_sem = sem_norm.normalize(acc.raw_scores.get("vector", 0.0))
            raw_bm25 = acc.raw_scores.get("keyword", 0.0)
            phi_bm25 = bm25_norm.normalize(raw_bm25)
            phi_graph = graph_norm.normalize(acc.raw_scores.get("graph", 0.0))

            phi_decay = self._time_decay(entry, now, raw_bm25)
            phi_cw = self._cognitive_weight(entry)
            phi_tier = self._tier_boost(entry)

            w = self.weights
            final = (
                w.get("semantic", 0.0) * phi_sem
                + w.get("lexical", 0.0) * phi_bm25
                + w.get("graph", 0.0) * phi_graph
                + w.get("time_decay", 0.0) * phi_decay
                + w.get("cognitive", 0.0) * phi_cw
                + w.get("tier", 0.0) * phi_tier
            )

            acc.hit.meta.update({
                "hybrid_final_score": final,
                "phi_semantic": phi_sem,
                "phi_lexical": phi_bm25,
                "phi_graph": phi_graph,
                "phi_decay": phi_decay,
                "phi_cognitive": phi_cw,
                "phi_tier": phi_tier,
            })
            acc.final_score = final

        ranked = sorted(by_key.values(), key=lambda a: a.final_score, reverse=True)
        return [a.hit for a in ranked[:top_k]]

    # ------------------------------------------------------------------
    # Signal computations
    # ------------------------------------------------------------------

    def _time_decay(
        self,
        entry: Optional[MemoryEntry],
        now: datetime,
        raw_bm25: float,
    ) -> float:
        if raw_bm25 >= self.decay_bypass_threshold:
            return 1.0
        if entry is None:
            return 0.5
        try:
            created = datetime.fromisoformat(entry.t_created)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            delta_days = max((now - created).total_seconds() / 86400.0, 0.0)
        except Exception:
            return 0.5
        return math.exp(-self.decay_lambda * delta_days)

    def _cognitive_weight(self, entry: Optional[MemoryEntry]) -> float:
        if entry is None:
            return 0.5
        salience = entry.meta.get("salience", 0.5) if entry.meta else 0.5
        strength = entry.strength if entry.strength else 1.0
        strength_norm = min(strength / 10.0, 1.0)
        return 0.6 * salience + 0.4 * strength_norm

    def _tier_boost(self, entry: Optional[MemoryEntry]) -> float:
        if entry is None:
            return 1.0
        return TIER_BOOST.get(entry.tier, 1.0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_entry(
        self,
        hit: Hit,
        cache: Dict[str, MemoryEntry],
    ) -> Optional[MemoryEntry]:
        if not self.memory_store or not self.page_store:
            return None
        page_id = hit.page_id
        if not page_id:
            return None
        if page_id in cache:
            return cache[page_id]
        try:
            get_fn = getattr(self.page_store, "get", None)
            if not get_fn:
                return None
            page = get_fn(int(page_id))
            if not page or not page.meta:
                return None
            memory_id = page.meta.get("memory_id")
            if not memory_id:
                return None
            entry = self.memory_store.get_entry_by_id(str(memory_id))
            cache[page_id] = entry
            return entry
        except Exception:
            return None


class _HitAccumulator:
    __slots__ = ("hit", "raw_scores", "ranks", "final_score")

    def __init__(self, hit: Hit) -> None:
        self.hit = hit
        self.raw_scores: Dict[str, float] = {}
        self.ranks: Dict[str, int] = {}
        self.final_score: float = 0.0


class _Normalizer:
    """Min-max normaliser for a list of floats."""

    def __init__(self, values: List[float]) -> None:
        if values:
            self._min = min(values)
            self._max = max(values)
        else:
            self._min = 0.0
            self._max = 0.0
        self._range = self._max - self._min

    def normalize(self, v: float) -> float:
        if self._range <= 0:
            return 0.5 if v > 0 else 0.0
        return (v - self._min) / self._range
