"""Module 17: Filtered Pick Generator."""
from __future__ import annotations

import random
from itertools import combinations

import pandas as pd

from app.services.balance import passes_balance_filter
from app.services.cluster import is_anti_cluster
from app.services.composite_scorer import ScoringWeights, compute_composite_scores
from app.services.consecutive import passes_consecutive_filter
from app.services.group_dist import passes_group_filter
from app.services.sum_range import passes_sum_gate, score_sum

_PICK = {"lotto": 6, "twostep": 4, "powerball": 5}
_POOL = {"lotto": 54, "twostep": 35, "powerball": 69}
_BONUS_POOL = {"twostep": 35, "powerball": 26}


def generate_picks(
    df: pd.DataFrame,
    game: str,
    count: int = 5,
    include_era2: bool = False,
    weights: ScoringWeights | None = None,
    precomputed: dict | None = None,
) -> list[dict]:
    """
    Generate `count` optimised picks for a given game.
    `precomputed` can contain pre-run analysis dicts to avoid recomputation.
    """
    from app.services import (
        cluster as cluster_mod,
        frequency as freq_mod,
        ml_engine,
        monte_carlo,
        positional as pos_mod,
        sum_range,
    )

    pc = precomputed or {}

    freq_data = pc.get("freq_data") or freq_mod.compute_frequency(df, game)
    pos_data = pc.get("pos_data") or pos_mod.compute_positional(df, game)
    clust_data = pc.get("clust_data") or cluster_mod.compute_clusters(df, game)
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

    # Sort by score descending — top candidates
    ranked = sorted(pool, key=lambda n: composite.get(n, 0), reverse=True)

    anti_pairs = clust_data.get("anti_pairs", [])
    results: list[dict] = []
    seen_combos: set[tuple] = set()
    attempts = 0
    max_attempts = 2000

    # Use top 20 candidates; expand if we can't fill `count` valid combos
    candidate_size = max(20, pick * 4)
    candidates = ranked[:candidate_size]

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        # Sample pick numbers from candidates, weighted by composite score
        weights_list = [composite.get(n, 1) for n in candidates]
        total_w = sum(weights_list)
        probs = [w / total_w for w in weights_list]

        try:
            chosen = _weighted_sample(candidates, pick, probs)
        except ValueError:
            continue

        combo = tuple(sorted(chosen))
        if combo in seen_combos:
            continue

        # Validate
        passes, notes = _validate(list(combo), game, sum_data, anti_pairs)
        if not passes and attempts < max_attempts // 2:
            continue  # Try again first half; relax in second half

        seen_combos.add(combo)
        combo_score = round(sum(composite.get(n, 0) for n in combo) / pick, 2)

        from app.services.balance import analyze_balance
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
            result["bonus"] = _pick_bonus(bonus_pool, bonus_freq)

        results.append(result)

    return sorted(results, key=lambda r: r["composite_score"], reverse=True)


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

    con_ok, con_note = passes_consecutive_filter(combo)
    if not con_ok:
        notes.append(con_note)

    for i, a in enumerate(combo):
        for b in combo[i + 1:]:
            if is_anti_cluster(a, b, anti_pairs):
                notes.append(f"Anti-cluster pair ({a},{b})")
                ok = False
                break

    return ok, notes


def _weighted_sample(candidates: list[int], k: int, probs: list[float]) -> list[int]:
    import numpy as np
    p = np.array(probs)
    p /= p.sum()
    return [int(x) for x in np.random.choice(candidates, size=k, replace=False, p=p)]


def _get_bonus_freq(df: pd.DataFrame, game: str) -> dict[int, int]:
    """Count bonus ball appearances."""
    if "bonus" not in df.columns:
        return {}
    counts = df["bonus"].dropna().astype(int).value_counts().to_dict()
    return counts


def _pick_bonus(bonus_pool: list[int], freq: dict) -> int:
    if not freq:
        return random.choice(bonus_pool)
    weights = [freq.get(n, 1) for n in bonus_pool]
    total = sum(weights)
    probs = [w / total for w in weights]
    import numpy as np
    return int(np.random.choice(bonus_pool, p=probs))
