import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def _load_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "sqlite:///:memory:"

    raise RuntimeError("DATABASE_URL environment variable is not set. Cannot start database engine.")


def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance ACID with performance in WAL
    cursor.execute("PRAGMA foreign_keys=ON")  # Strict OLTP data integrity
    cursor.close()


SQLALCHEMY_DATABASE_URL = _load_database_url()

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
    event.listens_for(engine, "connect")(set_sqlite_pragma)


def fallback_to_sqlite():
    """Dynamically reconfigures the engine and sessionmaker to use a local SQLite database."""
    global engine, SessionLocal, SQLALCHEMY_DATABASE_URL
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Configuring database fallback to local SQLite: healthcare.db")

    SQLALCHEMY_DATABASE_URL = "sqlite:///healthcare.db"
    c_args = {"check_same_thread": False}
    e_args = {
        "connect_args": c_args,
        "pool_pre_ping": True,
        "pool_recycle": 300
    }
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        **e_args
    )
    from sqlalchemy import event
    event.listens_for(engine, "connect")(set_sqlite_pragma)
    SessionLocal.configure(bind=engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback() # ACID compliance: Rollback dirty OLTP transactions
        raise
    finally:
        db.close()

def get_db():
    with get_db_context() as db:
        yield db
