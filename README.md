# 🚀 TeconSolutions Timesheet & Task Management System

A complete Employee Management System built with **FastAPI, MySQL, Gemini AI, LangChain, and ChromaDB**.

---

## 📋 Features

| Module | Description |
|--------|-------------|
| 🔐 Authentication | Session-based login with bcrypt, account locking |
| 👥 Employee Management | Add/edit employees, departments, roles |
| 📋 Task Management | Create tasks, assign to employees, track status |
| 🕐 Timesheet | Log daily hours, submit for approval |
| 🌴 Leave Management | Apply leave, approve/reject with balance tracking |
| 📅 Calendar | Visual calendar with leaves, holidays, tasks |
| 🎉 Holiday Management | Add/manage company holidays |
| 📊 Reports | Analytics dashboard with charts |
| 💬 Messages | Internal messaging between employees |
| 🔔 Notifications | Real-time notifications for all events |
| 🤖 AI Assistant | RAG-based chatbot using Gemini + ChromaDB |
| 📚 Knowledge Base | Upload PDF/DOCX/TXT for AI to learn from |

---

## 🛠️ Tech Stack

```
Backend:    FastAPI + Python 3.11+
Database:   MySQL 8.0+
Frontend:   HTML + Tailwind CSS + Vanilla JS
AI:         Google Gemini API + LangChain + ChromaDB
Auth:       Session-based (signed cookies)
Email:      SMTP (Gmail)
Security:   bcrypt password hashing
```

---

## 📁 Project Structure

```
TeconSolutions/
│
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (NEVER commit!)
├── .gitignore
│
├── app/
│   ├── database/
│   │   ├── connection.py      # MySQL connection pool
│   │   └── schema.sql         # Database tables
│   │
│   ├── models/                # Database operations (CRUD)
│   │   ├── user_model.py
│   │   ├── task_model.py
│   │   ├── timesheet_model.py
│   │   ├── leave_model.py
│   │   ├── holiday_model.py
│   │   ├── notification_model.py
│   │   └── ai_model.py
│   │
│   ├── routes/                # URL handlers
│   │   ├── auth.py            # Login/logout
│   │   ├── dashboard.py
│   │   ├── employees.py
│   │   ├── tasks.py
│   │   ├── timesheets.py
│   │   ├── leaves.py
│   │   ├── holidays.py
│   │   ├── calendar.py
│   │   ├── messages.py
│   │   ├── notifications.py
│   │   ├── profile.py
│   │   ├── reports.py
│   │   └── ai_assistant.py
│   │
│   ├── services/              # Business logic (extend here)
│   │
│   ├── rag/                   # AI components
│   │   ├── document_processor.py   # Extract text from PDF/DOCX/TXT
│   │   ├── vector_store.py         # ChromaDB operations
│   │   └── ai_assistant.py         # Main RAG pipeline
│   │
│   ├── utils/
│   │   ├── config.py          # Settings from .env
│   │   ├── session.py         # Cookie-based sessions
│   │   ├── email.py           # SMTP email sending
│   │   └── helpers.py         # Misc utilities
│   │
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── components/
│   │   │   ├── base.html      # Main layout (sidebar + navbar)
│   │   │   └── error.html
│   │   ├── auth/login.html
│   │   ├── dashboard/index.html
│   │   ├── employees/
│   │   ├── tasks/
│   │   ├── timesheets/
│   │   ├── leaves/
│   │   ├── holidays/
│   │   ├── calendar/
│   │   ├── reports/
│   │   ├── messages/
│   │   ├── profile/
│   │   └── ai/
│   │
│   └── static/
│       ├── css/main.css       # Custom styles
│       └── js/main.js         # Common JavaScript
│
├── uploads/                   # User uploaded files
│   ├── profiles/              # Profile photos
│   └── ai_docs/               # Knowledge base documents
│
└── vector_store/
    └── chroma_db/             # ChromaDB persistent storage
```

---

## ⚙️ Setup Instructions

### Step 1: Clone or Download the Project

```bash
cd TeconSolutions
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE TeconSolutions_db;
exit;

# Run the schema
mysql -u root -p TeconSolutions_db < app/database/schema.sql
```

### Step 5: Configure Environment Variables

Edit the `.env` file:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=TeconSolutions_db
DB_USER=root
DB_PASSWORD=your_mysql_password

# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail: Enable 2FA, then create App Password
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Change these to random strings in production!
SECRET_KEY=make-this-long-and-random-abc123
SESSION_SECRET=another-long-random-string-xyz789
```

### Step 6: Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Open in Browser

```
http://localhost:8000

Default Admin Login:
Email:    admin@TeconSolutions.com
Password: Admin@123
```

> ⚠️ **Change the admin password immediately after first login!**

---

## 🤖 Setting Up the AI Assistant

### Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add it to `.env`: `GEMINI_API_KEY=your_key_here`

### Upload Knowledge Documents
1. Login as Admin
2. Go to **Admin → Knowledge Base**
3. Upload PDF/DOCX/TXT files (Employee Handbook, Leave Policy, etc.)
4. Documents are automatically chunked and indexed in ChromaDB

### Use the AI Assistant
1. Any employee can go to **AI Assistant**
2. Ask questions like:
   - "How many annual leave days do I have left?"
   - "What tasks are assigned to me?"
   - "What is the maternity leave policy?"
   - "Do I need to submit a timesheet today?"

---

## 📧 Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Gmail
2. Go to Google Account → Security → App Passwords
3. Create an App Password for "Mail"
4. Use that 16-character password in `.env` as `SMTP_PASSWORD`

---

## 👤 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to everything |
| **Manager** | View all tasks/leaves/timesheets, approve/reject |
| **Employee** | Own tasks, timesheets, leaves, AI assistant |

---

## 🔒 Security Features

- ✅ Passwords hashed with **bcrypt** (12 rounds)
- ✅ Session cookies are **HMAC-signed** (can't be tampered)
- ✅ Account **auto-locks** after 5 failed login attempts
- ✅ Email notification on account lock
- ✅ HttpOnly cookies (safe from XSS)
- ✅ Role-based access control on every route

---

## 🗄️ Database Tables

| Table | Purpose |
|-------|---------|
| `users` | All employees and admins |
| `tasks` | Tasks created in the system |
| `task_assignments` | Which employee is assigned to which task |
| `timesheets` | Daily work hour logs |
| `leaves` | Leave requests |
| `holidays` | Company holidays |
| `messages` | Internal messages |
| `notifications` | System notifications |
| `ai_documents` | Knowledge base documents |
| `ai_chat_history` | AI conversation history per user |

---

## 🚀 Common Commands

```bash
# Run server (development)
uvicorn main:app --reload

# Run server (production)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Reset database
mysql -u root -p TeconSolutions_db < app/database/schema.sql

# Check if all packages are installed
pip list | grep -E "fastapi|mysql|chromadb|google"
```

---

## 🐛 Troubleshooting

### Database Connection Error
```
Check: DB_HOST, DB_USER, DB_PASSWORD in .env
Make sure MySQL is running: sudo service mysql start
```

### Gemini API Error
```
Check: GEMINI_API_KEY in .env is correct
Test: curl https://generativelanguage.googleapis.com/v1/models?key=YOUR_KEY
```

### ChromaDB Error
```
Make sure vector_store/chroma_db/ folder exists
Delete vector_store/chroma_db/ and re-upload documents if corrupted
```

### Email Not Sending
```
Check Gmail App Password (not regular password)
Make sure 2FA is enabled on Gmail account
Check SMTP_USER and SMTP_PASSWORD in .env
```

---

## 💡 Interview Tips

**Q: How does the AI assistant work?**
A: "When an employee asks a question, we first fetch their personal data (tasks, leaves, timesheets) from MySQL. Then we search ChromaDB for relevant company policy documents using vector similarity. We combine both into a prompt and send it to Google Gemini, which generates a personalized answer."

**Q: How are passwords secured?**
A: "We use bcrypt with 12 rounds to hash passwords before storing them. Bcrypt is a one-way hash, so even if the database is compromised, passwords can't be recovered."

**Q: How does session management work?**
A: "We use signed cookies. The user data is base64-encoded and signed with HMAC-SHA256 using a secret key. On each request, we verify the signature to ensure the cookie wasn't tampered with."

---

## 📄 License

This project is for educational purposes. Built by TeconSolutions.

---

*Built with ❤️ using FastAPI + Gemini AI*
