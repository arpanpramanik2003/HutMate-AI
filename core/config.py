import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "HutMate AI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./data/chroma")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/restaurant.db")

# Database URL: Supports SQLite and PostgreSQL (e.g., postgresql+psycopg2://user:pass@localhost:5432/hutmate)
DEFAULT_SQLITE_URL = f"sqlite:///{Path(SQLITE_DB_PATH).resolve().as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

# CORS Origins configuration
raw_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8000,http://127.0.0.1:5173,http://127.0.0.1:8000",
)
CORS_ORIGINS = [orig.strip() for orig in raw_cors.split(",") if orig.strip()]

# Multi-Tenant & RBAC configuration
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "default_hut")
RBAC_ENABLED = os.getenv("RBAC_ENABLED", "true").lower() in ("true", "1", "yes")

# Ensure required local storage directories exist
Path(CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
