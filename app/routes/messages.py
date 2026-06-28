# ============================================================
# routes/messages.py
# Internal messaging system
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import notification_model, user_model

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request, view: str = "inbox"):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]

    if view == "sent":
        messages = notification_model.get_sent_messages(user_id)
    else:
        messages = notification_model.get_inbox(user_id)

    employees = user_model.get_all_users()
    # Don't include self in recipients
    employees = [e for e in employees if e["id"] != user_id]

    return templates.TemplateResponse("messages/index.html", {
        "request": request,
        "session": session,
        "messages": messages,
        "employees": employees,
        "view": view,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/messages/send")
async def send_message(
    request: Request,
    receiver_id: int = Form(...),
    subject: str = Form(...),
    body: str = Form(...)
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        msg_id = notification_model.send_message(
            session["user_id"], receiver_id, subject, body
        )
        # Also create a notification for the receiver
        notification_model.create_notification(
            receiver_id,
            f"New message from {session['name']}",
            subject,
            "message_received",
            "/messages"
        )
        return JSONResponse({"success": True, "message": "Message sent!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/messages/{msg_id}", response_class=HTMLResponse)
async def view_message(request: Request, msg_id: int):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    msg = notification_model.get_message_by_id(msg_id)

    if not msg:
        return RedirectResponse("/messages", status_code=302)

    # Mark as read if receiver
    if msg["receiver_id"] == user_id:
        notification_model.mark_message_read(msg_id, user_id)

    return templates.TemplateResponse("messages/view.html", {
        "request": request,
        "session": session,
        "message": msg,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })
