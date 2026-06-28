# ============================================================
# models/ai_model.py
# Database operations for AI documents and chat history
# ============================================================

from app.database.connection import get_db
import json


def save_document(data: dict, uploaded_by: int) -> int:
    """Save uploaded document record to DB"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_documents (
                file_name, file_path, file_type, file_size_kb,
                category, description, uploaded_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["file_name"],
            data["file_path"],
            data["file_type"],
            data.get("file_size_kb", 0),
            data.get("category", "General"),
            data.get("description", ""),
            uploaded_by
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def mark_document_indexed(doc_id: int, chunk_count: int) -> bool:
    """Mark a document as indexed in ChromaDB"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ai_documents
            SET is_indexed = TRUE, indexed_at = NOW(), chunk_count = %s
            WHERE id = %s
        """, (chunk_count, doc_id))
        conn.commit()
        return True
    finally:
        conn.close()


def get_all_documents() -> list:
    """Get all AI knowledge base documents"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, CONCAT(u.first_name, ' ', u.last_name) as uploaded_by_name
            FROM ai_documents d
            JOIN users u ON d.uploaded_by = u.id
            ORDER BY d.created_at DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_document_by_id(doc_id: int) -> dict | None:
    """Get a single document"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ai_documents WHERE id = %s", (doc_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def delete_document(doc_id: int) -> dict | None:
    """Delete a document and return its info before deleting"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        # Get document info first (to delete file and chroma entries)
        cursor.execute("SELECT * FROM ai_documents WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        
        if doc:
            cursor.execute("DELETE FROM ai_documents WHERE id = %s", (doc_id,))
            conn.commit()
        
        return doc  # Return doc info so caller can clean up files
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def save_chat_message(user_id: int, question: str, answer: str, sources: list = None) -> int:
    """Save a chat exchange to history"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        sources_json = json.dumps(sources) if sources else "[]"
        cursor.execute("""
            INSERT INTO ai_chat_history (user_id, question, answer, sources_used)
            VALUES (%s, %s, %s, %s)
        """, (user_id, question, answer, sources_json))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_chat_history(user_id: int, limit: int = 20) -> list:
    """Get recent chat history for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM ai_chat_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        # Parse JSON sources
        for row in rows:
            try:
                row["sources_used"] = json.loads(row.get("sources_used") or "[]")
            except Exception:
                row["sources_used"] = []
        
        return list(reversed(rows))  # Return in chronological order
    finally:
        conn.close()


def clear_chat_history(user_id: int) -> bool:
    """Clear all chat history for a user"""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_chat_history WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()
