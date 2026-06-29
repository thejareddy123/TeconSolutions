# ============================================================
# routes/ai_assistant.py
# AI Assistant and Knowledge Base Management routes
# ============================================================

import os
import shutil
import uuid
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.session import get_session
from app.models import ai_model, notification_model
from app.rag import document_processor, ai_assistant, vector_store_chromadb
from app.utils.helpers import allowed_document_types, get_file_extension
from app.utils.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "ai_docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# AI Chat Assistant Page
# ============================================================

@router.get("/ai-assistant", response_class=HTMLResponse)
async def ai_page(request: Request):
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=302)

    user_id = session["user_id"]
    # Load previous chat history
    history = ai_model.get_chat_history(user_id)

    return templates.TemplateResponse("ai/assistant.html", {
        "request": request,
        "session": session,
        "chat_history": history,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/api/ai/ask")
async def ask_question(
    request: Request,
    question: str = Form(...)
):
    """
    Main AI endpoint - receives question, returns AI answer.
    
    Steps:
    1. Get employee context (personal data)
    2. Search ChromaDB for relevant documents
    3. Send everything to Gemini
    4. Return answer
    """
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not question.strip():
        return JSONResponse({"error": "Please enter a question"}, status_code=400)

    if not settings.GEMINI_API_KEY:
        return JSONResponse({
            "answer": "AI Assistant is not configured. Please add GEMINI_API_KEY to your .env file.",
            "sources": []
        })

    try:
        # Get AI response (this is where the magic happens!)
        result = ai_assistant.ask_ai_assistant(session["user_id"], question)

        # Save to chat history
        ai_model.save_chat_message(
            session["user_id"],
            question,
            result["answer"],
            result.get("sources", [])
        )

        return JSONResponse({
            "answer": result["answer"],
            "sources": result.get("sources", [])
        })

    except Exception as e:
        print(f"❌ AI error: {e}")
        return JSONResponse({
            "answer": "Sorry, I encountered an error. Please try again.",
            "sources": []
        })


@router.post("/api/ai/clear-history")
async def clear_history(request: Request):
    """Clear chat history for current user"""
    session = get_session(request)
    if not session:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ai_model.clear_chat_history(session["user_id"])
    return JSONResponse({"success": True, "message": "Chat history cleared!"})


# ============================================================
# Admin: Knowledge Base Management
# ============================================================

@router.get("/admin/knowledge-base", response_class=HTMLResponse)
async def knowledge_base_page(request: Request):
    session = get_session(request)
    if not session or session["role"] != "admin":
        return RedirectResponse("/dashboard", status_code=302)

    user_id = session["user_id"]
    documents = ai_model.get_all_documents()
    stats = vector_store_chromadb.get_collection_stats()

    return templates.TemplateResponse("ai/knowledge_base.html", {
        "request": request,
        "session": session,
        "documents": documents,
        "stats": stats,
        "unread_notifications": notification_model.get_unread_count(user_id),
        "unread_messages": notification_model.get_unread_message_count(user_id)
    })


@router.post("/admin/knowledge-base/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    category: str = Form("General"),
    description: str = Form("")
):
    """
    Upload a document to the knowledge base.
    
    Steps:
    1. Save file to disk
    2. Extract text from PDF/DOCX/TXT
    3. Split text into chunks
    4. Add chunks to ChromaDB (with embeddings)
    5. Save record to database
    """
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Only admins can upload documents"}, status_code=403)

    if not file.filename:
        return JSONResponse({"error": "No file selected"}, status_code=400)

    if not allowed_document_types(file.filename):
        return JSONResponse({"error": "Only PDF, DOCX, and TXT files are allowed"}, status_code=400)

    try:
        # Save file with unique name to avoid conflicts
        file_ext = get_file_extension(file.filename)
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Get file size in KB
        file_size_kb = os.path.getsize(file_path) // 1024

        # Save to database first (get doc_id)
        doc_id = ai_model.save_document({
            "file_name": file.filename,
            "file_path": file_path,
            "file_type": file_ext,
            "file_size_kb": file_size_kb,
            "category": category,
            "description": description
        }, session["user_id"])

        # Extract text from document
        text = document_processor.extract_text(file_path, file_ext)

        if not text.strip():
            return JSONResponse({
                "error": "Could not extract text from document. Make sure it's not an image-only PDF."
            }, status_code=400)

        # Split into chunks
        chunks = document_processor.chunk_text(text)

        if not chunks:
            return JSONResponse({"error": "Document appears to be empty"}, status_code=400)

        # Add to ChromaDB
        chunk_count = vector_store_chromadb.add_document_chunks(doc_id, file.filename, chunks)

        # Mark as indexed in database
        ai_model.mark_document_indexed(doc_id, chunk_count)

        return JSONResponse({
            "success": True,
            "message": f"Document uploaded and indexed! Created {chunk_count} searchable chunks.",
            "doc_id": doc_id,
            "chunks": chunk_count
        })

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return JSONResponse({"error": f"Upload failed: {str(e)}"}, status_code=500)


@router.post("/admin/knowledge-base/{doc_id}/delete")
async def delete_document(request: Request, doc_id: int):
    """Delete document from knowledge base and ChromaDB"""
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        # Get document info before deleting
        doc = ai_model.delete_document(doc_id)

        if doc:
            # Remove from ChromaDB
            vector_store_chromadb.delete_document_chunks(doc_id)

            # Delete file from disk
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])

        return JSONResponse({"success": True, "message": "Document deleted from knowledge base!"})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/admin/knowledge-base/{doc_id}/reindex")
async def reindex_document(request: Request, doc_id: int):
    """Re-process and re-index an existing document"""
    session = get_session(request)
    if not session or session["role"] != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        doc = ai_model.get_document_by_id(doc_id)
        if not doc:
            return JSONResponse({"error": "Document not found"}, status_code=404)

        # Remove old chunks
        vector_store_chromadb.delete_document_chunks(doc_id)

        # Re-extract and re-index
        text = document_processor.extract_text(doc["file_path"], doc["file_type"])
        chunks = document_processor.chunk_text(text)
        chunk_count = vector_store_chromadb.add_document_chunks(doc_id, doc["file_name"], chunks)

        ai_model.mark_document_indexed(doc_id, chunk_count)

        return JSONResponse({
            "success": True,
            "message": f"Document re-indexed! {chunk_count} chunks created."
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
