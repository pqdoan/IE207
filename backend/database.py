# database.py
# -----------------------------
# File này dùng để tạo: 
# - Engine kết nối MySQL
# - Session để thao tác DB
# -----------------------------

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_BACKEND = os.getenv("DB_BACKEND", "auto").lower()
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "IE105")

MYSQL_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///./app.db"


def build_engine():
    if DB_BACKEND == "sqlite":
        return create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

    try:
        engine = create_engine(
            MYSQL_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=30,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as exc:
        print(f"[DB] MySQL unavailable, falling back to SQLite: {exc}")
        return create_engine(SQLITE_URL, connect_args={"check_same_thread": False})


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
