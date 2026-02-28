"""Module 14: Expected Value Calculator."""
from __future__ import annotations

from app.services.probability import lotto_odds, twostep_odds, powerball_odds

# Ticket costs
TICKET_COST = {"lotto": 1.0, "twostep": 1.0, "powerball": 2.0}

# Tax discount (federal + state estimate for Texas — no state income tax)
FEDERAL_TAX_RATE = 0.37
# Texas has no state income tax, so effective take-home on lump sum ≈ 63%
LUMP_SUM_DISCOUNT = 0.60  # annuity-to-lump-sum is ~60% of advertised

# Signal thresholds
HOLD_THRESHOLD = -0.5      # EV per dollar wagered < -0.5 → HOLD
CONSIDER_THRESHOLD = -0.2  # EV per dollar wagered between -0.5 and -0.2 → CONSIDER
# Above CONSIDER_THRESHOLD → FAVORABLE


def compute_ev(game: str, jackpot: float, is_annuity: bool = True) -> dict:
    """
    Calculate expected value per ticket at the given jackpot level.
    jackpot: raw advertised jackpot amount (annuity value if is_annuity=True).
    """
    cost = TICKET_COST[game]

    # Adjust jackpot to after-tax lump sum
    if is_annuity:
        effective_jackpot = jackpot * LUMP_SUM_DISCOUNT * (1 - FEDERAL_TAX_RATE)
    else:
        effective_jackpot = jackpot * (1 - FEDERAL_TAX_RATE)

    if game == "lotto":
        tiers = lotto_odds()
    elif game == "twostep":
        tiers = twostep_odds()
    else:
        tiers = powerball_odds()

    ev = 0.0
    for tier in tiers:
        prob = tier["probability"]
        amount = tier["fixed_amount"]
        if amount is None:
            # Jackpot tier
            amount = effective_jackpot
        ev += prob * amount

    ev -= cost
    ev_per_dollar = ev / cost

    if ev_per_dollar < HOLD_THRESHOLD:
        signal = "HOLD"
    elif ev_per_dollar < CONSIDER_THRESHOLD:
        signal = "CONSIDER"
    else:
        signal = "FAVORABLE"

    # Breakeven jackpot (raw advertised, before tax adjustments)
    breakeven = _breakeven_jackpot(game, tiers, cost, is_annuity)

    return {
        "game": game,
        "jackpot_raw": jackpot,
        "jackpot_effective": round(effective_jackpot, 2),
        "ticket_cost": cost,
        "ev": round(ev, 4),
        "ev_per_dollar": round(ev_per_dollar, 4),
        "signal": signal,
        "breakeven_jackpot": round(breakeven, 0),
        "tier_contributions": [
            {
                "match": t["match"] if "match" in t else str(t.get("match_main")),
                "prize": t["prize"],
                "probability": t["probability"],
                "contribution": round(t["probability"] * (t["fixed_amount"] or effective_jackpot), 6),
            }
            for t in tiers
        ],
    }


def _breakeven_jackpot(game: str, tiers: list[dict], cost: float, is_annuity: bool) -> float:
    """Estimate the raw jackpot amount where EV = 0."""
    # Sum of EV from non-jackpot tiers
    fixed_ev = sum(
        t["probability"] * t["fixed_amount"]
        for t in tiers
        if t["fixed_amount"] is not None
    )
    jackpot_prob = next(t["probability"] for t in tiers if t["fixed_amount"] is None)

    # We need: jackpot_prob * effective_jackpot + fixed_ev = cost
    needed_effective = (cost - fixed_ev) / jackpot_prob if jackpot_prob > 0 else float("inf")

    # Convert effective → raw (reverse the tax+discount)
    discount = LUMP_SUM_DISCOUNT if is_annuity else 1.0
    raw = needed_effective / (discount * (1 - FEDERAL_TAX_RATE))
    return max(raw, 0)
