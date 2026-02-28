"""Tests for CSV parsing and era detection."""
import io
from datetime import date

import pandas as pd
import pytest

from app.services.data_loader import (
    _lotto_era,
    _pb_era,
    load_texas_lotto,
    load_texas_two_step,
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
