# -*- coding: utf-8 -*-
"""Retrieval engine — orchestrates multi-channel retrieval with temporal gating.

Pipeline:
    Query → [Sparse, Dense, Graph] → Normalization → Score Fusion
    → Temporal Gate → Deduplication → Reranking → Final Hits
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol

from mnemos.core.config import RetrievalConfig
from mnemos.core.interfaces import Reranker
from mnemos.retrieval.fusion import normalize_scores, reciprocal_rank_fusion
from mnemos.retrieval.models import Hit, RetrievalResult


class Retriever(Protocol):
    """Protocol for a retrieval channel."""

    name: str

    def search(self, queries: List[str], top_k: int = 10) -> List[Hit]: ...


class RetrievalEngine:
    """Multi-channel retrieval engine with temporal awareness.

    Channels are registered by name; missing channels are simply skipped.
    """

    def __init__(
        self,
        config: Optional[RetrievalConfig] = None,
        reranker: Optional[Reranker] = None,
    ) -> None:
        self._cfg = config or RetrievalConfig()
        self._channels: Dict[str, Retriever] = {}
        self._reranker = reranker
        self._temporal_filter: Optional[Callable[[List[Hit]], List[Hit]]] = None

    def register_channel(self, name: str, retriever: Retriever) -> None:
        self._channels[name] = retriever

    def set_temporal_filter(self, fn: Callable[[List[Hit]], List[Hit]]) -> None:
        """Register a callable that filters hits by temporal validity."""
        self._temporal_filter = fn

    def search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        temporal_filter: Optional[Callable[[List[Hit]], List[Hit]]] = None,
    ) -> RetrievalResult:
        """Execute multi-channel retrieval.

        1. Fan out to all registered channels.
        2. Collect and tag hits by source.
        3. Normalize per-channel scores.
        4. Fuse via RRF.
        5. Apply temporal gate.
        6. Deduplicate.
        7. Rerank (if reranker available).
        8. Return top_k.
        """
        k = top_k or self._cfg.top_k
        all_hits: List[Hit] = []
        channel_contributions: Dict[str, int] = {}

        # 1. Fan out
        for ch_name, retriever in self._channels.items():
            try:
                hits = retriever.search([query], top_k=k * 2)
                for h in hits:
                    h.source = ch_name
                all_hits.extend(hits)
                channel_contributions[ch_name] = len(hits)
            except Exception:
                channel_contributions[ch_name] = 0

        total_candidates = len(all_hits)

        if not all_hits:
            return RetrievalResult(
                query=query,
                total_candidates=0,
            )

        # 2. Normalize scores per channel
        by_channel: Dict[str, List[Hit]] = {}
        for h in all_hits:
            by_channel.setdefault(h.source, []).append(h)

        for ch_hits in by_channel.values():
            scores = [h.score for h in ch_hits]
            normed = normalize_scores(scores)
            for h, ns in zip(ch_hits, normed):
                h.score = ns

        # 3. RRF fusion
        ranked_lists = []
        for ch_name in sorted(by_channel.keys()):
            ch_hits = sorted(by_channel[ch_name], key=lambda h: h.score, reverse=True)
            ranked_lists.append([h.snippet for h in ch_hits])

        rrf_scores = dict(reciprocal_rank_fusion(ranked_lists, k=self._cfg.rrf_k))

        for h in all_hits:
            h.score = rrf_scores.get(h.snippet, 0.0)

        # 4. Temporal gate
        tf = temporal_filter or self._temporal_filter
        if tf is not None:
            all_hits = tf(all_hits)
        after_temporal = len(all_hits)

        # 5. Deduplicate (by snippet)
        seen: set[str] = set()
        deduped: List[Hit] = []
        for h in sorted(all_hits, key=lambda h: h.score, reverse=True):
            key = h.snippet.strip().lower()
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        after_dedup = len(deduped)

        # 6. Rerank
        if self._reranker and deduped:
            try:
                docs = [h.snippet for h in deduped]
                reranked = self._reranker.rerank(query, docs, top_n=k)
                reranked_hits = []
                for item in reranked:
                    idx = item.get("index", 0)
                    if 0 <= idx < len(deduped):
                        hit = deduped[idx]
                        hit.score = item.get("score", hit.score)
                        reranked_hits.append(hit)
                deduped = reranked_hits
            except Exception:
                pass

        # 7. Top-k
        deduped.sort(key=lambda h: h.score, reverse=True)
        final = deduped[:k]

        return RetrievalResult(
            hits=final,
            channel_contributions=channel_contributions,
            total_candidates=total_candidates,
            after_temporal_filter=after_temporal,
            after_dedup=after_dedup,
            query=query,
        )
