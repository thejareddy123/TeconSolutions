# ============================================================
# models/notification_model.py
# Database operations for notifications and messages
# ============================================================

from app.database.connection import get_db


# ============================================================
# NOTIFICATIONS
# ============================================================

def create_notification(user_id: int, title: str, message: str, 
                         notif_type: str = "general", link: str = "") -> int:
    """Create a notification for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, title, message, notif_type, link))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_notifications_for_user(user_id: int, limit: int = 20) -> list:
    """Get recent notifications for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def get_unread_count(user_id: int) -> int:
    """Count unread notifications"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def mark_notification_read(notif_id: int, user_id: int) -> bool:
    """Mark a notification as read"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE id = %s AND user_id = %s
        """, (notif_id, user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def mark_all_read(user_id: int) -> bool:
    """Mark all notifications as read for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ============================================================
# MESSAGES
# ============================================================

def send_message(sender_id: int, receiver_id: int, subject: str, body: str) -> int:
    """Send a message from one user to another"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, subject, body)
            VALUES (%s, %s, %s, %s)
        """, (sender_id, receiver_id, subject, body))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_inbox(user_id: int) -> list:
    """Get messages received by user"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*,
                   CONCAT(u.first_name, ' ', u.last_name) as sender_name,
                   u.profile_photo as sender_photo,
                   u.employee_id as sender_employee_id
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = %s
            ORDER BY m.created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_sent_messages(user_id: int) -> list:
    """Get messages sent by user"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*,
                   CONCAT(u.first_name, ' ', u.last_name) as receiver_name,
                   u.profile_photo as receiver_photo
            FROM messages m
            JOIN users u ON m.receiver_id = u.id
            WHERE m.sender_id = %s
            ORDER BY m.created_at DESC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_message_by_id(message_id: int) -> dict | None:
    """Get a specific message"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.*,
                   CONCAT(s.first_name, ' ', s.last_name) as sender_name,
                   CONCAT(r.first_name, ' ', r.last_name) as receiver_name
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE m.id = %s
        """, (message_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def mark_message_read(message_id: int, user_id: int) -> bool:
    """Mark a message as read"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE messages SET is_read = TRUE, read_at = NOW()
            WHERE id = %s AND receiver_id = %s
        """, (message_id, user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_unread_message_count(user_id: int) -> int:
    """Count unread messages"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE receiver_id = %s AND is_read = FALSE",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()
