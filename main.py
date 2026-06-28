# ============================================================
# main.py
# FastAPI Application Entry Point
# Run with: uvicorn main:app --reload
# ============================================================

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

# Import all route modules
from app.routes import (
    auth, dashboard, employees, tasks,
    timesheets, leaves, holidays, calendar,
    messages, notifications, profile, reports, ai_assistant
)
from app.database.connection import test_connection
from app.utils.config import settings

# ============================================================
# Create FastAPI app
# ============================================================
app = FastAPI(
    title="TraitSoftwares Timesheet & Task Management",
    description="Employee management system with AI assistant",
    version="1.0.0"
)

# ============================================================
# Mount static files (CSS, JS, images)
# ============================================================
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Also serve uploaded files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============================================================
# Register all routes
# ============================================================
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(employees.router)
app.include_router(tasks.router)
app.include_router(timesheets.router)
app.include_router(leaves.router)
app.include_router(holidays.router)
app.include_router(calendar.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(profile.router)
app.include_router(reports.router)
app.include_router(ai_assistant.router)


# ============================================================
# Startup Event - runs when server starts
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Check database connection and required folders on startup"""
    print("=" * 50)
    print(f"🚀 Starting {settings.COMPANY_NAME} App...")
    print("=" * 50)

    # Test database connection
    test_connection()

    # Create required folders
    folders = [
        "uploads",
        "uploads/profiles",
        "uploads/ai_docs",
        "vector_store/chroma_db",
        "app/static/css",
        "app/static/js",
        "app/static/images"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    print(f"✅ {settings.COMPANY_NAME} is ready!")
    print(f"🌐 Open: http://localhost:8000")
    print(f"📧 Admin login: admin@traitsoftwares.com / Admin@123")
    print("=" * 50)


# ============================================================
# Error Handlers
# ============================================================
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse(
        "components/error.html",
        {"request": request, "error": "Page not found", "code": 404},
        status_code=404
    )


@app.exception_handler(500)
async def server_error(request: Request, exc):
    return templates.TemplateResponse(
        "components/error.html",
        {"request": request, "error": "Internal server error", "code": 500},
        status_code=500
    )
