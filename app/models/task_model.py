# ============================================================
# models/task_model.py
# Database operations for tasks and task_assignments
# ============================================================

from app.database.connection import get_db


def create_task(data: dict) -> int:
    """Create a new task. Returns new task ID."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (
                title, description, created_by, priority, status,
                start_date, due_date, project_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["title"],
            data.get("description", ""),
            data["created_by"],
            data.get("priority", "medium"),
            data.get("status", "todo"),
            data.get("start_date"),
            data.get("due_date"),
            data.get("project_name", "")
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def assign_task(task_id: int, user_id: int, assigned_by: int) -> bool:
    """Assign a task to a user"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT IGNORE INTO task_assignments (task_id, user_id, assigned_by)
            VALUES (%s, %s, %s)
        """, (task_id, user_id, assigned_by))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_all_tasks(filters: dict = None) -> list:
    """Get all tasks with assignee info"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if filters:
            if filters.get("status"):
                where_clauses.append("t.status = %s")
                params.append(filters["status"])
            if filters.get("priority"):
                where_clauses.append("t.priority = %s")
                params.append(filters["priority"])
            if filters.get("search"):
                where_clauses.append("t.title LIKE %s")
                params.append(f"%{filters['search']}%")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        cursor.execute(f"""
            SELECT t.*,
                   CONCAT(u.first_name, ' ', u.last_name) as created_by_name,
                   GROUP_CONCAT(CONCAT(e.first_name, ' ', e.last_name) SEPARATOR ', ') as assignees,
                   GROUP_CONCAT(ta.user_id) as assignee_ids
            FROM tasks t
            JOIN users u ON t.created_by = u.id
            LEFT JOIN task_assignments ta ON t.id = ta.task_id
            LEFT JOIN users e ON ta.user_id = e.id
            {where_sql}
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """, params)
        
        return cursor.fetchall()
    finally:
        conn.close()


def get_tasks_for_user(user_id: int) -> list:
    """Get tasks assigned to a specific employee"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*,
                   CONCAT(u.first_name, ' ', u.last_name) as created_by_name
            FROM tasks t
            JOIN task_assignments ta ON t.id = ta.task_id
            JOIN users u ON t.created_by = u.id
            WHERE ta.user_id = %s
            ORDER BY 
                CASE t.status 
                    WHEN 'todo' THEN 1 
                    WHEN 'in_progress' THEN 2 
                    WHEN 'review' THEN 3
                    WHEN 'completed' THEN 4
                    ELSE 5 
                END,
                t.due_date ASC
        """, (user_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_task_by_id(task_id: int) -> dict | None:
    """Get single task with all details"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*,
                   CONCAT(u.first_name, ' ', u.last_name) as created_by_name
            FROM tasks t
            JOIN users u ON t.created_by = u.id
            WHERE t.id = %s
        """, (task_id,))
        task = cursor.fetchone()
        
        if task:
            # Also get assignees
            cursor.execute("""
                SELECT u.id, u.employee_id, 
                       CONCAT(u.first_name, ' ', u.last_name) as name,
                       u.profile_photo
                FROM task_assignments ta
                JOIN users u ON ta.user_id = u.id
                WHERE ta.task_id = %s
            """, (task_id,))
            task["assignees"] = cursor.fetchall()
        
        return task
    finally:
        conn.close()


def update_task(task_id: int, data: dict) -> bool:
    """Update task details"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET
                title = %s,
                description = %s,
                priority = %s,
                status = %s,
                start_date = %s,
                due_date = %s,
                project_name = %s
            WHERE id = %s
        """, (
            data["title"],
            data.get("description", ""),
            data.get("priority", "medium"),
            data.get("status", "todo"),
            data.get("start_date"),
            data.get("due_date"),
            data.get("project_name", ""),
            task_id
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_task_status(task_id: int, status: str, user_id: int) -> bool:
    """Update just the status of a task (called by employees)"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Set completed_date if marking as completed
        if status == "completed":
            cursor.execute(
                "UPDATE tasks SET status = %s, completed_date = CURDATE() WHERE id = %s",
                (status, task_id)
            )
        else:
            cursor.execute(
                "UPDATE tasks SET status = %s, completed_date = NULL WHERE id = %s",
                (status, task_id)
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_task(task_id: int) -> bool:
    """Delete a task"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def remove_task_assignment(task_id: int, user_id: int) -> bool:
    """Remove a user from a task"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM task_assignments WHERE task_id = %s AND user_id = %s",
            (task_id, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_task_stats() -> dict:
    """Get task statistics for dashboard"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) as todo,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN due_date < CURDATE() AND status NOT IN ('completed','cancelled') THEN 1 ELSE 0 END) as overdue
            FROM tasks
        """)
        return cursor.fetchone() or {}
    finally:
        conn.close()
