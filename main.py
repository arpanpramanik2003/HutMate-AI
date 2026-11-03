"""
HutMate AI — Main ASGI Entrypoint

Supports:
    uvicorn main:app --reload
    python main.py
"""

import uvicorn
from server import app  # noqa: F401

if __name__ == "__main__":
    print("🍽️  Starting HutMate AI (ReactJS UI + FastAPI Backend) on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

