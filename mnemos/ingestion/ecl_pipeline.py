# -*- coding: utf-8 -*-
"""
ECL Pipeline — Extract, Cognify, Load

Cognee-inspired ingestion that enriches memories at write-time:

  Extract  → parse raw text via loaders / chunkers  (existing infra)
  Cognify  → score emotional salience, initialise FSRS baselines
  Load     → commit to memory store + graph atomically via memorize()

Wires up the previously disconnected cognitive features
(EmotionalSalienceScorer, SpacedRepetitionScheduler) so every ingested
memory has salience and spaced-repetition metadata from birth.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from mnemos.ingestion.documents import Document, Chunk
from mnemos.ingestion.chunking import BaseChunker, SimpleChunker
from mnemos.ingestion.loaders import BaseLoader

logger = logging.getLogger(__name__)


class ECLPipeline:
    """
    Enterprise-grade ingestion pipeline implementing the ECL pattern.

    Parameters
    ----------
    chunker : optional chunker (defaults to SimpleChunker)
    deduplicate : skip chunks whose content hash already exists
    salience_scorer : EmotionalSalienceScorer instance (optional)
    scheduler : SpacedRepetitionScheduler instance (optional)
    """

    def __init__(
        self,
        chunker: Optional[BaseChunker] = None,
        deduplicate: bool = True,
        salience_scorer: Optional[Any] = None,
        scheduler: Optional[Any] = None,
    ) -> None:
        self.chunker = chunker or SimpleChunker()
        self.deduplicate = deduplicate
        self.salience_scorer = salience_scorer
        self.scheduler = scheduler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        loaders: List[BaseLoader],
        memory_agent: Any,
        user_id: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        documents: List[Document] = []
        for loader in loaders:
            documents.extend(loader.load())
        return self.ingest_documents(documents, memory_agent, user_id=user_id, extra_meta=extra_meta)

    def ingest_documents(
        self,
        documents: List[Document],
        memory_agent: Any,
        user_id: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        updates: List[Any] = []
        seen = self._existing_hashes(memory_agent) if self.deduplicate else set()

        for doc in documents:
            # --- EXTRACT ---
            chunks = self.chunker.chunk(doc)

            for ch in chunks:
                content_hash = self._hash(ch.text)
                if self.deduplicate and content_hash in seen:
                    continue

                meta = {
                    "source": ch.source,
                    "doc_id": ch.doc_id,
                    "chunk_id": ch.chunk_id,
                    "chunk_index": ch.index,
                    "content_hash": content_hash,
                }
                meta.update(ch.metadata)
                if extra_meta:
                    meta.update(extra_meta)

                # --- COGNIFY ---
                meta = self._cognify(ch.text, meta)

                # --- LOAD ---
                result = memory_agent.memorize(ch.text, meta=meta, user_id=user_id)
                updates.append(result)
                seen.add(content_hash)

        logger.info("ECL pipeline processed %d documents → %d memories", len(documents), len(updates))
        return updates

    # ------------------------------------------------------------------
    # Cognify step — enrich metadata with cognitive signals
    # ------------------------------------------------------------------

    def _cognify(self, text: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        if self.salience_scorer is not None:
            try:
                meta["salience"] = self.salience_scorer.score(text)
            except Exception as exc:
                logger.warning("Salience scoring failed: %s", exc)
                meta.setdefault("salience", 0.5)

        if self.scheduler is not None:
            try:
                meta.setdefault("fsrs_stability", self.scheduler.initial_stability)
                meta.setdefault("fsrs_difficulty", self.scheduler.initial_difficulty)
                from datetime import datetime, timedelta, timezone
                next_review = datetime.now(timezone.utc) + timedelta(
                    days=self.scheduler.initial_stability
                )
                meta.setdefault("fsrs_next_review", next_review.isoformat())
            except Exception as exc:
                logger.warning("FSRS initialization failed: %s", exc)

        return meta

    # ------------------------------------------------------------------
    # Helpers (same contract as IngestionPipeline)
    # ------------------------------------------------------------------

    def _existing_hashes(self, memory_agent: Any) -> set:
        hashes: set = set()
        page_store = getattr(memory_agent, "page_store", None)
        if not page_store:
            return hashes
        try:
            pages = page_store.load()
        except Exception:
            return hashes
        for p in pages:
            meta = getattr(p, "meta", None) or {}
            h = meta.get("content_hash")
            if h:
                hashes.add(str(h))
        return hashes

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
