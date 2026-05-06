"""Pick generation and exclusion management endpoints."""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.database import get_session
from app.models.schemas import ExcludedPickBatchRequest, ExcludedPickRequest, PickRequest
from app.services.composite_scorer import ScoringWeights
from app.services.data_loader import get_draws_df
from app.services.excluded_picks import (
    add_exclusion,
    bonus_exclusions,
    load_store,
    main_exclusions,
)
from app.services.pick_generator import generate_picks
from app.services.pick_history import record_generated_picks, recent_usage_snapshot
from app.services.probability import get_odds

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/picks", response_class=HTMLResponse)
async def picks_page(request: Request, game: str = Query("lotto")):
    return templates.TemplateResponse("picks.html", {"request": request, "default_game": game})


@router.post("/api/picks/generate")
async def generate(payload: PickRequest, db: Session = Depends(get_session)):
    df = get_draws_df(db, payload.game, include_era2=payload.include_era2)

    if df.empty:
        return {"error": "No data for this game. Upload a CSV first."}

    weights = ScoringWeights(
        frequency=payload.weight_frequency,
        positional=payload.weight_positional,
        cluster=payload.weight_cluster,
        due_score=payload.weight_due_score,
        momentum=payload.weight_momentum,
        heat=payload.weight_heat,
        group=payload.weight_group,
        lstm=payload.weight_lstm,
        ensemble=payload.weight_ensemble,
        monte_carlo=payload.weight_monte_carlo,
        coverage=payload.weight_coverage,
    )

    usage_snapshot = recent_usage_snapshot(payload.game, window=80)

    picks = generate_picks(
        df,
        payload.game,
        count=payload.count,
        weights=weights,
        diversity_level=payload.diversity_level,
        excluded_main=main_exclusions(payload.game),
        excluded_with_bonus=bonus_exclusions(payload.game),
        recent_main_usage=usage_snapshot.get("main", {}),
        recent_bonus_usage=usage_snapshot.get("bonus", {}),
    )
    record_generated_picks(payload.game, picks, max_history=300)
    odds = get_odds(payload.game)

    return {
        "game": payload.game,
        "picks": picks,
        "odds": odds,
        "draws_used": len(df),
    }


@router.get("/api/picks/exclusions")
async def get_exclusions():
    """Return the currently saved exclusion list used by generators."""
    return load_store()


@router.post("/api/picks/exclusions")
async def save_exclusion(payload: ExcludedPickRequest):
    """Save one played combination so it is excluded from future picks."""
    return add_exclusion(payload.game, payload.numbers, payload.bonus)


@router.post("/api/picks/exclusions/batch")
async def save_exclusion_batch(payload: ExcludedPickBatchRequest):
    """Save multiple played combinations so they are excluded from future picks."""
    saved = [add_exclusion(p.game, p.numbers, p.bonus) for p in payload.picks]
    return {"saved": saved, "count": len(saved)}
