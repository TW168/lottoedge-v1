"""Module 6: Sum Range Analysis + Howard's 70% Rule."""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_sum_range(df: pd.DataFrame, game: str) -> dict:
    """
    Compute sum distribution and the 70% band (15th–85th percentile).
    """
    from app.services.data_loader import get_main_numbers

    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    sums = [sum(nums) for nums in df["numbers"]]

    p15 = float(np.percentile(sums, 15))
    p85 = float(np.percentile(sums, 85))

    # Histogram bins
    min_sum = int(min(sums))
    max_sum = int(max(sums))
    bins = list(range(min_sum, max_sum + 2, max(1, (max_sum - min_sum) // 40)))
    hist, edges = np.histogram(sums, bins=bins)

    return {
        "min": min_sum,
        "max": max_sum,
        "mean": round(float(np.mean(sums)), 1),
        "median": float(np.median(sums)),
        "p15": round(p15, 1),
        "p85": round(p85, 1),
        "histogram": {
            "counts": hist.tolist(),
            "edges": [round(e, 1) for e in edges.tolist()],
        },
        "total_draws": len(sums),
    }


def passes_sum_gate(numbers: list[int], sum_data: dict) -> tuple[bool, str]:
    """Return (passes, reason). The primary validation gate for pick generation."""
    if not sum_data:
        return True, ""
    total = sum(numbers)
    low = sum_data.get("p15", 0)
    high = sum_data.get("p85", float("inf"))
    if low <= total <= high:
        return True, ""
    return False, f"Sum {total} outside 70% band [{low:.0f}–{high:.0f}]"


def score_sum(numbers: list[int], sum_data: dict) -> float:
    """Return 0–1 score based on how centrally the sum falls in the 70% band."""
    if not sum_data:
        return 0.5
    total = sum(numbers)
    mid = (sum_data["p15"] + sum_data["p85"]) / 2
    half_range = (sum_data["p85"] - sum_data["p15"]) / 2
    if half_range == 0:
        return 1.0
    distance = abs(total - mid) / half_range
    return max(0.0, 1.0 - distance)
