# database.py
# -----------------------------
# File này dùng để tạo:
# - Engine kết nối MySQL
# - Session để thao tác DB
# -----------------------------

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Cho phép ép dùng SQLite khi cần (DB_BACKEND=sqlite). Mặc định dùng MySQL.
DB_BACKEND = os.getenv("DB_BACKEND", "mysql").lower()
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "IE207")

# URL tới MySQL server (không kèm tên database) để có thể tạo database nếu chưa có
SERVER_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}"
MYSQL_URL = f"{SERVER_URL}/{DB_NAME}?charset=utf8mb4"
SQLITE_URL = "sqlite:///./app.db"


def ensure_database_exists():
    """Tạo database nếu nó chưa tồn tại trên MySQL server."""
    tmp_engine = create_engine(SERVER_URL, pool_pre_ping=True)
    try:
        with tmp_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        tmp_engine.dispose()


def build_engine():
    # Tùy chọn thoát hiểm: ép dùng SQLite nếu thực sự cần
    if DB_BACKEND == "sqlite":
        print("[DB] Using SQLite (DB_BACKEND=sqlite)")
        return create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

    try:
        ensure_database_exists()
        engine = create_engine(
            MYSQL_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=30,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[DB] Connected to MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return engine
    except Exception as exc:
        raise RuntimeError(
            "\n[DB] Không kết nối được MySQL.\n"
            f"      URL: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}\n"
            f"      Lỗi gốc: {exc}\n"
            "      Hãy kiểm tra:\n"
            "      1) MySQL server đã được cài và đang chạy chưa.\n"
            "      2) Thông tin DB_USER / DB_PASS / DB_HOST / DB_PORT đã đúng chưa "
            "(đặt qua biến môi trường).\n"
            "      3) Nếu muốn chạy tạm bằng SQLite: đặt DB_BACKEND=sqlite\n"
        ) from exc


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
