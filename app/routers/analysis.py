"""Analysis API endpoints — serve computed module data as JSON."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.database import get_session
from app.services import (
    balance,
    cluster,
    consecutive,
    frequency,
    group_dist,
    monte_carlo,
    positional,
    probability,
    sum_range,
)
from app.services.data_loader import count_draws, get_draws_df

router = APIRouter(prefix="/api")

VALID_GAMES = {"lotto", "twostep", "powerball"}


def _require_game(game: str):
    if game not in VALID_GAMES:
        raise ValueError(f"Unknown game: {game}")


def _load(db: Session, game: str, include_era2: bool = False):
    df = get_draws_df(db, game, include_era2=include_era2)
    return df


@router.get("/analysis/{game}")
def full_analysis(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    n_draws = count_draws(db, game, include_era2)

    if df.empty:
        return {"game": game, "draws": 0, "message": "No data. Please upload a CSV."}

    freq = frequency.compute_frequency(df, game)
    pos = positional.compute_positional(df, game)
    clust = cluster.compute_clusters(df, game)
    bal = balance.compute_historical_balance(df, game)
    sums = sum_range.compute_sum_range(df, game)
    grp = group_dist.compute_group_distribution(df, game)
    consec = consecutive.compute_consecutive_stats(df, game)

    return {
        "game": game,
        "draws": n_draws,
        "frequency": freq,
        "positional": pos,
        "clusters": clust,
        "balance": bal,
        "sum_range": sums,
        "groups": grp,
        "consecutive": consec,
        "odds": probability.get_odds(game),
    }


@router.get("/frequency/{game}")
def get_frequency(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    return frequency.compute_frequency(df, game)


@router.get("/positional/{game}")
def get_positional(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    return positional.compute_positional(df, game)


@router.get("/clusters/{game}")
def get_clusters(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    return cluster.compute_clusters(df, game)


@router.get("/skip/{game}")
def get_skip(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    return frequency.get_skip_data(df, game)


@router.get("/sum-range/{game}")
def get_sum_range(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    return sum_range.compute_sum_range(df, game)


@router.get("/probability/{game}")
def get_probability(game: str):
    _require_game(game)
    return {"game": game, "tiers": probability.get_odds(game)}


@router.get("/ml/predict/{game}")
def get_ml_prediction(
    game: str,
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    _require_game(game)
    df = _load(db, game, include_era2)
    if df.empty:
        return {}
    from app.services import ml_engine
    models = ml_engine.train_ensemble(df, game)
    return ml_engine.predict_scores(models, df, game)


@router.post("/coverage/build")
def build_coverage(payload: dict):
    from app.services.coverage import build_coverage as _build_coverage

    game = payload.get("game", "lotto")
    numbers = payload.get("numbers", [])
    budget = int(payload.get("budget", 10))
    wheel_type = payload.get("wheel_type", "abbreviated")
    key_numbers = payload.get("key_numbers", [])

    if game not in VALID_GAMES:
        return {"error": f"Unknown game: {game}"}
    if not numbers:
        return {"error": "No numbers provided"}

    return _build_coverage(
        game=game,
        numbers=numbers,
        budget=budget,
        wheel_type=wheel_type,
        key_numbers=key_numbers if key_numbers else None,
    )
