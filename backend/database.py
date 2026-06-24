import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def _get_sqlite_db_path() -> str:
    """Helper to detect local SQLite database file path based on environment."""
    db_path = "healthcare.db"
    # Detect Hugging Face Space persistent storage (/data)
    if os.path.exists("/data") and os.access("/data", os.W_OK):
        db_path = "/data/healthcare.db"
    elif os.getenv("SPACE_ID") or os.getenv("SPACES_ID"):
        try:
            os.makedirs("/data", exist_ok=True)
            if os.access("/data", os.W_OK):
                db_path = "/data/healthcare.db"
        except Exception:
            pass
    return db_path


def _load_database_url() -> str:
    # 1. TESTING environment variable takes priority, but respect DATABASE_URL override if not running pytest
    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        import sys
        if not (os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules):
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                if database_url.startswith("postgres://"):
                    return database_url.replace("postgres://", "postgresql://", 1)
                if database_url.startswith("libsql://"):
                    return database_url.replace("libsql://", "sqlite+libsql://", 1)
                return database_url
        return "sqlite:///:memory:"

    # 2. Check if Turso replication is configured via env
    if os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
        return f"sqlite+libsql:///{_get_sqlite_db_path()}"

    # 3. Use DATABASE_URL environment variable
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        if database_url.startswith("libsql://"):
            return database_url.replace("libsql://", "sqlite+libsql://", 1)
        return database_url

    raise RuntimeError("DATABASE_URL environment variable is not set. Cannot start database engine.")


def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB page cache
        cursor.execute("PRAGMA temp_store=MEMORY")   # Store temp tables in RAM
        cursor.execute("PRAGMA mmap_size=268435456") # 256MB memory-mapped I/O
    except Exception:
        try:
            cursor.execute("PRAGMA journal_mode=DELETE")
        except Exception:
            pass
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass
    cursor.close()


SQLALCHEMY_DATABASE_URL = _load_database_url()

connect_args = {}
if "libsql" in SQLALCHEMY_DATABASE_URL:
    # Load and verify LibSQL dependencies dynamically to avoid failing on startup
    # when LibSQL is not actually used but package is missing.
    try:
        import libsql_client  # noqa: F401
        import sqlalchemy_libsql  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "libsql-client and sqlalchemy-libsql packages are required to use LibSQL/Turso database. "
            "Please install them via: pip install libsql-client sqlalchemy-libsql"
        ) from e

    sync_url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    if sync_url:
        connect_args["sync_url"] = sync_url
    if auth_token:
        connect_args["auth_token"] = auth_token
elif "sqlite" in SQLALCHEMY_DATABASE_URL:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"connect_timeout": 5}

# Configure Pooling only for non-SQLite (e.g. Postgres)
engine_args = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    "pool_recycle": 60  # Recycle connections after 60s to let serverless Neon scale down to 0 CUs
}

if SQLALCHEMY_DATABASE_URL == "sqlite:///:memory:":
    from sqlalchemy.pool import StaticPool
    engine_args["poolclass"] = StaticPool
elif "sqlite" not in SQLALCHEMY_DATABASE_URL:
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 5   # Allow temporary burst connections under load
    engine_args["pool_timeout"] = 30  # Wait up to 30s for a connection before failing

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

    db_path = "healthcare.db"
    # Detect Hugging Face Space persistent storage (/data)
    if os.path.exists("/data") and os.access("/data", os.W_OK):
        db_path = "/data/healthcare.db"
        logger.info("Hugging Face Space persistent storage detected. Using SQLite: %s", db_path)
    elif os.getenv("SPACE_ID") or os.getenv("SPACES_ID"):
        try:
            os.makedirs("/data", exist_ok=True)
            if os.access("/data", os.W_OK):
                db_path = "/data/healthcare.db"
                logger.info("Using Hugging Face Space persistent SQLite: %s", db_path)
        except Exception as e:
            logger.warning("Failed to initialize /data on Hugging Face: %s. Defaulting to local db.", e)

    logger.warning("Configuring database fallback to SQLite: %s", db_path)

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
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


def fallback_to_memory():
    """Dynamically reconfigures the engine and sessionmaker to use an in-memory SQLite database with a StaticPool."""
    global engine, SessionLocal, SQLALCHEMY_DATABASE_URL
    import logging

    from sqlalchemy.pool import StaticPool
    logger = logging.getLogger(__name__)

    logger.warning("Configuring database fallback to in-memory SQLite (sqlite:///:memory:)")

    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    c_args = {"check_same_thread": False}
    e_args = {
        "connect_args": c_args,
        "poolclass": StaticPool,
    }
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        **e_args
    )
    SessionLocal.configure(bind=engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import Boolean, Column, DateTime


class SoftDeleteMixin(object):
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

Base = declarative_base()

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        try:
            db.rollback() # ACID compliance: Rollback dirty OLTP transactions
        except Exception as rollback_err:
            import logging
            logging.getLogger(__name__).warning("Failed to rollback transaction: %s", rollback_err)
        raise
    finally:
        try:
            db.close()
        except Exception as close_err:
            import logging
            logging.getLogger(__name__).warning("Failed to close database session: %s", close_err)

def get_db():
    with get_db_context() as db:
        yield db
