# -*- coding: utf-8 -*-
from __future__ import annotations

import warnings

try:
    from .consolidation import MemoryConsolidator
except ImportError:
    MemoryConsolidator = None  # type: ignore
    warnings.warn("MemoryConsolidator not available (optional dependencies may be missing)")

try:
    from .sleep import SleepConsolidationJob
except ImportError:
    SleepConsolidationJob = None  # type: ignore

__all__ = ["MemoryConsolidator", "SleepConsolidationJob"]
