# -*- coding: utf-8 -*-
"""Mnemos exception hierarchy.

Every public exception inherits from :class:`MnemosError` so callers can
catch a single base class when they want a blanket handler.
"""

from __future__ import annotations


class MnemosError(Exception):
    """Base exception for all Mnemos errors."""


class ConfigurationError(MnemosError):
    """Raised when configuration is invalid or missing."""


class StorageError(MnemosError):
    """Raised when a storage backend operation fails."""


class ProviderError(MnemosError):
    """Raised when an external provider (LLM, embeddings, reranker) fails."""


class TemporalError(MnemosError):
    """Raised when temporal semantics are violated (e.g. invalid intervals)."""


class ContradictionError(MnemosError):
    """Raised when contradiction resolution encounters an irrecoverable state."""


class RetrievalError(MnemosError):
    """Raised when a retrieval operation fails."""


class IngestionError(MnemosError):
    """Raised when document ingestion fails."""


class SerializationError(MnemosError):
    """Raised when serialization / deserialization of state fails."""
