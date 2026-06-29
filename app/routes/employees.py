# ============================================================
# routes/employees.py
# Employee management (admin only)
# ============================================================

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import user_model, notification_model
from app.utils import email as email_util
from app.utils.helpers import generate_temp_password, allowed_image_types
import os, shutil, uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "uploads/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(request):
    s = get_session(request)
    if not s or s["role"] not in ["admin", "manager"]:
        return None
    return s


@router.get("/employees", response_class=HTMLResponse)
async def employees_list(request: Request, search: str = ""):
    session = require_admin(request)
    if not session:
        return RedirectResponse("/dashboard", status_code=302)

    if search:
        users = user_model.search_users(search)
    else:
        users = user_model.get_all_users(include_inactive=True)

    managers = user_model.get_managers()
    unread_n = notification_model.get_unread_count(session["user_id"])
    unread_m = notification_model.get_unread_message_count(session["user_id"])

    return templates.TemplateResponse("employees/list.html", {
        "request": request,
        "session": session,
        "users": users,
        "managers": managers,
        "search": search,
        "unread_notifications": unread_n,
        "unread_messages": unread_m
    })


@router.post("/employees/create")
async def create_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    department: str = Form(""),
    designation: str = Form(""),
    role: str = Form("employee"),
    manager_id: str = Form(""),
    date_of_joining: str = Form(""),
    annual_leave: float = Form(12.0),
    sick_leave: float = Form(6.0),
):
    session = require_admin(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        # Generate employee ID and temp password
        employee_id = user_model.get_next_employee_id()
        temp_password = generate_temp_password()

        data = {
            "employee_id": employee_id,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip().lower(),
            "phone": phone,
            "password": temp_password,
            "role": role,
            "department": department,
            "designation": designation,
            "manager_id": int(manager_id) if manager_id else None,
            "date_of_joining": date_of_joining or None,
            "annual_leave_balance": annual_leave,
            "sick_leave_balance": sick_leave
        }

        new_id = user_model.create_user(data)

        # Send welcome email
        try:
            email_util.send_welcome_email(
                email, f"{first_name} {last_name}", employee_id, temp_password
            )
        except Exception:
            pass  # Email is optional, don't fail if it doesn't send

        # Create notification
        notification_model.create_notification(
            new_id,
            "Welcome to TeconSolutions! 🎉",
            f"Your account has been created. Employee ID: {employee_id}",
            "account_created"
        )

        return JSONResponse({"success": True, "message": f"Employee {employee_id} created!"})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/employees/{user_id}", response_class=HTMLResponse)
async def employee_detail(request: Request, user_id: int):
    session = require_admin(request)
    if not session:
        return RedirectResponse("/dashboard", status_code=302)

    user = user_model.get_user_by_id(user_id)
    if not user:
        return RedirectResponse("/employees", status_code=302)

    managers = user_model.get_managers()
    unread_n = notification_model.get_unread_count(session["user_id"])
    unread_m = notification_model.get_unread_message_count(session["user_id"])

    return templates.TemplateResponse("employees/detail.html", {
        "request": request,
        "session": session,
        "employee": user,
        "managers": managers,
        "unread_notifications": unread_n,
        "unread_messages": unread_m
    })


@router.post("/employees/{user_id}/update")
async def update_employee(
    request: Request,
    user_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(""),
    department: str = Form(""),
    designation: str = Form(""),
    role: str = Form("employee"),
    manager_id: str = Form(""),
    date_of_joining: str = Form(""),
    annual_leave: float = Form(12.0),
    sick_leave: float = Form(6.0),
    address: str = Form(""),
    date_of_birth: str = Form("")
):
    session = require_admin(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "department": department,
            "designation": designation,
            "role": role,
            "manager_id": int(manager_id) if manager_id else None,
            "date_of_joining": date_of_joining or None,
            "annual_leave_balance": annual_leave,
            "sick_leave_balance": sick_leave,
            "address": address,
            "date_of_birth": date_of_birth or None
        }
        user_model.update_user(user_id, data)
        return JSONResponse({"success": True, "message": "Employee updated!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/employees/{user_id}/toggle-status")
async def toggle_status(request: Request, user_id: int):
    session = require_admin(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    user_model.toggle_user_status(user_id)
    return JSONResponse({"success": True})


@router.post("/employees/{user_id}/photo")
async def upload_photo(
    request: Request,
    user_id: int,
    photo: UploadFile = File(...)
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Only allow admin or the user themselves to upload
    if session["role"] not in ["admin"] and session["user_id"] != user_id:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    if not allowed_image_types(photo.filename):
        return JSONResponse({"error": "Only JPG, PNG files allowed"}, status_code=400)

    # Save file with unique name
    ext = photo.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)

    # Update DB
    user_model.update_profile_photo(user_id, f"/static/uploads/profiles/{filename}")

    return JSONResponse({"success": True, "photo_url": f"/static/uploads/profiles/{filename}"})


@router.get("/api/employees", response_class=JSONResponse)
async def api_get_employees(request: Request):
    """API endpoint to get all active employees (for dropdowns)"""
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    users = user_model.get_all_users()
    result = [
        {
            "id": u["id"],
            "name": f"{u['first_name']} {u['last_name']}",
            "employee_id": u["employee_id"],
            "department": u.get("department", ""),
            "email": u["email"]
        }
        for u in users
    ]
    return JSONResponse(result)
