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

# Ensure required local storage directories exist
Path(CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

