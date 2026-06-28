# ============================================================
# rag/document_processor.py
# Reads and chunks documents for the AI knowledge base
# ============================================================

import os
from pypdf import PdfReader
from docx import Document as DocxDocument


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text from a PDF file.
    Reads each page and joins the text together.
    """
    try:
        reader = PdfReader(file_path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
        
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"❌ Error reading PDF {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract all text from a DOCX (Word) file.
    Reads each paragraph.
    """
    try:
        doc = DocxDocument(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"❌ Error reading DOCX {file_path}: {e}")
        return ""


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a plain text file"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading TXT {file_path}: {e}")
        return ""


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract text based on file type.
    
    Args:
        file_path: Path to the file
        file_type: 'pdf', 'docx', or 'txt'
    
    Returns:
        Extracted text as a string
    """
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    else:
        print(f"❌ Unsupported file type: {file_type}")
        return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Why overlap? So context isn't lost at chunk boundaries.
    
    Args:
        text: Full document text
        chunk_size: Max characters per chunk
        overlap: Characters to repeat between chunks
    
    Returns:
        List of text chunks
    """
    if not text.strip():
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at a sentence/paragraph boundary
        if end < text_length:
            # Look for a good break point (newline, period + space)
            break_chars = ["\n\n", "\n", ". ", "! ", "? "]
            for bc in break_chars:
                last_break = chunk.rfind(bc)
                if last_break > chunk_size // 2:  # At least halfway through
                    chunk = chunk[:last_break + len(bc)]
                    break
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        # Move start forward, subtract overlap so chunks share context
        start += len(chunk) - overlap
    
    return chunks
