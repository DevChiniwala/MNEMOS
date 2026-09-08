# -*- coding: utf-8 -*-
"""Context builder for retrieving and packaging evidence."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from mnemos.retrieval.models import Hit, RetrievalResult


class ContextResult(BaseModel):
    """The final compiled context ready for generation."""

    text: str = Field(..., description="Formatted context string")
    used_hits: List[Hit] = Field(default_factory=list)
    token_estimate: int = 0
    meta: Dict[str, str] = Field(default_factory=dict)


class ContextBuilder:
    """Builds optimal context windows from retrieval results.
    
    Responsible for budgeting tokens, selecting top hits, and formatting
    them with optional provenance markers.
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        chars_per_token: float = 4.0,
    ) -> None:
        self._max_tokens = max_tokens
        self._chars_per_token = chars_per_token

    def _estimate_tokens(self, text: str) -> int:
        return int(len(text) / self._chars_per_token)

    def build(
        self,
        retrieval_result: RetrievalResult,
        *,
        include_provenance: bool = True,
    ) -> ContextResult:
        """Construct the context string, stopping when token budget is met."""
        used_hits: List[Hit] = []
        current_tokens = 0
        lines = []

        if not retrieval_result.hits:
            return ContextResult(text="No relevant information found.", used_hits=[], token_estimate=0)

        for i, hit in enumerate(retrieval_result.hits):
            prefix = f"[Fact {i+1}]"
            if include_provenance and hit.source:
                prefix += f" (via {hit.source})"
            
            snippet_text = hit.snippet.strip()
            formatted = f"{prefix}: {snippet_text}"
            
            hit_tokens = self._estimate_tokens(formatted)
            if current_tokens + hit_tokens > self._max_tokens:
                break
                
            lines.append(formatted)
            used_hits.append(hit)
            current_tokens += hit_tokens

        text = "\n".join(lines)
        return ContextResult(
            text=text,
            used_hits=used_hits,
            token_estimate=current_tokens,
        )
