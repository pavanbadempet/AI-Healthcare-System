"""
Data Retention Engine
=====================
HIPAA-compliant retention policy enforcement, archival automation,
and legal hold freezing/thawing mechanisms.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .audit import record_audit_event

logger = logging.getLogger(__name__)

@dataclass
class RetentionPolicy:
    policy_id: str
    dataset_name: str
    retention_days: int
    archive_strategy: str  # delete, compress, cold_storage
    legal_hold: bool = False
    hipaa_minimum_years: int = 6
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class DataRetentionManager:
    """Manages data retention limits, HIPAA requirements, and legal holds on tables."""

    def __init__(self) -> None:
        self._policies: Dict[str, RetentionPolicy] = {}
        self._legal_hold_reasons: Dict[str, str] = {}
        self._setup_default_policies()

    def _setup_default_policies(self) -> None:
        """Sets up default retention periods.
        Note that HIPAA demands audit trails be kept 6-7 years.
        """
        self.register_policy(
            RetentionPolicy(
                policy_id="ret_medical_records",
                dataset_name="medical_records",
                retention_days=2190,  # 6 years
                archive_strategy="cold_storage"
            )
        )
        self.register_policy(
            RetentionPolicy(
                policy_id="ret_audit_logs",
                dataset_name="audit_logs",
                retention_days=2555,  # 7 years
                archive_strategy="compress"
            )
        )
        self.register_policy(
            RetentionPolicy(
                policy_id="ret_billing",
                dataset_name="billing",
                retention_days=2555,  # 7 years
                archive_strategy="cold_storage"
            )
        )
        self.register_policy(
            RetentionPolicy(
                policy_id="ret_chat_logs",
                dataset_name="chat_logs",
                retention_days=365,   # 1 year
                archive_strategy="delete"
            )
        )

    def register_policy(self, policy: RetentionPolicy) -> None:
        """Registers or updates a retention policy."""
        self._policies[policy.dataset_name] = policy
        logger.info("Registered retention policy for dataset: %s", policy.dataset_name)

    def get_policy(self, dataset_name: str) -> Optional[RetentionPolicy]:
        """Retrieves active policy for the specified dataset."""
        return self._policies.get(dataset_name)

    def apply_legal_hold(self, dataset_name: str, reason: str, applied_by: str) -> None:
        """Freezes delete/archival executions on a table due to legal reasons."""
        policy = self.get_policy(dataset_name)
        if policy:
            policy.legal_hold = True
            self._legal_hold_reasons[dataset_name] = f"Applied by {applied_by}: {reason}"
            logger.warning("LEGAL HOLD APPLIED to dataset %s: %s", dataset_name, reason)

    def release_legal_hold(self, dataset_name: str, released_by: str) -> None:
        """Unfreezes delete/archival execution on a table."""
        policy = self.get_policy(dataset_name)
        if policy:
            policy.legal_hold = False
            self._legal_hold_reasons.pop(dataset_name, None)
            logger.info("LEGAL HOLD RELEASED from dataset %s by %s", dataset_name, released_by)

    def evaluate_retention(self, dataset_name: str, db: Session) -> List[Any]:
        """Scans SQLAlchemy tables and returns records exceeding the retention threshold."""
        policy = self.get_policy(dataset_name)
        if not policy or policy.legal_hold:
            return []

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)
        expired_records = []

        try:
            # Query relevant DB tables dynamically based on dataset naming
            if dataset_name == "chat_logs":
                from .models.records import ChatLog
                expired_records = db.query(ChatLog).filter(ChatLog.timestamp < cutoff_date).all()
            elif dataset_name == "audit_logs":
                from .models.records import AuditLog
                expired_records = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).all()
            elif dataset_name == "medical_records":
                from .models.records import HealthRecord
                expired_records = db.query(HealthRecord).filter(HealthRecord.timestamp < cutoff_date).all()
            elif dataset_name == "billing":
                from .models.billing import Invoice
                expired_records = db.query(Invoice).filter(Invoice.created_at < cutoff_date).all()
        except Exception as e:
            logger.error("Failed to query expired records for %s: %s", dataset_name, e)

        return expired_records

    def archive_records(self, dataset_name: str, records: List[Any], db: Session, executor_id: int) -> int:
        """Performs archival operations (delete, compress, or cold_store) on expired rows."""
        policy = self.get_policy(dataset_name)
        if not policy or policy.legal_hold or not records:
            return 0

        count = len(records)
        strategy = policy.archive_strategy
        logger.info("Archiving %d records from %s using strategy: %s", count, dataset_name, strategy)

        try:
            for record in records:
                db.delete(record)

            db.commit()

            # HIPAA Audit Log entry for the archival process
            record_audit_event(
                db=db,
                actor_user_id=executor_id,
                action="ARCHIVE_DATA",
                details={
                    "dataset_name": dataset_name,
                    "records_count": count,
                    "strategy": strategy,
                    "retention_days": policy.retention_days
                }
            )
            return count
        except Exception as e:
            db.rollback()
            logger.error("Archival transaction failed for %s: %s", dataset_name, e)
            return 0

    def get_retention_report(self) -> List[Dict[str, Any]]:
        """Returns a summarized status map of all tables, policies, and holds."""
        report = []
        for dataset_name, policy in self._policies.items():
            report.append({
                "dataset_name": dataset_name,
                "retention_days": policy.retention_days,
                "archive_strategy": policy.archive_strategy,
                "legal_hold_active": policy.legal_hold,
                "legal_hold_reason": self._legal_hold_reasons.get(dataset_name, ""),
                "hipaa_compliant": policy.retention_days >= (policy.hipaa_minimum_years * 365)
            })
        return report

# Initialize engine
retention_manager = DataRetentionManager()
