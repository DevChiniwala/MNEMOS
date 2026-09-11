# -*- coding: utf-8 -*-
"""
AdaptiveContextManager — Token-Budget-Aware Context Packing

MemTier (arXiv:2605.03675) shows k=2 entries at 300-600 tokens outperforms
larger retrieval budgets.  This module packs the highest-scored memories into
a strict token budget, deduplicates overlapping content, and optionally
compresses via LLM distillation when the budget is tight.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import tiktoken

from mnemos.schemas import Hit
from mnemos.schemas.advanced_memory import AdvancedMemoryStore
from mnemos.generator import AbsGenerator

logger = logging.getLogger(__name__)

_TRIGRAM_SIMILARITY_THRESHOLD = 0.60


@dataclass
class ContextManagerConfig:
    max_tokens: int = 2000
    tiktoken_model: str = "cl100k_base"
    compress_when_ratio_exceeds: float = 1.5
    dedup_threshold: float = 0.60


class AdaptiveContextManager:
    """
    Packs retrieved memories into a token-bounded context string.

    1. Precise token counting via tiktoken (already a core dep).
    2. Greedy best-first packing by retrieval score.
    3. Trigram-based deduplication to skip near-duplicate content.
    4. LLM compression fallback when essential content exceeds budget.
    """

    def __init__(
        self,
        max_tokens: int = 2000,
        tiktoken_model: str = "cl100k_base",
        generator: Optional[AbsGenerator] = None,
        dedup_threshold: float = _TRIGRAM_SIMILARITY_THRESHOLD,
    ) -> None:
        self.max_tokens = max_tokens
        self.generator = generator
        self.dedup_threshold = dedup_threshold
        try:
            self._enc = tiktoken.get_encoding(tiktoken_model)
        except Exception:
            self._enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def pack(
        self,
        hits: List[Hit],
        memory_store: Optional[AdvancedMemoryStore] = None,
        profile_context: str = "",
    ) -> str:
        if not hits:
            return profile_context or "No memory currently."

        budget = self.max_tokens
        if profile_context:
            budget -= self.count_tokens(profile_context) + 4

        packed: List[str] = []
        packed_trigrams: List[Set[str]] = []
        used_tokens = 0

        total_candidate_tokens = sum(self.count_tokens(h.snippet) for h in hits)
        needs_compression = (
            self.generator is not None
            and total_candidate_tokens > budget * 1.5
        )

        if needs_compression:
            compressed = self._compress(hits, budget)
            if compressed:
                ctx = f"{profile_context}\n\n{compressed}" if profile_context else compressed
                return ctx

        for hit in hits:
            snippet = hit.snippet.strip()
            if not snippet:
                continue

            tg = _trigrams(snippet)
            if self._is_duplicate(tg, packed_trigrams):
                continue

            token_cost = self.count_tokens(snippet) + 2
            if used_tokens + token_cost > budget:
                continue

            score_tag = ""
            fsc = hit.meta.get("hybrid_final_score")
            if fsc is not None:
                score_tag = f" [score={fsc:.3f}]"

            page_ref = f"Page {hit.page_id}" if hit.page_id else "Memory"
            line = f"{page_ref}{score_tag}: {snippet}"
            packed.append(line)
            packed_trigrams.append(tg)
            used_tokens += token_cost

        context = "\n".join(packed) if packed else "No memory currently."
        if profile_context:
            return f"{profile_context}\n\n{context}"
        return context

    def _is_duplicate(
        self, candidate: Set[str], existing: List[Set[str]]
    ) -> bool:
        for prev in existing:
            if not prev or not candidate:
                continue
            overlap = len(candidate & prev)
            union = len(candidate | prev)
            if union > 0 and overlap / union >= self.dedup_threshold:
                return True
        return False

    def _compress(self, hits: List[Hit], budget: int) -> Optional[str]:
        if not self.generator:
            return None
        snippets = [h.snippet for h in hits[:20] if h.snippet.strip()]
        combined = "\n---\n".join(snippets)
        target_words = max(budget // 2, 100)

        prompt = (
            "Compress the following memory fragments into a single concise summary "
            f"of at most {target_words} words. Preserve all factual claims, dates, "
            "names, and causal relationships. Remove redundancy.\n\n"
            f"Fragments:\n{combined}\n\nCompressed summary:"
        )
        try:
            result = self.generator.generate_single(prompt=prompt)
            text = result.get("text", "").strip()
            if text and self.count_tokens(text) <= budget:
                return text
            return text[:budget * 4] if text else None
        except Exception as exc:
            logger.warning("Context compression failed: %s", exc)
            return None


def _trigrams(text: str) -> Set[str]:
    words = text.lower().split()
    if len(words) < 3:
        return set(words)
    return {f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2)}
