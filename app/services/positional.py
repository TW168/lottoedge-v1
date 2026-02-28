"""Module 2: Positional Analysis — which numbers appear most in each draw position."""
from __future__ import annotations

import pandas as pd


def compute_positional(df: pd.DataFrame, game: str) -> dict:
    """
    Build a positional frequency matrix.
    Returns: { position (1-indexed): { number: count } }
    """
    from app.services.data_loader import get_main_numbers

    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    pick = _pick_count(game)
    pool = _get_pool(game)

    # matrix[pos][num] = count
    matrix = {pos: {num: 0 for num in pool} for pos in range(1, pick + 1)}

    for nums in df["numbers"]:
        sorted_nums = sorted(nums)
        for pos, num in enumerate(sorted_nums, start=1):
            if pos <= pick:
                matrix[pos][num] += 1

    # Build leaders: top 5 per position
    leaders = {}
    for pos, counts in matrix.items():
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        leaders[pos] = [{"number": n, "count": c} for n, c in top]

    return {"matrix": matrix, "leaders": leaders, "positions": pick}


def positional_score(num: int, position: int, matrix: dict) -> float:
    """Return normalised positional score (0-1) for a number in a given position."""
    pos_counts = matrix.get(position, {})
    if not pos_counts:
        return 0.0
    max_count = max(pos_counts.values()) or 1
    return pos_counts.get(num, 0) / max_count


def _pick_count(game: str) -> int:
    return {"lotto": 6, "twostep": 4, "powerball": 5}[game]


def _get_pool(game: str) -> list[int]:
    if game == "lotto":
        return list(range(1, 55))
    if game == "twostep":
        return list(range(1, 36))
    return list(range(1, 70))
