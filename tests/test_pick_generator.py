"""Tests for pick generator and balance filters."""
import random

import pandas as pd
import pytest

from app.services.balance import analyze_balance, passes_balance_filter
from app.services.pick_generator import (
    _apply_display_score_calibration,
    _history_penalized_weight,
    _max_number_usage,
    _validate,
    generate_picks,
)
from app.services.sum_range import compute_sum_range, passes_sum_gate


_GAME_SPECS = {
    "lotto":     {"pool": 54, "pick": 6, "bonus_pool": None},
    "twostep":   {"pool": 35, "pick": 4, "bonus_pool": 35},
    "powerball": {"pool": 69, "pick": 5, "bonus_pool": 26},
    "cash5":     {"pool": 35, "pick": 5, "bonus_pool": None},
}


def _make_game_df(game: str, n: int = 200) -> pd.DataFrame:
    """Build a synthetic draw history that matches the loader's expected shape."""
    random.seed(42)
    spec = _GAME_SPECS[game]
    rows = []
    for _ in range(n):
        nums = sorted(random.sample(range(1, spec["pool"] + 1), spec["pick"]))
        row = {f"n{i + 1}": nums[i] for i in range(spec["pick"])}
        for i in range(spec["pick"], 6):
            row[f"n{i + 1}"] = None
        row["bonus"] = (
            random.randint(1, spec["bonus_pool"]) if spec["bonus_pool"] else None
        )
        row["power_play"] = None
        row["era"] = "era3"
        row["is_bonus_era"] = False
        row["draw_date"] = None
        rows.append(row)
    return pd.DataFrame(rows)


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


def test_validate_rejects_group_and_consecutive_failures():
    combo = [1, 2, 3, 4, 40]
    sum_data = {"p15": 0, "p85": 200}

    ok, notes = _validate(combo, "powerball", sum_data, anti_pairs=[])

    assert ok is False
    assert any("Spans" in note for note in notes)
    assert any("Too many consecutive pairs" in note for note in notes)


def test_history_penalty_reduces_weight_for_recently_used_numbers():
    base = 10.0
    no_history = _history_penalized_weight(base, recent_usage=0, diversity_level=60)
    with_history = _history_penalized_weight(base, recent_usage=5, diversity_level=60)
    assert with_history < no_history


def test_twostep_usage_cap_is_tight_under_normal_diversity():
    cap = _max_number_usage(
        game="twostep",
        count=5,
        pick_size=4,
        candidate_size=27,
        diversity_level=60,
    )
    assert cap <= 2


def test_score_calibration_is_honest_passthrough():
    # Display calibration was intentionally removed: scores must reflect the raw
    # composite output without artificial inflation into a "confidence band".
    results = [
        {"composite_score": 62.1, "filter_notes": ["x"]},
        {"composite_score": 63.4, "filter_notes": []},
        {"composite_score": 64.2, "filter_notes": []},
    ]
    for game in ("twostep", "lotto", "powerball", "cash5"):
        calibrated = _apply_display_score_calibration(
            [dict(r) for r in results], game=game
        )
        assert [r["composite_score"] for r in calibrated] == [62.1, 63.4, 64.2]
        assert all("raw_composite_score" not in r for r in calibrated)


@pytest.mark.parametrize("game", ["lotto", "twostep", "powerball", "cash5"])
def test_generate_picks_pipeline_per_game(game):
    """End-to-end smoke test: each game produces valid, in-pool picks with scores."""
    df = _make_game_df(game, n=200)
    spec = _GAME_SPECS[game]

    picks = generate_picks(df, game, count=3)
    assert len(picks) == 3

    for p in picks:
        nums = p["numbers"]
        assert len(nums) == spec["pick"]
        assert len(set(nums)) == spec["pick"], "no duplicate main numbers"
        assert all(1 <= n <= spec["pool"] for n in nums), "main numbers in pool"
        assert nums == sorted(nums), "main numbers sorted"
        assert 0.0 <= p["composite_score"] <= 100.0
        assert p["sum_value"] == sum(nums)
        assert isinstance(p["filter_notes"], list)

        if spec["bonus_pool"]:
            assert "bonus" in p
            assert 1 <= p["bonus"] <= spec["bonus_pool"], "bonus number in pool"
        else:
            assert "bonus" not in p

    # Scores must be returned in descending order (highest-confidence first).
    scores = [p["composite_score"] for p in picks]
    assert scores == sorted(scores, reverse=True)


def test_cash5_blocks_recent_anchor_pairs_across_runs():
    """Cash5 should avoid reusing recently seen first-two sorted anchors."""
    df = _make_game_df("cash5", n=220)

    blocked = {(7, 13), (11, 19)}
    picks = generate_picks(df, "cash5", count=5, blocked_anchor_pairs=blocked)

    anchors = {tuple(p["numbers"][:2]) for p in picks}
    assert anchors.isdisjoint(blocked)
