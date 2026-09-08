# -*- coding: utf-8 -*-
"""In-memory (and file-backed) memory store.

Substantially redesigned from the original monolithic store:
* Proper bi-temporal queries via :mod:`mnemos.temporal`
* Explicit mutation audit log
* Lineage / version history
* Configurable decay (R = e^{-t/S})
* Tier promotion/demotion
* Thread-safe with reentrant lock + file lock for multi-process safety
"""

from __future__ import annotations

import json
import math
import threading
import uuid
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel, Field

from mnemos.core.config import MemoryConfig
from mnemos.core.exceptions import SerializationError, StorageError
from mnemos.memory.models import (
    MemoryEntry,
    MemoryMutation,
    MemoryStatus,
    MemoryTier,
    MutationType,
)
from mnemos.temporal.model import TemporalCoordinates, _parse, _parse_opt, _utcnow_iso


# ── Persistence helpers ───────────────────────────────────────────────


def _atomic_write_json(path: Path, data: Any, **kwargs: Any) -> None:
    """Write JSON atomically via tmp-file + rename."""
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, **kwargs)
        tmp.replace(path)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise StorageError(f"Atomic write failed: {exc}") from exc


@contextmanager
def _file_lock(lock_path: Path) -> Iterator[None]:
    """Minimal cross-process file lock (advisory)."""
    import time

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(200):
        try:
            fd = lock_path.open("x")
            fd.close()
            break
        except FileExistsError:
            time.sleep(0.05)
    else:
        raise StorageError(f"Could not acquire file lock {lock_path}")
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


# ── State container ───────────────────────────────────────────────────


class _StoreState(BaseModel):
    entries: List[MemoryEntry] = Field(default_factory=list)
    mutations: List[MemoryMutation] = Field(default_factory=list)


# ── Store ─────────────────────────────────────────────────────────────

# Tier weights for retrieval scoring
TIER_WEIGHTS: Dict[str, float] = {
    MemoryTier.LONG: 1.5,
    MemoryTier.MID: 1.2,
    MemoryTier.SHORT: 1.0,
}


class InMemoryStore:
    """Thread-safe, optionally file-backed memory store.

    Implements the :class:`mnemos.core.interfaces.MemoryStore` protocol.
    """

    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        dir_path: Optional[str] = None,
    ) -> None:
        self._cfg = config or MemoryConfig()
        self._lock = threading.RLock()
        self._dir_path = Path(dir_path) if dir_path else None
        self._state = _StoreState()

        if self._dir_path:
            self._state_file = self._dir_path / "mnemos_memory.json"
            if self._state_file.exists():
                self._state = self._load()
                if self._cfg.enable_auto_cleanup:
                    self.cleanup_expired()
        else:
            self._state_file = None  # type: ignore[assignment]

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self) -> _StoreState:
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _StoreState(**data)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise SerializationError(f"Failed to load memory state: {exc}") from exc

    def _save(self) -> None:
        if self._dir_path is None:
            return
        self._dir_path.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(
            self._state_file,
            self._state.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )

    def _persistence_lock(self):
        if self._dir_path is None:
            return nullcontext()
        return _file_lock(self._state_file.with_suffix(".lock"))

    def _refresh(self) -> None:
        if self._state_file is not None and self._state_file.exists():
            self._state = self._load()

    # ── Decay ─────────────────────────────────────────────────────────

    def _retention(self, entry: MemoryEntry) -> float:
        """Compute retention score R = e^{-t_days / S_days}.

        *t_days* is measured from the most recent access (or observation,
        or creation) to now.  *S_days* is the entry's strength, clamped ≥ 1
        for numerical stability.
        """
        now = datetime.now(timezone.utc)
        last = (
            _parse_opt(entry.last_accessed)
            or _parse_opt(entry.temporal.observed_at)
            or _parse(entry.temporal.created_at)
        )
        if last is None:
            return 1.0
        t_days = max((now - last).total_seconds() / 86400.0, 0.0)
        s_days = max(entry.strength, 1.0)
        return math.exp(-t_days / s_days)

    # ── Tier lifecycle ────────────────────────────────────────────────

    def _promote_demote(self) -> None:
        now = datetime.now(timezone.utc)
        for e in self._state.entries:
            if e.status != MemoryStatus.ACTIVE:
                continue
            observed = _parse_opt(e.temporal.observed_at) or now
            age_days = (now - observed).days
            promoted = False

            if e.tier == MemoryTier.SHORT:
                if (
                    age_days >= self._cfg.short_to_mid_days
                    and e.strength >= self._cfg.short_to_mid_strength
                ) or e.strength >= self._cfg.short_to_mid_strength * 2:
                    e.tier = MemoryTier.MID
                    promoted = True
            elif e.tier == MemoryTier.MID:
                if (
                    age_days >= self._cfg.mid_to_long_days
                    and e.strength >= self._cfg.mid_to_long_strength
                ) or e.strength >= self._cfg.mid_to_long_strength * 2:
                    e.tier = MemoryTier.LONG
                    promoted = True

            if self._cfg.demotion_enabled and not promoted:
                last_ts = _parse_opt(e.last_accessed) or observed
                inactive_days = (now - last_ts).days
                retention = self._retention(e)
                if e.tier == MemoryTier.LONG:
                    if inactive_days >= self._cfg.demotion_grace_days and retention < 0.35:
                        e.tier = MemoryTier.MID
                elif e.tier == MemoryTier.MID:
                    if inactive_days >= self._cfg.demotion_grace_days and retention < 0.25:
                        e.tier = MemoryTier.SHORT

    # ── Mutations ─────────────────────────────────────────────────────

    def _record_mutation(
        self, mutation_type: MutationType, entry_id: str, target_id: Optional[str] = None, **details: Any,
    ) -> None:
        self._state.mutations.append(
            MemoryMutation(
                mutation_type=mutation_type,
                entry_id=entry_id,
                target_id=target_id,
                details=details,
            )
        )

    # ── Public API ────────────────────────────────────────────────────

    def add_entry(self, entry: MemoryEntry) -> str:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                self._state.entries.append(entry)
                self._record_mutation(MutationType.ADD, entry.id)
                self._promote_demote()
                self._save()
                return entry.id

    def update_entry(self, entry_id: str, new_entry: MemoryEntry) -> None:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                for e in self._state.entries:
                    if e.id == entry_id and e.status == MemoryStatus.ACTIVE:
                        e.status = MemoryStatus.SUPERSEDED
                        e.temporal.valid_until = new_entry.temporal.valid_from or _utcnow_iso()
                        e.temporal.expired_at = _utcnow_iso()
                new_entry.version_of = entry_id
                self._state.entries.append(new_entry)
                self._record_mutation(MutationType.UPDATE, new_entry.id, target_id=entry_id)
                self._promote_demote()
                self._save()

    def supersede_entry(self, entry_id: str, valid_until: Optional[str] = None) -> None:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                for e in self._state.entries:
                    if e.id == entry_id and e.status == MemoryStatus.ACTIVE:
                        e.status = MemoryStatus.SUPERSEDED
                        e.temporal.valid_until = valid_until or _utcnow_iso()
                        e.temporal.expired_at = _utcnow_iso()
                self._record_mutation(MutationType.SUPERSEDE, entry_id)
                self._save()

    def delete_entry(self, entry_id: str) -> None:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                for e in self._state.entries:
                    if e.id == entry_id and e.status == MemoryStatus.ACTIVE:
                        e.status = MemoryStatus.DELETED
                        e.temporal.valid_until = e.temporal.valid_until or _utcnow_iso()
                        e.temporal.expired_at = _utcnow_iso()
                self._record_mutation(MutationType.DELETE, entry_id)
                self._save()

    def merge_entries(self, entry_ids: List[str], merged_entry: MemoryEntry) -> str:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                for e in self._state.entries:
                    if e.id in entry_ids and e.status == MemoryStatus.ACTIVE:
                        e.status = MemoryStatus.MERGED
                        e.temporal.expired_at = _utcnow_iso()
                merged_entry.merged_from = entry_ids
                self._state.entries.append(merged_entry)
                self._record_mutation(
                    MutationType.MERGE, merged_entry.id, details={"source_ids": entry_ids}
                )
                self._save()
                return merged_entry.id

    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            self._refresh()
            for e in self._state.entries:
                if e.id == entry_id:
                    return e.model_copy(deep=True)
            return None

    def get_active_entries(self) -> List[MemoryEntry]:
        with self._lock:
            self._refresh()
            return [e.model_copy(deep=True) for e in self._state.entries if e.status == MemoryStatus.ACTIVE]

    def get_all_entries(self, include_inactive: bool = True) -> List[MemoryEntry]:
        with self._lock:
            self._refresh()
            if include_inactive:
                return [e.model_copy(deep=True) for e in self._state.entries]
            return self.get_active_entries()

    def touch(self, entry_ids: List[str]) -> None:
        with self._lock:
            with self._persistence_lock():
                self._refresh()
                now = _utcnow_iso()
                for e in self._state.entries:
                    if e.id in entry_ids and e.status == MemoryStatus.ACTIVE:
                        e.last_accessed = now
                        e.strength += 1.0
                self._promote_demote()
                self._save()

    def cleanup_expired(self) -> int:
        with self._lock:
            removed = 0
            now = datetime.now(timezone.utc)
            for e in self._state.entries:
                if e.status != MemoryStatus.ACTIVE:
                    continue
                valid_until = _parse_opt(e.temporal.valid_until)
                if valid_until and valid_until <= now:
                    e.status = MemoryStatus.EXPIRED
                    e.temporal.expired_at = _utcnow_iso()
                    removed += 1
                    continue
                if self._cfg.ttl_seconds is not None:
                    created = _parse(e.temporal.created_at)
                    if now - created > timedelta(seconds=self._cfg.ttl_seconds):
                        e.status = MemoryStatus.EXPIRED
                        e.temporal.expired_at = _utcnow_iso()
                        removed += 1
                        continue
                if self._retention(e) < self._cfg.retention_threshold:
                    e.status = MemoryStatus.EXPIRED
                    e.temporal.expired_at = _utcnow_iso()
                    removed += 1

            if not self._cfg.retain_history:
                self._state.entries = [e for e in self._state.entries if e.status == MemoryStatus.ACTIVE]

            if removed:
                self._save()
            return removed

    # ── Bi-temporal queries ───────────────────────────────────────────

    def query_as_of(
        self,
        valid_at: str | datetime,
        *,
        transaction_at: str | datetime | None = None,
    ) -> List[MemoryEntry]:
        """Bi-temporal point-in-time query.

        Returns entries that were *valid at* ``valid_at`` and (optionally)
        *known to the system at* ``transaction_at``.
        """
        valid = self._coerce_dt(valid_at)
        transaction = self._coerce_dt(transaction_at) if transaction_at else None
        with self._lock:
            self._refresh()
            matches: List[MemoryEntry] = []
            for entry in self._state.entries:
                v_start = (
                    _parse_opt(entry.temporal.valid_from)
                    or _parse_opt(entry.temporal.observed_at)
                    or _parse(entry.temporal.created_at)
                )
                v_end = _parse_opt(entry.temporal.valid_until)
                if v_start is None or valid < v_start:
                    continue
                if v_end is not None and valid >= v_end:
                    continue
                if transaction is not None:
                    created = _parse(entry.temporal.created_at)
                    retired = _parse_opt(entry.temporal.expired_at)
                    if transaction < created:
                        continue
                    if retired is not None and transaction >= retired:
                        continue
                matches.append(entry.model_copy(deep=True))
            matches.sort(key=lambda e: (e.temporal.valid_from or e.temporal.observed_at, e.id))
            return matches

    def get_version_history(self, entry_id: str) -> List[MemoryEntry]:
        """Return the full version chain rooted at *entry_id*, oldest first."""
        with self._lock:
            self._refresh()
            by_id = {e.id: e for e in self._state.entries}
            current = by_id.get(entry_id)
            if current is None:
                return []
            # Walk up to root
            seen: set[str] = set()
            while current.version_of and current.version_of in by_id:
                if current.id in seen:
                    break
                seen.add(current.id)
                current = by_id[current.version_of]
            root_id = current.id

            def _root_of(e: MemoryEntry) -> str:
                c = e
                visited: set[str] = set()
                while c.version_of and c.version_of in by_id:
                    if c.id in visited:
                        break
                    visited.add(c.id)
                    c = by_id[c.version_of]
                return c.id

            history = [e.model_copy(deep=True) for e in self._state.entries if _root_of(e) == root_id]
            history.sort(key=lambda e: (e.temporal.created_at, e.id))
            return history

    def diff_as_of(
        self,
        before: str | datetime,
        after: str | datetime,
        *,
        transaction_at: str | datetime | None = None,
    ) -> Dict[str, List[MemoryEntry]]:
        """Return added, removed, and changed entries between two valid times."""
        before_entries = self.query_as_of(before, transaction_at=transaction_at)
        after_entries = self.query_as_of(after, transaction_at=transaction_at)

        def _roots(entries: List[MemoryEntry]) -> Dict[str, MemoryEntry]:
            mapped: Dict[str, MemoryEntry] = {}
            for e in entries:
                h = self.get_version_history(e.id)
                root = h[0].id if h else e.id
                mapped[root] = e
            return mapped

        old = _roots(before_entries)
        new = _roots(after_entries)
        return {
            "added": [new[k] for k in sorted(new.keys() - old.keys())],
            "removed": [old[k] for k in sorted(old.keys() - new.keys())],
            "changed": [
                new[k]
                for k in sorted(old.keys() & new.keys())
                if old[k].id != new[k].id or old[k].content != new[k].content
            ],
        }

    def get_ranked_entries(self, limit: int = 50) -> List[MemoryEntry]:
        with self._lock:
            self._refresh()
            self._promote_demote()
            active = [e for e in self._state.entries if e.status == MemoryStatus.ACTIVE]
            scored = [(e, TIER_WEIGHTS.get(e.tier, 1.0) * self._retention(e)) for e in active]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [e.model_copy(deep=True) for e, _ in scored[:limit]]

    def get_mutation_log(self) -> List[MemoryMutation]:
        with self._lock:
            self._refresh()
            return list(self._state.mutations)

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _coerce_dt(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = _parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
