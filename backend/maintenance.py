"""SOTA System Maintenance & Data Compliance Engine.

Performs database storage reclamation, index tuning, vector database optimization,
and enforces HIPAA/GDPR data retention purging policies.
"""

import logging
import os
import sqlite3
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.data_retention import retention_manager
from backend.rag import DB_FILE

logger = logging.getLogger(__name__)

def run_system_maintenance(db: Session, executor_id: int = 1) -> Dict[str, Any]:
    """Executes automated system maintenance tasks: storage tuning and data purging."""
    report = {
        "status": "success",
        "database_optimized": False,
        "vector_store_optimized": False,
        "purged_records": {}
    }

    # 1. Optimize SQLite/Postgres primary database
    try:
        bind_url = str(db.get_bind().url)
        if "sqlite" in bind_url:
            db.execute(text("VACUUM"))
            db.execute(text("PRAGMA optimize"))
            report["database_optimized"] = True
            logger.info("Executed SQLite primary database VACUUM & PRAGMA optimize.")
        else:
            # PostgreSQL requires autocommit for VACUUM. We run ANALYZE instead.
            db.execute(text("ANALYZE"))
            report["database_optimized"] = True
            logger.info("Executed PostgreSQL primary database ANALYZE.")
        db.commit()
    except Exception as db_err:
        db.rollback()
        logger.warning("Primary database optimization skipped or failed: %s", db_err)

    # 2. Optimize SQLite-backed Vector Store
    try:
        if os.path.exists(DB_FILE):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("VACUUM")
            conn.close()
            report["vector_store_optimized"] = True
            logger.info("Executed SQLite Vector Store VACUUM.")
    except Exception as vs_err:
        logger.warning("Vector database optimization failed: %s", vs_err)

    # 3. Enforce HIPAA/GDPR Data Retention Policies
    datasets = ["chat_logs", "audit_logs", "medical_records", "billing"]
    for dataset in datasets:
        try:
            expired = retention_manager.evaluate_retention(dataset, db)
            purged = retention_manager.archive_records(dataset, expired, db, executor_id)
            report["purged_records"][dataset] = purged
            if purged > 0:
                logger.info("Purged/Archived %d expired records from %s", purged, dataset)
        except Exception as purge_err:
            logger.error("Failed to prune expired records for %s: %s", dataset, purge_err)
            report["purged_records"][dataset] = 0

    return report
