"""PHI-safe privacy operation planning.

The helpers in this module do not delete data. They build aggregate deletion
and retention plans so admins can see every backend surface that must be
handled before executing a real patient erasure workflow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from . import models


class PrivacyOperationNotFound(ValueError):
    pass


DATABASE_SURFACES = (
    ("users", models.User, "id"),
    ("health_records", models.HealthRecord, "user_id"),
    ("chat_logs", models.ChatLog, "user_id"),
    ("appointments", models.Appointment, "user_id"),
    ("encounters", models.Encounter, "patient_id"),
    ("admissions", models.Admission, "patient_id"),
    ("clinical_orders", models.ClinicalOrder, "patient_id"),
    ("care_events", models.CareEvent, "patient_id"),
    ("vital_observations", models.VitalObservation, "patient_id"),
    ("monitoring_signals", models.MonitoringSignal, "patient_id"),
    ("diagnostic_results", models.DiagnosticResult, "patient_id"),
    ("prescriptions", models.Prescription, "patient_id"),
    ("dispense_records", models.DispenseRecord, "patient_id"),
    ("invoices", models.Invoice, "patient_id"),
    ("billing_payments", models.BillingPayment, "patient_id"),
    ("discharge_summaries", models.DischargeSummary, "patient_id"),
    ("nursing_tasks", models.NursingTask, "patient_id"),
    ("interoperability_consents", models.InteroperabilityConsent, "patient_id"),
    ("abdm_consent_events", models.ABDMConsentEvent, "patient_id"),
    ("interoperability_exports", models.InteroperabilityExport, "patient_id"),
)

LAKEHOUSE_DATASETS = (
    "patient_accounts",
    "encounters",
    "vital_observations",
    "diagnostic_results",
    "prescriptions",
    "invoices",
    "interoperability_exports",
    "abdm_consent_events",
)


def _count_for_patient(db: Session, model: type, column_name: str, patient_id: int) -> int:
    column = getattr(model, column_name)
    return int(db.query(model).filter(column == patient_id).count())


def _database_surface_counts(db: Session, patient_id: int) -> dict[str, int]:
    return {
        table_name: _count_for_patient(db, model, column_name, patient_id)
        for table_name, model, column_name in DATABASE_SURFACES
    }


def _health_record_ids(db: Session, patient_id: int) -> list[str]:
    return [
        str(record_id)
        for (record_id,) in db.query(models.HealthRecord.id)
        .filter(models.HealthRecord.user_id == patient_id)
        .order_by(models.HealthRecord.id.asc())
        .all()
    ]


def build_patient_deletion_plan(db: Session, patient_id: int) -> dict[str, Any]:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if patient is None:
        raise PrivacyOperationNotFound("Patient not found")

    table_counts = _database_surface_counts(db, patient_id)
    health_record_ids = _health_record_ids(db, patient_id)
    total_records = sum(table_counts.values())
    return {
        "source": "backend.privacy_operations",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "patient_id": patient_id,
        "facility_id": patient.facility_id,
        "destructive_actions_executed": False,
        "database": {
            "tables": table_counts,
            "total_records": total_records,
            "action": "delete_or_anonymize_patient_scoped_rows_after_legal_hold_review",
        },
        "vector_store": {
            "record_ids_pending_delete": len(health_record_ids),
            "delete_function": "backend.rag.delete_record_from_db",
            "record_level_payloads_exposed": False,
        },
        "lakehouse": {
            "propagation_required": True,
            "datasets": list(LAKEHOUSE_DATASETS),
            "action": "propagate_delete_or_tombstone_to_bronze_silver_gold_zones",
            "record_level_payloads_exposed": False,
        },
        "interoperability": {
            "consents_to_revoke": table_counts["interoperability_consents"],
            "export_manifests_to_retain_for_reconciliation": table_counts["interoperability_exports"],
            "bundle_payloads_returned": False,
        },
        "backups": {
            "operator_action_required": True,
            "note": "Apply contract-specific backup retention and legal-hold policy; do not restore deleted patient data outside approved rollback windows.",
        },
        "audit": {
            "retain_phi_safe_audit_events": True,
            "reason": "Security, fraud, and compliance audit trails should remain PHI-minimized and legally reviewed.",
        },
        "privacy_note": "Aggregate deletion plan only; no patient names, contact details, clinical free text, raw values, or vector text are returned.",
    }
