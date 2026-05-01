"""Lotto Edge — FastAPI application entry point."""
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from fastapi.encoders import ENCODERS_BY_TYPE
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

# Teach FastAPI's JSON encoder to handle numpy scalar types
ENCODERS_BY_TYPE[np.integer] = int
ENCODERS_BY_TYPE[np.floating] = float
ENCODERS_BY_TYPE[np.bool_] = bool
ENCODERS_BY_TYPE[np.ndarray] = list

from app.config import GAMES
from app.core.rate_limiter import limiter
from app.models.database import Draw, get_session, init_db
from app.routers import about, analysis, dashboard, jackpot, picks, predictions, upload
from app.services.data_loader import (
    load_texas_cash_five,
    load_powerball,
    load_texas_lotto,
    load_texas_two_step,
    upsert_draws,
)

_LOADERS = {
    "cash5": load_texas_cash_five,
    "lotto": load_texas_lotto,
    "twostep": load_texas_two_step,
    "powerball": load_powerball,
}


def _auto_seed_db() -> None:
    """Seed the database from CSV files in data/ if they exist and the
    corresponding game table is empty.  Runs once at startup so users
    never have to re-upload after a restart."""
    from sqlalchemy.orm import Session as _Session

    db: _Session = next(get_session())
    for game, cfg in GAMES.items():
        csv_path = cfg["csv_file"]
        if not csv_path.exists():
            continue
        existing = db.query(Draw).filter(Draw.game == game).count()
        if existing > 0:
            continue  # already loaded — skip to avoid duplicates
        try:
            df = _LOADERS[game](csv_path)
            upsert_draws(db, game, df)
        except Exception as exc:  # noqa: BLE001
            # Log but don't crash startup if a CSV is malformed
            print(f"[LottoEdge] Auto-seed failed for {game}: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _auto_seed_db()
    yield


app = FastAPI(
    title="Lotto Edge",
    description="Texas Lottery Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(picks.router)
app.include_router(jackpot.router)
app.include_router(analysis.router)
app.include_router(predictions.router)
app.include_router(about.router)
