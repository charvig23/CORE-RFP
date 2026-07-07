import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def _create_engine(url):
    if url and url.startswith("postgresql"):
        return create_engine(url)
    return create_engine("sqlite:///./fallback.db", connect_args={"check_same_thread": False})

# Try Supabase first
engine = _create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ Connected to Supabase (Postgres)")
except Exception as e:
    print(f"⚠ Supabase failed ({e}), falling back to SQLite")
    engine = _create_engine(None)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()