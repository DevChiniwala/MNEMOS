# -*- coding: utf-8 -*-
"""In-memory (and file-backed) page store for source provenance."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, List, Optional

from mnemos.core.exceptions import StorageError
from mnemos.memory.models import Page


def _atomic_write_json(path: Path, data: Any, **kwargs: Any) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, **kwargs)
        tmp.replace(path)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise StorageError(f"Atomic write failed: {exc}") from exc


class InMemoryPageStore:
    """Append-only page store with optional file persistence.

    Implements :class:`mnemos.core.interfaces.PageStore`.
    """

    def __init__(self, dir_path: Optional[str] = None) -> None:
        self._dir_path = Path(dir_path) if dir_path else None
        self._pages: List[Page] = []
        self._lock = threading.RLock()
        if self._dir_path:
            self._pages_file = self._dir_path / "mnemos_pages.json"
            if self._pages_file.exists():
                self._pages = self._load()
        else:
            self._pages_file = None  # type: ignore[assignment]

    def _load(self) -> List[Page]:
        try:
            with open(self._pages_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [Page(**p) for p in data]
            return [Page(**p) for p in data.get("pages", [])]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise StorageError(f"Failed to load pages: {exc}") from exc

    def _save(self) -> None:
        if self._dir_path is None:
            return
        self._dir_path.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(
            self._pages_file,
            [p.model_dump() for p in self._pages],
            ensure_ascii=False,
            indent=2,
        )

    def add(self, page: Page) -> int:
        with self._lock:
            idx = len(self._pages)
            self._pages.append(page)
            self._save()
            return idx

    def load(self) -> List[Page]:
        with self._lock:
            if self._pages_file is not None and self._pages_file.exists():
                self._pages = self._load()
            return list(self._pages)

    def get(self, index: int) -> Optional[Page]:
        with self._lock:
            if 0 <= index < len(self._pages):
                return self._pages[index]
            return None

    def count(self) -> int:
        with self._lock:
            return len(self._pages)
