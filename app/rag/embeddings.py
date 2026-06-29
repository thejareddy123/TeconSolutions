# ============================================================
# rag/embeddings.py
# Google Gemini Embedding Service
# ============================================================

import google.generativeai as genai  # type: ignore[import]
from app.utils.config import settings

# Configure Gemini once
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiEmbeddingService:
    """
    Handles generating embeddings using Google's embedding model.
    """

    def __init__(self):
        self.model = "models/embedding-001"

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        """
        if not text:
            return []

        try:
            response = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )

            return response["embedding"]

        except Exception as e:
            print(f"❌ Embedding Error: {e}")
            return []

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for search query.
        """

        if not query:
            return []

        try:
            response = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )

            return response["embedding"]

        except Exception as e:
            print(f"❌ Query Embedding Error: {e}")
            return []


# Singleton instance
embedding_service = GeminiEmbeddingService()


def generate_embedding(text: str):
    """
    Convenience wrapper.
    """
    return embedding_service.embed_text(text)


def generate_query_embedding(query: str):
    """
    Convenience wrapper.
    """
    return embedding_service.embed_query(query)