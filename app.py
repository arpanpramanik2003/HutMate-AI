"""
HutMate AI — Application Entrypoint (ReactJS UI + FastAPI Backend)

Run with:
    python app.py
or:
    uvicorn server:app --reload --port 8000
"""

import uvicorn
from server import app  # noqa: F401

if __name__ == "__main__":
    print("🍽️  Starting HutMate AI (ReactJS UI + FastAPI Backend) on http://localhost:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
