import sqlite3
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core import config
from database.models import Base, User

# SQLAlchemy 2.0 Engine and Session Setup
# If SQLite, use connect_args to allow multithreaded queries
connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=connect_args, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency generator that provides a transactional SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_connection() -> sqlite3.Connection:
    """
    Return a legacy direct connection to the SQLite database with dictionary row access.
    Preserved for backwards-compatibility.
    """
    Path(config.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all operational tables for inventory, orders, suppliers, recipes, and users."""
    Base.metadata.create_all(bind=engine)

    # Seed default RBAC users if empty
    with SessionLocal() as db:
        if not db.query(User).first():
            default_users = [
                User(username="owner", display_name="Restaurant Owner (Admin)", role="OWNER"),
                User(username="chef", display_name="Master Chef Rajesh", role="HEAD_CHEF"),
                User(username="cook", display_name="Line Cook Amit", role="LINE_COOK"),
            ]
            db.add_all(default_users)
            db.commit()

if __name__ == "__main__":
    init_db()
    print("Database schema and ORM models initialized successfully.")
