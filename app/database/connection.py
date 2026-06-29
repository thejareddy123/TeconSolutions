# ============================================================
# database/connection.py
# Handles MySQL database connection
# ============================================================

import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Database configuration - reads from .env file
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME", "TeconSolutions_db"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Create a connection pool so we don't open/close connections too often
# pool_size=5 means we keep 5 connections ready to use
connection_pool = pooling.MySQLConnectionPool(
    pool_name="TeconSolutions_pool",
    pool_size=5,
    **DB_CONFIG
)


def get_db():
    """
    Get a database connection from the pool.
    Always use this function to get a connection.
    
    Usage:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)  # dictionary=True returns rows as dicts
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        conn.close()  # Returns connection back to pool
    """
    try:
        connection = connection_pool.get_connection()
        return connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e


def test_connection():
    """Test if database connection works - call this on startup"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        print("✅ Database connected successfully!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
