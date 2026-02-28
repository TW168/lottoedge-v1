"""Module 3: Cluster & Pair Analysis — co-occurrence frequencies and affinity scores."""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations

import pandas as pd


def compute_clusters(df: pd.DataFrame, game: str) -> dict:
    """
    Compute pair co-occurrence counts and affinity scores.
    Returns top 30 pairs, top 10 triplets, and anti-clusters.
    """
    from app.services.data_loader import get_main_numbers

    df = get_main_numbers(df, game)
    if df.empty:
        return {"pairs": [], "triplets": [], "anti_pairs": [], "pair_matrix": {}}

    n_draws = len(df)
    pick = _pick_count(game)
    pool_size = _pool_size(game)

    # Expected count per pair under uniform random
    # Each draw has C(pick,2) pairs; expected = n_draws * C(pick,2) / C(pool,2)
    from math import comb
    expected = n_draws * comb(pick, 2) / comb(pool_size, 2) if pool_size > pick else 1

    pair_counts: dict[tuple, int] = defaultdict(int)
    triplet_counts: dict[tuple, int] = defaultdict(int)

    for nums in df["numbers"]:
        for pair in combinations(sorted(nums), 2):
            pair_counts[pair] += 1
        for trip in combinations(sorted(nums), 3):
            triplet_counts[trip] += 1

    # Top pairs with affinity score
    pairs_list = [
        {
            "pair": list(p),
            "count": c,
            "affinity": round(c / expected, 3) if expected else 0,
        }
        for p, c in sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:30]
    ]

    # Top triplets
    triplets_list = [
        {"triplet": list(t), "count": c}
        for t, c in sorted(triplet_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Anti-clusters: pairs that appeared 0 or 1 time with the most draws
    anti = [
        {"pair": list(p), "count": c}
        for p, c in sorted(pair_counts.items(), key=lambda x: x[1])[:20]
        if c <= 1
    ]

    # Sparse pair matrix for lookup (only non-zero)
    pair_matrix: dict[int, dict[int, int]] = defaultdict(dict)
    for (a, b), c in pair_counts.items():
        pair_matrix[a][b] = c
        pair_matrix[b][a] = c

    return {
        "pairs": pairs_list,
        "triplets": triplets_list,
        "anti_pairs": anti,
        "pair_matrix": dict(pair_matrix),
        "expected_count": round(expected, 3),
    }


def pair_affinity_score(num: int, selected: list[int], pair_matrix: dict) -> float:
    """Average affinity score of num with already-selected numbers."""
    if not selected:
        return 0.5
    scores = [pair_matrix.get(num, {}).get(s, 0) for s in selected]
    return sum(scores) / len(scores)


def is_anti_cluster(a: int, b: int, anti_pairs: list[dict]) -> bool:
    pair = sorted([a, b])
    return any(p["pair"] == pair for p in anti_pairs)


def _pick_count(game: str) -> int:
    return {"lotto": 6, "twostep": 4, "powerball": 5}[game]


def _pool_size(game: str) -> int:
    return {"lotto": 54, "twostep": 35, "powerball": 69}[game]
