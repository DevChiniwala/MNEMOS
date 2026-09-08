# -*- coding: utf-8 -*-
"""Bi-temporal coordinate model for Mnemos memories.

Every memory carries two independent time dimensions:

**System time** — when Mnemos *observed/recorded* the information.
  - ``created_at``  — when the entry was first written.
  - ``expired_at``  — when the entry was retired from the active ledger.

**Valid time** — when the information was *true in the external world*.
  - ``valid_from``  — when the fact became true.
  - ``valid_until`` — when the fact stopped being true (``None`` = still true).

These two axes are *never collapsed*: a late-arriving correction may have
``created_at = 2026-09-01`` (system) but ``valid_from = 2025-03-01`` (valid).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


class TemporalCoordinates(BaseModel):
    """Bi-temporal timestamps attached to every memory entry."""

    # ── System time ────────────────────────────────────────────────────
    created_at: str = Field(default_factory=_utcnow_iso)
    observed_at: str = Field(default_factory=_utcnow_iso)
    expired_at: Optional[str] = Field(default=None)

    # ── Valid time ─────────────────────────────────────────────────────
    valid_from: Optional[str] = Field(default=None)
    valid_until: Optional[str] = Field(default=None)


class TemporalState(BaseModel):
    """Convenience wrapper holding both parsed datetimes for comparisons."""

    created_at: datetime
    observed_at: datetime
    expired_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    @classmethod
    def from_coordinates(cls, coords: TemporalCoordinates) -> "TemporalState":
        return cls(
            created_at=_parse(coords.created_at),
            observed_at=_parse(coords.observed_at),
            expired_at=_parse_opt(coords.expired_at),
            valid_from=_parse_opt(coords.valid_from),
            valid_until=_parse_opt(coords.valid_until),
        )

    @property
    def is_open_ended(self) -> bool:
        """True when there is no explicit ``valid_until``."""
        return self.valid_until is None

    @property
    def is_retired(self) -> bool:
        """True when the system has expired this entry."""
        return self.expired_at is not None


# ── helpers ────────────────────────────────────────────────────────────


def _parse(iso: str) -> datetime:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_opt(iso: Optional[str]) -> Optional[datetime]:
    if iso is None:
        return None
    try:
        return _parse(iso)
    except (ValueError, TypeError):
        return None
