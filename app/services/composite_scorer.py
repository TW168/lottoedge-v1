"""Module 16: Composite Scoring Engine — combine all module scores into 0–100 per number."""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class ScoringWeights:
    frequency: float = 15.0
    positional: float = 12.0
    cluster: float = 10.0
    due_score: float = 12.0
    momentum: float = 8.0
    heat: float = 8.0
    group: float = 5.0
    lstm: float = 10.0
    ensemble: float = 10.0
    monte_carlo: float = 5.0
    coverage: float = 5.0

    def normalised(self) -> "ScoringWeights":
        total = sum(vars(self).values())
        if total == 0:
            return self
        d = {k: v / total for k, v in vars(self).items()}
        return ScoringWeights(**d)


def compute_composite_scores(
    pool: list[int],
    freq_data: dict,
    positional_data: dict,
    cluster_data: dict,
    ml_scores: dict[int, float],
    mc_data: dict,
    weights: ScoringWeights | None = None,
) -> dict[int, float]:
    """
    Score every number in the pool from 0–100.
    All sub-scores are normalised to 0–1 before weighting.
    """
    if weights is None:
        weights = ScoringWeights()

    w = weights.normalised()
    pair_matrix = cluster_data.get("pair_matrix", {})
    mc_counts = mc_data.get("counts", {})
    mc_max = max(mc_counts.values(), default=1) or 1
    pos_matrix = positional_data.get("matrix", {})

    scores: dict[int, float] = {}

    for num in pool:
        fd = freq_data.get(num, {})

        # Sub-scores (all 0–1)
        s_freq = _norm(fd.get("medium_rate", 0), 0, _max_rate(freq_data, "medium_rate"))
        s_heat = _norm(fd.get("short_rate", 0), 0, _max_rate(freq_data, "short_rate"))
        s_due = _clamp(fd.get("due_score", 1.0) / 3.0)   # cap at 3x overdue
        s_momentum = 1.0 if fd.get("trend") == "rising" else 0.5 if fd.get("trend") == "stable" else 0.2

        # Positional: average score across all positions
        if pos_matrix:
            pos_scores = [
                pos_matrix.get(pos, {}).get(num, 0)
                for pos in pos_matrix
            ]
            pos_max = max(
                max(pos_matrix[pos].values(), default=1) for pos in pos_matrix
            ) or 1
            s_pos = sum(pos_scores) / (len(pos_scores) * pos_max) if pos_scores else 0.5
        else:
            s_pos = 0.5

        # Cluster: avg pair count with top co-appearing numbers
        raw_pairs = list(pair_matrix.get(num, {}).values())
        max_pair = max((max(v.values(), default=0) for v in pair_matrix.values()), default=1) or 1
        s_cluster = (sum(raw_pairs[:5]) / (5 * max_pair)) if raw_pairs else 0.5

        # Group (value = 1 if number belongs to a diverse group, else 0.5)
        s_group = 0.5  # computed externally when selecting combos

        s_ml = ml_scores.get(num, 0.5)
        s_mc = _norm(mc_counts.get(num, 0), 0, mc_max)

        # Combine
        score = (
            w.frequency  * s_freq +
            w.positional * s_pos +
            w.cluster    * s_cluster +
            w.due_score  * s_due +
            w.momentum   * s_momentum +
            w.heat       * s_heat +
            w.group      * s_group +
            w.lstm       * s_ml +      # lstm folded into ml_scores
            w.ensemble   * s_ml +
            w.monte_carlo * s_mc +
            w.coverage   * 0.5         # coverage computed at combo level
        ) * 100

        scores[num] = round(_clamp(score / 100) * 100, 2)

    return scores


def _max_rate(freq_data: dict, key: str) -> float:
    vals = [v.get(key, 0) for v in freq_data.values() if isinstance(v, dict)]
    return max(vals, default=1) or 1


def _norm(val: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.5
    return _clamp((val - lo) / (hi - lo))


def _clamp(val: float) -> float:
    return max(0.0, min(1.0, val))
