"""Module 10: Barboianu Probability Engine — exact odds for all prize tiers."""
from __future__ import annotations

from math import comb


def lottery_probability(n: int, k: int, p: int, t: int) -> float:
    """
    P(match exactly t numbers) in a lottery L(n, k, p, t).
    n = pool size, k = ticket pick count, p = drawn count, t = match count.
    Formula: C(p,t) * C(n-p, k-t) / C(n,k)
    """
    if t > min(k, p) or k - t > n - p:
        return 0.0
    return comb(p, t) * comb(n - p, k - t) / comb(n, k)


# ── Texas Lotto odds ───────────────────────────────────────────────────────────

LOTTO_TIERS = [
    {"match": 6, "prize": "Jackpot ($5M+)", "fixed_amount": None},
    {"match": 5, "prize": "$2,000",         "fixed_amount": 2000},
    {"match": 4, "prize": "$50",            "fixed_amount": 50},
    {"match": 3, "prize": "$3",             "fixed_amount": 3},
]


def lotto_odds() -> list[dict]:
    n, k = 54, 6
    tiers = []
    for tier in LOTTO_TIERS:
        t = tier["match"]
        prob = lottery_probability(n, k, k, t)
        odds = round(1 / prob) if prob > 0 else None
        tiers.append({**tier, "probability": prob, "odds": f"1 in {odds:,}" if odds else "N/A"})
    return tiers


# ── Texas Two Step odds ────────────────────────────────────────────────────────

TWOSTEP_TIERS = [
    {"match": "4+BB", "prize": "Jackpot ($200K+)", "fixed_amount": None,   "match_main": 4, "match_bonus": 1},
    {"match": "4",    "prize": "$100",              "fixed_amount": 100,    "match_main": 4, "match_bonus": 0},
    {"match": "3+BB", "prize": "$25",               "fixed_amount": 25,     "match_main": 3, "match_bonus": 1},
    {"match": "3",    "prize": "$5",                "fixed_amount": 5,      "match_main": 3, "match_bonus": 0},
    {"match": "2+BB", "prize": "$4",                "fixed_amount": 4,      "match_main": 2, "match_bonus": 1},
    {"match": "1+BB", "prize": "$3",                "fixed_amount": 3,      "match_main": 1, "match_bonus": 1},
    {"match": "0+BB", "prize": "$2",                "fixed_amount": 2,      "match_main": 0, "match_bonus": 1},
]


def twostep_odds() -> list[dict]:
    """Texas Two Step uses two separate draws (main 4/35 + bonus 1/35)."""
    n_main, k_main = 35, 4
    n_bonus = 35  # bonus drawn independently

    tiers = []
    for tier in TWOSTEP_TIERS:
        mm = tier["match_main"]
        mb = tier["match_bonus"]

        # P(match mm of 4 main numbers from pool of 35)
        p_main = lottery_probability(n_main, k_main, k_main, mm)
        # P(match bonus ball) = 1/35
        p_bonus = (1 / n_bonus) if mb == 1 else ((n_bonus - 1) / n_bonus)

        prob = p_main * p_bonus
        odds = round(1 / prob) if prob > 0 else None
        tiers.append({**tier, "probability": prob, "odds": f"1 in {odds:,}" if odds else "N/A"})
    return tiers


# ── Powerball odds ─────────────────────────────────────────────────────────────

POWERBALL_TIERS = [
    {"match": "5+PB", "prize": "Jackpot ($20M+)", "fixed_amount": None,        "match_white": 5, "match_pb": 1},
    {"match": "5",    "prize": "$1,000,000",       "fixed_amount": 1_000_000,   "match_white": 5, "match_pb": 0},
    {"match": "4+PB", "prize": "$50,000",          "fixed_amount": 50_000,      "match_white": 4, "match_pb": 1},
    {"match": "4",    "prize": "$100",             "fixed_amount": 100,         "match_white": 4, "match_pb": 0},
    {"match": "3+PB", "prize": "$100",             "fixed_amount": 100,         "match_white": 3, "match_pb": 1},
    {"match": "3",    "prize": "$7",               "fixed_amount": 7,           "match_white": 3, "match_pb": 0},
    {"match": "2+PB", "prize": "$7",               "fixed_amount": 7,           "match_white": 2, "match_pb": 1},
    {"match": "1+PB", "prize": "$4",               "fixed_amount": 4,           "match_white": 1, "match_pb": 1},
    {"match": "0+PB", "prize": "$4",               "fixed_amount": 4,           "match_white": 0, "match_pb": 1},
]


# ── Texas Cash Five odds ──────────────────────────────────────────────────────

CASH5_TIERS = [
    {"match": 5, "prize": "Jackpot", "fixed_amount": None},
    {"match": 4, "prize": "$500", "fixed_amount": 500},
    {"match": 3, "prize": "$20", "fixed_amount": 20},
]


def cash5_odds() -> list[dict]:
    """Texas Cash Five exact odds for 5/35 game structure."""
    n, k = 35, 5
    tiers = []
    for tier in CASH5_TIERS:
        t = tier["match"]
        prob = lottery_probability(n, k, k, t)
        odds = round(1 / prob) if prob > 0 else None
        tiers.append({**tier, "probability": prob, "odds": f"1 in {odds:,}" if odds else "N/A"})
    return tiers


def powerball_odds() -> list[dict]:
    n_white, k_white = 69, 5
    n_pb = 26

    tiers = []
    for tier in POWERBALL_TIERS:
        mw = tier["match_white"]
        mpb = tier["match_pb"]

        p_white = lottery_probability(n_white, k_white, k_white, mw)
        p_pb = (1 / n_pb) if mpb == 1 else ((n_pb - 1) / n_pb)

        prob = p_white * p_pb
        odds = round(1 / prob) if prob > 0 else None
        tiers.append({**tier, "probability": prob, "odds": f"1 in {odds:,}" if odds else "N/A"})
    return tiers


# ── Convenience dispatcher ─────────────────────────────────────────────────────

def get_odds(game: str) -> list[dict]:
    if game == "cash5":
        return cash5_odds()
    if game == "lotto":
        return lotto_odds()
    if game == "twostep":
        return twostep_odds()
    return powerball_odds()
