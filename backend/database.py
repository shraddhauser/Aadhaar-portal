"""
backend/database.py
Database connection pool using SQLAlchemy.
Supports local SQLite file storage or MySQL via .env configuration.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# -----------------------------------------------------------------
# Connection string — override via environment variables in prod
# -----------------------------------------------------------------
DB_ENGINE   = os.getenv("DB_ENGINE", "sqlite").lower()
DB_URL      = os.getenv("DB_URL", "")
DB_FILE     = os.getenv("DB_FILE", "aadhaar_analytics.db")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "aadhaar_analytics")

if DB_URL:
    DATABASE_URL = DB_URL
elif DB_ENGINE == "sqlite":
    db_path = Path(DB_FILE)
    if not db_path.is_absolute():
        db_path = Path(__file__).resolve().parent.parent / db_path
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

connect_args = {"check_same_thread": False} if DB_ENGINE == "sqlite" else {}
engine_kwargs = {"connect_args": connect_args}
if DB_ENGINE != "sqlite":
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
