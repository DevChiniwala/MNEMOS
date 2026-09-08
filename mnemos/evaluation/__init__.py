# -*- coding: utf-8 -*-
"""Mnemos evaluation — datasets and runner logic."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class EvalResult(BaseModel):
    """Result of an evaluation run."""

    metric: str
    score: float
    details: Dict[str, Any]


class Evaluator:
    """Base evaluator for running benchmarks."""

    def evaluate(self, predictions: List[str], ground_truth: List[str]) -> List[EvalResult]:
        """Run evaluation metrics."""
        return []
