"""Module 13: Monte Carlo Simulation using historical frequency distributions."""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd


def run_monte_carlo(
    df: pd.DataFrame,
    game: str,
    n_simulations: int = 100_000,
) -> dict:
    """
    Simulate n_simulations draws using historical frequency as weights.
    Returns frequency counts for each number across simulations.
    """
    from app.services.data_loader import get_main_numbers
    from app.services.frequency import _get_pool

    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    pool = _get_pool(game)
    pick = _pick_count(game)

    # Build probability weights from historical frequency
    all_numbers = [n for nums in df["numbers"] for n in nums]
    counter = Counter(all_numbers)
    weights = np.array([counter.get(n, 0) for n in pool], dtype=float)
    if weights.sum() == 0:
        weights = np.ones(len(pool))
    weights /= weights.sum()

    # Run simulations
    sim_counts = Counter()
    rng = np.random.default_rng(42)

    for _ in range(n_simulations):
        drawn = rng.choice(pool, size=pick, replace=False, p=weights)
        for n in drawn:
            sim_counts[n] += 1

    total_appearances = sum(sim_counts.values())

    return {
        "simulations": n_simulations,
        "counts": {n: sim_counts.get(n, 0) for n in pool},
        "frequencies": {
            n: round(sim_counts.get(n, 0) / total_appearances * 100, 4)
            for n in pool
        },
        "top_numbers": sorted(pool, key=lambda n: sim_counts.get(n, 0), reverse=True)[:15],
    }


def _pick_count(game: str) -> int:
    return {"lotto": 6, "twostep": 4, "powerball": 5}[game]
