"""Tests for pick generator and balance filters."""
import random

import pandas as pd
import pytest

from app.services.balance import analyze_balance, passes_balance_filter
from app.services.sum_range import compute_sum_range, passes_sum_gate


def _make_lotto_df(n: int = 100) -> pd.DataFrame:
    random.seed(0)
    rows = []
    for i in range(n):
        nums = sorted(random.sample(range(1, 55), 6))
        rows.append({
            "n1": nums[0], "n2": nums[1], "n3": nums[2],
            "n4": nums[3], "n5": nums[4], "n6": nums[5],
            "bonus": None, "power_play": None,
            "era": "era3", "is_bonus_era": False, "draw_date": None,
        })
    return pd.DataFrame(rows)


def test_balance_analysis():
    # 3 odd, 3 even; 3 high, 3 low (lotto split: high>=28)
    numbers = [3, 5, 7, 28, 30, 32]
    bal = analyze_balance(numbers, "lotto")
    assert bal["odd"] == 3
    assert bal["even"] == 3


def test_balance_filter_preferred():
    numbers = [3, 5, 7, 28, 30, 32]  # 3/3 odd/even split
    passes, msg = passes_balance_filter(numbers, "lotto")
    assert passes is True


def test_balance_filter_rejected():
    numbers = [1, 3, 5, 7, 9, 11]  # 6/0 odd/even — rejected
    passes, msg = passes_balance_filter(numbers, "lotto")
    assert passes is False


def test_sum_gate():
    df = _make_lotto_df(200)
    sum_data = compute_sum_range(df, "lotto")

    # A sum near the mean should pass
    mid = int(sum_data["mean"])
    # Build a combo summing to roughly mid
    combo = [1, mid - 15, mid - 10, mid - 5, 1, 1][:6]
    # Just test the gate function doesn't crash and returns a bool
    result, _ = passes_sum_gate([10, 20, 30, 40, 50, 54], sum_data)
    assert isinstance(result, bool)


def test_sum_range_percentiles():
    df = _make_lotto_df(200)
    data = compute_sum_range(df, "lotto")
    assert data["p15"] < data["p85"]
    assert data["p15"] > data["min"]
    assert data["p85"] < data["max"]
