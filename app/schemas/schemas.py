# ============================================================
# schemas/schemas.py
# Pydantic models for data validation (optional but good practice)
# FastAPI can use these for request body validation
# ============================================================

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


# ============================================================
# USER SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = ""
    department: Optional[str] = ""
    designation: Optional[str] = ""
    role: str = "employee"
    manager_id: Optional[int] = None
    date_of_joining: Optional[date] = None
    annual_leave_balance: float = 12.0
    sick_leave_balance: float = 6.0


class UserUpdate(BaseModel):
    """Schema for updating user info"""
    first_name: str
    last_name: str
    phone: Optional[str] = ""
    department: Optional[str] = ""
    designation: Optional[str] = ""
    role: str = "employee"
    manager_id: Optional[int] = None
    date_of_joining: Optional[date] = None
    annual_leave_balance: float = 12.0
    sick_leave_balance: float = 6.0
    address: Optional[str] = ""
    date_of_birth: Optional[date] = None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str
    confirm_password: str


# ============================================================
# TASK SCHEMAS
# ============================================================

class TaskCreate(BaseModel):
    """Schema for creating a task"""
    title: str
    description: Optional[str] = ""
    priority: str = "medium"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    project_name: Optional[str] = ""


class TaskUpdate(TaskCreate):
    """Schema for updating a task (same fields + status)"""
    status: str = "todo"


# ============================================================
# TIMESHEET SCHEMAS
# ============================================================

class TimesheetLog(BaseModel):
    """Schema for logging timesheet hours"""
    work_date: date
    hours_worked: float
    description: str
    task_id: Optional[int] = None


# ============================================================
# LEAVE SCHEMAS
# ============================================================

class LeaveApply(BaseModel):
    """Schema for applying leave"""
    leave_type: str
    start_date: date
    end_date: date
    reason: str


class LeaveReject(BaseModel):
    """Schema for rejecting leave"""
    reason: str


# ============================================================
# MESSAGE SCHEMAS
# ============================================================

class MessageSend(BaseModel):
    """Schema for sending a message"""
    receiver_id: int
    subject: str
    body: str


# ============================================================
# HOLIDAY SCHEMAS
# ============================================================

class HolidayCreate(BaseModel):
    """Schema for adding a holiday"""
    name: str
    holiday_date: date
    holiday_type: str = "national"
    description: Optional[str] = ""


# ============================================================
# AI SCHEMAS
# ============================================================

class AIQuestion(BaseModel):
    """Schema for asking the AI assistant"""
    question: str


# ============================================================
# RESPONSE SCHEMAS (standard API responses)
# ============================================================

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
