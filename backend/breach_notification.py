"""HIPAA/GDPR Breach Notification Framework.

Provides incident reporting, tracking, and 72-hour notification countdown
as required by HIPAA §164.408 and GDPR Article 33.
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BreachSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachStatus(str, Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    NOTIFIED = "notified"
    RESOLVED = "resolved"


@dataclass
class BreachReport:
    incident_id: str = field(default_factory=lambda: f"BREACH-{uuid.uuid4().hex[:8].upper()}")
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    affected_records_estimate: int = 0
    severity: BreachSeverity = BreachSeverity.MEDIUM
    status: BreachStatus = BreachStatus.REPORTED
    reporter: str = "system"
    phi_involved: bool = False
    notification_deadline: datetime = field(default=None)
    containment_actions: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.notification_deadline is None:
            self.notification_deadline = self.detected_at + timedelta(hours=72)

    @property
    def hours_until_deadline(self) -> float:
        remaining = self.notification_deadline - datetime.now(timezone.utc)
        return max(0.0, remaining.total_seconds() / 3600)

    @property
    def is_overdue(self) -> bool:
        return datetime.now(timezone.utc) > self.notification_deadline and self.status != BreachStatus.NOTIFIED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "detected_at": self.detected_at.isoformat(),
            "description": self.description,
            "affected_records_estimate": self.affected_records_estimate,
            "severity": self.severity.value,
            "status": self.status.value,
            "reporter": self.reporter,
            "phi_involved": self.phi_involved,
            "notification_deadline": self.notification_deadline.isoformat(),
            "hours_until_deadline": round(self.hours_until_deadline, 1),
            "is_overdue": self.is_overdue,
            "containment_actions": self.containment_actions,
            "notes": self.notes,
        }


class BreachNotificationManager:
    def __init__(self):
        self._incidents: Dict[str, BreachReport] = {}

    def report_breach(
        self,
        description: str,
        reporter: str = "system",
        severity: BreachSeverity = BreachSeverity.MEDIUM,
        affected_records: int = 0,
        phi_involved: bool = False,
    ) -> BreachReport:
        report = BreachReport(
            description=description,
            reporter=reporter,
            severity=severity,
            affected_records_estimate=affected_records,
            phi_involved=phi_involved,
        )
        self._incidents[report.incident_id] = report
        logger.critical(
            "SECURITY BREACH REPORTED: %s | Severity: %s | PHI: %s | Affected: %d | Deadline: %s",
            report.incident_id,
            severity.value,
            phi_involved,
            affected_records,
            report.notification_deadline.isoformat(),
        )
        return report

    def get_incident(self, incident_id: str) -> Optional[BreachReport]:
        return self._incidents.get(incident_id)

    def update_status(self, incident_id: str, status: BreachStatus, note: str = "") -> Optional[BreachReport]:
        report = self._incidents.get(incident_id)
        if report is None:
            return None
        report.status = status
        if note:
            report.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] {note}")
        logger.info("Breach %s status updated to %s", incident_id, status.value)
        return report

    def add_containment_action(self, incident_id: str, action: str) -> Optional[BreachReport]:
        report = self._incidents.get(incident_id)
        if report is None:
            return None
        report.containment_actions.append(action)
        return report

    def list_incidents(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        incidents = [
            report.to_dict()
            for report in self._incidents.values()
            if include_resolved or report.status != BreachStatus.RESOLVED
        ]
        return sorted(incidents, key=lambda x: x["detected_at"], reverse=True)

    def get_overdue_incidents(self) -> List[Dict[str, Any]]:
        return [
            report.to_dict()
            for report in self._incidents.values()
            if report.is_overdue
        ]


# Global singleton
breach_manager = BreachNotificationManager()
