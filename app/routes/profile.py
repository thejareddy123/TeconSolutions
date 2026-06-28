# ============================================================
# routes/profile.py
# User profile management
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import user_model, notification_model
from app.utils.helpers import verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    user = user_model.get_user_by_id(user_id)

    return templates.TemplateResponse("profile/index.html", {
        "request": request,
        "session": session,
        "user": user,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/profile/update")
async def update_profile(
    request: Request,
    phone: str = Form(""),
    address: str = Form(""),
    date_of_birth: str = Form("")
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    user_id = session["user_id"]
    user = user_model.get_user_by_id(user_id)

    # Only allow employees to update their own contact info
    # Admins can update everything via /employees
    data = {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": phone,
        "department": user.get("department", ""),
        "designation": user.get("designation", ""),
        "role": user["role"],
        "manager_id": user.get("manager_id"),
        "date_of_joining": user.get("date_of_joining"),
        "annual_leave_balance": user.get("annual_leave_balance", 12),
        "sick_leave_balance": user.get("sick_leave_balance", 6),
        "address": address,
        "date_of_birth": date_of_birth or None
    }

    user_model.update_user(user_id, data)
    return JSONResponse({"success": True, "message": "Profile updated!"})


@router.post("/profile/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if new_password != confirm_password:
        return JSONResponse({"error": "New passwords do not match"}, status_code=400)

    if len(new_password) < 8:
        return JSONResponse({"error": "Password must be at least 8 characters"}, status_code=400)

    user = user_model.get_user_by_id(session["user_id"])
    if not verify_password(current_password, user["password_hash"]):
        return JSONResponse({"error": "Current password is incorrect"}, status_code=400)

    user_model.update_password(session["user_id"], new_password)
    return JSONResponse({"success": True, "message": "Password changed successfully!"})
