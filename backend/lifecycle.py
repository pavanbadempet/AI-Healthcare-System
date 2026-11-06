"""Application lifecycle management, database migration runners, and startup diagnostics."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text

from . import database, models, prediction
from .seeding import create_default_admin, seed_hospital_operations_data

logger = logging.getLogger(__name__)

startup_diagnostics: dict = {}


def run_migrations():
    """
    Run Alembic database migrations programmatically on startup.
    Hides exception details to prevent leaking database credentials/info.
    """
    # Programmatic migrations are disabled during testing to allow clean sqlite:memory setup.
    if os.getenv("TESTING"):
        return

    try:
        logger.info("Running database migrations via Alembic...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_path = os.path.join(base_dir, "alembic.ini")

        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "backend", "migrations"))

        inspector = inspect(database.engine)
        table_names = set(inspector.get_table_names())
        application_tables = table_names - {"alembic_version"}
        current_revision = None
        if "alembic_version" in table_names:
            with database.engine.connect() as connection:
                current_revision = connection.scalar(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )

        if application_tables and current_revision is None:
            logger.info("Adopting existing unversioned database at baseline revision.")
            models.Base.metadata.create_all(bind=database.engine)
            command.stamp(alembic_cfg, "0001_baseline")

        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully.")
    except Exception:
        logger.warning("Migration check failed. Ensuring database schema via metadata.create_all...")
        models.Base.metadata.create_all(bind=database.engine)


def _uses_sqlite_database() -> bool:
    return str(database.SQLALCHEMY_DATABASE_URL).startswith("sqlite")


def restore_sqlite_backup() -> bool:
    if not _uses_sqlite_database():
        return False

    from .supabase_backup import restore_database

    return restore_database()


def backup_sqlite_database() -> bool:
    if not _uses_sqlite_database():
        return False

    from .supabase_backup import backup_database

    return backup_database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_diagnostics
    try:
        from .axiom_logger import setup_axiom_logging
        setup_axiom_logging()
    except Exception as e:
        logger.warning("Failed to initialize Axiom logging: %s", e)

    # Restore SQLite database from Supabase Storage backup if configured
    try:
        restore_sqlite_backup()
    except Exception as e:
        logger.warning("Failed to restore database from Supabase: %s", e)

    # Mask any sensitive database passwords in URL for logging/diagnostics
    db_url = str(database.SQLALCHEMY_DATABASE_URL)
    if "@" in db_url:
        # e.g., postgresql://user:password@host/db -> postgresql://user:***@host/db
        parts = db_url.split("@")
        prefix = parts[0].rsplit(":", 1)[0]
        startup_diagnostics["database_url"] = f"{prefix}:***@{parts[1]}"
    else:
        startup_diagnostics["database_url"] = db_url

    startup_diagnostics["engine"] = str(database.engine)

    # Database initialization (runs here instead of module level to avoid
    # side effects during import and to support test isolation)
    try:
        with database.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to primary database successfully.")
        startup_diagnostics["primary_conn"] = "success"
    except Exception as e:
        logger.warning("Primary database connection failed: %s. Falling back to SQLite.", e)
        startup_diagnostics["primary_conn"] = f"failed: {str(e)}"
        database.fallback_to_sqlite()
        restore_sqlite_backup()
        startup_diagnostics["fallback_engine"] = str(database.engine)

    try:
        models.Base.metadata.create_all(bind=database.engine)
        startup_diagnostics["schema_creation"] = "success"
    except Exception as err:
        logger.warning("Primary database schema creation failed: %s. Falling back to local SQLite WAL.", err)
        startup_diagnostics["schema_creation"] = f"failed: {str(err)}"
        database.fallback_to_sqlite()
        restore_sqlite_backup()
        try:
            models.Base.metadata.create_all(bind=database.engine)
            startup_diagnostics["schema_creation_sqlite"] = "success"
        except Exception as err_sqlite:
            logger.warning("File-based SQLite creation failed: %s. Falling back to in-memory SQLite.", err_sqlite)
            database.fallback_to_memory()
            try:
                models.Base.metadata.create_all(bind=database.engine)
                startup_diagnostics["schema_creation_memory"] = "success"
            except Exception as err_mem:
                startup_diagnostics["schema_creation_memory"] = f"failed: {str(err_mem)}"

    # Seeding
    try:
        create_default_admin()
        seed_hospital_operations_data()
        startup_diagnostics["seeding"] = "success"
    except Exception as seed_err:
        logger.warning("Primary database seeding failed: %s. Retrying seed on local fallback database...", seed_err)
        database.fallback_to_sqlite()
        try:
            models.Base.metadata.create_all(bind=database.engine)
            create_default_admin()
            seed_hospital_operations_data()
            startup_diagnostics["seeding"] = "success_fallback"
        except Exception as seed_fallback_err:
            startup_diagnostics["seeding"] = f"failed: {str(seed_fallback_err)}"

    logger.info("Loading AI models...")
    try:
        prediction.initialize_models()
        startup_diagnostics["models_loaded"] = "success"
    except Exception as model_err:
        startup_diagnostics["models_loaded"] = f"failed: {str(model_err)}"

    logger.info("Starting Clinical Event Bus...")
    try:
        from .clinical_intelligence import register_intelligence_event_handlers
        from .event_bus import event_bus
        from .prediction import register_prediction_event_handlers

        await event_bus.start()
        register_intelligence_event_handlers()
        register_prediction_event_handlers()
        startup_diagnostics["event_bus"] = "success"
    except Exception as eb_err:
        startup_diagnostics["event_bus"] = f"failed: {str(eb_err)}"

    logger.info("*" * 60)
    logger.info(" AI Healthcare System LEGAL & MEDICAL DISCLAIMER ACTIVE")
    logger.info(" Provided 'AS IS' for Clinical Decision Support only.")
    logger.info(" Ult Diagnostic Responsibility lies with the Licensed Clinician.")
    logger.info("*" * 60)

    yield
    logger.info("Shutting down...")

    # Stop Clinical Event Bus
    try:
        from .event_bus import event_bus
        await event_bus.stop()
        logger.info("Clinical Event Bus stopped.")
    except Exception as eb_stop_err:
        logger.warning("Failed to stop Event Bus: %s", eb_stop_err)

    # Backup SQLite database to Supabase Storage backup if configured
    try:
        backup_sqlite_database()
    except Exception as e:
        logger.warning("Failed to backup database to Supabase: %s", e)
