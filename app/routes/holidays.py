# ============================================================
# routes/holidays.py
# Holiday management routes
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import holiday_model, notification_model
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/holidays", response_class=HTMLResponse)
async def holidays_page(request: Request, year: int = 0):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    if not year:
        year = datetime.now().year

    holidays = holiday_model.get_all_holidays(year)
    user_id = session["user_id"]

    return templates.TemplateResponse("holidays/list.html", {
        "request": request,
        "session": session,
        "holidays": holidays,
        "year": year,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/holidays/create")
async def create_holiday(
    request: Request,
    name: str = Form(...),
    holiday_date: str = Form(...),
    holiday_type: str = Form("national"),
    description: str = Form("")
):
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Only admins can add holidays"}, status_code=403)

    try:
        holiday_model.create_holiday(
            {"name": name, "holiday_date": holiday_date,
             "holiday_type": holiday_type, "description": description},
            session["user_id"]
        )
        return JSONResponse({"success": True, "message": f"Holiday '{name}' added!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/holidays/{holiday_id}/delete")
async def delete_holiday(request: Request, holiday_id: int):
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Only admins can delete holidays"}, status_code=403)

    holiday_model.delete_holiday(holiday_id)
    return JSONResponse({"success": True, "message": "Holiday deleted!"})
