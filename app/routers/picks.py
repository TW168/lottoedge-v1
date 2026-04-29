"""Pick generation endpoints."""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.database import get_session
from app.models.schemas import PickRequest
from app.services.composite_scorer import ScoringWeights
from app.services.data_loader import get_draws_df
from app.services.pick_generator import generate_picks
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

    picks = generate_picks(
        df,
        payload.game,
        count=payload.count,
        weights=weights,
        diversity_level=payload.diversity_level,
    )
    odds = get_odds(payload.game)

    return {
        "game": payload.game,
        "picks": picks,
        "odds": odds,
        "draws_used": len(df),
    }
