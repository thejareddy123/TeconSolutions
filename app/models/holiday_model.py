# ============================================================
# models/holiday_model.py
# Database operations for holidays table
# ============================================================

from app.database.connection import get_db


def get_all_holidays(year: int = None) -> list:
    """Get all holidays, optionally filtered by year"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        if year:
            cursor.execute("""
                SELECT h.*, CONCAT(u.first_name, ' ', u.last_name) as created_by_name
                FROM holidays h
                LEFT JOIN users u ON h.created_by = u.id
                WHERE YEAR(h.holiday_date) = %s
                ORDER BY h.holiday_date ASC
            """, (year,))
        else:
            cursor.execute("""
                SELECT h.*, CONCAT(u.first_name, ' ', u.last_name) as created_by_name
                FROM holidays h
                LEFT JOIN users u ON h.created_by = u.id
                ORDER BY h.holiday_date ASC
            """)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_upcoming_holidays(limit: int = 5) -> list:
    """Get next N upcoming holidays"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM holidays
            WHERE holiday_date >= CURDATE()
            ORDER BY holiday_date ASC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        conn.close()


def create_holiday(data: dict, created_by: int) -> int:
    """Add a new holiday"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO holidays (name, holiday_date, description, holiday_type, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data["name"],
            data["holiday_date"],
            data.get("description", ""),
            data.get("holiday_type", "national"),
            created_by
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_holiday(holiday_id: int) -> bool:
    """Delete a holiday"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM holidays WHERE id = %s", (holiday_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_holidays_for_month(month: int, year: int) -> list:
    """Get holidays for a specific month (for calendar)"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM holidays
            WHERE MONTH(holiday_date) = %s AND YEAR(holiday_date) = %s
            ORDER BY holiday_date ASC
        """, (month, year))
        return cursor.fetchall()
    finally:
        conn.close()


def is_holiday(check_date: str) -> bool:
    """Check if a date is a holiday"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM holidays WHERE holiday_date = %s",
            (check_date,)
        )
        row = cursor.fetchone()
        return row[0] > 0
    finally:
        conn.close()
