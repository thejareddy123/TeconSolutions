# ============================================================
# routes/tasks.py
# Task management routes
# ============================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import task_model, user_model, notification_model
from app.utils import email as email_util

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, status: str = "", priority: str = "", search: str = ""):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    role = session["role"]

    # Admins/managers see all tasks; employees see only their tasks
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if search:
        filters["search"] = search

    if role in ["admin", "manager"]:
        tasks = task_model.get_all_tasks(filters)
    else:
        tasks = task_model.get_tasks_for_user(user_id)
        # Apply filters client-side for employee view
        if status:
            tasks = [t for t in tasks if t["status"] == status]

    employees = user_model.get_all_users() if role in ["admin", "manager"] else []

    return templates.TemplateResponse("tasks/list.html", {
        "request": request,
        "session": session,
        "tasks": tasks,
        "employees": employees,
        "filters": {"status": status, "priority": priority, "search": search},
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/tasks/create")
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    start_date: str = Form(""),
    due_date: str = Form(""),
    project_name: str = Form(""),
    assignees: str = Form("")   # comma-separated user IDs
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Only managers/admins can create tasks"}, status_code=403)

    try:
        task_data = {
            "title": title,
            "description": description,
            "created_by": session["user_id"],
            "priority": priority,
            "start_date": start_date or None,
            "due_date": due_date or None,
            "project_name": project_name
        }

        task_id = task_model.create_task(task_data)

        # Assign to selected employees
        if assignees:
            assignee_ids = [int(x) for x in assignees.split(",") if x.strip()]
            for uid in assignee_ids:
                task_model.assign_task(task_id, uid, session["user_id"])

                # Notify each assigned employee
                notification_model.create_notification(
                    uid,
                    f"New Task Assigned: {title}",
                    f"You have been assigned a new task by {session['name']}. Due: {due_date or 'No deadline'}",
                    "task_assigned",
                    "/tasks"
                )

                # Send email notification
                assignee = user_model.get_user_by_id(uid)
                if assignee:
                    try:
                        email_util.send_task_assignment_email(
                            assignee["email"],
                            f"{assignee['first_name']} {assignee['last_name']}",
                            title, due_date or "No deadline", session["name"]
                        )
                    except Exception:
                        pass

        return JSONResponse({"success": True, "task_id": task_id, "message": "Task created!"})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: int):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    task = task_model.get_task_by_id(task_id)
    if not task:
        return RedirectResponse("/tasks", status_code=302)

    employees = user_model.get_all_users() if session["role"] in ["admin", "manager"] else []
    user_id = session["user_id"]

    return templates.TemplateResponse("tasks/detail.html", {
        "request": request,
        "session": session,
        "task": task,
        "employees": employees,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/tasks/{task_id}/update-status")
async def update_task_status(
    request: Request,
    task_id: int,
    status: str = Form(...)
):
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    valid_statuses = ["todo", "in_progress", "review", "completed", "cancelled"]
    if status not in valid_statuses:
        return JSONResponse({"error": "Invalid status"}, status_code=400)

    task_model.update_task_status(task_id, status, session["user_id"])
    return JSONResponse({"success": True, "message": f"Task status updated to {status}"})


@router.post("/tasks/{task_id}/update")
async def update_task(
    request: Request,
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    status: str = Form("todo"),
    start_date: str = Form(""),
    due_date: str = Form(""),
    project_name: str = Form("")
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        task_model.update_task(task_id, {
            "title": title,
            "description": description,
            "priority": priority,
            "status": status,
            "start_date": start_date or None,
            "due_date": due_date or None,
            "project_name": project_name
        })
        return JSONResponse({"success": True, "message": "Task updated!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/tasks/{task_id}/assign")
async def assign_task(
    request: Request,
    task_id: int,
    user_id: int = Form(...)
):
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    task_model.assign_task(task_id, user_id, session["user_id"])

    # Notify the employee
    task = task_model.get_task_by_id(task_id)
    if task:
        notification_model.create_notification(
            user_id,
            f"Task Assigned: {task['title']}",
            f"You've been assigned to task: {task['title']}",
            "task_assigned", "/tasks"
        )

    return JSONResponse({"success": True, "message": "Employee assigned to task!"})


@router.post("/tasks/{task_id}/delete")
async def delete_task(request: Request, task_id: int):
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Only admins can delete tasks"}, status_code=403)

    task_model.delete_task(task_id)
    return JSONResponse({"success": True, "message": "Task deleted!"})
