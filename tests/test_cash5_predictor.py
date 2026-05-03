"""Tests for Cash Five prediction algorithms."""
from __future__ import annotations

import random

import pandas as pd
import pytest

from app.services.cash5_predictor import (
    EnsembleWeights,
    ensemble_predict,
    frequency_analysis,
    gap_analysis,
    hot_cold_analysis,
    markov_chain_analysis,
    monte_carlo_analysis,
    pattern_recognition_analysis,
    predict_from_dataframe,
)


@pytest.fixture
def synthetic_cash5_draws() -> list[list[int]]:
    """Build 1200 deterministic synthetic Cash Five draws.

    Returns:
        A list of sorted five-number combinations sampled from 1-35.
    """
    random.seed(20260430)
    draws: list[list[int]] = []
    for _ in range(1200):
        draws.append(sorted(random.sample(range(1, 36), 5)))
    return draws


@pytest.fixture
def synthetic_cash5_df(synthetic_cash5_draws: list[list[int]]) -> pd.DataFrame:
    """Convert synthetic draw list to DataFrame with n1-n5 schema."""
    rows = []
    for draw in synthetic_cash5_draws:
        rows.append(
            {
                "n1": draw[0],
                "n2": draw[1],
                "n3": draw[2],
                "n4": draw[3],
                "n5": draw[4],
            }
        )
    return pd.DataFrame(rows)


def test_frequency_analysis_returns_chi_square(
    synthetic_cash5_draws: list[list[int]],
):
    result = frequency_analysis(synthetic_cash5_draws)
    assert "chi_square" in result
    assert "p_value" in result
    assert len(result["counts"]) == 35
    assert 0.0 <= result["p_value"] <= 1.0


def test_hot_cold_deviation_window(
    synthetic_cash5_draws: list[list[int]],
):
    result = hot_cold_analysis(synthetic_cash5_draws, window=150)
    assert result["window"] == 150
    assert len(result["deviations"]) == 35


def test_gap_analysis_overdue_flags(
    synthetic_cash5_draws: list[list[int]],
):
    result = gap_analysis(synthetic_cash5_draws)
    overdue_count = sum(1 for m in result["metrics"].values() if m["overdue"])
    assert len(result["metrics"]) == 35
    assert overdue_count >= 0


def test_markov_chain_shape_and_predictions(
    synthetic_cash5_draws: list[list[int]],
):
    result = markov_chain_analysis(synthetic_cash5_draws)
    assert len(result["scores"]) == 35
    assert len(result["top_predictions"]) == 10


def test_monte_carlo_modal_numbers(
    synthetic_cash5_draws: list[list[int]],
):
    result = monte_carlo_analysis(synthetic_cash5_draws, simulations=1500)
    assert len(result["modal_numbers"]) == 5
    assert len(result["sample_tickets"]) == 10


def test_pattern_recognition_output(
    synthetic_cash5_draws: list[list[int]],
):
    result = pattern_recognition_analysis(synthetic_cash5_draws)
    assert "dominant_odd_count" in result
    assert "dominant_low_count" in result
    assert len(result["scores"]) == 35


def test_ensemble_predict_includes_split_and_ev(
    synthetic_cash5_draws: list[list[int]],
):
    result = ensemble_predict(
        draws=synthetic_cash5_draws,
        weights=EnsembleWeights(),
        window=120,
        monte_carlo_samples=1200,
        jackpot=120000.0,
        ticket_cost=1.0,
    )
    assert result["game"] == "cash5"
    assert len(result["top_numbers"]) == 5
    assert len(result["alternate_numbers"]) == 5
    assert 0.0 <= result["split_risk_score"] <= 100.0
    assert "ev_before_split" in result
    assert "ev_after_split" in result


def test_predict_from_dataframe(
    synthetic_cash5_df: pd.DataFrame,
):
    result = predict_from_dataframe(
        df=synthetic_cash5_df,
        weights=EnsembleWeights(),
        window=100,
        monte_carlo_samples=1000,
        jackpot=100000.0,
        ticket_cost=1.0,
    )
    assert result["game"] == "cash5"
    assert len(result["top_numbers"]) == 5


def test_markov_scores_are_not_all_equal(
    synthetic_cash5_draws: list[list[int]],
):
    """Markov scores must be non-uniform after the new-arrivals-only fix."""
    result = markov_chain_analysis(synthetic_cash5_draws, window=200)
    scores = list(result["scores"].values())
    assert len(set(round(s, 4) for s in scores)) > 1, (
        "All Markov scores are equal — transition matrix is still uniform"
    )


def test_monte_carlo_window_uses_recent_draws(
    synthetic_cash5_draws: list[list[int]],
):
    """Monte Carlo with a short window must differ from full-history run."""
    full = monte_carlo_analysis(synthetic_cash5_draws, simulations=2000, window=0)
    recent = monte_carlo_analysis(synthetic_cash5_draws, simulations=2000, window=50)
    # Scores need not be identical — if they are, the window had no effect.
    # With only 50 draws the frequency distribution should differ from the full 1200.
    full_scores = list(full["scores"].values())
    recent_scores = list(recent["scores"].values())
    assert full_scores != recent_scores, (
        "Monte Carlo window parameter had no effect on sampling probabilities"
    )


def test_pattern_recognition_has_sum_fields(
    synthetic_cash5_draws: list[list[int]],
):
    """Pattern recognition must now expose mean_sum and ideal_contribution."""
    result = pattern_recognition_analysis(synthetic_cash5_draws)
    assert "mean_sum" in result
    assert "ideal_contribution" in result
    # Ideal contribution should sit near the middle of the 1-35 pool
    assert 8.0 <= result["ideal_contribution"] <= 28.0
