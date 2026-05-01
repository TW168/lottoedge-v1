"""Cash Five UI page routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/cash5", response_class=HTMLResponse)
async def cash5_page(request: Request):
    """Render Cash Five prediction dashboard page."""
    return templates.TemplateResponse("cash5.html", {"request": request})
