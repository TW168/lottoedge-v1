"""Texas Cash Five prediction algorithms and ensemble scoring."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import comb
from statistics import mean, pstdev
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2

POOL_MIN = 1
POOL_MAX = 35
PICK_SIZE = 5


@dataclass
class EnsembleWeights:
    """Weights used by the Cash Five ensemble predictor."""

    frequency: float = 1.0
    hot_cold: float = 1.0
    gap: float = 1.0
    markov: float = 1.0
    monte_carlo: float = 1.0
    pattern: float = 1.0


def _extract_draws(df: pd.DataFrame) -> list[list[int]]:
    """Extract sorted Cash Five combinations from draw DataFrame rows.

    Numbers outside the valid pool (1–35) are silently dropped so that draws
    from other games stored in the same table cannot corrupt analysis functions.
    Rows that do not yield exactly five valid numbers after filtering are skipped.

    Args:
        df: Draw history with number columns n1-n5.

    Returns:
        List of sorted five-number combinations.
    """
    draws: list[list[int]] = []
    for _, row in df.iterrows():
        nums = [
            int(row[col])
            for col in ("n1", "n2", "n3", "n4", "n5")
            if POOL_MIN <= int(row[col]) <= POOL_MAX
        ]
        if len(nums) == PICK_SIZE:
            draws.append(sorted(nums))
    return draws


def _normalize_scores(raw: dict[int, float]) -> dict[int, float]:
    """Normalize a score map to range [0, 1].

    Args:
        raw: Raw number-to-score mapping.

    Returns:
        Normalized score mapping.
    """
    values = list(raw.values())
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return {k: 0.5 for k in raw}
    return {k: (v - min_v) / (max_v - min_v) for k, v in raw.items()}


def frequency_analysis(draws: list[list[int]]) -> dict[str, Any]:
    """Run frequency analysis and chi-square goodness-of-fit test.

    Mathematical basis:
        If draws are uniform, each number has expected count E = total_picks / 35.
        The chi-square statistic is X^2 = sum((O_i - E)^2 / E).

    Args:
        draws: Historical Cash Five combinations.

    Returns:
        Frequency counts, expected frequency, chi-square statistic, p-value,
        and normalized per-number scores.
    """
    counts = Counter()
    for combo in draws:
        counts.update(combo)

    total_picks = len(draws) * PICK_SIZE
    expected = total_picks / POOL_MAX if total_picks else 0.0

    if expected > 0:
        chi_square = sum(((counts.get(num, 0) - expected) ** 2) / expected for num in range(1, 36))
        p_value = float(chi2.sf(chi_square, POOL_MAX - 1))
    else:
        chi_square = 0.0
        p_value = 1.0

    score_map = {num: float(counts.get(num, 0)) for num in range(1, 36)}

    return {
        "counts": {num: counts.get(num, 0) for num in range(1, 36)},
        "expected_frequency": round(expected, 6),
        "chi_square": round(chi_square, 6),
        "p_value": round(p_value, 6),
        "scores": _normalize_scores(score_map),
    }


def hot_cold_analysis(draws: list[list[int]], window: int = 120) -> dict[str, Any]:
    """Compute rolling hot/cold deviations against expected frequency.

    Mathematical basis:
        In a window of N draws, expected count per number is N * 5 / 35.
        Deviation is O_i - E where O_i is observed count in the window.

    Args:
        draws: Historical Cash Five combinations.
        window: Number of most recent draws to analyze.

    Returns:
        Expected count, ranked deviations, and normalized score map.
    """
    recent = draws[-window:] if window > 0 else draws
    counts = Counter()
    for combo in recent:
        counts.update(combo)

    expected = (len(recent) * PICK_SIZE) / POOL_MAX if recent else 0.0
    deviations = {num: float(counts.get(num, 0) - expected) for num in range(1, 36)}
    ranked = sorted(deviations.items(), key=lambda kv: kv[1], reverse=True)

    return {
        "window": len(recent),
        "expected": round(expected, 6),
        "deviations": [{"number": num, "deviation": round(dev, 6)} for num, dev in ranked],
        "scores": _normalize_scores(deviations),
    }


def gap_analysis(draws: list[list[int]]) -> dict[str, Any]:
    """Compute gap statistics and flag overdue numbers.

    Mathematical basis:
        For each number i, define gaps as draw index differences between appearances.
        A number is flagged overdue when current_gap > mean_gap + std_gap.

    Args:
        draws: Historical Cash Five combinations.

    Returns:
        Gap metrics, overdue flags, and normalized due-score map.
    """
    appearances = {num: [] for num in range(1, 36)}
    for idx, combo in enumerate(draws):
        for num in combo:
            appearances[num].append(idx)

    metrics: dict[int, dict[str, float | bool]] = {}
    due_scores: dict[int, float] = {}
    total_draws = len(draws)

    for num in range(1, 36):
        idxs = appearances[num]
        if not idxs:
            current_gap = float(total_draws)
            mean_gap = float(total_draws)
            std_gap = 0.0
        elif len(idxs) == 1:
            current_gap = float(total_draws - 1 - idxs[-1])
            mean_gap = float(total_draws / 2)
            std_gap = mean_gap / 2
        else:
            gaps = [idxs[i + 1] - idxs[i] for i in range(len(idxs) - 1)]
            current_gap = float(total_draws - 1 - idxs[-1])
            mean_gap = float(mean(gaps))
            std_gap = float(pstdev(gaps)) if len(gaps) > 1 else 0.0

        threshold = mean_gap + std_gap
        overdue = current_gap > threshold
        due_score = current_gap / mean_gap if mean_gap > 0 else 0.0

        metrics[num] = {
            "current_gap": round(current_gap, 4),
            "mean_gap": round(mean_gap, 4),
            "std_gap": round(std_gap, 4),
            "overdue": overdue,
        }
        due_scores[num] = due_score

    return {
        "metrics": metrics,
        "scores": _normalize_scores(due_scores),
    }


def markov_chain_analysis(draws: list[list[int]], alpha: float = 1.0) -> dict[str, Any]:
    """Build a transition matrix and score next-draw likelihoods.

    Mathematical basis:
        Transition probability P(j|i) is estimated as:
        (count(i -> j) + alpha) / (row_total(i) + alpha * 35),
        where alpha is Laplace smoothing for sparse rows.

    Args:
        draws: Historical Cash Five combinations.
        alpha: Laplace smoothing value.

    Returns:
        Transition matrix, last draw, and normalized per-number predictions.
    """
    matrix = np.zeros((POOL_MAX, POOL_MAX), dtype=float)

    for idx in range(len(draws) - 1):
        current = draws[idx]
        nxt = draws[idx + 1]
        for i in current:
            for j in nxt:
                matrix[i - 1, j - 1] += 1.0

    row_sums = matrix.sum(axis=1, keepdims=True)
    probs = (matrix + alpha) / (row_sums + alpha * POOL_MAX)

    last_draw = draws[-1] if draws else []
    raw_scores = {num: 0.0 for num in range(1, 36)}
    if last_draw:
        for candidate in range(1, 36):
            raw_scores[candidate] = float(
                np.mean([probs[source - 1, candidate - 1] for source in last_draw])
            )

    return {
        "last_draw": last_draw,
        "scores": _normalize_scores(raw_scores),
        "top_predictions": [
            {"number": num, "score": round(score, 6)}
            for num, score in sorted(raw_scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ],
    }


def monte_carlo_analysis(draws: list[list[int]], simulations: int = 5000) -> dict[str, Any]:
    """Generate candidate tickets by weighted Monte Carlo simulation.

    Mathematical basis:
        Numbers are sampled without replacement using empirical probabilities
        estimated from historical frequency counts.

    Args:
        draws: Historical Cash Five combinations.
        simulations: Number of synthetic tickets to generate.

    Returns:
        Candidate ticket samples, per-number frequencies, and normalized scores.
    """
    counts = Counter()
    for combo in draws:
        counts.update(combo)

    total = sum(counts.values())
    if total == 0:
        probs = np.array([1 / POOL_MAX] * POOL_MAX)
    else:
        probs = np.array([counts.get(num, 0) / total for num in range(1, 36)], dtype=float)

    tickets: list[list[int]] = []
    hit_counts = Counter()
    population = np.arange(1, 36)

    for _ in range(max(simulations, 1)):
        ticket = np.random.choice(population, size=PICK_SIZE, replace=False, p=probs)
        nums = sorted(int(n) for n in ticket.tolist())
        tickets.append(nums)
        hit_counts.update(nums)

    raw_scores = {num: float(hit_counts.get(num, 0)) for num in range(1, 36)}
    modal_numbers = [num for num, _ in hit_counts.most_common(PICK_SIZE)]

    return {
        "simulations": simulations,
        "modal_numbers": sorted(modal_numbers),
        "scores": _normalize_scores(raw_scores),
        "sample_tickets": tickets[:10],
    }


def pattern_recognition_analysis(draws: list[list[int]]) -> dict[str, Any]:
    """Learn dominant historical composition patterns and score numbers.

    Mathematical basis:
        This model estimates common odd-count and low-count distributions from
        historical draws. Numbers are scored by how often they help satisfy
        the dominant composition constraints.

    Args:
        draws: Historical Cash Five combinations.

    Returns:
        Dominant pattern summary and normalized per-number pattern scores.
    """
    odd_counter = Counter()
    low_counter = Counter()
    consecutive_counter = Counter()

    for combo in draws:
        odd_count = sum(1 for n in combo if n % 2 == 1)
        low_count = sum(1 for n in combo if n <= 17)
        consecutive_count = sum(1 for i in range(len(combo) - 1) if combo[i + 1] - combo[i] == 1)
        odd_counter[odd_count] += 1
        low_counter[low_count] += 1
        consecutive_counter[consecutive_count] += 1

    dominant_odd = odd_counter.most_common(1)[0][0] if odd_counter else 3
    dominant_low = low_counter.most_common(1)[0][0] if low_counter else 2

    raw_scores: dict[int, float] = {}
    for num in range(1, 36):
        odd_match = dominant_odd / PICK_SIZE if num % 2 == 1 else (PICK_SIZE - dominant_odd) / PICK_SIZE
        low_match = dominant_low / PICK_SIZE if num <= 17 else (PICK_SIZE - dominant_low) / PICK_SIZE
        raw_scores[num] = (odd_match + low_match) / 2.0

    return {
        "dominant_odd_count": dominant_odd,
        "dominant_low_count": dominant_low,
        "dominant_consecutive_pairs": consecutive_counter.most_common(1)[0][0] if consecutive_counter else 1,
        "scores": _normalize_scores(raw_scores),
    }


def split_risk_score(numbers: list[int]) -> float:
    """Estimate co-winner risk from number-popularity heuristics.

    Mathematical basis:
        This is a heuristic index combining birthday-bias concentration,
        culturally popular picks, and consecutive runs. It models share risk,
        not win probability.

    Args:
        numbers: Predicted ticket numbers.

    Returns:
        Split-risk score in [0, 100], where larger means higher share risk.
    """
    if not numbers:
        return 0.0

    birthday_ratio = sum(1 for n in numbers if n <= 31) / len(numbers)
    common_pool = {1, 2, 3, 5, 7, 8, 11, 13, 21, 22, 23, 24}
    common_ratio = sum(1 for n in numbers if n in common_pool) / len(numbers)
    consecutive_pairs = sum(1 for i in range(len(numbers) - 1) if numbers[i + 1] - numbers[i] == 1)
    consecutive_ratio = consecutive_pairs / (len(numbers) - 1) if len(numbers) > 1 else 0.0

    raw = 100.0 * (0.55 * birthday_ratio + 0.30 * common_ratio + 0.15 * consecutive_ratio)
    return round(max(0.0, min(100.0, raw)), 4)


def ev_after_split(
    jackpot: float,
    split_risk: float,
    ticket_cost: float = 1.0,
    prize_match_4: float = 500.0,
    prize_match_3: float = 20.0,
) -> dict[str, float]:
    """Compute expected value before and after estimated jackpot splitting.

    Mathematical basis:
        EV_before = P5*J + P4*A4 + P3*A3 - cost.
        EV_after adjusts only jackpot term by expected split divisor:
        J_split = J / (1 + (split_risk/100)*4).

    Args:
        jackpot: Current jackpot estimate.
        split_risk: Split-risk score in [0, 100].
        ticket_cost: Cost per ticket.
        prize_match_4: Assumed 4-match prize.
        prize_match_3: Assumed 3-match prize.

    Returns:
        Dictionary containing EV values and split divisor.
    """
    p5 = 1.0 / comb(35, 5)
    p4 = (comb(5, 4) * comb(30, 1)) / comb(35, 5)
    p3 = (comb(5, 3) * comb(30, 2)) / comb(35, 5)

    expected_split_divisor = 1.0 + (max(0.0, min(split_risk, 100.0)) / 100.0) * 4.0

    ev_before = p5 * jackpot + p4 * prize_match_4 + p3 * prize_match_3 - ticket_cost
    ev_after = (
        p5 * (jackpot / expected_split_divisor)
        + p4 * prize_match_4
        + p3 * prize_match_3
        - ticket_cost
    )

    return {
        "ev_before_split": round(ev_before, 6),
        "ev_after_split": round(ev_after, 6),
        "expected_split_divisor": round(expected_split_divisor, 6),
    }


def ensemble_predict(
    draws: list[list[int]],
    weights: EnsembleWeights,
    window: int,
    monte_carlo_samples: int,
    jackpot: float,
    ticket_cost: float,
) -> dict[str, Any]:
    """Combine all Cash Five algorithms into a weighted ensemble prediction.

    Args:
        draws: Historical Cash Five combinations.
        weights: Per-algorithm ensemble weights.
        window: Rolling window for hot/cold analysis.
        monte_carlo_samples: Number of Monte Carlo simulations.
        jackpot: Jackpot value for EV estimation.
        ticket_cost: Cost per ticket.

    Returns:
        Combined result containing top numbers, alternates, confidence,
        split risk, and EV before/after split.
    """
    freq = frequency_analysis(draws)
    hot = hot_cold_analysis(draws, window=window)
    gap = gap_analysis(draws)
    markov = markov_chain_analysis(draws)
    mc = monte_carlo_analysis(draws, simulations=monte_carlo_samples)
    pattern = pattern_recognition_analysis(draws)

    weight_values = {
        "frequency": max(weights.frequency, 0.0),
        "hot_cold": max(weights.hot_cold, 0.0),
        "gap": max(weights.gap, 0.0),
        "markov": max(weights.markov, 0.0),
        "monte_carlo": max(weights.monte_carlo, 0.0),
        "pattern": max(weights.pattern, 0.0),
    }
    total_w = sum(weight_values.values()) or 1.0

    combined: dict[int, float] = {}
    for num in range(1, 36):
        combined[num] = (
            weight_values["frequency"] * freq["scores"][num]
            + weight_values["hot_cold"] * hot["scores"][num]
            + weight_values["gap"] * gap["scores"][num]
            + weight_values["markov"] * markov["scores"][num]
            + weight_values["monte_carlo"] * mc["scores"][num]
            + weight_values["pattern"] * pattern["scores"][num]
        ) / total_w

    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)
    top_numbers = sorted(num for num, _ in ranked[:5])
    alternates = sorted(num for num, _ in ranked[5:10])

    top_score_values = [score for _, score in ranked[:5]]
    confidence = round(float(np.mean(top_score_values) * 100.0), 4)

    split_risk = split_risk_score(top_numbers)
    ev_stats = ev_after_split(jackpot=jackpot, split_risk=split_risk, ticket_cost=ticket_cost)

    return {
        "game": "cash5",
        "top_numbers": top_numbers,
        "alternate_numbers": alternates,
        "confidence_score": confidence,
        "split_risk_score": split_risk,
        "ev_before_split": ev_stats["ev_before_split"],
        "ev_after_split": ev_stats["ev_after_split"],
        "components": {
            "frequency": freq,
            "hot_cold": hot,
            "gap": gap,
            "markov": markov,
            "monte_carlo": mc,
            "pattern": pattern,
        },
    }


def predict_from_dataframe(
    df: pd.DataFrame,
    weights: EnsembleWeights,
    window: int,
    monte_carlo_samples: int,
    jackpot: float,
    ticket_cost: float,
) -> dict[str, Any]:
    """Run the full Cash Five prediction flow from DataFrame input.

    Args:
        df: Draw history DataFrame with n1-n5 columns.
        weights: Ensemble weight configuration.
        window: Rolling window for hot/cold analysis.
        monte_carlo_samples: Number of Monte Carlo simulation tickets.
        jackpot: Jackpot value used in EV metrics.
        ticket_cost: Ticket cost in dollars.

    Returns:
        Prediction payload including algorithm outputs and ensemble metrics.
    """
    draws = _extract_draws(df)
    return ensemble_predict(
        draws=draws,
        weights=weights,
        window=window,
        monte_carlo_samples=monte_carlo_samples,
        jackpot=jackpot,
        ticket_cost=ticket_cost,
    )
