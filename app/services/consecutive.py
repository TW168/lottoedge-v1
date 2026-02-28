"""Module 9: Consecutive Number Analysis."""
from __future__ import annotations

import pandas as pd


def count_consecutive_pairs(numbers: list[int]) -> int:
    s = sorted(numbers)
    return sum(1 for i in range(len(s) - 1) if s[i + 1] - s[i] == 1)


def compute_consecutive_stats(df: pd.DataFrame, game: str) -> dict:
    from app.services.data_loader import get_main_numbers
    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    total = len(df)
    with_any = sum(1 for nums in df["numbers"] if count_consecutive_pairs(nums) >= 1)
    with_two = sum(1 for nums in df["numbers"] if count_consecutive_pairs(nums) >= 2)

    return {
        "total_draws": total,
        "with_any_consecutive_pct": round(with_any / total * 100, 1),
        "with_two_plus_pct": round(with_two / total * 100, 1),
        "recommended_max_consecutive_pairs": 1,
    }


def passes_consecutive_filter(numbers: list[int], max_pairs: int = 2) -> tuple[bool, str]:
    pairs = count_consecutive_pairs(numbers)
    if pairs <= max_pairs:
        return True, ""
    return False, f"Too many consecutive pairs ({pairs})"
