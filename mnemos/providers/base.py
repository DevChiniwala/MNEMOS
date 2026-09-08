# -*- coding: utf-8 -*-
"""Base/mock providers for testing without external APIs."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class MockGenerator:
    """Deterministic mock generator for testing.

    Can be initialized with a response function for custom behavior.
    """

    def __init__(
        self,
        default_response: str = "",
        response_fn: Optional[Callable[[str], str]] = None,
    ) -> None:
        self._default = default_response
        self._fn = response_fn

    def generate(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        text = self._fn(prompt) if self._fn else self._default
        result: Dict[str, Any] = {"text": text, "json": None}
        if schema is not None:
            import json as _json
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    result["json"] = _json.loads(text[start:end])
            except Exception:
                pass
        return result


class MockEmbedder:
    """Deterministic mock embedder that returns fixed-dimension vectors."""

    def __init__(self, dimensions: int = 8) -> None:
        self._dim = dimensions

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors = []
        for text in texts:
            # Simple hash-based deterministic embedding
            h = hash(text)
            vec = [(h >> i & 0xFF) / 255.0 for i in range(self._dim)]
            vectors.append(vec)
        return vectors


class MockReranker:
    """Mock reranker that returns documents in original order with linear scores."""

    def rerank(
        self,
        query: str,
        documents: List[str],
        *,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        results = []
        for i, doc in enumerate(documents[:top_n]):
            results.append({
                "index": i,
                "score": 1.0 - (i / max(len(documents), 1)),
            })
        return results
