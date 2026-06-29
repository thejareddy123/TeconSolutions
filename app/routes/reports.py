# ============================================================
# routes/reports.py
# Reports and analytics
# ============================================================

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import (
    timesheet_model, leave_model, task_model,
    user_model, notification_model
)
from app.database.connection import get_db
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    if session["role"] not in ["admin", "manager"]:
        return RedirectResponse("/dashboard", status_code=302)

    user_id = session["user_id"]
    today = datetime.now()

    # Summary stats
    task_stats = task_model.get_task_stats()
    leave_stats = leave_model.get_leave_stats()
    ts_stats = timesheet_model.get_timesheet_stats()
    total_employees = len(user_model.get_all_users())

    # Department breakdown
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT department, COUNT(*) as count
        FROM users WHERE is_active = TRUE AND department != ''
        GROUP BY department ORDER BY count DESC
    """)
    dept_breakdown = cursor.fetchall()

    # Monthly timesheet hours (last 6 months)
    cursor.execute("""
        SELECT
            EXTRACT(YEAR FROM work_date) AS year_num,
            EXTRACT(MONTH FROM work_date) AS month_num,
            SUM(hours_worked) AS total_hours,
            COUNT(DISTINCT user_id) AS active_employees
        FROM timesheets
        WHERE work_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        AND status = 'approved'
        GROUP BY
            EXTRACT(YEAR FROM work_date),
            EXTRACT(MONTH FROM work_date)
        ORDER BY
            year_num,
            month_num
    """)

    monthly_hours = cursor.fetchall()

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    for row in monthly_hours:
        row["month_label"] = f"{month_names[row['month_num']]} {row['year_num']}"

    # Leave type breakdown this year
    cursor.execute("""
        SELECT leave_type, COUNT(*) as count, SUM(total_days) as total_days
        FROM leaves
        WHERE status = 'approved' AND YEAR(start_date) = YEAR(CURDATE())
        GROUP BY leave_type
    """)
    leave_breakdown = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse("reports/index.html", {
        "request": request,
        "session": session,
        "task_stats": task_stats,
        "leave_stats": leave_stats,
        "ts_stats": ts_stats,
        "total_employees": total_employees,
        "dept_breakdown": dept_breakdown,
        "monthly_hours": monthly_hours,
        "leave_breakdown": leave_breakdown,
        "current_month": today.strftime("%B %Y"),
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.get("/api/reports/employee/{user_id}")
async def employee_report(request: Request, user_id: int, year: int = 0):
    """Get individual employee report as JSON"""
    session = get_session(request)
    if not session or session["role"] not in ["admin", "manager"]:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not year:
        year = datetime.now().year

    # Timesheets for the year
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            MONTH(work_date) as month_num,
            DATE_FORMAT(work_date, '%b') as month_name,
            SUM(hours_worked) as total_hours,
            COUNT(*) as days_logged
        FROM timesheets
        WHERE user_id = %s AND YEAR(work_date) = %s AND status = 'approved'
        GROUP BY MONTH(work_date)
        ORDER BY month_num
    """, (user_id, year))
    monthly_ts = cursor.fetchall()

    # Leave summary
    cursor.execute("""
        SELECT leave_type, SUM(total_days) as days_taken
        FROM leaves
        WHERE user_id = %s AND YEAR(start_date) = %s AND status = 'approved'
        GROUP BY leave_type
    """, (user_id, year))
    leave_summary = cursor.fetchall()

    conn.close()

    employee = user_model.get_user_by_id(user_id)

    return JSONResponse({
        "employee": {
            "name": f"{employee['first_name']} {employee['last_name']}",
            "employee_id": employee["employee_id"],
            "department": employee.get("department", "")
        },
        "monthly_timesheets": monthly_ts,
        "leave_summary": leave_summary,
        "year": year
    })
