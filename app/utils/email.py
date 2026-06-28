# ============================================================
# utils/email.py
# Simple email sending utility using SMTP
# ============================================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.utils.config import settings


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML content of the email
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Create the email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        
        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()  # Enable encryption
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        
        print(f"✅ Email sent to {to_email}: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False


# ============================================================
# Pre-built email templates
# ============================================================

def send_welcome_email(to_email: str, name: str, employee_id: str, temp_password: str):
    """Send welcome email when a new account is created"""
    subject = f"Welcome to {settings.COMPANY_NAME} - Your Account Details"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1e40af; color: white; padding: 20px; text-align: center;">
            <h1>{settings.COMPANY_NAME}</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Welcome, {name}! 🎉</h2>
            <p>Your account has been created. Here are your login details:</p>
            <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                <p><strong>Employee ID:</strong> {employee_id}</p>
                <p><strong>Email:</strong> {to_email}</p>
                <p><strong>Temporary Password:</strong> <code style="background:#eee;padding:4px 8px;">{temp_password}</code></p>
            </div>
            <p style="color: #e74c3c;"><strong>⚠️ Please change your password after first login!</strong></p>
            <p>Login at: <a href="http://localhost:8000/login">http://localhost:8000/login</a></p>
        </div>
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>© {settings.COMPANY_NAME}. This is an automated email.</p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def send_leave_status_email(to_email: str, name: str, leave_type: str, 
                             start_date: str, end_date: str, status: str, 
                             reason: str = ""):
    """Send email when leave is approved or rejected"""
    emoji = "✅" if status == "approved" else "❌"
    color = "#27ae60" if status == "approved" else "#e74c3c"
    
    subject = f"{emoji} Leave Request {status.capitalize()} - {settings.COMPANY_NAME}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {color}; color: white; padding: 20px; text-align: center;">
            <h1>{emoji} Leave {status.capitalize()}</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <p>Dear {name},</p>
            <p>Your leave request has been <strong>{status}</strong>.</p>
            <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                <p><strong>Leave Type:</strong> {leave_type.capitalize()}</p>
                <p><strong>From:</strong> {start_date}</p>
                <p><strong>To:</strong> {end_date}</p>
                <p><strong>Status:</strong> <span style="color:{color};">{status.upper()}</span></p>
                {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
            </div>
        </div>
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>© {settings.COMPANY_NAME}. This is an automated email.</p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def send_task_assignment_email(to_email: str, name: str, task_title: str, 
                                due_date: str, assigned_by: str):
    """Send email when a task is assigned"""
    subject = f"📋 New Task Assigned: {task_title} - {settings.COMPANY_NAME}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1e40af; color: white; padding: 20px; text-align: center;">
            <h1>📋 New Task Assigned</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <p>Dear {name},</p>
            <p>A new task has been assigned to you.</p>
            <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
                <p><strong>Task:</strong> {task_title}</p>
                <p><strong>Due Date:</strong> {due_date}</p>
                <p><strong>Assigned By:</strong> {assigned_by}</p>
            </div>
            <p>Login to view task details: <a href="http://localhost:8000/tasks">View Tasks</a></p>
        </div>
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>© {settings.COMPANY_NAME}. This is an automated email.</p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def send_account_locked_email(to_email: str, name: str):
    """Send email when account is locked due to too many failed attempts"""
    subject = f"🔒 Account Locked - {settings.COMPANY_NAME}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #e74c3c; color: white; padding: 20px; text-align: center;">
            <h1>🔒 Account Locked</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <p>Dear {name},</p>
            <p>Your account has been locked due to multiple failed login attempts.</p>
            <p>Please contact HR or your system administrator to unlock your account.</p>
            <p>Email: <a href="mailto:{settings.COMPANY_EMAIL}">{settings.COMPANY_EMAIL}</a></p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def send_timesheet_status_email(to_email: str, name: str, work_date: str, 
                                  status: str, notes: str = ""):
    """Send email when timesheet is approved or rejected"""
    emoji = "✅" if status == "approved" else "❌"
    subject = f"{emoji} Timesheet {status.capitalize()} - {work_date}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="padding: 30px;">
            <p>Dear {name},</p>
            <p>Your timesheet for <strong>{work_date}</strong> has been <strong>{status}</strong>.</p>
            {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)
