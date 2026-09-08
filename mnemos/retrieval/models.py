# -*- coding: utf-8 -*-
"""Retrieval data models — Hit, SearchPlan, RetrievalResult."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Hit(BaseModel):
    """A single retrieval hit from any channel."""

    page_id: Optional[str] = Field(None, description="Page ID in store")
    memory_id: Optional[str] = Field(None, description="Memory entry ID")
    snippet: str = Field(..., description="Text snippet")
    source: str = Field(..., description="Channel (sparse/dense/graph/index)")
    score: float = Field(default=0.0, description="Relevance score")
    meta: Dict[str, Any] = Field(default_factory=dict)


class SearchPlan(BaseModel):
    """Structured search plan for multi-channel retrieval."""

    info_needs: List[str] = Field(default_factory=list)
    keyword_queries: List[str] = Field(default_factory=list)
    vector_queries: List[str] = Field(default_factory=list)
    graph_queries: List[str] = Field(default_factory=list)
    page_indices: List[int] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    """Aggregated result from the retrieval engine."""

    hits: List[Hit] = Field(default_factory=list)
    channel_contributions: Dict[str, int] = Field(default_factory=dict)
    total_candidates: int = 0
    after_temporal_filter: int = 0
    after_dedup: int = 0
    query: str = ""
