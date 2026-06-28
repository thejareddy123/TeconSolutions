# ============================================================
# models/user_model.py
# Database operations for users table
# ============================================================

from app.database.connection import get_db
from app.utils.helpers import hash_password


def get_user_by_email(email: str) -> dict | None:
    """Find a user by their email address"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)  # Returns rows as dicts
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND is_active = TRUE",
            (email,)
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    """Find a user by their ID"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT u.*, 
               CONCAT(m.first_name, ' ', m.last_name) as manager_name
               FROM users u
               LEFT JOIN users m ON u.manager_id = m.id
               WHERE u.id = %s""",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_all_users(include_inactive: bool = False) -> list:
    """Get all users, optionally including inactive ones"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        where = "" if include_inactive else "WHERE u.is_active = TRUE"
        
        cursor.execute(f"""
            SELECT u.id, u.employee_id, u.first_name, u.last_name, 
                   u.email, u.phone, u.role, u.department, u.designation,
                   u.date_of_joining, u.is_active, u.is_locked,
                   u.profile_photo, u.annual_leave_balance, u.sick_leave_balance,
                   u.created_at, u.last_login,
                   CONCAT(m.first_name, ' ', m.last_name) as manager_name
            FROM users u
            LEFT JOIN users m ON u.manager_id = m.id
            {where}
            ORDER BY u.first_name
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def create_user(data: dict) -> int:
    """
    Create a new user in the database.
    Returns the new user's ID.
    
    data should contain: employee_id, first_name, last_name, email,
    password (plain text), role, department, designation, etc.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Hash the password before saving
        password_hash = hash_password(data["password"])
        
        cursor.execute("""
            INSERT INTO users (
                employee_id, first_name, last_name, email, phone,
                password_hash, role, department, designation,
                date_of_joining, manager_id,
                annual_leave_balance, sick_leave_balance,
                date_of_birth, address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["employee_id"],
            data["first_name"],
            data["last_name"],
            data["email"],
            data.get("phone", ""),
            password_hash,
            data.get("role", "employee"),
            data.get("department", ""),
            data.get("designation", ""),
            data.get("date_of_joining"),
            data.get("manager_id"),
            data.get("annual_leave_balance", 12.00),
            data.get("sick_leave_balance", 6.00),
            data.get("date_of_birth"),
            data.get("address", "")
        ))
        
        conn.commit()
        return cursor.lastrowid  # Return the new user's ID
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_user(user_id: int, data: dict) -> bool:
    """Update user profile information"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET
                first_name = %s,
                last_name = %s,
                phone = %s,
                department = %s,
                designation = %s,
                manager_id = %s,
                role = %s,
                date_of_joining = %s,
                annual_leave_balance = %s,
                sick_leave_balance = %s,
                address = %s,
                date_of_birth = %s
            WHERE id = %s
        """, (
            data["first_name"],
            data["last_name"],
            data.get("phone", ""),
            data.get("department", ""),
            data.get("designation", ""),
            data.get("manager_id"),
            data.get("role", "employee"),
            data.get("date_of_joining"),
            data.get("annual_leave_balance", 12),
            data.get("sick_leave_balance", 6),
            data.get("address", ""),
            data.get("date_of_birth"),
            user_id
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_password(user_id: int, new_password: str) -> bool:
    """Update user's password"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        new_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_profile_photo(user_id: int, photo_path: str) -> bool:
    """Update user's profile photo path"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_photo = %s WHERE id = %s",
            (photo_path, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def update_last_login(user_id: int):
    """Update the last_login timestamp"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = NOW(), failed_login_attempts = 0 WHERE id = %s",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()


def increment_failed_login(user_id: int) -> int:
    """
    Increment failed login counter.
    Returns new count so we can lock account if needed.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        
        # Get new count
        cursor.execute(
            "SELECT failed_login_attempts FROM users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def lock_user_account(user_id: int) -> bool:
    """Lock a user account"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_locked = TRUE WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def toggle_user_status(user_id: int) -> bool:
    """Toggle user active/inactive status"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_active = NOT is_active, is_locked = FALSE WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_next_employee_id() -> str:
    """Generate next employee ID like EMP002, EMP003..."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM users")
        row = cursor.fetchone()
        last_id = row[0] if row[0] else 0
        return f"EMP{str(last_id + 1).zfill(3)}"
    finally:
        conn.close()


def get_managers() -> list:
    """Get all managers and admins (for dropdown menus)"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, CONCAT(first_name, ' ', last_name) as name, role
            FROM users
            WHERE role IN ('admin', 'manager') AND is_active = TRUE
            ORDER BY first_name
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def search_users(query: str) -> list:
    """Search users by name, email, or employee ID"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT id, employee_id, first_name, last_name, email, department, role
            FROM users
            WHERE is_active = TRUE AND (
                first_name LIKE %s OR
                last_name LIKE %s OR
                email LIKE %s OR
                employee_id LIKE %s
            )
            ORDER BY first_name
            LIMIT 20
        """, (search_term, search_term, search_term, search_term))
        return cursor.fetchall()
    finally:
        conn.close()
