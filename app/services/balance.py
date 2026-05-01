"""Modules 4 & 5: Odd/Even and High/Low balance analysis and filtering."""
from __future__ import annotations


# ── Game constants ─────────────────────────────────────────────────────────────

_ODD_EVEN_PREFERRED = {
    "lotto":     [(3, 3), (4, 2), (2, 4)],
    "twostep":   [(2, 2), (3, 1), (1, 3)],
    "powerball": [(3, 2), (2, 3), (4, 1), (1, 4)],
    "cash5":     [(3, 2), (2, 3), (4, 1), (1, 4)],
}

_HIGH_SPLIT = {
    "lotto":     28,   # High = 28-54, Low = 1-27
    "twostep":   18,   # High = 18-35, Low = 1-17
    "powerball": 35,   # High = 35-69, Low = 1-34
    "cash5":     18,   # High = 18-35, Low = 1-17
}


# ── Analysis ───────────────────────────────────────────────────────────────────

def analyze_balance(numbers: list[int], game: str) -> dict:
    """Return odd/even and high/low stats for a combination."""
    odd = sum(1 for n in numbers if n % 2 == 1)
    even = len(numbers) - odd

    split = _HIGH_SPLIT[game]
    high = sum(1 for n in numbers if n >= split)
    low = len(numbers) - high

    return {
        "odd": odd,
        "even": even,
        "high": high,
        "low": low,
        "odd_even_ok": (odd, even) in _ODD_EVEN_PREFERRED[game],
        "high_low_ok": (high, low) in _ODD_EVEN_PREFERRED[game],  # same preferred splits
    }


def passes_balance_filter(numbers: list[int], game: str) -> tuple[bool, str]:
    """Return (passes, reason). Used in pick generator validation."""
    stats = analyze_balance(numbers, game)
    if not stats["odd_even_ok"]:
        return False, f"Odd/even split {stats['odd']}/{stats['even']} not preferred"
    if not stats["high_low_ok"]:
        return False, f"High/low split {stats['high']}/{stats['low']} not preferred"
    return True, ""


def compute_historical_balance(df, game: str) -> dict:
    """Compute historical odd/even and high/low distribution for the dashboard."""
    from app.services.data_loader import get_main_numbers
    df = get_main_numbers(df, game)
    if df.empty:
        return {}

    oe_dist: dict[str, int] = {}
    hl_dist: dict[str, int] = {}

    split = _HIGH_SPLIT[game]
    for nums in df["numbers"]:
        odd = sum(1 for n in nums if n % 2 == 1)
        even = len(nums) - odd
        key_oe = f"{odd}o/{even}e"
        oe_dist[key_oe] = oe_dist.get(key_oe, 0) + 1

        high = sum(1 for n in nums if n >= split)
        low = len(nums) - high
        key_hl = f"{high}h/{low}l"
        hl_dist[key_hl] = hl_dist.get(key_hl, 0) + 1

    total = len(df)
    return {
        "odd_even": {
            k: {"count": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(oe_dist.items(), key=lambda x: x[1], reverse=True)
        },
        "high_low": {
            k: {"count": v, "pct": round(v / total * 100, 1)}
            for k, v in sorted(hl_dist.items(), key=lambda x: x[1], reverse=True)
        },
        "preferred_oe": [f"{o}o/{e}e" for o, e in _ODD_EVEN_PREFERRED[game]],
        "preferred_hl": [f"{h}h/{l}l" for h, l in _ODD_EVEN_PREFERRED[game]],
    }
