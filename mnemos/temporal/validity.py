# -*- coding: utf-8 -*-
"""Temporal validity predicates for memory entries.

These functions answer questions such as:
- "Is this memory valid *now*?"
- "Was this memory valid at time T?"
- "Was this memory known to the system at time T?"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from mnemos.temporal.model import TemporalCoordinates, _parse, _parse_opt


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_valid_at(
    coords: TemporalCoordinates,
    point: datetime,
) -> bool:
    """Return ``True`` if the fact described by *coords* was valid at *point*.

    Validity is determined by the ``valid_from`` / ``valid_until`` window.
    When ``valid_from`` is ``None`` we fall back to ``observed_at`` (the fact
    was valid when it was first observed).
    """
    valid_start = _parse_opt(coords.valid_from) or _parse(coords.observed_at)
    valid_end = _parse_opt(coords.valid_until)
    if point < valid_start:
        return False
    if valid_end is not None and point >= valid_end:
        return False
    return True


def is_known_at(
    coords: TemporalCoordinates,
    point: datetime,
) -> bool:
    """Return ``True`` if the system had recorded this entry by *point*.

    This queries the **system-time** axis: an entry is "known" once
    ``created_at <= point`` and (``expired_at`` is ``None`` or ``expired_at > point``).
    """
    created = _parse(coords.created_at)
    expired = _parse_opt(coords.expired_at)
    if point < created:
        return False
    if expired is not None and point >= expired:
        return False
    return True


def temporal_filter(
    entries: List[Any],
    valid_at: Optional[datetime] = None,
    transaction_at: Optional[datetime] = None,
    *,
    coords_attr: str = "temporal",
) -> List[Any]:
    """Filter a list of objects carrying :class:`TemporalCoordinates`.

    Parameters
    ----------
    entries:
        Objects with a ``temporal`` attribute (or *coords_attr*) that is a
        :class:`TemporalCoordinates` instance.
    valid_at:
        If given, only entries *valid at* this moment survive.
    transaction_at:
        If given, only entries *known to the system* at this moment survive.
    coords_attr:
        Name of the attribute on each entry that holds the coordinates.

    Returns
    -------
    list:
        Filtered list in the same order as *entries*.
    """
    result: List[Any] = []
    for entry in entries:
        coords: TemporalCoordinates = getattr(entry, coords_attr)
        if valid_at is not None and not is_valid_at(coords, valid_at):
            continue
        if transaction_at is not None and not is_known_at(coords, transaction_at):
            continue
        result.append(entry)
    return result
