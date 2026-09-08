# -*- coding: utf-8 -*-
"""Mnemos observability — metrics and event tracking."""

from __future__ import annotations

import logging
from typing import Any, Dict


class EventTracker:
    """Simple event tracker for observability metrics."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("mnemos.observability")

    def track(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Log a structured event."""
        self.logger.info(f"EVENT {event_name}: {payload}")
