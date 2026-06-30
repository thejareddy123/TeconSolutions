# 🚀 TeconSolutions Timesheet & Task Management System

A complete Employee Management System built with **FastAPI, MySQL, Gemini AI, LangChain, and ChromaDB**.



# 📋 Features

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
├── .env                       # Environment variables 
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
│   ├── services/              # Business logic 
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


Default Admin Login:
Email:    admin@TeconSolutions.com
Password: Admin@123





# Upload Knowledge Documents
1. Login as Admin
2. Go to **Admin → Knowledge Base**
3. Upload PDF/DOCX/TXT files (Employee Handbook, Leave Policy, etc.)
4. Documents are automatically chunked and indexed in ChromaDB

# Use the AI Assistant
1. Any employee can go to **AI Assistant**
2. Ask questions like:
   - "How many annual leave days do I have left?"
   - "What tasks are assigned to me?"
   - "What is the maternity leave policy?"
   - "Do I need to submit a timesheet today?"

-

# 👤 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to everything |
| **Manager** | View all tasks/leaves/timesheets, approve/reject |
| **Employee** | Own tasks, timesheets, leaves, AI assistant |

---

# 🔒 Security Features

- ✅ Passwords hashed with **bcrypt** (12 rounds)
- ✅ Session cookies are **HMAC-signed** (can't be tampered)
- ✅ Account **auto-locks** after 5 failed login attempts
- ✅ Email notification on account lock
- ✅ HttpOnly cookies (safe from XSS)
- ✅ Role-based access control on every route

---

# 🗄️ Database Tables

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





