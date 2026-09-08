# -*- coding: utf-8 -*-
"""Score fusion and normalization.

Implements Reciprocal Rank Fusion (RRF) and min-max normalization.

RRF formula:
    RRF(d) = Σ  1 / (k + rank_i(d))
             i

where k is a constant (default 60) and rank_i(d) is the rank of
document d in result list i (1-indexed).
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def normalize_scores(scores: List[float]) -> List[float]:
    """Min-max normalize scores to [0, 1].

    Returns all zeros if min == max.
    """
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    rng = hi - lo
    if rng == 0:
        return [0.0] * len(scores)
    return [(s - lo) / rng for s in scores]


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]],
    *,
    k: int = 60,
) -> List[Tuple[str, float]]:
    """Compute RRF scores across multiple ranked lists of document IDs.

    Parameters
    ----------
    ranked_lists:
        Each inner list is an ordered list of document IDs (best first).
    k:
        RRF constant. Higher k reduces the influence of high-ranking items.

    Returns
    -------
    list:
        ``[(doc_id, rrf_score), ...]`` sorted by descending RRF score.
    """
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank_0, doc_id in enumerate(ranked):
            rank_1 = rank_0 + 1  # 1-indexed
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank_1)

    result = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return result


def weighted_fusion(
    channel_scores: Dict[str, Dict[str, float]],
    weights: Dict[str, float],
) -> List[Tuple[str, float]]:
    """Weighted linear combination of per-channel scores.

    Parameters
    ----------
    channel_scores:
        ``{channel_name: {doc_id: normalized_score}}``
    weights:
        ``{channel_name: weight}``  — should sum to 1.0.

    Returns
    -------
    list:
        ``[(doc_id, combined_score)]`` sorted descending.
    """
    combined: Dict[str, float] = {}
    for channel, doc_scores in channel_scores.items():
        w = weights.get(channel, 0.0)
        for doc_id, score in doc_scores.items():
            combined[doc_id] = combined.get(doc_id, 0.0) + w * score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
