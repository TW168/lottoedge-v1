"""Dashboard — main HTML page + summary data API."""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.database import JackpotEntry, get_session
from app.services.data_loader import count_draws, get_draws_df
from app.services.expected_value import compute_ev
from app.services.frequency import compute_frequency

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

GAMES = [
    {"id": "lotto",     "name": "Texas Lotto"},
    {"id": "twostep",   "name": "Texas Two Step"},
    {"id": "powerball", "name": "Powerball"},
    {"id": "cash5",     "name": "Cash Five"},
]


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    game: str = Query("lotto"),
    include_era2: bool = Query(False),
    db: Session = Depends(get_session),
):
    n_draws = count_draws(db, game, include_era2)
    df = get_draws_df(db, game, include_era2)

    freq_data = {}
    if not df.empty:
        freq_data = compute_frequency(df, game)

    # Current jackpot entries for sidebar
    jackpots = {
        e.game: {"amount": e.amount, "ev": compute_ev(e.game, e.amount, e.is_annuity)}
        for e in db.query(JackpotEntry).all()
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "games": GAMES,
            "active_game": game,
            "n_draws": n_draws,
            "include_era2": include_era2,
            "freq_data": freq_data,
            "jackpots": jackpots,
            "has_data": not df.empty,
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    game: str = Query("lotto"),
    include_era2: bool = Query(False),
    page: int = Query(1),
    db: Session = Depends(get_session),
):
    PAGE_SIZE = 50
    from app.models.database import Draw
    query = db.query(Draw).filter(Draw.game == game)
    if game == "lotto" and not include_era2:
        query = query.filter(Draw.era != "era2")
    total = query.count()
    draws = (
        query.order_by(Draw.draw_date.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "games": GAMES,
            "active_game": game,
            "draws": draws,
            "page": page,
            "total_pages": max(1, -(-total // PAGE_SIZE)),
            "total": total,
            "include_era2": include_era2,
        },
    )


@router.get("/coverage", response_class=HTMLResponse)
async def coverage_page(request: Request):
    return templates.TemplateResponse("coverage.html", {"request": request})
