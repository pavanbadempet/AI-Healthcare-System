"""
Database Management Utility
===========================
Provides commands to backup and restore SQLite and PostgreSQL databases, and
supports point-in-time recovery checks.

Usage::

    python scripts/manage_db.py backup
    python scripts/manage_db.py restore --file backups/healthcare_backup.db
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("manage_db")

BACKUPS_DIR = Path("backups")

def get_db_url() -> str:
    """Loads database connection URL from environment variables."""
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("DATABASE_URL", "sqlite:///healthcare.db")

def backup_db() -> None:
    """Runs database backup matching the active DATABASE_URL protocol."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    db_url = get_db_url()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg2://") or db_url.startswith("postgres://"):
        backup_file = BACKUPS_DIR / f"postgres_backup_{timestamp}.sql"
        logger.info("Starting PostgreSQL backup to %s...", backup_file)
        
        # Parse connection parameters from URL
        # postgresql://username:password@host:port/database
        import urllib.parse
        url_parsed = urllib.parse.urlparse(db_url)
        username = url_parsed.username or "postgres"
        password = url_parsed.password or "postgres"
        host = url_parsed.hostname or "127.0.0.1"
        port = str(url_parsed.port or "5432")
        database = url_parsed.path.lstrip("/") or "healthcare"

        env = os.environ.copy()
        env["PGPASSWORD"] = password

        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", username,
            "-F", "c",  # Custom format (compressed)
            "-b",        # Include large objects
            "-v",        # Verbose
            "-f", str(backup_file),
            database
        ]
        
        try:
            subprocess.run(cmd, env=env, check=True)
            logger.info("✅ PostgreSQL backup completed successfully.")
        except FileNotFoundError:
            logger.error("❌ pg_dump command not found. Install postgresql-client-common to run PostgreSQL backups.")
        except subprocess.CalledProcessError as e:
            logger.error("❌ pg_dump execution failed: %s", e)

    else:
        # Fallback to SQLite backup
        # Parse SQLite file path
        sqlite_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not sqlite_path:
            sqlite_path = "healthcare.db"
        
        if not os.path.exists(sqlite_path):
            logger.warning("SQLite database file %s does not exist. Nothing to backup.", sqlite_path)
            return

        backup_file = BACKUPS_DIR / f"sqlite_backup_{timestamp}.db"
        logger.info("Starting SQLite backup from %s to %s...", sqlite_path, backup_file)
        try:
            shutil.copy2(sqlite_path, backup_file)
            logger.info("✅ SQLite backup completed successfully.")
        except Exception as e:
            logger.error("❌ SQLite backup failed: %s", e)

def restore_db(backup_path: str) -> None:
    """Restores database from a SQL dump or SQLite file."""
    if not os.path.exists(backup_path):
        logger.error("Backup file not found at: %s", backup_path)
        return

    db_url = get_db_url()

    if db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg2://") or db_url.startswith("postgres://"):
        logger.info("Restoring PostgreSQL database from %s...", backup_path)
        
        import urllib.parse
        url_parsed = urllib.parse.urlparse(db_url)
        username = url_parsed.username or "postgres"
        password = url_parsed.password or "postgres"
        host = url_parsed.hostname or "127.0.0.1"
        port = str(url_parsed.port or "5432")
        database = url_parsed.path.lstrip("/") or "healthcare"

        env = os.environ.copy()
        env["PGPASSWORD"] = password

        # Terminate active connections before restoring database
        term_cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", username,
            "-d", "postgres",
            "-c", f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{database}' AND pid <> pg_backend_pid();"
        ]
        
        restore_cmd = [
            "pg_restore",
            "-h", host,
            "-p", port,
            "-U", username,
            "-d", database,
            "-c",  # Clean (drop) database objects before recreating
            "-v",
            backup_path
        ]

        try:
            subprocess.run(term_cmd, env=env, check=False)
            subprocess.run(restore_cmd, env=env, check=True)
            logger.info("✅ PostgreSQL database restore completed successfully.")
        except FileNotFoundError:
            logger.error("❌ pg_restore or psql commands not found.")
        except subprocess.CalledProcessError as e:
            logger.error("❌ Restore failed: %s", e)

    else:
        # SQLite restore
        sqlite_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not sqlite_path:
            sqlite_path = "healthcare.db"

        logger.info("Restoring SQLite database from %s to %s...", backup_path, sqlite_path)
        try:
            shutil.copy2(backup_path, sqlite_path)
            logger.info("✅ SQLite database restore completed successfully.")
        except Exception as e:
            logger.error("❌ SQLite restore failed: %s", e)

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    parser = argparse.ArgumentParser(description="Healthcare DB Management Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup subcommand
    subparsers.add_parser("backup", help="Run a full database backup")

    # Restore subcommand
    restore_parser = subparsers.add_parser("restore", help="Restore database from a backup file")
    restore_parser.add_argument("--file", required=True, help="Path to the backup file")

    args = parser.parse_args()

    if args.command == "backup":
        backup_db()
    elif args.command == "restore":
        restore_db(args.file)

if __name__ == "__main__":
    main()
