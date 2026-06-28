# ============================================================
# routes/calendar.py
# Calendar view combining leaves, holidays, and tasks
# ============================================================

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import leave_model, holiday_model, task_model, notification_model
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]

    return templates.TemplateResponse("calendar/index.html", {
        "request": request,
        "session": session,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.get("/api/calendar/events")
async def get_calendar_events(request: Request, month: int = 0, year: int = 0):
    """
    API endpoint that returns calendar events as JSON.
    Called by the JavaScript calendar widget.
    """
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    today = datetime.now()
    if not month:
        month = today.month
    if not year:
        year = today.year

    user_id = session["user_id"]
    role = session["role"]
    events = []

    # Get holidays
    holidays = holiday_model.get_holidays_for_month(month, year)
    for h in holidays:
        events.append({
            "id": f"holiday_{h['id']}",
            "title": f"🎉 {h['name']}",
            "date": str(h["holiday_date"]),
            "type": "holiday",
            "color": "#f59e0b"
        })

    # Get leaves (all approved for admins, own leaves for employees)
    if role in ["admin", "manager"]:
        leaves = leave_model.get_approved_leaves_for_month(month, year)
    else:
        all_leaves = leave_model.get_leaves_for_user(user_id)
        leaves = [l for l in all_leaves if l["status"] == "approved"]

    for l in leaves:
        events.append({
            "id": f"leave_{l['id']}",
            "title": f"🏖️ {l.get('employee_name', 'You')} - {l['leave_type'].capitalize()} Leave",
            "start": str(l["start_date"]),
            "end": str(l["end_date"]),
            "type": "leave",
            "color": "#10b981"
        })

    # Get tasks with due dates
    if role in ["admin", "manager"]:
        tasks = task_model.get_all_tasks()
    else:
        tasks = task_model.get_tasks_for_user(user_id)

    for t in tasks:
        if t.get("due_date"):
            due = t["due_date"]
            # Only include tasks for this month
            if hasattr(due, 'month') and due.month == month and due.year == year:
                color = "#ef4444" if t["status"] not in ["completed"] else "#6b7280"
                events.append({
                    "id": f"task_{t['id']}",
                    "title": f"📋 {t['title']}",
                    "date": str(due),
                    "type": "task",
                    "color": color,
                    "priority": t["priority"]
                })

    return JSONResponse({"events": events, "month": month, "year": year})
