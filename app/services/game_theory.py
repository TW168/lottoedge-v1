"""Game-theoretic utilities for split-avoidance number selection."""

from __future__ import annotations

import numpy as np


def calculate_number_popularity(
    draw_history: list[list[int]],
    pool_size: int,
    recency_decay: float = 0.995,
) -> dict[int, float]:
    """Estimate normalized popularity for each number.

    Args:
        draw_history: Ordered historical draws (oldest to newest).
        pool_size: Count of valid numbers in this game pool.
        recency_decay: Per-step decay for older draws; values closer to 1 keep
            history flatter while lower values favor recent draws.

    Returns:
        Mapping of number -> normalized popularity score in [0, 1].
    """
    weights = np.zeros(pool_size, dtype=float)
    if not draw_history:
        return {n: 0.5 for n in range(1, pool_size + 1)}

    for step, draw in enumerate(reversed(draw_history)):
        decay_weight = recency_decay**step
        for raw_num in draw:
            num = int(raw_num)
            if 1 <= num <= pool_size:
                weights[num - 1] += decay_weight

    lo = float(np.min(weights))
    hi = float(np.max(weights))
    if hi <= lo:
        return {n: 0.5 for n in range(1, pool_size + 1)}

    return {
        n: float((weights[n - 1] - lo) / (hi - lo)) for n in range(1, pool_size + 1)
    }


def compute_split_avoidance_utility(popularity: dict[int, float]) -> dict[int, float]:
    """Convert popularity into utility for avoiding shared jackpots.

    Lower-popularity numbers receive higher utility.

    Args:
        popularity: Mapping of number -> popularity score in [0, 1].

    Returns:
        Mapping of number -> utility score in [0, 1].
    """
    return {number: 1.0 - score for number, score in popularity.items()}


def game_theoretic_selection(
    utility_scores: dict[int, float],
    num_picks: int,
) -> list[int]:
    """Select highest-utility numbers from split-avoidance scores.

    Args:
        utility_scores: Mapping of number -> utility score in [0, 1].
        num_picks: Number of numbers to return.

    Returns:
        Sorted list of selected numbers.
    """
    ranked = sorted(utility_scores.items(), key=lambda item: item[1], reverse=True)
    return sorted([number for number, _ in ranked[:num_picks]])