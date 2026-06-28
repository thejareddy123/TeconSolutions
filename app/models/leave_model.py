# ============================================================
# models/leave_model.py
# Database operations for leaves table
# ============================================================

from app.database.connection import get_db


def create_leave_request(data: dict) -> int:
    """Submit a new leave request. Returns new leave ID."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leaves (
                user_id, leave_type, start_date, end_date, total_days, reason
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["user_id"],
            data["leave_type"],
            data["start_date"],
            data["end_date"],
            data["total_days"],
            data["reason"]
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def approve_leave(leave_id: int, reviewer_id: int) -> bool:
    """Approve a leave request and deduct from balance"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get leave details first
        cursor.execute("SELECT * FROM leaves WHERE id = %s", (leave_id,))
        leave = cursor.fetchone()
        
        if not leave or leave["status"] != "pending":
            return False
        
        # Update leave status
        cursor.execute("""
            UPDATE leaves 
            SET status = 'approved', reviewed_by = %s, reviewed_at = NOW()
            WHERE id = %s
        """, (reviewer_id, leave_id))
        
        # Deduct from leave balance
        if leave["leave_type"] == "annual":
            cursor.execute("""
                UPDATE users 
                SET annual_leave_balance = annual_leave_balance - %s
                WHERE id = %s AND annual_leave_balance >= %s
            """, (leave["total_days"], leave["user_id"], leave["total_days"]))
        elif leave["leave_type"] == "sick":
            cursor.execute("""
                UPDATE users 
                SET sick_leave_balance = sick_leave_balance - %s
                WHERE id = %s AND sick_leave_balance >= %s
            """, (leave["total_days"], leave["user_id"], leave["total_days"]))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def reject_leave(leave_id: int, reviewer_id: int, reason: str) -> bool:
    """Reject a leave request"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leaves 
            SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW(), rejection_reason = %s
            WHERE id = %s AND status = 'pending'
        """, (reviewer_id, reason, leave_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def cancel_leave(leave_id: int, user_id: int) -> bool:
    """Cancel a pending leave request"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leaves 
            SET status = 'cancelled'
            WHERE id = %s AND user_id = %s AND status = 'pending'
        """, (leave_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_leaves_for_user(user_id: int, year: int = None) -> list:
    """Get all leaves for an employee"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        params = [user_id]
        extra_where = ""
        
        if year:
            extra_where = "AND YEAR(l.start_date) = %s"
            params.append(year)
        
        cursor.execute(f"""
            SELECT l.*,
                   CONCAT(u.first_name, ' ', u.last_name) as reviewer_name
            FROM leaves l
            LEFT JOIN users u ON l.reviewed_by = u.id
            WHERE l.user_id = %s {extra_where}
            ORDER BY l.created_at DESC
        """, params)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_leaves(filters: dict = None) -> list:
    """Get all leaves (for admin/manager)"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get("status"):
                where_clauses.append("l.status = %s")
                params.append(filters["status"])
            if filters.get("user_id"):
                where_clauses.append("l.user_id = %s")
                params.append(filters["user_id"])
            if filters.get("leave_type"):
                where_clauses.append("l.leave_type = %s")
                params.append(filters["leave_type"])
        
        cursor.execute(f"""
            SELECT l.*,
                   CONCAT(e.first_name, ' ', e.last_name) as employee_name,
                   e.employee_id,
                   e.department,
                   CONCAT(m.first_name, ' ', m.last_name) as reviewer_name
            FROM leaves l
            JOIN users e ON l.user_id = e.id
            LEFT JOIN users m ON l.reviewed_by = m.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY l.created_at DESC
        """, params)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_leave_by_id(leave_id: int) -> dict | None:
    """Get a specific leave request by ID"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.*,
                   CONCAT(e.first_name, ' ', e.last_name) as employee_name,
                   e.email as employee_email,
                   e.employee_id
            FROM leaves l
            JOIN users e ON l.user_id = e.id
            WHERE l.id = %s
        """, (leave_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_leave_balance(user_id: int) -> dict:
    """Get leave balances for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT annual_leave_balance, sick_leave_balance
            FROM users WHERE id = %s
        """, (user_id,))
        return cursor.fetchone() or {"annual_leave_balance": 0, "sick_leave_balance": 0}
    finally:
        conn.close()


def get_leave_stats() -> dict:
    """Overall leave stats for dashboard"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM leaves
            WHERE YEAR(created_at) = YEAR(CURDATE())
        """)
        return cursor.fetchone() or {}
    finally:
        conn.close()


def get_approved_leaves_for_month(month: int, year: int) -> list:
    """Get all approved leaves for a specific month (for calendar)"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.*,
                   CONCAT(u.first_name, ' ', u.last_name) as employee_name,
                   u.department
            FROM leaves l
            JOIN users u ON l.user_id = u.id
            WHERE l.status = 'approved'
              AND (
                  (MONTH(l.start_date) = %s AND YEAR(l.start_date) = %s)
                  OR (MONTH(l.end_date) = %s AND YEAR(l.end_date) = %s)
              )
        """, (month, year, month, year))
        return cursor.fetchall()
    finally:
        conn.close()
