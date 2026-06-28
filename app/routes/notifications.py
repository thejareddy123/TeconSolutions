# ============================================================
# routes/notifications.py
# ============================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from app.utils.session import get_session
from app.models import notification_model

router = APIRouter(prefix="/notifications")


@router.get("/")
async def get_notifications(request: Request):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    notifs = notification_model.get_notifications_for_user(session["user_id"])
    # Convert datetime objects to strings for JSON
    for n in notifs:
        if n.get("created_at"):
            n["created_at"] = str(n["created_at"])
    return JSONResponse({"notifications": notifs})


@router.post("/{notif_id}/read")
async def mark_read(request: Request, notif_id: int):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    notification_model.mark_notification_read(notif_id, session["user_id"])
    return JSONResponse({"success": True})


@router.post("/mark-all-read")
async def mark_all_read(request: Request):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    notification_model.mark_all_read(session["user_id"])
    return JSONResponse({"success": True})
