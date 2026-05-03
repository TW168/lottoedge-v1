"""CSV parsing and era detection for all three games."""
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.database import Draw


# ── Era boundary constants ─────────────────────────────────────────────────────

LOTTO_ERA2_START = date(2003, 5, 7)
LOTTO_ERA2_END = date(2006, 4, 22)

PB_ERA2_START = date(2012, 1, 18)
PB_ERA3_START = date(2015, 10, 7)


# ── Era detection ──────────────────────────────────────────────────────────────

def _lotto_era(d: date) -> str:
    if d < LOTTO_ERA2_START:
        return "era1"
    if d <= LOTTO_ERA2_END:
        return "era2"
    return "era3"


def _pb_era(d: date) -> str:
    if d < PB_ERA2_START:
        return "era1"
    if d < PB_ERA3_START:
        return "era2"
    return "era3"


# ── CSV loaders ────────────────────────────────────────────────────────────────

def load_texas_lotto(filepath: str | Path) -> pd.DataFrame:
    """
    Load Texas Lotto CSV with era detection.
    Columns: Game Name, Month, Day, Year, Num1-Num5, [Num6 or Bonus Ball]
    """
    df = pd.read_csv(
        filepath,
        header=None,
        names=["game", "month", "day", "year", "n1", "n2", "n3", "n4", "n5", "n6"],
    )
    df["draw_date"] = pd.to_datetime(df[["year", "month", "day"]]).dt.date
    df["era"] = df["draw_date"].apply(_lotto_era)
    df["is_bonus_era"] = df["era"] == "era2"
    return df.sort_values("draw_date").reset_index(drop=True)


def load_texas_two_step(filepath: str | Path) -> pd.DataFrame:
    """
    Load Texas Two Step CSV. Single consistent format.
    Columns: Game Name, Month, Day, Year, Num1-Num4, Bonus Ball
    """
    df = pd.read_csv(
        filepath,
        header=None,
        names=["game", "month", "day", "year", "n1", "n2", "n3", "n4", "bonus"],
    )
    df["draw_date"] = pd.to_datetime(df[["year", "month", "day"]]).dt.date
    df["era"] = "era1"
    df["is_bonus_era"] = False
    return df.sort_values("draw_date").reset_index(drop=True)


def load_texas_cash_five(filepath: str | Path) -> pd.DataFrame:
    """
    Load Texas Cash Five CSV.
    Columns: Game Name, Month, Day, Year, Num1-Num5
    """
    df = pd.read_csv(
        filepath,
        header=None,
        names=["game", "month", "day", "year", "n1", "n2", "n3", "n4", "n5"],
    )
    df["draw_date"] = pd.to_datetime(df[["year", "month", "day"]]).dt.date
    df["era"] = "era1"
    df["is_bonus_era"] = False
    return df.sort_values("draw_date").reset_index(drop=True)


def load_powerball(filepath: str | Path) -> pd.DataFrame:
    """
    Load Powerball CSV with era detection.
    Columns: Game Name, Month, Day, Year, Num1-Num5, Powerball, Power Play
    """
    df = pd.read_csv(
        filepath,
        header=None,
        names=["game", "month", "day", "year", "n1", "n2", "n3", "n4", "n5", "bonus", "power_play"],
    )
    df["draw_date"] = pd.to_datetime(df[["year", "month", "day"]]).dt.date
    df["era"] = df["draw_date"].apply(_pb_era)
    df["is_bonus_era"] = False
    return df.sort_values("draw_date").reset_index(drop=True)


# ── DB import ──────────────────────────────────────────────────────────────────

def upsert_draws(db: Session, game: str, df: pd.DataFrame) -> dict[str, int]:
    """Insert new draws into DB and update existing dates if values changed."""
    existing_by_date = {
        r.draw_date: r
        for r in db.query(Draw).filter(Draw.game == game).all()
    }

    rows = []
    updated = 0

    tracked_fields = [
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "n6",
        "bonus",
        "power_play",
        "era",
        "is_bonus_era",
    ]

    for _, row in df.iterrows():
        row_date = row["draw_date"]
        existing_row = existing_by_date.get(row_date)

        payload = {
            "n1": int(row["n1"]),
            "n2": int(row["n2"]),
            "n3": int(row["n3"]),
            "n4": int(row["n4"]),
            "n5": int(row["n5"]) if pd.notna(row.get("n5")) else None,
            "n6": int(row["n6"]) if pd.notna(row.get("n6")) else None,
            "bonus": int(row["bonus"]) if pd.notna(row.get("bonus")) else None,
            "power_play": int(row["power_play"]) if pd.notna(row.get("power_play")) else None,
            "era": row["era"],
            "is_bonus_era": bool(row.get("is_bonus_era", False)),
        }

        if existing_row is not None:
            changed = False
            for field in tracked_fields:
                if getattr(existing_row, field) != payload[field]:
                    setattr(existing_row, field, payload[field])
                    changed = True

            if changed:
                updated += 1
            continue

        draw = Draw(
            game=game,
            draw_date=row_date,
            **payload,
        )
        rows.append(draw)

    inserted = len(rows)
    if rows or updated:
        db.bulk_save_objects(rows)
        db.commit()

    return {"inserted": inserted, "updated": updated}


def get_draws_df(db: Session, game: str, include_era2: bool = False) -> pd.DataFrame:
    """
    Return all draws for a game as a DataFrame.
    For Texas Lotto, exclude era2 by default (different game structure).
    """
    query = db.query(Draw).filter(Draw.game == game)
    if game == "lotto" and not include_era2:
        query = query.filter(Draw.era != "era2")
    if game == "powerball" and not include_era2:
        query = query.filter(Draw.era == "era3")
    draws = query.order_by(Draw.draw_date).all()

    if not draws:
        return pd.DataFrame()

    records = []
    for d in draws:
        records.append({
            "draw_date": d.draw_date,
            "n1": d.n1, "n2": d.n2, "n3": d.n3, "n4": d.n4,
            "n5": d.n5, "n6": d.n6,
            "bonus": d.bonus,
            "power_play": d.power_play,
            "era": d.era,
            "is_bonus_era": d.is_bonus_era,
        })
    return pd.DataFrame(records)


def get_main_numbers(df: pd.DataFrame, game: str) -> pd.DataFrame:
    """
    Return a DataFrame with only the main number columns as a list per row.
    Each row gets a 'numbers' column containing a sorted list.
    For era2 lotto draws, n6 is a bonus ball — exclude it from main numbers.
    """
    if game == "lotto":
        # Era2 draws: n6 is the bonus ball, not a 6th main number.
        # Only include n6 for non-era2 rows.
        def _lotto_nums(row):
            nums = [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]
            if not row.get("is_bonus_era", False) and pd.notna(row.get("n6")):
                nums.append(row["n6"])
            return sorted([int(x) for x in nums if pd.notna(x)])

        result = df.copy()
        result["numbers"] = result.apply(_lotto_nums, axis=1)
        return result
    elif game == "twostep":
        cols = ["n1", "n2", "n3", "n4"]
    elif game == "cash5":
        cols = ["n1", "n2", "n3", "n4", "n5"]
        result = df.copy()
        result["numbers"] = result[cols].apply(
            lambda row: sorted([int(x) for x in row if pd.notna(x) and 1 <= int(x) <= 35]),
            axis=1,
        )
        # Drop rows that don't have exactly 5 valid numbers (bad/mixed data)
        result = result[result["numbers"].apply(len) == 5].reset_index(drop=True)
        return result
    else:  # powerball
        cols = ["n1", "n2", "n3", "n4", "n5"]

    result = df.copy()
    result["numbers"] = result[cols].apply(
        lambda row: sorted([int(x) for x in row if pd.notna(x)]), axis=1
    )
    return result


def count_draws(db: Session, game: str, include_era2: bool = False) -> int:
    query = db.query(Draw).filter(Draw.game == game)
    if game == "lotto" and not include_era2:
        query = query.filter(Draw.era != "era2")
    if game == "powerball" and not include_era2:
        query = query.filter(Draw.era == "era3")
    return query.count()
