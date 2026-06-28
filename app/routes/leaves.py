# ============================================================
# routes/leaves.py
# Leave management routes
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import leave_model, user_model, notification_model
from app.utils import email as email_util
from app.utils.helpers import calculate_working_days
from datetime import date, datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/leaves", response_class=HTMLResponse)
async def leaves_page(request: Request, status: str = "", leave_type: str = ""):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    role = session["role"]

    filters = {}
    if status:
        filters["status"] = status
    if leave_type:
        filters["leave_type"] = leave_type

    if role in ["admin", "manager"]:
        leaves = leave_model.get_all_leaves(filters)
        employees = user_model.get_all_users()
    else:
        leaves = leave_model.get_leaves_for_user(user_id)
        employees = []
        if status:
            leaves = [l for l in leaves if l["status"] == status]

    balance = leave_model.get_leave_balance(user_id)

    return templates.TemplateResponse("leaves/list.html", {
        "request": request,
        "session": session,
        "leaves": leaves,
        "employees": employees,
        "balance": balance,
        "filters": {"status": status, "leave_type": leave_type},
        "today": date.today().isoformat(),
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/leaves/apply")
async def apply_leave(
    request: Request,
    leave_type: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(...)
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        # Calculate working days
        s_date = date.fromisoformat(start_date)
        e_date = date.fromisoformat(end_date)

        if s_date > e_date:
            return JSONResponse({"error": "End date must be after start date"}, status_code=400)

        if s_date < date.today():
            return JSONResponse({"error": "Cannot apply leave for past dates"}, status_code=400)

        total_days = calculate_working_days(s_date, e_date)

        if total_days <= 0:
            return JSONResponse({"error": "No working days in selected range"}, status_code=400)

        # Check balance for annual/sick leaves
        balance = leave_model.get_leave_balance(session["user_id"])
        if leave_type == "annual" and balance["annual_leave_balance"] < total_days:
            return JSONResponse({
                "error": f"Insufficient annual leave balance. You have {balance['annual_leave_balance']} days remaining."
            }, status_code=400)
        if leave_type == "sick" and balance["sick_leave_balance"] < total_days:
            return JSONResponse({
                "error": f"Insufficient sick leave balance. You have {balance['sick_leave_balance']} days remaining."
            }, status_code=400)

        data = {
            "user_id": session["user_id"],
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "reason": reason
        }

        leave_id = leave_model.create_leave_request(data)

        # Notify managers/admins
        managers = user_model.get_managers()
        for mgr in managers:
            notification_model.create_notification(
                mgr["id"],
                f"Leave Request from {session['name']}",
                f"{session['name']} applied for {leave_type} leave from {start_date} to {end_date} ({total_days} days)",
                "leave_applied", "/leaves"
            )

        return JSONResponse({"success": True, "message": f"Leave request submitted! ({total_days} working days)"})

    except ValueError as e:
        return JSONResponse({"error": f"Invalid date format: {e}"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/leaves/{leave_id}/approve")
async def approve_leave(request: Request, leave_id: int):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    leave = leave_model.get_leave_by_id(leave_id)
    if not leave:
        return JSONResponse({"error": "Leave not found"}, status_code=404)

    success = leave_model.approve_leave(leave_id, session["user_id"])

    if success:
        # Notify employee
        notification_model.create_notification(
            leave["user_id"],
            "Leave Approved ✅",
            f"Your {leave['leave_type']} leave from {leave['start_date']} to {leave['end_date']} has been approved.",
            "leave_approved", "/leaves"
        )
        try:
            email_util.send_leave_status_email(
                leave["employee_email"],
                leave["employee_name"],
                leave["leave_type"],
                str(leave["start_date"]),
                str(leave["end_date"]),
                "approved"
            )
        except Exception:
            pass

        return JSONResponse({"success": True, "message": "Leave approved!"})
    return JSONResponse({"error": "Could not approve leave"}, status_code=400)


@router.post("/leaves/{leave_id}/reject")
async def reject_leave(
    request: Request,
    leave_id: int,
    reason: str = Form(...)
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    leave = leave_model.get_leave_by_id(leave_id)
    if not leave:
        return JSONResponse({"error": "Leave not found"}, status_code=404)

    success = leave_model.reject_leave(leave_id, session["user_id"], reason)

    if success:
        notification_model.create_notification(
            leave["user_id"],
            "Leave Rejected ❌",
            f"Your {leave['leave_type']} leave was rejected. Reason: {reason}",
            "leave_rejected", "/leaves"
        )
        try:
            email_util.send_leave_status_email(
                leave["employee_email"],
                leave["employee_name"],
                leave["leave_type"],
                str(leave["start_date"]),
                str(leave["end_date"]),
                "rejected", reason
            )
        except Exception:
            pass

        return JSONResponse({"success": True, "message": "Leave rejected."})
    return JSONResponse({"error": "Could not reject"}, status_code=400)


@router.post("/leaves/{leave_id}/cancel")
async def cancel_leave(request: Request, leave_id: int):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    success = leave_model.cancel_leave(leave_id, session["user_id"])
    if success:
        return JSONResponse({"success": True, "message": "Leave request cancelled."})
    return JSONResponse({"error": "Cannot cancel this leave"}, status_code=400)
