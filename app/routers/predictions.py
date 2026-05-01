"""Cash Five prediction endpoints with split-aware EV metrics."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.rate_limiter import limiter
from app.models.database import CashFivePredictionRun, Draw, get_session
from app.models.schemas import CashFivePredictionRequest, CashFivePredictionResponse
from app.services import cash5_predictor
from app.services.cash5_predictor import EnsembleWeights
from app.services.data_loader import get_draws_df

router = APIRouter(prefix="/api", tags=["cash5-predictions"])

DISCLAIMER = (
    "Lottery draws are independent random events; past results do not influence "
    "future outcomes. These tools are for entertainment and pattern exploration only."
)


@router.post(
    "/cash5/history",
    summary="Insert a Cash Five draw",
    description="Insert a Texas Cash Five historical draw into the draws table.",
    status_code=201,
    responses={
        201: {
            "description": "Draw inserted",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1201,
                        "game": "cash5",
                        "draw_date": "2026-04-30",
                        "numbers": [3, 8, 14, 19, 33],
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
def add_cash5_history(
    request: Request,
    draw_date: date = Query(..., description="Draw date in ISO format."),
    n1: int = Query(..., ge=1, le=35),
    n2: int = Query(..., ge=1, le=35),
    n3: int = Query(..., ge=1, le=35),
    n4: int = Query(..., ge=1, le=35),
    n5: int = Query(..., ge=1, le=35),
    db: Session = Depends(get_session),
):
    numbers = sorted([n1, n2, n3, n4, n5])
    if len(set(numbers)) != 5:
        raise HTTPException(status_code=400, detail="Cash Five numbers must be unique.")

    existing = db.query(Draw).filter(Draw.game == "cash5", Draw.draw_date == draw_date).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Draw for this date already exists.")

    row = Draw(
        game="cash5",
        draw_date=draw_date,
        n1=numbers[0],
        n2=numbers[1],
        n3=numbers[2],
        n4=numbers[3],
        n5=numbers[4],
        era="era1",
        is_bonus_era=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"id": row.id, "game": row.game, "draw_date": row.draw_date, "numbers": numbers}


@router.get(
    "/cash5/history",
    summary="List Cash Five history",
    description="Return historical Texas Cash Five draws sorted by most recent date.",
    responses={
        200: {
            "description": "History list",
            "content": {
                "application/json": {
                    "example": {
                        "game": "cash5",
                        "total": 1200,
                        "draws": [
                            {"draw_date": "2026-04-30", "numbers": [3, 8, 14, 19, 33]},
                            {"draw_date": "2026-04-29", "numbers": [4, 12, 16, 28, 34]},
                        ],
                    }
                }
            },
        }
    },
)
@limiter.limit("60/minute")
def get_cash5_history(
    request: Request,
    limit: int = Query(200, ge=1, le=5000),
    db: Session = Depends(get_session),
):
    rows = (
        db.query(Draw)
        .filter(Draw.game == "cash5")
        .order_by(Draw.draw_date.desc())
        .limit(limit)
        .all()
    )

    draws = [
        {
            "draw_date": row.draw_date,
            "numbers": sorted([row.n1, row.n2, row.n3, row.n4, row.n5]),
        }
        for row in rows
    ]
    return {"game": "cash5", "total": len(draws), "draws": draws}


def _load_cash5_df(db: Session):
    df = get_draws_df(db, "cash5")
    if df.empty:
        raise HTTPException(status_code=404, detail="No Cash Five draw history loaded.")
    return df


@router.get(
    "/predictions/frequency",
    summary="Cash Five frequency analysis",
    description="Compute 1-35 frequencies and chi-square goodness-of-fit versus uniform.",
)
@limiter.limit("30/minute")
def prediction_frequency(request: Request, db: Session = Depends(get_session)):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.frequency_analysis(draws)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.get(
    "/predictions/hot-cold",
    summary="Cash Five hot/cold analysis",
    description="Rank numbers by deviation from expected count in a rolling window.",
)
@limiter.limit("30/minute")
def prediction_hot_cold(
    request: Request,
    window: int = Query(120, ge=10, le=1000),
    db: Session = Depends(get_session),
):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.hot_cold_analysis(draws, window=window)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.get(
    "/predictions/gap",
    summary="Cash Five gap analysis",
    description="Flag overdue numbers using mean-gap plus one standard deviation.",
)
@limiter.limit("30/minute")
def prediction_gap(request: Request, db: Session = Depends(get_session)):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.gap_analysis(draws)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.get(
    "/predictions/markov",
    summary="Cash Five Markov chain prediction",
    description="Build transition matrix P(j|i) and score next-number likelihoods.",
)
@limiter.limit("20/minute")
def prediction_markov(request: Request, db: Session = Depends(get_session)):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.markov_chain_analysis(draws)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.get(
    "/predictions/monte-carlo",
    summary="Cash Five Monte Carlo simulation",
    description="Generate weighted candidate tickets and return modal numbers.",
)
@limiter.limit("10/minute")
def prediction_monte_carlo(
    request: Request,
    simulations: int = Query(5000, ge=100, le=200000),
    db: Session = Depends(get_session),
):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.monte_carlo_analysis(draws, simulations=simulations)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.get(
    "/predictions/patterns",
    summary="Cash Five pattern recognition",
    description="Analyze historical sum, odd/even, low/high, and consecutive patterns.",
)
@limiter.limit("20/minute")
def prediction_patterns(request: Request, db: Session = Depends(get_session)):
    df = _load_cash5_df(db)
    draws = cash5_predictor._extract_draws(df)
    result = cash5_predictor.pattern_recognition_analysis(draws)
    return {"game": "cash5", "result": result, "disclaimer": DISCLAIMER}


@router.post(
    "/predictions/ensemble",
    summary="Cash Five ensemble predictor",
    description=(
        "Run all Cash Five algorithms and return top picks with confidence, "
        "split-risk score, and EV-before/after-split metrics."
    ),
    response_model=CashFivePredictionResponse,
    responses={
        200: {
            "description": "Ensemble prediction",
            "content": {
                "application/json": {
                    "example": {
                        "game": "cash5",
                        "top_numbers": [4, 9, 17, 22, 31],
                        "alternate_numbers": [2, 13, 21, 27, 35],
                        "confidence_score": 72.35,
                        "split_risk_score": 64.0,
                        "ev_before_split": -0.312451,
                        "ev_after_split": -0.624118,
                        "disclaimer": DISCLAIMER,
                    }
                }
            },
        }
    },
)
@limiter.limit("10/minute")
def prediction_ensemble(
    request: Request,
    payload: CashFivePredictionRequest,
    db: Session = Depends(get_session),
):
    df = _load_cash5_df(db)

    weights = EnsembleWeights(
        frequency=payload.weight_frequency,
        hot_cold=payload.weight_hot_cold,
        gap=payload.weight_gap,
        markov=payload.weight_markov,
        monte_carlo=payload.weight_monte_carlo,
        pattern=payload.weight_pattern,
    )

    result = cash5_predictor.predict_from_dataframe(
        df=df,
        weights=weights,
        window=payload.window,
        monte_carlo_samples=payload.monte_carlo_samples,
        jackpot=payload.jackpot,
        ticket_cost=payload.ticket_cost,
    )

    db_row = CashFivePredictionRun(
        created_on=date.today(),
        top_numbers=",".join(str(x) for x in result["top_numbers"]),
        alternate_numbers=",".join(str(x) for x in result["alternate_numbers"]),
        confidence_score=result["confidence_score"],
        split_risk_score=result["split_risk_score"],
        ev_before_split=result["ev_before_split"],
        ev_after_split=result["ev_after_split"],
        jackpot=payload.jackpot,
        ticket_cost=payload.ticket_cost,
    )
    db.add(db_row)
    db.commit()

    return CashFivePredictionResponse(
        game="cash5",
        top_numbers=result["top_numbers"],
        alternate_numbers=result["alternate_numbers"],
        confidence_score=result["confidence_score"],
        split_risk_score=result["split_risk_score"],
        ev_before_split=result["ev_before_split"],
        ev_after_split=result["ev_after_split"],
        disclaimer=DISCLAIMER,
    )
