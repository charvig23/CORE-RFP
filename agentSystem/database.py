from pathlib import Path
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_DB_PATH = Path(os.getenv("TEMP", tempfile.gettempdir())) / "ey_agent_system.db"

# Prefer Supabase/Postgres, but keep a local SQLite fallback for development/offline use.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith(("postgresql://", "postgres://")) and "sslmode=" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{LOCAL_DB_PATH.as_posix()}"


def _create_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


# Try Supabase first. If it is paused or unreachable, fall back to local SQLite.
engine = _create_engine(DATABASE_URL)
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print(
        f"[DB] Connection failed for {DATABASE_URL}: {e}\n"
        f"[DB] Falling back to local SQLite database at {LOCAL_DB_PATH}"
    )
    DATABASE_URL = f"sqlite:///{LOCAL_DB_PATH.as_posix()}"
    engine = _create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
