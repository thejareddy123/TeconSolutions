# ============================================================
# utils/helpers.py
# Common helper functions used throughout the app
# ============================================================

import bcrypt
import random
import string
from datetime import datetime, date
import pytz
from app.utils.config import settings


# ============================================================
# Password Functions
# ============================================================

def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    This is a one-way hash - you can't get the original password back.
    
    Usage:
        hashed = hash_password("mypassword123")
        # Store 'hashed' in database
    """
    # bcrypt automatically adds a 'salt' for extra security
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = secure but not too slow
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches the stored hash.
    
    Usage:
        is_correct = verify_password("mypassword123", stored_hash)
    """
    password_bytes = plain_password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def generate_temp_password(length: int = 10) -> str:
    """Generate a random temporary password"""
    # Include uppercase, lowercase, digits, and special chars
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(random.choices(chars, k=length))


# ============================================================
# Date & Time Functions
# ============================================================

def get_current_datetime():
    """Get current datetime in company timezone"""
    tz = pytz.timezone(settings.TIMEZONE)
    return datetime.now(tz)


def get_current_date():
    """Get current date in company timezone"""
    return get_current_datetime().date()


def calculate_working_days(start_date: date, end_date: date) -> float:
    """
    Calculate number of working days between two dates.
    Excludes weekends (Saturday=5, Sunday=6).
    
    Returns float because half-days might be supported later.
    """
    if start_date > end_date:
        return 0
    
    total_days = 0
    current = start_date
    
    while current <= end_date:
        # weekday() returns 0=Monday, 6=Sunday
        if current.weekday() < 5:  # Monday to Friday
            total_days += 1
        current = date(current.year, current.month, current.day + 1) if False else \
                  date.fromordinal(current.toordinal() + 1)
    
    return float(total_days)


def format_date(d) -> str:
    """Format a date object to readable string"""
    if d is None:
        return ""
    if isinstance(d, str):
        return d
    return d.strftime("%d %b %Y")  # e.g., "15 Aug 2025"


def format_datetime(dt) -> str:
    """Format datetime to readable string"""
    if dt is None:
        return ""
    return dt.strftime("%d %b %Y, %I:%M %p")  # e.g., "15 Aug 2025, 10:30 AM"


# ============================================================
# Employee ID Generation
# ============================================================

def generate_employee_id(last_id: int) -> str:
    """
    Generate next employee ID.
    Example: If last_id is 5, returns "EMP006"
    """
    return f"EMP{str(last_id + 1).zfill(3)}"  # zfill(3) pads with zeros


# ============================================================
# File Helpers
# ============================================================

def allowed_document_types(filename: str) -> bool:
    """Check if uploaded document is PDF, DOCX, or TXT"""
    allowed = {".pdf", ".docx", ".txt"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def allowed_image_types(filename: str) -> bool:
    """Check if uploaded image is JPG, JPEG, or PNG"""
    allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def get_file_extension(filename: str) -> str:
    """Get file extension without dot, lowercase"""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


# ============================================================
# Misc Helpers
# ============================================================

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if too long"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def get_initials(name: str) -> str:
    """Get initials from full name. 'John Doe' -> 'JD'"""
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return "??"
