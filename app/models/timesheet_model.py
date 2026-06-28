# ============================================================
# models/timesheet_model.py
# Database operations for timesheets table
# ============================================================

from app.database.connection import get_db


def create_timesheet(data: dict) -> int:
    """Create or update a timesheet entry"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Use INSERT ... ON DUPLICATE KEY UPDATE
        # Because each user can only have one entry per day
        cursor.execute("""
            INSERT INTO timesheets (
                user_id, work_date, hours_worked, task_id, description, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hours_worked = VALUES(hours_worked),
                task_id = VALUES(task_id),
                description = VALUES(description),
                status = IF(status = 'rejected', 'draft', status)
        """, (
            data["user_id"],
            data["work_date"],
            data["hours_worked"],
            data.get("task_id"),
            data["description"],
            data.get("status", "draft")
        ))
        
        conn.commit()
        return cursor.lastrowid or 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def submit_timesheet(timesheet_id: int, user_id: int) -> bool:
    """Submit a timesheet for approval"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE timesheets 
            SET status = 'submitted'
            WHERE id = %s AND user_id = %s AND status = 'draft'
        """, (timesheet_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def approve_timesheet(timesheet_id: int, reviewer_id: int, notes: str = "") -> bool:
    """Approve a submitted timesheet"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE timesheets 
            SET status = 'approved', reviewed_by = %s, reviewed_at = NOW(), review_notes = %s
            WHERE id = %s AND status = 'submitted'
        """, (reviewer_id, notes, timesheet_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def reject_timesheet(timesheet_id: int, reviewer_id: int, notes: str) -> bool:
    """Reject a submitted timesheet"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE timesheets 
            SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW(), review_notes = %s
            WHERE id = %s AND status = 'submitted'
        """, (reviewer_id, notes, timesheet_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_timesheets_for_user(user_id: int, month: int = None, year: int = None) -> list:
    """Get all timesheets for an employee, optionally filtered by month/year"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        params = [user_id]
        extra_where = ""
        
        if month and year:
            extra_where = "AND MONTH(t.work_date) = %s AND YEAR(t.work_date) = %s"
            params.extend([month, year])
        
        cursor.execute(f"""
            SELECT t.*, 
                   tk.title as task_title,
                   CONCAT(u.first_name, ' ', u.last_name) as reviewer_name
            FROM timesheets t
            LEFT JOIN tasks tk ON t.task_id = tk.id
            LEFT JOIN users u ON t.reviewed_by = u.id
            WHERE t.user_id = %s {extra_where}
            ORDER BY t.work_date DESC
        """, params)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_timesheets(filters: dict = None) -> list:
    """Get all timesheets (for admin/manager view)"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get("status"):
                where_clauses.append("t.status = %s")
                params.append(filters["status"])
            if filters.get("user_id"):
                where_clauses.append("t.user_id = %s")
                params.append(filters["user_id"])
            if filters.get("month") and filters.get("year"):
                where_clauses.append("MONTH(t.work_date) = %s AND YEAR(t.work_date) = %s")
                params.extend([filters["month"], filters["year"]])
        
        cursor.execute(f"""
            SELECT t.*,
                   CONCAT(e.first_name, ' ', e.last_name) as employee_name,
                   e.employee_id,
                   e.department,
                   tk.title as task_title,
                   CONCAT(m.first_name, ' ', m.last_name) as reviewer_name
            FROM timesheets t
            JOIN users e ON t.user_id = e.id
            LEFT JOIN tasks tk ON t.task_id = tk.id
            LEFT JOIN users m ON t.reviewed_by = m.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY t.work_date DESC, e.first_name ASC
        """, params)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_timesheet_by_date(user_id: int, work_date: str) -> dict | None:
    """Get a specific timesheet entry for a user on a date"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM timesheets
            WHERE user_id = %s AND work_date = %s
        """, (user_id, work_date))
        return cursor.fetchone()
    finally:
        conn.close()


def get_monthly_hours(user_id: int, month: int, year: int) -> dict:
    """Get total hours worked in a month"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                SUM(hours_worked) as total_hours,
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'approved' THEN hours_worked ELSE 0 END) as approved_hours
            FROM timesheets
            WHERE user_id = %s AND MONTH(work_date) = %s AND YEAR(work_date) = %s
        """, (user_id, month, year))
        return cursor.fetchone() or {"total_hours": 0, "total_days": 0, "approved_hours": 0}
    finally:
        conn.close()


def get_timesheet_stats() -> dict:
    """Overall timesheet stats for dashboard"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as pending_review,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM timesheets
            WHERE MONTH(work_date) = MONTH(CURDATE()) AND YEAR(work_date) = YEAR(CURDATE())
        """)
        return cursor.fetchone() or {}
    finally:
        conn.close()
