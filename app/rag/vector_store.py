# ============================================================
# rag/vector_store.py
# ChromaDB setup and operations for storing/searching embeddings
# ============================================================

import chromadb
from chromadb.utils import embedding_functions
import os
from app.utils.config import settings


# Collection name in ChromaDB where all document chunks are stored
COLLECTION_NAME = "traitsoftwares_knowledge"


def get_chroma_client():
    """
    Get ChromaDB client (persistent - saves to disk).
    Data is saved in the vector_store/chroma_db folder.
    """
    # Make sure the folder exists
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    
    client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    return client


def get_collection():
    """
    Get or create the ChromaDB collection.
    Uses Google Gemini for embeddings (converting text to vectors).
    """
    client = get_chroma_client()
    
    # Use Google's embedding model
    embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=settings.GEMINI_API_KEY,
        model_name="models/embedding-001"  # Google's embedding model
    )
    
    # Get existing collection or create new one
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "TraitSoftwares HR knowledge base"}
    )
    
    return collection


def add_document_chunks(doc_id: int, file_name: str, chunks: list[str]) -> int:
    """
    Add document chunks to ChromaDB.
    Each chunk gets an ID, the text, and metadata.
    
    Returns: Number of chunks added
    """
    if not chunks:
        return 0
    
    collection = get_collection()
    
    # Prepare data for ChromaDB
    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": str(doc_id), "file_name": file_name, "chunk_index": i} 
                 for i in range(len(chunks))]
    
    # Add to ChromaDB (it will auto-generate embeddings)
    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas
    )
    
    print(f"✅ Added {len(chunks)} chunks for document: {file_name}")
    return len(chunks)


def search_similar(query: str, n_results: int = 5) -> list[dict]:
    """
    Search ChromaDB for text similar to the query.
    
    Args:
        query: The question or search text
        n_results: How many similar chunks to return
    
    Returns:
        List of dicts with 'text' and 'source' keys
    """
    try:
        collection = get_collection()
        
        # Check if collection has any documents
        if collection.count() == 0:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count())
        )
        
        # Format results nicely
        chunks = []
        if results and results["documents"] and results["documents"][0]:
            for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
                chunks.append({
                    "text": text,
                    "source": metadata.get("file_name", "Unknown"),
                    "doc_id": metadata.get("doc_id", "")
                })
        
        return chunks
        
    except Exception as e:
        print(f"❌ ChromaDB search error: {e}")
        return []


def delete_document_chunks(doc_id: int):
    """Remove all chunks for a specific document from ChromaDB"""
    try:
        collection = get_collection()
        
        # Find all chunks for this document
        results = collection.get(
            where={"doc_id": str(doc_id)}
        )
        
        if results["ids"]:
            collection.delete(ids=results["ids"])
            print(f"✅ Deleted {len(results['ids'])} chunks for doc ID: {doc_id}")
    
    except Exception as e:
        print(f"❌ Error deleting chunks for doc {doc_id}: {e}")


def get_collection_stats() -> dict:
    """Get stats about the knowledge base"""
    try:
        collection = get_collection()
        return {
            "total_chunks": collection.count(),
            "collection_name": COLLECTION_NAME
        }
    except Exception as e:
        return {"total_chunks": 0, "error": str(e)}
