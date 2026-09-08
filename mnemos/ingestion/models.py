# -*- coding: utf-8 -*-
"""Ingestion data models."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A raw document before chunking."""

    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """A segment of a document ready for indexing/memory."""

    doc_id: str
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
