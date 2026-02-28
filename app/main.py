"""LottoEdge — FastAPI application entry point."""
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from fastapi.encoders import ENCODERS_BY_TYPE
from fastapi.staticfiles import StaticFiles

# Teach FastAPI's JSON encoder to handle numpy scalar types
ENCODERS_BY_TYPE[np.integer] = int
ENCODERS_BY_TYPE[np.floating] = float
ENCODERS_BY_TYPE[np.bool_] = bool
ENCODERS_BY_TYPE[np.ndarray] = list

from app.models.database import init_db
from app.routers import about, analysis, dashboard, jackpot, picks, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="LottoEdge",
    description="Texas Lottery Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(picks.router)
app.include_router(jackpot.router)
app.include_router(analysis.router)
app.include_router(about.router)
