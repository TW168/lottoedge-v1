"""Module 17: Filtered Pick Generator."""
from __future__ import annotations

from math import ceil
import random

import numpy as np
import pandas as pd

from app.services.balance import analyze_balance, passes_balance_filter
from app.services.cluster import compute_clusters, is_anti_cluster
from app.services.composite_scorer import ScoringWeights, compute_composite_scores
from app.services.consecutive import passes_consecutive_filter
from app.services.game_theory import (
    calculate_number_popularity,
    compute_split_avoidance_utility,
)
from app.services.group_dist import passes_group_filter
from app.services.reinforcement_learning import LotteryRLAgent
from app.services.sum_range import passes_sum_gate
from app.services import (
    frequency as freq_mod,
    ml_engine,
    monte_carlo,
    positional as pos_mod,
    sum_range,
)

_PICK = {"lotto": 6, "twostep": 4, "powerball": 5, "cash5": 5}
_POOL = {"lotto": 54, "twostep": 35, "powerball": 69, "cash5": 35}
_BONUS_POOL = {"twostep": 35, "powerball": 26}


def generate_picks(
    df: pd.DataFrame,
    game: str,
    count: int = 5,
    weights: ScoringWeights | None = None,
    diversity_level: int = 60,
    precomputed: dict | None = None,
    excluded_main: set[tuple[int, ...]] | None = None,
    excluded_with_bonus: set[tuple[tuple[int, ...], int]] | None = None,
    recent_main_usage: dict[int, int] | None = None,
    recent_bonus_usage: dict[int, int] | None = None,
) -> list[dict]:
    """
    Generate `count` optimised picks for a given game.
    `precomputed` can contain pre-run analysis dicts to avoid recomputation.
    """
    pc = precomputed or {}

    freq_data = pc.get("freq_data") or freq_mod.compute_frequency(df, game)
    pos_data = pc.get("pos_data") or pos_mod.compute_positional(df, game)
    clust_data = pc.get("clust_data") or compute_clusters(df, game)
    sum_data = pc.get("sum_data") or sum_range.compute_sum_range(df, game)
    mc_data = pc.get("mc_data") or monte_carlo.run_monte_carlo(df, game, n_simulations=50_000)
    ml_models = pc.get("ml_models") or ml_engine.train_ensemble(df, game)
    ml_scores = pc.get("ml_scores") or ml_engine.predict_scores(ml_models, df, game)

    pool = list(range(1, _POOL[game] + 1))
    pick = _PICK[game]

    composite = compute_composite_scores(
        pool=pool,
        freq_data=freq_data,
        positional_data=pos_data,
        cluster_data=clust_data,
        ml_scores=ml_scores,
        mc_data=mc_data,
        weights=weights,
    )

    draw_history = _extract_draw_history(df, pick_size=pick)
    gt_scores = _compute_game_theory_scores(draw_history=draw_history, pool_size=_POOL[game])
    rl_scores = _compute_rl_scores(
        draw_history=draw_history,
        pool_size=_POOL[game],
        pick_size=pick,
    )

    composite = _blend_strategy_scores(
        base_scores=composite,
        gt_scores=gt_scores,
        rl_scores=rl_scores,
    )

    # Sort by score descending — top candidates
    ranked = sorted(pool, key=lambda n: composite.get(n, 0), reverse=True)

    anti_pairs = clust_data.get("anti_pairs", [])
    excluded_main = excluded_main or set()
    excluded_with_bonus = excluded_with_bonus or set()
    recent_main_usage = recent_main_usage or {}
    recent_bonus_usage = recent_bonus_usage or {}
    results: list[dict] = []
    seen_combos: set[tuple] = set()
    attempts = 0
    max_attempts = 2000

    # Expand candidate window based on requested diversity and ticket count.
    candidate_size = _dynamic_candidate_size(
        pool_size=len(pool),
        pick_size=pick,
        count=count,
        diversity_level=diversity_level,
    )
    candidates = ranked[:candidate_size]
    number_usage: dict[int, int] = dict.fromkeys(candidates, 0)
    bonus_usage: dict[int, int] = {}
    diversity_level = _clamp_int(diversity_level, 0, 100)
    max_overlap = _max_allowed_overlap(game, pick, diversity_level)
    max_number_usage = _max_number_usage(
        game=game,
        count=count,
        pick_size=pick,
        candidate_size=len(candidates),
        diversity_level=diversity_level,
    )

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        # Penalize heavily reused numbers so generated tickets have wider coverage.
        weights_list = [
            _history_penalized_weight(
                base_weight=_diversified_weight(
                    composite.get(n, 1),
                    number_usage.get(n, 0),
                    diversity_level,
                ),
                recent_usage=recent_main_usage.get(n, 0),
                diversity_level=diversity_level,
            )
            for n in candidates
        ]
        total_w = sum(weights_list)
        probs = [w / total_w for w in weights_list]

        try:
            chosen = _weighted_sample(candidates, pick, probs)
        except ValueError:
            continue

        combo = tuple(sorted(chosen))
        if combo in seen_combos:
            continue
        if combo in excluded_main:
            continue

        usage_cap = max_number_usage
        if attempts > max_attempts // 2:
            usage_cap += 1
        if any(number_usage.get(n, 0) >= usage_cap for n in combo):
            continue

        # Avoid near-duplicate tickets (for lotto: no 5/6 overlap; target <= 3 shared).
        overlap_cap = max_overlap
        if attempts > max_attempts // 2:
            overlap_cap += 1
        if any(_overlap_count(combo, tuple(r["numbers"])) > overlap_cap for r in results):
            continue

        # Validate
        passes, notes = _validate(list(combo), game, sum_data, anti_pairs)
        if not passes and attempts < max_attempts // 2:
            continue  # Try again first half; relax in second half

        seen_combos.add(combo)
        for num in combo:
            number_usage[num] = number_usage.get(num, 0) + 1
        combo_score = round(sum(composite.get(n, 0) for n in combo) / pick, 2)

        bal = analyze_balance(list(combo), game)

        result = {
            "numbers": list(combo),
            "composite_score": combo_score,
            "sum_value": sum(combo),
            "odd": bal["odd"],
            "even": bal["even"],
            "high": bal["high"],
            "low": bal["low"],
            "passes_sum_gate": passes_sum_gate(list(combo), sum_data)[0],
            "filter_notes": notes,
        }

        # Generate bonus ball if needed
        if game in _BONUS_POOL:
            bonus_pool = list(range(1, _BONUS_POOL[game] + 1))
            bonus_freq = _get_bonus_freq(df, game)
            bonus = _pick_bonus(
                bonus_pool=bonus_pool,
                freq=bonus_freq,
                bonus_usage=bonus_usage,
                recent_bonus_usage=recent_bonus_usage,
                diversity_level=diversity_level,
            )
            if (combo, bonus) in excluded_with_bonus:
                continue
            result["bonus"] = bonus
            bonus_usage[bonus] = bonus_usage.get(bonus, 0) + 1

        results.append(result)

    calibrated = _apply_display_score_calibration(results, game)
    return sorted(calibrated, key=lambda r: r["composite_score"], reverse=True)


def _apply_display_score_calibration(results: list[dict], game: str) -> list[dict]:
    """Pass through results without score manipulation.

    Scores are reported as-is from composite_scorer. No artificial
    calibration, banding, or flooring is applied.
    """
    return results


def _validate(combo: list[int], game: str, sum_data: dict, anti_pairs: list) -> tuple[bool, list[str]]:
    notes = []
    ok = True

    sum_ok, sum_note = passes_sum_gate(combo, sum_data)
    if not sum_ok:
        notes.append(sum_note)
        ok = False

    bal_ok, bal_note = passes_balance_filter(combo, game)
    if not bal_ok:
        notes.append(bal_note)
        ok = False

    grp_ok, grp_note = passes_group_filter(combo, game)
    if not grp_ok:
        notes.append(grp_note)
        ok = False

    con_ok, con_note = passes_consecutive_filter(combo)
    if not con_ok:
        notes.append(con_note)
        ok = False

    for i, a in enumerate(combo):
        for b in combo[i + 1:]:
            if is_anti_cluster(a, b, anti_pairs):
                notes.append(f"Anti-cluster pair ({a},{b})")
                ok = False
                break

    return ok, notes


def _weighted_sample(candidates: list[int], k: int, probs: list[float]) -> list[int]:
    rng = np.random.default_rng()
    p = np.array(probs)
    p /= p.sum()
    return [int(x) for x in rng.choice(candidates, size=k, replace=False, p=p)]


def _diversified_weight(base_weight: float, usage_count: int, diversity_level: int) -> float:
    """Reduce weight for numbers already used in prior generated tickets."""
    penalty_factor = 0.25 + (1.25 * (diversity_level / 100.0))
    return max(1e-6, base_weight / (1.0 + (penalty_factor * usage_count)))


def _history_penalized_weight(base_weight: float, recent_usage: int, diversity_level: int) -> float:
    """Penalize numbers that were overused in recent generator runs."""
    history_factor = 0.1 + (0.9 * (diversity_level / 100.0))
    return max(1e-6, base_weight / (1.0 + (history_factor * recent_usage)))


def _overlap_count(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    """Count shared numbers between two picks."""
    return len(set(a).intersection(b))


def _max_allowed_overlap(game: str, pick_size: int, diversity_level: int) -> int:
    """Return overlap cap between generated tickets for each game."""
    # Higher diversity level means lower overlap cap.
    relax = round((100 - diversity_level) / 35)
    if game in {"lotto", "powerball"}:
        return max(2, (pick_size - 3) + relax)
    return max(1, (pick_size - 2) + relax)


def _max_number_usage(
    game: str,
    count: int,
    pick_size: int,
    candidate_size: int,
    diversity_level: int,
) -> int:
    """Compute how many times a number may appear in one generated run."""
    avg_usage = (max(1, count) * max(1, pick_size)) / max(1, candidate_size)
    slack = 0.4 + ((100 - diversity_level) / 60.0)
    cap = ceil(avg_usage + slack)

    # Two Step needs stronger anti-repeat controls to avoid sticky anchors.
    if game == "twostep":
        cap = min(cap, 2 if diversity_level >= 45 else 3)
    return max(1, cap)


def _dynamic_candidate_size(
    pool_size: int,
    pick_size: int,
    count: int,
    diversity_level: int,
) -> int:
    """Choose candidate pool size to balance quality and diversity."""
    base = max(20, pick_size * 4)
    spread_target = (count * pick_size) + round((diversity_level / 100.0) * (pick_size * 3 + count))
    return min(pool_size, max(base, spread_target))


def _clamp_int(value: int, low: int, high: int) -> int:
    """Clamp integer values to a configured inclusive range."""
    return max(low, min(high, int(value)))


def _clamp(value: float) -> float:
    """Clamp a float to the inclusive [0, 1] range."""
    return max(0.0, min(1.0, float(value)))


def _get_bonus_freq(df: pd.DataFrame, game: str) -> dict[int, int]:
    """Count bonus ball appearances."""
    if "bonus" not in df.columns:
        return {}
    return df["bonus"].dropna().astype(int).value_counts().to_dict()


def _pick_bonus(
    bonus_pool: list[int],
    freq: dict,
    bonus_usage: dict[int, int],
    recent_bonus_usage: dict[int, int],
    diversity_level: int,
) -> int:
    if not freq:
        return random.choice(bonus_pool)

    weights = []
    penalty_factor = 0.2 + (1.4 * (diversity_level / 100.0))
    history_factor = 0.1 + (1.0 * (diversity_level / 100.0))
    for n in bonus_pool:
        base = float(freq.get(n, 1))
        run_penalty = 1.0 + (penalty_factor * bonus_usage.get(n, 0))
        history_penalty = 1.0 + (history_factor * recent_bonus_usage.get(n, 0))
        weights.append(max(1e-6, base / (run_penalty * history_penalty)))

    total = sum(weights)
    probs = [w / total for w in weights]
    rng = np.random.default_rng()
    return int(rng.choice(bonus_pool, p=probs))


def _extract_draw_history(df: pd.DataFrame, pick_size: int) -> list[list[int]]:
    """Extract historical draws from canonical n1..n6 columns."""
    cols = [f"n{i}" for i in range(1, pick_size + 1)]
    existing_cols = [col for col in cols if col in df.columns]
    if not existing_cols:
        return []

    history: list[list[int]] = []
    for _, row in df[existing_cols].iterrows():
        draw = [int(v) for v in row.tolist() if pd.notna(v)]
        if len(draw) == pick_size:
            history.append(sorted(draw))
    return history


def _compute_game_theory_scores(
    draw_history: list[list[int]],
    pool_size: int,
) -> dict[int, float]:
    """Compute split-avoidance utility scores for each number."""
    popularity = calculate_number_popularity(draw_history=draw_history, pool_size=pool_size)
    return compute_split_avoidance_utility(popularity)


def _compute_rl_scores(
    draw_history: list[list[int]],
    pool_size: int,
    pick_size: int,
) -> dict[int, float]:
    """Compute per-number RL preference scores."""
    agent = LotteryRLAgent(pool_size=pool_size, num_picks=pick_size)
    agent.train(draw_history=draw_history, episodes=200)
    return agent.number_scores()


def _blend_strategy_scores(
    base_scores: dict[int, float],
    gt_scores: dict[int, float],
    rl_scores: dict[int, float],
) -> dict[int, float]:
    """Blend base composite scores with game-theory and RL signals.

    The blend keeps the existing pipeline dominant while adding small tactical
    corrections from split-avoidance (game theory) and temporal adaptation (RL).
    """
    blended: dict[int, float] = {}
    for number, raw_score in base_scores.items():
        base = _clamp(raw_score / 100.0)
        gt = gt_scores.get(number, 0.5)
        rl = rl_scores.get(number, 0.5)
        score = (0.85 * base) + (0.10 * gt) + (0.05 * rl)
        blended[number] = round(_clamp(score) * 100, 2)
    return blended
