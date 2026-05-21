"""Persistence and usage snapshots for generated picks."""
from __future__ import annotations

import json
from pathlib import Path

STORE_PATH = Path("data/pick_history.json")
_SUPPORTED_GAMES = ("lotto", "twostep", "powerball", "cash5")


def _default_payload() -> dict:
    """Create the default payload shape.

    Returns:
        Empty game-to-history mapping.
    """
    return {"games": {game: [] for game in _SUPPORTED_GAMES}}


def _load_payload() -> dict:
    """Load history payload from disk, returning defaults if absent/invalid.

    Returns:
        Parsed payload with required keys.
    """
    if not STORE_PATH.exists():
        return _default_payload()

    try:
        payload = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_payload()

    merged = _default_payload()
    games = payload.get("games", {}) if isinstance(payload, dict) else {}
    for game, rows in games.items():
        if game in merged["games"] and isinstance(rows, list):
            merged["games"][game] = rows
    return merged


def _save_payload(payload: dict) -> None:
    """Persist history payload to disk.

    Args:
        payload: Payload to write.
    """
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record_generated_picks(
    game: str,
    picks: list[dict],
    max_history: int = 300,
) -> None:
    """Append generated picks to on-disk history.

    Args:
        game: Game key.
        picks: Generated pick payloads.
        max_history: Max rows to retain per game.
    """
    if game not in _SUPPORTED_GAMES:
        return

    payload = _load_payload()
    rows = payload["games"][game]

    for pick in picks:
        numbers = sorted(int(n) for n in pick.get("numbers", []))
        if not numbers:
            continue
        row = {"numbers": numbers}
        bonus = pick.get("bonus")
        if bonus is not None:
            row["bonus"] = int(bonus)
        rows.append(row)

    payload["games"][game] = rows[-max(1, int(max_history)):]
    _save_payload(payload)


def recent_usage_snapshot(game: str, window: int = 80) -> dict[str, dict[int, int]]:
    """Count recent number usage from generated pick history.

    Args:
        game: Game key.
        window: Number of most recent generated picks to analyze.

    Returns:
        Usage maps for main and bonus values.
    """
    payload = _load_payload()
    rows = payload["games"].get(game, [])[-max(1, int(window)) :]

    main_usage: dict[int, int] = {}
    bonus_usage: dict[int, int] = {}

    for row in rows:
        for number in row.get("numbers", []):
            number_int = int(number)
            main_usage[number_int] = main_usage.get(number_int, 0) + 1

        bonus = row.get("bonus")
        if bonus is not None:
            bonus_int = int(bonus)
            bonus_usage[bonus_int] = bonus_usage.get(bonus_int, 0) + 1

    return {"main": main_usage, "bonus": bonus_usage}


def recent_anchor_pairs(
    game: str,
    window: int = 80,
    prefix_len: int = 2,
) -> set[tuple[int, ...]]:
    """Collect recent leading-number tuples from generated picks.

    Args:
        game: Game key.
        window: Number of most recent generated picks to analyze.
        prefix_len: Leading tuple size to capture from each sorted pick.

    Returns:
        Set of leading tuples observed in recent history.
    """
    payload = _load_payload()
    rows = payload["games"].get(game, [])[-max(1, int(window)) :]

    out: set[tuple[int, ...]] = set()
    for row in rows:
        numbers = sorted(int(n) for n in row.get("numbers", []))
        if len(numbers) >= prefix_len:
            out.add(tuple(numbers[:prefix_len]))
    return out
