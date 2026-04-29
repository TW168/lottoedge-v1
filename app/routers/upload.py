"""CSV upload endpoints."""
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.models.database import get_session
from app.services.data_loader import (
    load_powerball,
    load_texas_lotto,
    load_texas_two_step,
    upsert_draws,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_LOADERS = {
    "lotto": load_texas_lotto,
    "twostep": load_texas_two_step,
    "powerball": load_powerball,
}

_FILENAMES = {
    "lotto": "texas_lotto.csv",
    "twostep": "texas_two_step.csv",
    "powerball": "powerball.csv",
}


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/api/upload/{game}")
async def upload_csv(game: str, file: UploadFile = File(...)):
    if game not in _LOADERS:
        return {"error": f"Unknown game: {game}"}

    # Save file to data/
    dest = DATA_DIR / _FILENAMES[game]
    content = await file.read()
    dest.write_bytes(content)

    # Parse and store
    try:
        df = _LOADERS[game](dest)
    except Exception as e:
        return {"error": f"Parse error: {e}"}

    db: Session = next(get_session())
    inserted = upsert_draws(db, game, df)

    return {
        "game": game,
        "rows_parsed": len(df),
        "rows_inserted": inserted,
        "total_rows": len(df),
    }
