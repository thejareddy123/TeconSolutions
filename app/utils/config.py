# ============================================================
# utils/config.py
# Central configuration - reads from .env file
# ============================================================

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """
    All app settings in one place.
    Values come from the .env file.
    """
    
    # App
    APP_NAME: str = os.getenv("APP_NAME", "TeconSolutions")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "TeconSolutions_db")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Session
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "session-secret-key")
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", 480))
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # ChromaDB
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./vector_store/chroma_db")
    
    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    
    # Files
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 10))
    
    # Company
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "TeconSolutions")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")


# Create a single instance to use throughout the app
settings = Settings()
