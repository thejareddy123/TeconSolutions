#!/usr/bin/env python3
# ============================================================
# setup_check.py
# Run this script to verify your setup is correct
# Usage: python setup_check.py
# ============================================================

import sys
import os

print("=" * 60)
print("🔍 TraitSoftwares Setup Checker")
print("=" * 60)

errors = []
warnings = []

# ============================================================
# Check Python version
# ============================================================
py_version = sys.version_info
if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 9):
    errors.append(f"Python 3.9+ required, found {py_version.major}.{py_version.minor}")
else:
    print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")

# ============================================================
# Check required packages
# ============================================================
required_packages = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("jinja2", "jinja2"),
    ("mysql.connector", "mysql-connector-python"),
    ("bcrypt", "bcrypt"),
    ("dotenv", "python-dotenv"),
    ("google.generativeai", "google-generativeai"),
    ("chromadb", "chromadb"),
    ("pypdf", "pypdf"),
    ("docx", "python-docx"),
    ("pytz", "pytz"),
]

print("\n📦 Checking packages...")
for import_name, package_name in required_packages:
    try:
        __import__(import_name)
        print(f"  ✅ {package_name}")
    except ImportError:
        errors.append(f"Missing package: {package_name} — run: pip install {package_name}")
        print(f"  ❌ {package_name} — NOT INSTALLED")

# ============================================================
# Check .env file
# ============================================================
print("\n🔧 Checking .env file...")
if not os.path.exists(".env"):
    errors.append(".env file not found! Copy .env and fill in your values.")
    print("  ❌ .env file missing!")
else:
    print("  ✅ .env file found")
    
    # Load and check specific keys
    from dotenv import load_dotenv
    load_dotenv()
    
    checks = [
        ("DB_PASSWORD", "MySQL password"),
        ("GEMINI_API_KEY", "Gemini AI key"),
        ("SECRET_KEY", "App secret key"),
        ("SESSION_SECRET", "Session secret key"),
    ]
    
    for key, desc in checks:
        val = os.getenv(key, "")
        if not val or val.startswith("your-") or val.startswith("your_"):
            warnings.append(f"{key} not configured ({desc})")
            print(f"  ⚠️  {key} — needs to be set")
        else:
            print(f"  ✅ {key} — configured")

# ============================================================
# Check database connection
# ============================================================
print("\n🗄️  Checking database...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    import mysql.connector
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "traitsoftwares_db")
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()
    
    required_tables = ["users", "tasks", "timesheets", "leaves", "holidays",
                        "messages", "notifications", "ai_documents", "ai_chat_history"]
    
    for table in required_tables:
        if table in tables:
            print(f"  ✅ Table '{table}' exists")
        else:
            errors.append(f"Table '{table}' missing — run: mysql -u root -p traitsoftwares_db < app/database/schema.sql")
            print(f"  ❌ Table '{table}' MISSING")

except Exception as e:
    errors.append(f"Database connection failed: {e}")
    print(f"  ❌ Connection failed: {e}")

# ============================================================
# Check required folders
# ============================================================
print("\n📁 Checking folders...")
required_folders = [
    "uploads",
    "uploads/profiles",
    "uploads/ai_docs",
    "vector_store",
    "app/static/css",
    "app/static/js",
    "app/templates",
]

for folder in required_folders:
    if os.path.exists(folder):
        print(f"  ✅ {folder}/")
    else:
        os.makedirs(folder, exist_ok=True)
        print(f"  ✅ {folder}/ (created)")

# ============================================================
# Check static files
# ============================================================
print("\n🎨 Checking static files...")
static_files = [
    "app/static/css/main.css",
    "app/static/js/main.js",
]
for f in static_files:
    if os.path.exists(f):
        print(f"  ✅ {f}")
    else:
        warnings.append(f"Static file missing: {f}")
        print(f"  ⚠️  {f} — missing")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)

if errors:
    print(f"❌ Found {len(errors)} ERROR(S):")
    for i, err in enumerate(errors, 1):
        print(f"   {i}. {err}")

if warnings:
    print(f"\n⚠️  Found {len(warnings)} WARNING(S):")
    for i, warn in enumerate(warnings, 1):
        print(f"   {i}. {warn}")

if not errors and not warnings:
    print("✅ All checks passed! Your setup looks good.")
    print("\n🚀 Run the app with:")
    print("   uvicorn main:app --reload")
    print("\n🌐 Open: http://localhost:8000")
    print("👤 Admin: admin@traitsoftwares.com / Admin@123")
elif not errors:
    print("\n✅ No critical errors. Warnings are optional improvements.")
    print("\n🚀 You can still run: uvicorn main:app --reload")
else:
    print("\n❌ Please fix errors before running the app.")

print("=" * 60)
