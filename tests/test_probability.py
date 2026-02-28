"""Tests for Barboianu probability engine."""
from math import comb

import pytest

from app.services.probability import (
    get_odds,
    lotto_odds,
    lottery_probability,
    powerball_odds,
    twostep_odds,
)


def test_jackpot_probability():
    # Texas Lotto jackpot: C(6,6)*C(48,0)/C(54,6)
    expected = 1 / comb(54, 6)
    prob = lottery_probability(54, 6, 6, 6)
    assert abs(prob - expected) < 1e-12


def test_lotto_odds_structure():
    tiers = lotto_odds()
    assert len(tiers) == 4
    jackpot_tier = next(t for t in tiers if t["match"] == 6)
    assert jackpot_tier["odds"] == "1 in 25,827,165"


def test_lotto_odds_jackpot_value():
    tiers = lotto_odds()
    jackpot_prob = tiers[0]["probability"]
    assert abs(1 / jackpot_prob - 25_827_165) < 10  # within 10 of published odds


def test_powerball_jackpot_odds():
    tiers = powerball_odds()
    jackpot_tier = tiers[0]
    # Published: 1 in 292,201,338
    assert abs(1 / jackpot_tier["probability"] - 292_201_338) < 1000


def test_probabilities_sum_less_than_one():
    for game in ["lotto", "twostep", "powerball"]:
        tiers = get_odds(game)
        total = sum(t["probability"] for t in tiers)
        assert total < 1.0, f"{game} total probability >= 1: {total}"


def test_lottery_probability_zero_for_impossible():
    # Can't match 7 when only 6 drawn
    assert lottery_probability(54, 6, 6, 7) == 0.0
