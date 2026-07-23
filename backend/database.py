import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

def get_encryption_key() -> str:
    """Returns a 32-url-safe base64-encoded bytes string for ALE encryption.
    Falls back to a default testing key if not set in environment."""
    key = os.getenv("DB_ENCRYPTION_KEY")
    if not key:
        import warnings
        warnings.warn("DB_ENCRYPTION_KEY not set. Using unsafe default key for development.")
        return "vK1w0r7qYn_2Bq5b-2iL5f3LqYgJ3u1QcQZ1bXoZ0r0="
    return key


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
    # (Removed hardcoded SQLite override for HF Spaces)

    # 1. TESTING environment variable takes priority, but respect DATABASE_URL override if not running pytest
    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        import sys
        if not (os.getenv("PYTEST_CURRENT_TEST") or "pytest" in sys.modules):
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                database_url = database_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
                if database_url.startswith("postgres://"):
                    return database_url.replace("postgres://", "postgresql://", 1)
                if database_url.startswith("libsql://"):
                    return database_url.replace("libsql://", "sqlite+libsql://", 1)
                return database_url
        return "sqlite:///:memory:"

    # 2. Check if Turso replication is configured via env
    if os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
        return f"sqlite+libsql:///{_get_sqlite_db_path()}"

    # 3. Use DATABASE_URL environment variable if set and not requested to use local SQLite
    database_url = os.getenv("DATABASE_URL")
    if database_url and not os.getenv("FORCE_LOCAL_SQLITE"):
        database_url = database_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        if database_url.startswith("libsql://"):
            return database_url.replace("libsql://", "sqlite+libsql://", 1)
        return database_url

    # Default fallback to local SQLite database (Zero-Configuration Sandbox Rule)
    return f"sqlite:///{_get_sqlite_db_path()}"


def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB page cache
        cursor.execute("PRAGMA temp_store=MEMORY")   # Store temp tables in RAM
        cursor.execute("PRAGMA mmap_size=536870912") # 512MB memory-mapped I/O
        cursor.execute("PRAGMA journal_size_limit=67108864") # 64MB WAL truncation limit
        cursor.execute("PRAGMA busy_timeout=5000")   # 5-second lock timeout
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
    connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }

# Configure SOTA Enterprise Pooling for non-SQLite (e.g. Postgres / Neon / CockroachDB)
engine_args = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    "pool_recycle": 60  # Recycle connections after 60s for serverless elasticity
}

if SQLALCHEMY_DATABASE_URL == "sqlite:///:memory:":
    from sqlalchemy.pool import StaticPool
    engine_args["poolclass"] = StaticPool
elif "sqlite" not in SQLALCHEMY_DATABASE_URL:
    is_neon_free_tier = "neon.tech" in SQLALCHEMY_DATABASE_URL
    default_pool = 5 if is_neon_free_tier else 20
    default_overflow = 10 if is_neon_free_tier else 20

    engine_args["pool_size"] = int(os.getenv("DB_POOL_SIZE", str(default_pool)))
    engine_args["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", str(default_overflow)))
    engine_args["pool_timeout"] = 30  # Wait up to 30s before throwing timeout exception


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fallback_to_sqlite():
    """Dynamically reconfigures the engine and sessionmaker to use a local SQLite database."""
    global engine, SessionLocal, SQLALCHEMY_DATABASE_URL
    import logging
    logger = logging.getLogger(__name__)

    db_path = "healthcare.db"
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


# Enable WAL Mode for Performance (SQLite Only)
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    from sqlalchemy import event
    event.listens_for(engine, "connect")(set_sqlite_pragma)
else:
    # Auto-probe connection to enforce Zero-Configuration Sandbox Rule
    try:
        with engine.connect() as conn:
            pass
    except Exception as _e:
        import logging
        logging.getLogger(__name__).warning("Remote database connection failed (%s). Falling back to local SQLite WAL.", _e)
        fallback_to_sqlite()


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


def apply_postgres_rls_policy(db_session, table_name: str, tenant_col: str = "facility_id") -> bool:
    """
    SOTA PostgreSQL Row-Level Security (RLS) Policy Generator.
    Enforces active tenant/facility isolation at the database kernel level.
    """
    if "postgresql" not in SQLALCHEMY_DATABASE_URL:
        return False
    try:
        from sqlalchemy import text
        db_session.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"))
        db_session.execute(text(
            f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} "
            f"FOR ALL USING ({tenant_col} = current_setting('app.current_facility_id', true));"
        ))
        db_session.commit()
        return True
    except Exception:
        db_session.rollback()
        return False


def set_session_tenant_context(db_session, facility_id: str) -> None:
    """Sets PostgreSQL session-level tenant context for RLS evaluation."""
    if "postgresql" in SQLALCHEMY_DATABASE_URL:
        try:
            from sqlalchemy import text
            db_session.execute(text(f"SET LOCAL app.current_facility_id = '{facility_id}';"))
        except Exception:
            pass

