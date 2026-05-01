"""Module 8: Number Group Distribution."""
from __future__ import annotations

import pandas as pd

_GROUPS = {
    "lotto":     [(1, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 54)],
    "twostep":   [(1, 9), (10, 19), (20, 29), (30, 35)],
    "powerball": [(1, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 59), (60, 69)],
    "cash5":     [(1, 9), (10, 19), (20, 29), (30, 35)],
}

_PREFERRED_SPAN = {
    "lotto":     (4, 5),
    "twostep":   (3, 4),
    "powerball": (4, 5),
    "cash5":     (3, 4),
}


def group_label(num: int, game: str) -> str:
    for lo, hi in _GROUPS[game]:
        if lo <= num <= hi:
            return f"{lo}–{hi}"
    return "?"


def spans_groups(numbers: list[int], game: str) -> int:
    """Return number of distinct groups spanned."""
    groups_hit = set()
    for num in numbers:
        for lo, hi in _GROUPS[game]:
            if lo <= num <= hi:
                groups_hit.add((lo, hi))
    return len(groups_hit)


def passes_group_filter(numbers: list[int], game: str) -> tuple[bool, str]:
    span = spans_groups(numbers, game)
    lo, hi = _PREFERRED_SPAN[game]
    if lo <= span <= hi:
        return True, ""
    return False, f"Spans {span} groups (preferred {lo}–{hi})"


def compute_group_distribution(df: pd.DataFrame, game: str) -> dict:
    from app.services.data_loader import get_main_numbers
    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    groups = _GROUPS[game]
    span_counts: dict[int, int] = {}

    # Per-group frequency
    group_freq: dict[str, int] = {f"{lo}–{hi}": 0 for lo, hi in groups}

    for nums in df["numbers"]:
        span = spans_groups(nums, game)
        span_counts[span] = span_counts.get(span, 0) + 1
        for num in nums:
            lbl = group_label(num, game)
            if lbl in group_freq:
                group_freq[lbl] += 1

    total = len(df)
    return {
        "groups": [f"{lo}–{hi}" for lo, hi in groups],
        "group_freq": group_freq,
        "span_distribution": {
            k: {"count": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(span_counts.items())
        },
        "preferred_span": _PREFERRED_SPAN[game],
    }
