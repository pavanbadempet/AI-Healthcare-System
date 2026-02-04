from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Allow override via env var for deployment, default to local SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./healthcare.db"

# Fix for Render/Heroku using 'postgres://' instead of 'postgresql://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Configure Pooling only for non-SQLite (e.g. Postgres)
engine_args = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    "pool_recycle": 300
}

if "sqlite" not in SQLALCHEMY_DATABASE_URL:
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 0

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    **engine_args
)

# Enable WAL Mode for Performance (SQLite Only)
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
