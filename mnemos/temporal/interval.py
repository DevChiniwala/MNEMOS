# -*- coding: utf-8 -*-
"""Time interval arithmetic for Mnemos temporal reasoning.

Intervals are **half-open** ``[start, end)`` by convention:
the start instant is included; the end instant is excluded.
An open-ended interval has ``end = None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from mnemos.core.exceptions import TemporalError


@dataclass(frozen=True)
class TimeInterval:
    """A half-open ``[start, end)`` time interval.

    ``end = None`` means the interval extends to the present (open-ended).
    """

    start: datetime
    end: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end <= self.start:
            raise TemporalError(
                f"Interval end ({self.end.isoformat()}) must be "
                f"after start ({self.start.isoformat()})"
            )

    @property
    def is_open_ended(self) -> bool:
        return self.end is None

    def duration_seconds(self) -> Optional[float]:
        """Return duration in seconds, or ``None`` if open-ended."""
        if self.end is None:
            return None
        return (self.end - self.start).total_seconds()


def interval_contains(interval: TimeInterval, point: datetime) -> bool:
    """Return ``True`` if *point* is inside the half-open interval."""
    if point < interval.start:
        return False
    if interval.end is not None and point >= interval.end:
        return False
    return True


def intervals_overlap(a: TimeInterval, b: TimeInterval) -> bool:
    """Return ``True`` if two intervals share any common instant."""
    # a starts after b ends
    if b.end is not None and a.start >= b.end:
        return False
    # b starts after a ends
    if a.end is not None and b.start >= a.end:
        return False
    return True


def interval_intersection(
    a: TimeInterval, b: TimeInterval
) -> Optional[TimeInterval]:
    """Return the intersection of two intervals, or ``None`` if disjoint."""
    if not intervals_overlap(a, b):
        return None
    start = max(a.start, b.start)
    if a.end is None and b.end is None:
        end = None
    elif a.end is None:
        end = b.end
    elif b.end is None:
        end = a.end
    else:
        end = min(a.end, b.end)
    return TimeInterval(start=start, end=end)
