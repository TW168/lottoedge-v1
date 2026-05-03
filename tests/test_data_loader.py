"""Tests for CSV parsing and era detection."""
import io
from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.database import Base, Draw
from app.services.data_loader import (
    _lotto_era,
    _pb_era,
    count_draws,
    get_draws_df,
    load_texas_lotto,
    load_texas_two_step,
    upsert_draws,
)


def test_lotto_era_detection():
    assert _lotto_era(date(2000, 1, 1)) == "era1"
    assert _lotto_era(date(2003, 6, 1)) == "era2"
    assert _lotto_era(date(2010, 1, 1)) == "era3"


def test_pb_era_detection():
    assert _pb_era(date(2011, 1, 1)) == "era1"
    assert _pb_era(date(2013, 1, 1)) == "era2"
    assert _pb_era(date(2020, 1, 1)) == "era3"


def _make_csv(rows: list[list]) -> io.BytesIO:
    lines = [",".join(str(x) for x in row) for row in rows]
    return io.BytesIO("\n".join(lines).encode())


def test_load_lotto_era3(tmp_path):
    csv_content = (
        "Texas Lotto,1,3,2020,5,12,23,34,45,50\n"
        "Texas Lotto,1,6,2020,2,9,18,27,36,54\n"
    )
    p = tmp_path / "lotto.csv"
    p.write_text(csv_content)
    df = load_texas_lotto(str(p))
    assert len(df) == 2
    assert (df["era"] == "era3").all()
    assert df["is_bonus_era"].sum() == 0


def test_load_lotto_era2_flagged(tmp_path):
    csv_content = "Texas Lotto,6,1,2004,5,12,23,34,45,7\n"
    p = tmp_path / "lotto.csv"
    p.write_text(csv_content)
    df = load_texas_lotto(str(p))
    assert df.iloc[0]["era"] == "era2"
    assert df.iloc[0]["is_bonus_era"] == True


def test_load_twostep(tmp_path):
    csv_content = "Texas Two Step,3,15,2022,5,12,23,30,8\n"
    p = tmp_path / "twostep.csv"
    p.write_text(csv_content)
    df = load_texas_two_step(str(p))
    assert len(df) == 1
    assert df.iloc[0]["bonus"] == 8
    assert df.iloc[0]["era"] == "era1"


def test_upsert_draws_updates_existing_row():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    first = pd.DataFrame([
        {
            "draw_date": date(2026, 5, 2),
            "n1": 1,
            "n2": 2,
            "n3": 3,
            "n4": 4,
            "n5": 5,
            "n6": 6,
            "bonus": None,
            "power_play": None,
            "era": "era3",
            "is_bonus_era": False,
        }
    ])

    corrected = pd.DataFrame([
        {
            "draw_date": date(2026, 5, 2),
            "n1": 1,
            "n2": 2,
            "n3": 3,
            "n4": 4,
            "n5": 8,
            "n6": 9,
            "bonus": None,
            "power_play": None,
            "era": "era3",
            "is_bonus_era": False,
        }
    ])

    with Session(engine) as db:
        first_stats = upsert_draws(db, "lotto", first)
        second_stats = upsert_draws(db, "lotto", corrected)

        row = db.query(Draw).filter(Draw.game == "lotto").one()

    assert first_stats == {"inserted": 1, "updated": 0}
    assert second_stats == {"inserted": 0, "updated": 1}
    assert row.n5 == 8
    assert row.n6 == 9


def test_powerball_default_filters_to_era3_only():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    rows = pd.DataFrame([
        {
            "draw_date": date(2011, 1, 1),
            "n1": 1,
            "n2": 2,
            "n3": 3,
            "n4": 4,
            "n5": 5,
            "n6": None,
            "bonus": 6,
            "power_play": 2,
            "era": "era1",
            "is_bonus_era": False,
        },
        {
            "draw_date": date(2016, 1, 1),
            "n1": 11,
            "n2": 12,
            "n3": 13,
            "n4": 14,
            "n5": 15,
            "n6": None,
            "bonus": 16,
            "power_play": 3,
            "era": "era3",
            "is_bonus_era": False,
        },
    ])

    with Session(engine) as db:
        upsert_draws(db, "powerball", rows)

        default_df = get_draws_df(db, "powerball", include_era2=False)
        full_df = get_draws_df(db, "powerball", include_era2=True)

        default_count = count_draws(db, "powerball", include_era2=False)
        full_count = count_draws(db, "powerball", include_era2=True)

    assert len(default_df) == 1
    assert default_df.iloc[0]["era"] == "era3"
    assert len(full_df) == 2
    assert default_count == 1
    assert full_count == 2
