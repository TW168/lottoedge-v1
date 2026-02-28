"""Tests for frequency analysis."""
import pandas as pd
import pytest

from app.services.frequency import _compute_skips, compute_frequency


def _make_df(draws: list[list[int]]) -> pd.DataFrame:
    """Create a minimal DataFrame with a 'numbers' column."""
    return pd.DataFrame({"numbers": draws})


def _wrap_in_game_df(draws: list[list[int]], game: str = "twostep") -> pd.DataFrame:
    """Create a DataFrame with the right columns for get_main_numbers to work."""
    rows = []
    for nums in draws:
        row = {"n1": nums[0], "n2": nums[1], "n3": nums[2], "n4": nums[3], "bonus": None, "era": "era1", "is_bonus_era": False, "draw_date": None}
        rows.append(row)
    return pd.DataFrame(rows)


def test_skip_computation():
    # Number 5 appears at indices 0, 2, 4 — gaps are 2, 2
    draws = [[5, 10, 15, 20], [1, 2, 3, 4], [5, 6, 7, 8], [9, 11, 12, 13], [5, 14, 16, 17]]
    skips = _compute_skips(draws, [5])
    assert skips[5]["avg_skip"] == 2.0
    assert skips[5]["current_skip"] == 0  # appeared in last draw


def test_due_score_overdue():
    # Number 1 appears only at start, then absent
    draws = [[1, 2, 3, 4]] + [[5, 6, 7, 8]] * 20
    skips = _compute_skips(draws, [1])
    # current_skip = 20, avg_skip from just the one gap won't exist — handle gracefully
    assert skips[1]["current_skip"] == 20


def test_frequency_classifications():
    # Build 40 draws for twostep (4 numbers each)
    import random
    random.seed(42)
    draws = [sorted(random.sample(range(1, 36), 4)) for _ in range(50)]
    df = _wrap_in_game_df(draws)
    result = compute_frequency(df, "twostep")
    assert len(result) == 35
    # Every number should have a classification
    for num, data in result.items():
        assert data["classification"] in {"hot", "cold", "overdue", "neutral"}
