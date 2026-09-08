# -*- coding: utf-8 -*-
"""Simple text chunking utility."""

from typing import List

from mnemos.ingestion.models import Chunk, Document


class SimpleChunker:
    """Chunks documents by a fixed character size with overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document: Document) -> List[Chunk]:
        """Split document into overlapping chunks."""
        text = document.text
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)
        chunk_idx = 0

        while start < text_len:
            end = min(start + self._chunk_size, text_len)
            
            # Try to snap to the nearest space to avoid breaking words
            if end < text_len:
                last_space = text.rfind(" ", start, end)
                if last_space != -1 and last_space > start + (self._chunk_size // 2):
                    end = last_space

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        doc_id=document.id,
                        chunk_id=f"{document.id}_{chunk_idx}",
                        text=chunk_text,
                        metadata=document.metadata.copy(),
                    )
                )
                chunk_idx += 1

            start = end - self._overlap
            # Prevent infinite loops if overlap >= chunk_size
            if start <= end - (self._chunk_size - self._overlap):
                start = end

        return chunks
