"""Persistent storage and lookup helpers for excluded lottery picks."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException

STORE_PATH = Path("data/excluded_picks.json")
_PICK_SIZE = {"lotto": 6, "twostep": 4, "powerball": 5, "cash5": 5}
_POOL_MAX = {"lotto": 54, "twostep": 35, "powerball": 69, "cash5": 35}
_BONUS_MAX = {"twostep": 35, "powerball": 26}


def _default_payload() -> dict:
    """Create the default exclusion payload shape.

    Returns:
        Empty payload with all supported games and list keys present.
    """
    return {
        "lotto": {"main": []},
        "cash5": {"main": []},
        "twostep": {"main": [], "with_bonus": []},
        "powerball": {"main": [], "with_bonus": []},
    }


def load_store() -> dict:
    """Load exclusions from disk.

    Returns:
        Parsed exclusion payload. If no file exists, returns default payload.

    Raises:
        HTTPException: If the stored JSON cannot be parsed.
    """
    if not STORE_PATH.exists():
        return _default_payload()

    try:
        payload = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Excluded picks store is corrupted and could not be parsed.",
        ) from exc

    merged = _default_payload()
    for game, game_data in payload.items():
        if game in merged and isinstance(game_data, dict):
            merged[game].update(game_data)
    return merged


def save_store(payload: dict) -> None:
    """Persist exclusions to disk.

    Args:
        payload: Exclusion payload to write.
    """
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def normalize_numbers(game: str, numbers: list[int]) -> list[int]:
    """Validate and normalize a main-number set for a game.

    Args:
        game: Game key (lotto, twostep, powerball, cash5).
        numbers: Proposed numbers.

    Returns:
        Sorted number list.

    Raises:
        HTTPException: If game is unknown or numbers are invalid.
    """
    if game not in _PICK_SIZE:
        raise HTTPException(status_code=400, detail=f"Unsupported game: {game}")

    required = _PICK_SIZE[game]
    if len(numbers) != required:
        raise HTTPException(
            status_code=400,
            detail=f"{game} requires exactly {required} main numbers.",
        )

    pool_max = _POOL_MAX[game]
    if any(n < 1 or n > pool_max for n in numbers):
        raise HTTPException(
            status_code=400,
            detail=f"{game} numbers must be in the range 1-{pool_max}.",
        )

    uniq = sorted({int(n) for n in numbers})
    if len(uniq) != required:
        raise HTTPException(status_code=400, detail="Main numbers must be unique.")
    return uniq


def normalize_bonus(game: str, bonus: int | None) -> int | None:
    """Validate bonus value for games that include a bonus ball.

    Args:
        game: Game key.
        bonus: Bonus value or None.

    Returns:
        Normalized bonus value.

    Raises:
        HTTPException: If bonus is invalid for the game.
    """
    if game not in _BONUS_MAX:
        return None

    if bonus is None:
        raise HTTPException(status_code=400, detail=f"{game} requires a bonus value.")

    max_bonus = _BONUS_MAX[game]
    if bonus < 1 or bonus > max_bonus:
        raise HTTPException(
            status_code=400,
            detail=f"{game} bonus must be in the range 1-{max_bonus}.",
        )
    return int(bonus)


def add_exclusion(game: str, numbers: list[int], bonus: int | None = None) -> dict:
    """Add an exclusion entry if it does not already exist.

    Args:
        game: Game key.
        numbers: Main number set.
        bonus: Optional bonus value.

    Returns:
        Summary payload including whether an insert occurred.
    """
    norm_numbers = normalize_numbers(game, numbers)
    norm_bonus = normalize_bonus(game, bonus)
    payload = load_store()

    inserted = False
    if game in _BONUS_MAX:
        row = {"numbers": norm_numbers, "bonus": norm_bonus}
        bucket = payload[game]["with_bonus"]
        if row not in bucket:
            bucket.append(row)
            inserted = True
    else:
        bucket = payload[game]["main"]
        if norm_numbers not in bucket:
            bucket.append(norm_numbers)
            inserted = True

    if inserted:
        save_store(payload)

    return {
        "game": game,
        "numbers": norm_numbers,
        "bonus": norm_bonus,
        "inserted": inserted,
    }


def main_exclusions(game: str) -> set[tuple[int, ...]]:
    """Read exclusion set for main-number combinations.

    Args:
        game: Game key.

    Returns:
        Set of normalized tuples for quick membership checks.
    """
    payload = load_store()
    rows = payload.get(game, {}).get("main", [])
    return {tuple(sorted(int(n) for n in row)) for row in rows}


def bonus_exclusions(game: str) -> set[tuple[tuple[int, ...], int]]:
    """Read exclusion set for full combinations with bonus.

    Args:
        game: Game key.

    Returns:
        Set of ((main numbers), bonus) tuples.
    """
    payload = load_store()
    rows = payload.get(game, {}).get("with_bonus", [])
    out: set[tuple[tuple[int, ...], int]] = set()
    for row in rows:
        nums = tuple(sorted(int(n) for n in row.get("numbers", [])))
        bonus = int(row.get("bonus", 0))
        if nums and bonus:
            out.add((nums, bonus))
    return out
