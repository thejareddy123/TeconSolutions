# ============================================================
# utils/session.py
# Simple session management using cookies
# ============================================================

import json
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from fastapi import Request, Response
from app.utils.config import settings


# Session cookie name
SESSION_COOKIE = "ts_session"


def create_session(response: Response, user_data: dict):
    """
    Save user info in a signed cookie (session).
    
    user_data should contain:
    {
        "user_id": 1,
        "email": "user@example.com",
        "role": "employee",
        "name": "John Doe",
        "employee_id": "EMP001"
    }
    """
    # Add expiry time to session data
    user_data["expires"] = (
        datetime.now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
    ).isoformat()
    
    # Convert to JSON and encode as base64
    session_json = json.dumps(user_data)
    session_b64 = base64.b64encode(session_json.encode()).decode()
    
    # Create a signature so we can verify it wasn't tampered with
    signature = hmac.new(
        settings.SESSION_SECRET.encode(),
        session_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Final cookie value: data.signature
    cookie_value = f"{session_b64}.{signature}"
    
    # Set cookie in response
    response.set_cookie(
        key=SESSION_COOKIE,
        value=cookie_value,
        max_age=settings.SESSION_EXPIRE_MINUTES * 60,  # Convert to seconds
        httponly=True,       # Can't access with JavaScript (security)
        samesite="lax"       # CSRF protection
    )


def get_session(request: Request) -> dict | None:
    """
    Read and verify the session cookie.
    Returns user data dict or None if no valid session.
    """
    cookie_value = request.cookies.get(SESSION_COOKIE)
    
    if not cookie_value:
        return None
    
    try:
        # Split cookie into data and signature
        session_b64, signature = cookie_value.rsplit(".", 1)
        
        # Verify signature
        expected_sig = hmac.new(
            settings.SESSION_SECRET.encode(),
            session_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            # Signature doesn't match - cookie was tampered with!
            return None
        
        # Decode session data
        session_json = base64.b64decode(session_b64.encode()).decode()
        session_data = json.loads(session_json)
        
        # Check if session has expired
        expires = datetime.fromisoformat(session_data.get("expires", ""))
        if datetime.now() > expires:
            return None  # Session expired
        
        return session_data
        
    except Exception:
        # Any error means invalid session
        return None


def clear_session(response: Response):
    """Remove the session cookie (logout)"""
    response.delete_cookie(SESSION_COOKIE)


def require_login(request: Request):
    """
    Get current logged-in user.
    Returns user data or None if not logged in.
    
    Use this in route handlers to check if user is logged in.
    """
    return get_session(request)


def require_admin(request: Request):
    """
    Get current user only if they are admin.
    Returns user data or None if not admin.
    """
    session = get_session(request)
    if session and session.get("role") == "admin":
        return session
    return None


def require_manager_or_admin(request: Request):
    """
    Get current user only if they are manager or admin.
    """
    session = get_session(request)
    if session and session.get("role") in ["admin", "manager"]:
        return session
    return None
