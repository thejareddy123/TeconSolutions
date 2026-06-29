# ============================================================
# routes/dashboard.py
# Main dashboard page
# ============================================================

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import (
    user_model, task_model, leave_model,
    timesheet_model, notification_model, holiday_model
)
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page with summary cards"""
    
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)
    
    user_id = session["user_id"]
    role = session["role"]
    today = datetime.now()
    now_hour = today.hour
    
    # Get data based on role
    if role == "admin":
        # Admin sees system-wide stats
        task_stats = task_model.get_task_stats()
        leave_stats = leave_model.get_leave_stats()
        timesheet_stats = timesheet_model.get_timesheet_stats()
        all_users = user_model.get_all_users()
        total_employees = len(all_users)
        recent_leaves = leave_model.get_all_leaves({"status": "pending"})[:5]
        recent_timesheets = timesheet_model.get_all_timesheets({"status": "submitted"})[:5]
        
        context = {
            "request": request,
            "session": session,
            "now_hour": now_hour,
            "task_stats": task_stats,
            "leave_stats": leave_stats,
            "timesheet_stats": timesheet_stats,
            "total_employees": total_employees,
            "recent_leaves": recent_leaves,
            "recent_timesheets": recent_timesheets,
            "is_admin": True
        }
    else:
        # Employee sees their personal stats
        my_tasks = task_model.get_tasks_for_user(user_id)
        pending_tasks = [t for t in my_tasks if t["status"] in ["todo", "in_progress"]]
        
        leave_balance = leave_model.get_leave_balance(user_id)
        my_leaves = leave_model.get_leaves_for_user(user_id)
        pending_leaves = [l for l in my_leaves if l["status"] == "pending"]
        
        monthly_hours = timesheet_model.get_monthly_hours(
            user_id, today.month, today.year
        )
        
        notifications = notification_model.get_notifications_for_user(user_id, limit=5)
        upcoming_holidays = holiday_model.get_upcoming_holidays(limit=3)
        
        context = {
            "request": request,
            "session": session,
            "now_hour": now_hour,
            "my_tasks": my_tasks[:5],
            "pending_tasks_count": len(pending_tasks),
            "leave_balance": leave_balance,
            "pending_leaves": pending_leaves,
            "monthly_hours": monthly_hours,
            "notifications": notifications,
            "upcoming_holidays": upcoming_holidays,
            "current_month": today.strftime("%B %Y"),
            "is_admin": False
        }
    
    # Unread counts (shown in navbar for all users)
    context["unread_notifications"] = notification_model.get_unread_count(user_id)
    context["unread_messages"] = notification_model.get_unread_message_count(user_id)
    
    return templates.TemplateResponse("dashboard/index.html", context)
