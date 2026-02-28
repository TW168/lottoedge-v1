"""Module 1: Frequency Analysis — hot, cold, overdue, momentum tracking."""
from __future__ import annotations

import pandas as pd
import numpy as np


def compute_frequency(df: pd.DataFrame, game: str) -> dict:
    """
    Compute frequency analysis across three time windows.
    Returns a dict keyed by number with frequency stats and classifications.
    """
    from app.services.data_loader import get_main_numbers

    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    pool = _get_pool(game)
    all_draws = df["numbers"].tolist()
    n = len(all_draws)

    short = all_draws[max(0, n - 10):]
    medium = all_draws[max(0, n - 30):]
    long_ = all_draws[max(0, n - 100):]

    def count(draws, num):
        return sum(1 for combo in draws if num in combo)

    result = {}
    for num in pool:
        sf = count(short, num)
        mf = count(medium, num)
        lf = count(long_, num)

        # Normalise to per-draw rates
        sr = sf / max(len(short), 1)
        mr = mf / max(len(medium), 1)
        lr = lf / max(len(long_), 1)

        # Trend
        if sr > lr * 1.2:
            trend = "rising"
        elif sr < lr * 0.8:
            trend = "falling"
        else:
            trend = "stable"

        result[num] = {
            "number": num,
            "short_freq": sf,
            "medium_freq": mf,
            "long_freq": lf,
            "short_rate": round(sr, 4),
            "medium_rate": round(mr, 4),
            "long_rate": round(lr, 4),
            "trend": trend,
            # classification filled below
            "classification": None,
            "heat_score": round(mr * 100, 2),
        }

    # Classification thresholds (top/bottom 20% by medium rate)
    rates = sorted([v["medium_rate"] for v in result.values()])
    n_rates = len(rates)
    hot_thresh = rates[int(n_rates * 0.80)] if n_rates else 0
    cold_thresh = rates[int(n_rates * 0.20)] if n_rates else 0

    # Overdue: current skip > average skip
    skips = _compute_skips(all_draws, pool)

    for num, data in result.items():
        mr = data["medium_rate"]
        avg_skip = skips.get(num, {}).get("avg_skip", 999)
        cur_skip = skips.get(num, {}).get("current_skip", 0)

        if mr >= hot_thresh:
            data["classification"] = "hot"
        elif mr <= cold_thresh:
            data["classification"] = "cold"
        elif cur_skip > avg_skip:
            data["classification"] = "overdue"
        else:
            data["classification"] = "neutral"

        data["avg_skip"] = avg_skip
        data["current_skip"] = cur_skip
        data["due_score"] = round(cur_skip / avg_skip, 3) if avg_skip > 0 else 0

    return result


def _get_pool(game: str) -> list[int]:
    if game == "lotto":
        return list(range(1, 55))
    if game == "twostep":
        return list(range(1, 36))
    return list(range(1, 70))  # powerball white balls


def _compute_skips(all_draws: list[list[int]], pool: list[int]) -> dict:
    """Compute average skip and current skip for each number."""
    result = {}
    n = len(all_draws)

    for num in pool:
        appearances = [i for i, combo in enumerate(all_draws) if num in combo]
        if len(appearances) < 2:
            avg_skip = n if not appearances else n - appearances[-1]
            cur_skip = (n - 1) - appearances[-1] if appearances else n
            result[num] = {"avg_skip": avg_skip, "current_skip": cur_skip}
            continue

        gaps = [appearances[i + 1] - appearances[i] for i in range(len(appearances) - 1)]
        avg_skip = float(np.mean(gaps))
        cur_skip = (n - 1) - appearances[-1]
        result[num] = {
            "avg_skip": round(avg_skip, 2),
            "current_skip": cur_skip,
            "max_skip": max(gaps),
        }

    return result


def get_skip_data(df: pd.DataFrame, game: str) -> dict:
    """Return skip data for all numbers (for Module 7 / charts)."""
    from app.services.data_loader import get_main_numbers
    df = get_main_numbers(df, game)
    if df.empty:
        return {}
    pool = _get_pool(game)
    all_draws = df["numbers"].tolist()
    return _compute_skips(all_draws, pool)
