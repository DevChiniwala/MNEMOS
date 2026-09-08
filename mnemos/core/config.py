# -*- coding: utf-8 -*-
"""Mnemos typed configuration system.

Validates all config at startup; clearly separates required vs optional;
never exposes secrets in repr/logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM provider."""
    model_name: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 512
    timeout: float = 60.0
    system_prompt: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"LLMConfig(model_name={self.model_name!r}, "
            f"base_url={self.base_url!r}, "
            f"api_key='***')"
        )


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding provider."""
    model_name: str = "embed-v4.0"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    dimensions: int = 1024
    batch_size: int = 96

    def __repr__(self) -> str:
        return (
            f"EmbeddingConfig(model_name={self.model_name!r}, "
            f"api_key='***')"
        )


@dataclass(frozen=True)
class RerankerConfig:
    """Configuration for reranker provider."""
    model_name: str = "rerank-v3.5"
    api_key: Optional[str] = None
    top_n: int = 10

    def __repr__(self) -> str:
        return (
            f"RerankerConfig(model_name={self.model_name!r}, "
            f"api_key='***')"
        )


@dataclass(frozen=True)
class GraphConfig:
    """Configuration for Neo4j graph backend (optional)."""
    uri: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "neo4j"

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.username and self.password)

    def __repr__(self) -> str:
        return (
            f"GraphConfig(uri={self.uri!r}, "
            f"database={self.database!r}, "
            f"password='***')"
        )


@dataclass(frozen=True)
class MemoryConfig:
    """Configuration for memory store behaviour."""
    retention_threshold: float = 0.2
    ttl_seconds: Optional[int] = None
    short_to_mid_days: int = 7
    mid_to_long_days: int = 30
    short_to_mid_strength: float = 3.0
    mid_to_long_strength: float = 6.0
    demotion_enabled: bool = True
    demotion_grace_days: int = 14
    retain_history: bool = True
    enable_auto_cleanup: bool = True


@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration for the retrieval engine."""
    sparse_weight: float = 0.3
    dense_weight: float = 0.5
    graph_weight: float = 0.2
    rrf_k: int = 60
    top_k: int = 10
    rerank_top_n: int = 10
    enable_temporal_filter: bool = True


@dataclass(frozen=True)
class MnemosConfig:
    """Top-level configuration aggregating all sub-configs."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    reranker: RerankerConfig = field(default_factory=RerankerConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    storage_dir: Optional[str] = None

    def validate(self) -> None:
        """Raise :class:`ConfigurationError` on invalid config."""
        from mnemos.core.exceptions import ConfigurationError

        if self.memory.retention_threshold < 0 or self.memory.retention_threshold > 1:
            raise ConfigurationError(
                "retention_threshold must be in [0, 1]"
            )
        if self.retrieval.rrf_k < 1:
            raise ConfigurationError("rrf_k must be >= 1")
        weights = (
            self.retrieval.sparse_weight
            + self.retrieval.dense_weight
            + self.retrieval.graph_weight
        )
        if abs(weights - 1.0) > 0.01:
            raise ConfigurationError(
                f"Retrieval weights must sum to 1.0, got {weights:.3f}"
            )
