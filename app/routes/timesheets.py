# ============================================================
# routes/timesheets.py
# Timesheet management routes
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import timesheet_model, task_model, user_model, notification_model
from app.utils import email as email_util
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/timesheets", response_class=HTMLResponse)
async def timesheets_page(request: Request, month: int = 0, year: int = 0):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    role = session["role"]
    today = datetime.now()

    # Default to current month/year
    if not month:
        month = today.month
    if not year:
        year = today.year

    if role in ["admin", "manager"]:
        timesheets = timesheet_model.get_all_timesheets({"month": month, "year": year})
        employees = user_model.get_all_users()
    else:
        timesheets = timesheet_model.get_timesheets_for_user(user_id, month, year)
        employees = []

    # Get user's tasks for the timesheet form dropdown
    my_tasks = task_model.get_tasks_for_user(user_id)

    monthly_hours = timesheet_model.get_monthly_hours(user_id, month, year)

    return templates.TemplateResponse("timesheets/list.html", {
        "request": request,
        "session": session,
        "timesheets": timesheets,
        "employees": employees,
        "my_tasks": my_tasks,
        "month": month,
        "year": year,
        "monthly_hours": monthly_hours,
        "current_month_name": datetime(year, month, 1).strftime("%B %Y"),
        "today": today.strftime("%Y-%m-%d"),
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/timesheets/log")
async def log_timesheet(
    request: Request,
    work_date: str = Form(...),
    hours_worked: float = Form(...),
    description: str = Form(...),
    task_id: str = Form("")
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if hours_worked <= 0 or hours_worked > 24:
        return JSONResponse({"error": "Hours must be between 0 and 24"}, status_code=400)

    try:
        data = {
            "user_id": session["user_id"],
            "work_date": work_date,
            "hours_worked": hours_worked,
            "task_id": int(task_id) if task_id else None,
            "description": description,
            "status": "draft"
        }
        timesheet_model.create_timesheet(data)
        return JSONResponse({"success": True, "message": "Timesheet entry saved!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/timesheets/{ts_id}/submit")
async def submit_timesheet(request: Request, ts_id: int):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    success = timesheet_model.submit_timesheet(ts_id, session["user_id"])
    if success:
        return JSONResponse({"success": True, "message": "Timesheet submitted for approval!"})
    return JSONResponse({"error": "Could not submit timesheet"}, status_code=400)


@router.post("/timesheets/{ts_id}/approve")
async def approve_timesheet(
    request: Request,
    ts_id: int,
    notes: str = Form("")
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Get timesheet details first (for notification)
    timesheets = timesheet_model.get_all_timesheets()
    ts = next((t for t in timesheets if t["id"] == ts_id), None)

    success = timesheet_model.approve_timesheet(ts_id, session["user_id"], notes)

    if success and ts:
        # Notify employee
        notification_model.create_notification(
            ts["user_id"],
            "Timesheet Approved ✅",
            f"Your timesheet for {ts['work_date']} has been approved.",
            "timesheet_approved", "/timesheets"
        )
        # Email
        try:
            employee = user_model.get_user_by_id(ts["user_id"])
            if employee:
                email_util.send_timesheet_status_email(
                    employee["email"],
                    f"{employee['first_name']} {employee['last_name']}",
                    str(ts["work_date"]), "approved", notes
                )
        except Exception:
            pass

        return JSONResponse({"success": True, "message": "Timesheet approved!"})
    return JSONResponse({"error": "Could not approve"}, status_code=400)


@router.post("/timesheets/{ts_id}/reject")
async def reject_timesheet(
    request: Request,
    ts_id: int,
    notes: str = Form(...)
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    timesheets = timesheet_model.get_all_timesheets()
    ts = next((t for t in timesheets if t["id"] == ts_id), None)

    success = timesheet_model.reject_timesheet(ts_id, session["user_id"], notes)

    if success and ts:
        notification_model.create_notification(
            ts["user_id"],
            "Timesheet Rejected ❌",
            f"Your timesheet for {ts['work_date']} was rejected. Reason: {notes}",
            "timesheet_rejected", "/timesheets"
        )
        try:
            employee = user_model.get_user_by_id(ts["user_id"])
            if employee:
                email_util.send_timesheet_status_email(
                    employee["email"],
                    f"{employee['first_name']} {employee['last_name']}",
                    str(ts["work_date"]), "rejected", notes
                )
        except Exception:
            pass

        return JSONResponse({"success": True, "message": "Timesheet rejected."})
    return JSONResponse({"error": "Could not reject"}, status_code=400)
