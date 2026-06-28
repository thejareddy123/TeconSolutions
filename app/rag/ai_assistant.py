# ============================================================
# rag/ai_assistant.py
# The core AI Assistant - combines employee data + RAG + Gemini
# ============================================================

import google.generativeai as genai
from app.utils.config import settings
from app.rag.vector_store import search_similar
from app.models import user_model, task_model, leave_model, timesheet_model, holiday_model
from datetime import datetime


# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def get_employee_context(user_id: int) -> str:
    """
    Build a detailed context string about the employee.
    This gives the AI personalized information to answer with.
    
    Think of this as a "briefing sheet" for the AI before it answers.
    """
    # Get employee profile
    user = user_model.get_user_by_id(user_id)
    if not user:
        return "Employee not found."
    
    full_name = f"{user['first_name']} {user['last_name']}"
    
    # Get leave balances
    leave_balance = leave_model.get_leave_balance(user_id)
    
    # Get pending leaves
    all_leaves = leave_model.get_leaves_for_user(user_id)
    pending_leaves = [l for l in all_leaves if l["status"] == "pending"]
    approved_leaves = [l for l in all_leaves if l["status"] == "approved"]
    
    # Get assigned tasks
    tasks = task_model.get_tasks_for_user(user_id)
    pending_tasks = [t for t in tasks if t["status"] in ["todo", "in_progress"]]
    overdue_tasks = [t for t in tasks 
                     if t["due_date"] and t["due_date"] < datetime.now().date() 
                     and t["status"] not in ["completed", "cancelled"]]
    
    # Get recent timesheets
    today = datetime.now()
    timesheets = timesheet_model.get_timesheets_for_user(
        user_id, month=today.month, year=today.year
    )
    monthly_hours = timesheet_model.get_monthly_hours(user_id, today.month, today.year)
    
    # Get upcoming holidays
    holidays = holiday_model.get_upcoming_holidays(limit=5)
    
    # Build the context string
    context = f"""
=== EMPLOYEE PROFILE ===
Name: {full_name}
Employee ID: {user['employee_id']}
Department: {user.get('department', 'N/A')}
Designation: {user.get('designation', 'N/A')}
Manager: {user.get('manager_name', 'N/A')}
Date of Joining: {user.get('date_of_joining', 'N/A')}
Today's Date: {datetime.now().strftime('%d %B %Y, %A')}

=== LEAVE BALANCE ===
Annual Leave Balance: {leave_balance.get('annual_leave_balance', 0)} days remaining
Sick Leave Balance: {leave_balance.get('sick_leave_balance', 0)} days remaining

=== PENDING LEAVE REQUESTS ===
{f"You have {len(pending_leaves)} pending leave request(s):" if pending_leaves else "No pending leave requests."}
{chr(10).join([f"- {l['leave_type'].capitalize()} leave from {l['start_date']} to {l['end_date']} ({l['total_days']} days)" for l in pending_leaves]) if pending_leaves else ""}

=== RECENT APPROVED LEAVES ===
{f"Recent approved leaves this year:" if approved_leaves else "No approved leaves this year."}
{chr(10).join([f"- {l['leave_type'].capitalize()} from {l['start_date']} to {l['end_date']} ({l['total_days']} days)" for l in approved_leaves[:3]]) if approved_leaves else ""}

=== TASKS ===
Total Assigned Tasks: {len(tasks)}
Pending/In-Progress Tasks: {len(pending_tasks)}
Overdue Tasks: {len(overdue_tasks)}

{f"Pending Tasks:" if pending_tasks else "No pending tasks."}
{chr(10).join([f"- [{t['status'].upper()}] {t['title']} (Due: {t.get('due_date', 'No deadline')}, Priority: {t['priority']})" for t in pending_tasks[:5]]) if pending_tasks else ""}

{f"⚠️ OVERDUE Tasks:" if overdue_tasks else ""}
{chr(10).join([f"- {t['title']} (Was due: {t.get('due_date', 'N/A')})" for t in overdue_tasks]) if overdue_tasks else ""}

=== TIMESHEET (This Month) ===
Days Logged: {monthly_hours.get('total_days', 0)}
Total Hours: {monthly_hours.get('total_hours', 0) or 0}
Approved Hours: {monthly_hours.get('approved_hours', 0) or 0}

=== UPCOMING HOLIDAYS ===
{chr(10).join([f"- {h['name']} on {h['holiday_date']} ({h.get('holiday_type', 'holiday')})" for h in holidays]) if holidays else "No upcoming holidays."}
"""
    
    return context.strip()


def ask_ai_assistant(user_id: int, question: str) -> dict:
    """
    Main function: Ask the AI assistant a question.
    
    Workflow:
    1. Get employee context (personal data)
    2. Search ChromaDB for relevant policy documents
    3. Combine context + documents + question
    4. Send to Gemini AI
    5. Return the answer
    
    Args:
        user_id: ID of the employee asking
        question: The question they're asking
    
    Returns:
        {"answer": str, "sources": list}
    """
    
    # Step 1: Get employee's personal context
    employee_context = get_employee_context(user_id)
    
    # Step 2: Search knowledge base for relevant policies/documents
    relevant_chunks = search_similar(question, n_results=4)
    
    # Format retrieved document chunks
    knowledge_base_text = ""
    sources = []
    
    if relevant_chunks:
        knowledge_base_text = "\n=== RELEVANT COMPANY POLICIES / DOCUMENTS ===\n"
        for chunk in relevant_chunks:
            knowledge_base_text += f"\n[From: {chunk['source']}]\n{chunk['text']}\n"
            if chunk["source"] not in sources:
                sources.append(chunk["source"])
    
    # Step 3: Build the full prompt for Gemini
    prompt = f"""You are an intelligent HR assistant for {settings.COMPANY_NAME}. 
You help employees with questions about their work, leaves, tasks, timesheets, and company policies.

Always be:
- Helpful and professional
- Specific to this employee's actual data (don't make up numbers)
- Clear and concise
- Friendly but professional

{employee_context}

{knowledge_base_text}

=== EMPLOYEE'S QUESTION ===
{question}

=== YOUR ANSWER ===
Please answer based on the employee's actual data and company policies above.
If you don't have enough information to answer accurately, say so clearly.
Do not make up information not present in the context.
"""
    
    # Step 4: Call Gemini API
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(prompt)
        answer = response.text
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        answer = "I'm having trouble connecting to the AI service right now. Please try again later."
    
    return {
        "answer": answer,
        "sources": sources
    }
