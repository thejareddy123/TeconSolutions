# ============================================================
# services/notification_service.py
# Business logic for sending notifications + emails together
# This is where you put complex business rules
# ============================================================

from app.models import notification_model, user_model
from app.utils import email as email_util


def notify_leave_applied(leave_id: int, employee_id: int, leave_type: str,
                          start_date: str, end_date: str, total_days: float):
    """
    Notify all managers when an employee applies for leave.
    This handles both in-app notification and email.
    """
    employee = user_model.get_user_by_id(employee_id)
    if not employee:
        return
    
    emp_name = f"{employee['first_name']} {employee['last_name']}"
    
    # Get all managers and admins to notify
    managers = user_model.get_managers()
    
    for mgr in managers:
        # In-app notification
        notification_model.create_notification(
            user_id=mgr["id"],
            title=f"New Leave Request from {emp_name}",
            message=f"{emp_name} applied for {leave_type} leave from {start_date} to {end_date} ({total_days} days). Please review.",
            notif_type="leave_applied",
            link="/leaves"
        )


def notify_leave_decision(leave_id: int, employee_id: int, status: str,
                           leave_type: str, start_date: str, end_date: str,
                           rejection_reason: str = ""):
    """
    Notify employee when their leave is approved or rejected.
    """
    employee = user_model.get_user_by_id(employee_id)
    if not employee:
        return
    
    emp_name = f"{employee['first_name']} {employee['last_name']}"
    emoji = "✅" if status == "approved" else "❌"
    
    # In-app notification
    msg = f"Your {leave_type} leave from {start_date} to {end_date} has been {status}."
    if rejection_reason:
        msg += f" Reason: {rejection_reason}"
    
    notification_model.create_notification(
        user_id=employee_id,
        title=f"Leave {status.capitalize()} {emoji}",
        message=msg,
        notif_type=f"leave_{status}",
        link="/leaves"
    )
    
    # Email notification
    try:
        email_util.send_leave_status_email(
            to_email=employee["email"],
            name=emp_name,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            status=status,
            reason=rejection_reason
        )
    except Exception as e:
        print(f"⚠️ Email notification failed: {e}")
        # Don't raise - email failure shouldn't break the approval


def notify_task_assigned(task_id: int, task_title: str, assigned_to_id: int,
                          assigned_by_name: str, due_date: str = ""):
    """
    Notify an employee when a task is assigned to them.
    """
    employee = user_model.get_user_by_id(assigned_to_id)
    if not employee:
        return
    
    # In-app notification
    notification_model.create_notification(
        user_id=assigned_to_id,
        title=f"New Task Assigned: {task_title}",
        message=f"You have been assigned a new task by {assigned_by_name}. Due: {due_date or 'No deadline'}",
        notif_type="task_assigned",
        link="/tasks"
    )
    
    # Email notification
    try:
        email_util.send_task_assignment_email(
            to_email=employee["email"],
            name=f"{employee['first_name']} {employee['last_name']}",
            task_title=task_title,
            due_date=due_date or "No deadline",
            assigned_by=assigned_by_name
        )
    except Exception as e:
        print(f"⚠️ Task assignment email failed: {e}")


def notify_timesheet_decision(timesheet_id: int, employee_id: int,
                               work_date: str, status: str, notes: str = ""):
    """
    Notify employee when timesheet is approved or rejected.
    """
    employee = user_model.get_user_by_id(employee_id)
    if not employee:
        return
    
    emoji = "✅" if status == "approved" else "❌"
    
    notification_model.create_notification(
        user_id=employee_id,
        title=f"Timesheet {status.capitalize()} {emoji}",
        message=f"Your timesheet for {work_date} has been {status}.{' Note: ' + notes if notes else ''}",
        notif_type=f"timesheet_{status}",
        link="/timesheets"
    )
    
    try:
        email_util.send_timesheet_status_email(
            to_email=employee["email"],
            name=f"{employee['first_name']} {employee['last_name']}",
            work_date=work_date,
            status=status,
            notes=notes
        )
    except Exception as e:
        print(f"⚠️ Timesheet email failed: {e}")


def notify_new_message(sender_name: str, receiver_id: int, subject: str):
    """
    Notify user when they receive a new message.
    """
    notification_model.create_notification(
        user_id=receiver_id,
        title=f"New Message from {sender_name}",
        message=subject,
        notif_type="message_received",
        link="/messages"
    )
