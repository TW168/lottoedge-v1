"""Module 11: Coverage Design Optimizer — wheeling and balanced overlap systems."""
from __future__ import annotations

import math
from itertools import combinations


def _pick_count(game: str) -> int:
    return {"lotto": 6, "twostep": 4, "powerball": 5}[game]


def _pool_size(game: str) -> int:
    return {"lotto": 54, "twostep": 35, "powerball": 69}[game]


def full_wheel(numbers: list[int], pick: int) -> list[list[int]]:
    """Generate every combination (full wheel) from the given number pool."""
    return [list(c) for c in combinations(sorted(numbers), pick)]


def abbreviated_wheel(numbers: list[int], pick: int, budget: int) -> list[list[int]]:
    """
    Generate an abbreviated wheel: balanced coverage of up to `budget` tickets.
    Uses a greedy round-robin assignment ensuring each number appears roughly equally.
    This maximises pair coverage within the budget constraint.
    """
    numbers = sorted(numbers)
    n = len(numbers)
    if n < pick:
        return [numbers[:pick]] if n >= pick else []

    all_combos = list(combinations(numbers, pick))
    if len(all_combos) <= budget:
        return [list(c) for c in all_combos]

    # Greedy balanced selection: track per-number appearances
    selected: list[list[int]] = []
    appearances = {num: 0 for num in numbers}
    covered_pairs: set[tuple] = set()

    # Sort combos by pair coverage gain (descending)
    def pair_gain(combo):
        return sum(1 for p in combinations(combo, 2) if p not in covered_pairs)

    remaining = list(all_combos)
    while len(selected) < budget and remaining:
        # Score by pair gain first, then by balancing appearances
        best = max(remaining, key=lambda c: (
            pair_gain(c),
            -sum(appearances[x] for x in c)
        ))
        selected.append(list(best))
        remaining.remove(best)
        for p in combinations(best, 2):
            covered_pairs.add(p)
        for x in best:
            appearances[x] += 1

    return selected


def key_number_wheel(
    key_numbers: list[int],
    fill_numbers: list[int],
    pick: int,
    budget: int,
) -> list[list[int]]:
    """
    Key number wheel: key numbers appear on every ticket.
    Fill slots from fill_numbers up to pick count.
    """
    key_numbers = sorted(key_numbers)
    fill_numbers = sorted(set(fill_numbers) - set(key_numbers))
    fill_per_ticket = pick - len(key_numbers)

    if fill_per_ticket <= 0 or not fill_numbers:
        return [key_numbers[:pick]]

    all_fills = list(combinations(fill_numbers, fill_per_ticket))
    selected_fills = all_fills[:budget]
    return [sorted(key_numbers + list(f)) for f in selected_fills]


def compute_guarantee(
    n_pool: int, n_picks: int, pick: int, n_tickets: int
) -> str:
    """
    Simplified guarantee statement: given n_picks selected numbers,
    with n_tickets covering them, if at least W of your picks are in
    the winning draw, you are guaranteed at least a partial match.
    """
    # Rough heuristic: guarantee level based on coverage ratio
    total_combos = math.comb(n_picks, pick)
    coverage_ratio = min(1.0, n_tickets / total_combos) if total_combos > 0 else 0
    if coverage_ratio >= 1.0:
        return f"Full coverage: guaranteed jackpot if {pick}/{n_pool} winning numbers are in your pool"
    guaranteed_matches = max(2, int(pick * coverage_ratio))
    return (
        f"~{coverage_ratio * 100:.0f}% coverage of your {n_picks}-number pool; "
        f"estimated guarantee: {guaranteed_matches}-match if winning numbers are in pool"
    )


def build_coverage(
    game: str,
    numbers: list[int],
    budget: int,
    wheel_type: str = "abbreviated",
    key_numbers: list[int] | None = None,
) -> dict:
    """
    Main entry point: build a ticket set for the given configuration.

    wheel_type: "full" | "abbreviated" | "key_number"
    Returns: { tickets, ticket_count, cost, guarantee, coverage_pct, wheel_type }
    """
    pick = _pick_count(game)
    ticket_cost = {"lotto": 1, "twostep": 1, "powerball": 2}[game]

    numbers = sorted(set(numbers))
    if len(numbers) < pick:
        return {"error": f"Need at least {pick} numbers; got {len(numbers)}"}

    if wheel_type == "full":
        tickets = full_wheel(numbers, pick)
        if len(tickets) > 500:
            tickets = tickets[:500]  # safety cap
    elif wheel_type == "key_number" and key_numbers:
        key_numbers = [n for n in key_numbers if n in numbers]
        fill = [n for n in numbers if n not in key_numbers]
        tickets = key_number_wheel(key_numbers, fill, pick, budget)
    else:
        tickets = abbreviated_wheel(numbers, pick, budget)

    # Pair coverage analysis
    total_pairs = math.comb(len(numbers), 2)
    covered_pairs = set()
    for ticket in tickets:
        for p in combinations(ticket, 2):
            covered_pairs.add(p)
    coverage_pct = round(len(covered_pairs) / total_pairs * 100, 1) if total_pairs else 0

    guarantee = compute_guarantee(len(numbers), len(numbers), pick, len(tickets))

    return {
        "wheel_type": wheel_type,
        "pool": numbers,
        "tickets": tickets,
        "ticket_count": len(tickets),
        "cost": len(tickets) * ticket_cost,
        "ticket_cost": ticket_cost,
        "pair_coverage_pct": coverage_pct,
        "pairs_covered": len(covered_pairs),
        "total_pairs": total_pairs,
        "guarantee": guarantee,
    }
