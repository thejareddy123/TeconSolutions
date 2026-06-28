# ============================================================
# routes/auth.py
# Login, logout routes
# ============================================================

from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import user_model
from app.utils.session import create_session, clear_session, get_session
from app.utils.helpers import verify_password
from app.utils import email as email_util

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Max failed login attempts before locking
MAX_FAILED_ATTEMPTS = 5


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page. Redirect to dashboard if already logged in."""
    session = get_session(request)
    if session:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission"""
    
    # Find user by email
    user = user_model.get_user_by_email(email.strip().lower())
    
    if not user:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid email or password."
        })
    
    # Check if account is locked
    if user["is_locked"]:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Your account is locked. Please contact HR."
        })
    
    # Check if account is active
    if not user["is_active"]:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Your account is inactive. Please contact HR."
        })
    
    # Verify password
    if not verify_password(password, user["password_hash"]):
        # Increment failed attempts
        attempts = user_model.increment_failed_login(user["id"])
        
        # Lock account if too many failures
        if attempts >= MAX_FAILED_ATTEMPTS:
            user_model.lock_user_account(user["id"])
            # Send lock notification email (in background, don't wait)
            try:
                email_util.send_account_locked_email(
                    user["email"],
                    f"{user['first_name']} {user['last_name']}"
                )
            except Exception:
                pass  # Don't fail login process if email fails
            
            return templates.TemplateResponse("auth/login.html", {
                "request": request,
                "error": "Account locked after too many failed attempts. Contact HR."
            })
        
        remaining = MAX_FAILED_ATTEMPTS - attempts
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": f"Invalid email or password. {remaining} attempt(s) remaining."
        })
    
    # ✅ Login successful!
    user_model.update_last_login(user["id"])
    
    # Create session data
    session_data = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": f"{user['first_name']} {user['last_name']}",
        "employee_id": user["employee_id"],
        "first_name": user["first_name"]
    }
    
    # Set session cookie in response
    redirect = RedirectResponse("/dashboard", status_code=302)
    create_session(redirect, session_data)
    return redirect


@router.get("/logout")
async def logout(response: Response):
    """Log out the user by clearing session"""
    redirect = RedirectResponse("/login", status_code=302)
    clear_session(redirect)
    return redirect


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to dashboard or login"""
    session = get_session(request)
    if session:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)
