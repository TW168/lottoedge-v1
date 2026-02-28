"""Jackpot monitor — manual jackpot entry and EV calculation."""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.database import JackpotEntry, get_session
from app.models.schemas import JackpotUpdate
from app.services.expected_value import compute_ev

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/jackpot", response_class=HTMLResponse)
async def jackpot_page(request: Request, db: Session = Depends(get_session)):
    entries = _get_current_jackpots(db)
    return templates.TemplateResponse("jackpot.html", {"request": request, "jackpots": entries})


@router.post("/api/jackpot/update")
async def update_jackpot(payload: JackpotUpdate, db: Session = Depends(get_session)):
    existing = db.query(JackpotEntry).filter(JackpotEntry.game == payload.game).first()
    if existing:
        existing.amount = payload.amount
        existing.next_draw_date = payload.next_draw_date
        existing.is_annuity = payload.is_annuity
        existing.updated_at = date.today()
    else:
        entry = JackpotEntry(
            game=payload.game,
            amount=payload.amount,
            next_draw_date=payload.next_draw_date,
            is_annuity=payload.is_annuity,
            updated_at=date.today(),
        )
        db.add(entry)
    db.commit()

    ev = compute_ev(payload.game, payload.amount, payload.is_annuity)
    return {"status": "ok", "ev": ev}


@router.get("/api/jackpot/ev/{game}")
async def get_ev(game: str, db: Session = Depends(get_session)):
    entry = db.query(JackpotEntry).filter(JackpotEntry.game == game).first()
    if not entry:
        return {"game": game, "message": "No jackpot data entered yet"}
    return compute_ev(game, entry.amount, entry.is_annuity)


def _get_current_jackpots(db: Session) -> list[dict]:
    entries = db.query(JackpotEntry).all()
    result = []
    for e in entries:
        ev = compute_ev(e.game, e.amount, e.is_annuity)
        result.append({
            "game": e.game,
            "amount": e.amount,
            "next_draw_date": e.next_draw_date,
            "is_annuity": e.is_annuity,
            "updated_at": e.updated_at,
            "ev": ev,
        })
    return result
