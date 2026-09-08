# -*- coding: utf-8 -*-
"""Temporal query types for Mnemos.

Callers express *what kind* of temporal question they are asking so the
retrieval engine can apply the right filters and scoring.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TemporalQueryType(str, Enum):
    """Discriminator for temporal query semantics."""

    CURRENT = "current"          # "What is true now?"
    HISTORICAL = "historical"    # "What was true at T?"
    TIMELINE = "timeline"        # "Show the full timeline"
    DIFF = "diff"                # "What changed between T1 and T2?"


class TemporalQuery(BaseModel):
    """A query with explicit temporal intent.

    Examples
    --------
    >>> TemporalQuery(text="Where does Alice work?", query_type=TemporalQueryType.CURRENT)
    >>> TemporalQuery(
    ...     text="Where did Alice work?",
    ...     query_type=TemporalQueryType.HISTORICAL,
    ...     valid_at="2025-03-01T00:00:00+00:00",
    ... )
    """

    text: str = Field(..., description="Natural-language query")
    query_type: TemporalQueryType = Field(default=TemporalQueryType.CURRENT)

    # For HISTORICAL queries
    valid_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp: only facts valid at this moment",
    )
    # For DIFF queries
    diff_start: Optional[str] = Field(default=None)
    diff_end: Optional[str] = Field(default=None)
    # Optional: restrict to system-time axis
    transaction_at: Optional[str] = Field(default=None)
