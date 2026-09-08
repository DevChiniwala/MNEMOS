# -*- coding: utf-8 -*-
"""Contradiction resolution pipeline.

Redesigned from the original monolithic prompt-driven approach into
explicit, composable steps:

    candidate discovery → semantic comparison → temporal comparison
    → contradiction classification → resolution policy → version transition

Possible outcomes:
    NO_CONFLICT, DUPLICATE, SUPERSEDE, MERGE, AMBIGUOUS

Ambiguous cases preserve uncertainty rather than aggressively overwriting.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from mnemos.core.interfaces import Generator
from mnemos.memory.models import MemoryEntry, MemoryStatus
from mnemos.temporal.model import _parse_opt


class ConflictOutcome(str, Enum):
    NO_CONFLICT = "no_conflict"
    DUPLICATE = "duplicate"
    SUPERSEDE = "supersede"
    MERGE = "merge"
    AMBIGUOUS = "ambiguous"


class ConflictResult(BaseModel):
    """Result of comparing a new entry against an existing one."""

    outcome: ConflictOutcome
    existing_id: str
    new_id: str
    reason: str = ""
    confidence: float = 1.0


class ConflictResolver:
    """Explicit contradiction resolution pipeline.

    Can operate in two modes:
    1. **Rule-based** (no LLM needed): temporal and string heuristics.
    2. **LLM-assisted**: uses a generator for semantic comparison.
    """

    def __init__(self, generator: Optional[Generator] = None) -> None:
        self._generator = generator

    def find_candidates(
        self,
        new_entry: MemoryEntry,
        existing: List[MemoryEntry],
        *,
        entity_overlap_threshold: int = 1,
    ) -> List[MemoryEntry]:
        """Step 1: discover potentially conflicting existing entries.

        Heuristic: entries that share entity names in their metadata.
        """
        new_entities = set(
            e.get("name", "").lower()
            for e in new_entry.meta.get("entities", [])
            if isinstance(e, dict)
        )
        if not new_entities:
            # Fallback: simple substring match
            candidates = []
            new_words = set(new_entry.content.lower().split())
            for e in existing:
                if e.status != MemoryStatus.ACTIVE:
                    continue
                old_words = set(e.content.lower().split())
                overlap = new_words & old_words
                if len(overlap) >= 3:
                    candidates.append(e)
            return candidates

        candidates = []
        for e in existing:
            if e.status != MemoryStatus.ACTIVE or e.id == new_entry.id:
                continue
            old_entities = set(
                ent.get("name", "").lower()
                for ent in e.meta.get("entities", [])
                if isinstance(ent, dict)
            )
            if len(new_entities & old_entities) >= entity_overlap_threshold:
                candidates.append(e)
        return candidates

    def compare_temporal(
        self, new_entry: MemoryEntry, existing: MemoryEntry
    ) -> ConflictOutcome:
        """Step 2: temporal comparison.

        If the new fact has a later valid_from than the existing,
        it likely supersedes.
        """
        new_valid = _parse_opt(new_entry.temporal.valid_from)
        old_valid = _parse_opt(existing.temporal.valid_from)
        old_until = _parse_opt(existing.temporal.valid_until)

        # If old fact already has an end date, it's already bounded
        if old_until is not None:
            return ConflictOutcome.NO_CONFLICT

        # If new fact is temporally later, it may supersede
        if new_valid and old_valid and new_valid > old_valid:
            return ConflictOutcome.SUPERSEDE

        return ConflictOutcome.AMBIGUOUS

    def compare_semantic(
        self, new_content: str, existing_content: str
    ) -> ConflictOutcome:
        """Step 3: semantic comparison using LLM (if available).

        Falls back to string heuristics if no generator.
        """
        if self._generator is None:
            return self._heuristic_compare(new_content, existing_content)

        prompt = (
            "Compare these two facts and determine their relationship.\n\n"
            f"Existing fact: {existing_content}\n"
            f"New fact: {new_content}\n\n"
            "Respond with exactly one JSON object:\n"
            '{"outcome": "no_conflict" | "duplicate" | "supersede" | "merge" | "ambiguous", '
            '"reason": "brief explanation"}\n'
        )
        try:
            resp = self._generator.generate(prompt, temperature=0.0, max_tokens=128)
            text = resp.get("text", "")
            import json

            data = json.loads(text[text.find("{") : text.rfind("}") + 1])
            outcome_str = data.get("outcome", "ambiguous")
            return ConflictOutcome(outcome_str)
        except Exception:
            return ConflictOutcome.AMBIGUOUS

    def _heuristic_compare(
        self, new_content: str, existing_content: str
    ) -> ConflictOutcome:
        """Simple heuristic: high overlap = duplicate, otherwise ambiguous."""
        new_words = set(new_content.lower().split())
        old_words = set(existing_content.lower().split())
        if not new_words or not old_words:
            return ConflictOutcome.NO_CONFLICT
        overlap = len(new_words & old_words) / max(len(new_words), len(old_words))
        if overlap > 0.85:
            return ConflictOutcome.DUPLICATE
        if overlap > 0.5:
            return ConflictOutcome.MERGE
        return ConflictOutcome.NO_CONFLICT

    def resolve(
        self,
        new_entry: MemoryEntry,
        existing: List[MemoryEntry],
    ) -> List[ConflictResult]:
        """Run the full conflict resolution pipeline.

        Returns a list of :class:`ConflictResult` for each candidate.
        """
        candidates = self.find_candidates(new_entry, existing)
        results: List[ConflictResult] = []

        for candidate in candidates:
            # Temporal check first (cheap)
            temporal_outcome = self.compare_temporal(new_entry, candidate)
            if temporal_outcome == ConflictOutcome.SUPERSEDE:
                results.append(
                    ConflictResult(
                        outcome=ConflictOutcome.SUPERSEDE,
                        existing_id=candidate.id,
                        new_id=new_entry.id,
                        reason="New fact is temporally later",
                        confidence=0.8,
                    )
                )
                continue

            # Semantic check (may use LLM)
            semantic_outcome = self.compare_semantic(
                new_entry.content, candidate.content
            )
            results.append(
                ConflictResult(
                    outcome=semantic_outcome,
                    existing_id=candidate.id,
                    new_id=new_entry.id,
                    reason=f"Semantic comparison: {semantic_outcome.value}",
                )
            )

        return results
