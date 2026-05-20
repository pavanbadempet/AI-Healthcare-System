"""PHI-safe data quality and lineage reporting for healthcare operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models


OPENLINEAGE_NAMESPACE = "ai-healthcare-system"
OPENLINEAGE_PRODUCER = "https://github.com/pavan/AI-Healthcare-System/backend.data_quality"
OPENLINEAGE_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/definitions/RunEvent"


DATASET_LINEAGE: dict[str, dict[str, Any]] = {
    "patient_accounts": {
        "source_tables": ["users"],
        "upstream_modules": ["auth.py", "admin.py"],
        "downstream_uses": ["hospital_operations.py", "prediction.py", "interoperability.py"],
        "freshness_field": "created_at",
    },
    "encounters": {
        "source_tables": ["encounters"],
        "upstream_modules": ["hospital_operations.py"],
        "downstream_uses": ["monitoring.py", "diagnostics.py", "pharmacy.py", "billing.py"],
        "freshness_field": "started_at",
    },
    "vital_observations": {
        "source_tables": ["vital_observations"],
        "upstream_modules": ["monitoring.py"],
        "downstream_uses": ["monitoring.py", "interoperability.py", "data_engineering_platform.py"],
        "freshness_field": "observed_at",
    },
    "diagnostic_results": {
        "source_tables": ["diagnostic_results"],
        "upstream_modules": ["diagnostics.py"],
        "downstream_uses": ["interoperability.py", "report.py", "data_engineering_platform.py"],
        "freshness_field": "created_at",
    },
    "prescriptions": {
        "source_tables": ["prescriptions", "prescription_items"],
        "upstream_modules": ["pharmacy.py"],
        "downstream_uses": ["interoperability.py", "billing.py"],
        "freshness_field": "created_at",
    },
    "invoices": {
        "source_tables": ["invoices", "invoice_line_items", "billing_payments"],
        "upstream_modules": ["billing.py"],
        "downstream_uses": ["interoperability.py", "admin.py"],
        "freshness_field": "issued_at",
    },
    "interoperability_exports": {
        "source_tables": ["interoperability_exports"],
        "upstream_modules": ["interoperability.py", "fhir.py", "abdm.py"],
        "downstream_uses": ["audit.py", "admin.py"],
        "freshness_field": "created_at",
    },
}


def _scope_query(query, model, facility_id: int | None):
    if facility_id is None:
        return query
    facility_column = getattr(model, "facility_id", None)
    if facility_column is None:
        return query
    return query.filter(facility_column == facility_id)


def _count(query) -> int:
    return int(query.count())


def _check(
    *,
    check_id: str,
    dataset: str,
    description: str,
    total_count: int,
    failed_count: int,
    severity: str = "warning",
) -> dict[str, Any]:
    passed_count = max(total_count - failed_count, 0)
    score = 1.0 if total_count == 0 else passed_count / total_count
    return {
        "id": check_id,
        "dataset": dataset,
        "description": description,
        "severity": severity,
        "status": "passed" if failed_count == 0 else "failed",
        "total_count": total_count,
        "failed_count": failed_count,
        "score": round(score, 4),
    }


def _dataset_summary(db: Session, name: str, model, facility_id: int | None, query_filter=None) -> dict[str, Any]:
    query = _scope_query(db.query(model), model, facility_id)
    if query_filter is not None:
        query = query.filter(query_filter)
    lineage = DATASET_LINEAGE[name]
    return {
        "name": name,
        "record_count": _count(query),
        "pii_exposed": False,
        "lineage": {
            "source_tables": list(lineage["source_tables"]),
            "upstream_modules": list(lineage["upstream_modules"]),
            "downstream_uses": list(lineage["downstream_uses"]),
            "freshness_field": lineage["freshness_field"],
        },
    }


def _patient_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.User), models.User, facility_id).filter(models.User.role == "patient")
    total = _count(query)
    missing_dob = _count(query.filter(or_(models.User.dob.is_(None), models.User.dob == "")))
    return [
        _check(
            check_id="patients_birth_date_completeness",
            dataset="patient_accounts",
            description="Patient accounts should have birth date populated for clinical context.",
            total_count=total,
            failed_count=missing_dob,
        )
    ]


def _vital_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.VitalObservation), models.VitalObservation, facility_id)
    spo2_query = query.filter(models.VitalObservation.spo2.is_not(None))
    heart_rate_query = query.filter(models.VitalObservation.heart_rate.is_not(None))
    return [
        _check(
            check_id="vitals_spo2_range",
            dataset="vital_observations",
            description="SpO2 values must be between 0 and 100 percent.",
            total_count=_count(spo2_query),
            failed_count=_count(spo2_query.filter(or_(models.VitalObservation.spo2 < 0, models.VitalObservation.spo2 > 100))),
            severity="critical",
        ),
        _check(
            check_id="vitals_heart_rate_range",
            dataset="vital_observations",
            description="Heart rate values must remain within a clinically plausible numeric range.",
            total_count=_count(heart_rate_query),
            failed_count=_count(
                heart_rate_query.filter(or_(models.VitalObservation.heart_rate < 20, models.VitalObservation.heart_rate > 250))
            ),
            severity="critical",
        ),
    ]


def _diagnostic_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.DiagnosticResult), models.DiagnosticResult, facility_id)
    total = _count(query)
    missing_summary = _count(query.filter(or_(models.DiagnosticResult.summary.is_(None), models.DiagnosticResult.summary == "")))
    return [
        _check(
            check_id="diagnostics_summary_completeness",
            dataset="diagnostic_results",
            description="Diagnostic results should include a non-empty summary for clinician review.",
            total_count=total,
            failed_count=missing_summary,
        )
    ]


def _prescription_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.Prescription), models.Prescription, facility_id)
    total = _count(query)
    missing_items = _count(query.outerjoin(models.PrescriptionItem).filter(models.PrescriptionItem.id.is_(None)))
    return [
        _check(
            check_id="prescriptions_have_items",
            dataset="prescriptions",
            description="Prescriptions should have at least one medication item.",
            total_count=total,
            failed_count=missing_items,
            severity="critical",
        )
    ]


def _invoice_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.Invoice), models.Invoice, facility_id)
    total = _count(query)
    negative_amounts = _count(
        query.filter(or_(
            models.Invoice.subtotal < 0,
            models.Invoice.discount_amount < 0,
            models.Invoice.tax_amount < 0,
            models.Invoice.total_amount < 0,
            models.Invoice.paid_amount < 0,
            models.Invoice.balance_amount < 0,
        ))
    )
    return [
        _check(
            check_id="invoices_amounts_non_negative",
            dataset="invoices",
            description="Invoice monetary fields must not be negative.",
            total_count=total,
            failed_count=negative_amounts,
            severity="critical",
        )
    ]


def _interoperability_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    query = _scope_query(db.query(models.InteroperabilityExport), models.InteroperabilityExport, facility_id)
    total = _count(query)
    missing_manifest = _count(
        query.filter(or_(
            models.InteroperabilityExport.bundle_sha256.is_(None),
            models.InteroperabilityExport.manifest_signature.is_(None),
            models.InteroperabilityExport.resource_count <= 0,
        ))
    )
    return [
        _check(
            check_id="interop_exports_manifest_integrity",
            dataset="interoperability_exports",
            description="Interoperability exports should have resource count, bundle hash, and manifest signature.",
            total_count=total,
            failed_count=missing_manifest,
            severity="critical",
        )
    ]


def _quality_checks(db: Session, facility_id: int | None) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.extend(_patient_checks(db, facility_id))
    checks.extend(_vital_checks(db, facility_id))
    checks.extend(_diagnostic_checks(db, facility_id))
    checks.extend(_prescription_checks(db, facility_id))
    checks.extend(_invoice_checks(db, facility_id))
    checks.extend(_interoperability_checks(db, facility_id))
    return checks


def _overall_score(checks: list[dict[str, Any]]) -> float:
    if not checks:
        return 1.0
    return round(sum(check["score"] for check in checks) / len(checks), 4)


def _checks_by_dataset(checks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for check in checks:
        grouped.setdefault(check["dataset"], []).append(check)
    return grouped


def _lineage_events(
    *,
    datasets: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    generated_at: str,
    facility_id: int | None,
    run_id: str,
) -> list[dict[str, Any]]:
    checks_by_dataset = _checks_by_dataset(checks)
    events = []
    for dataset in datasets:
        dataset_checks = checks_by_dataset.get(dataset["name"], [])
        failed_checks = [
            check["id"] for check in dataset_checks if check["status"] == "failed"
        ]
        events.append({
            "eventType": "COMPLETE",
            "eventTime": generated_at,
            "producer": OPENLINEAGE_PRODUCER,
            "schemaURL": OPENLINEAGE_SCHEMA_URL,
            "run": {
                "runId": run_id,
                "facets": {
                    "dataQualityRun": {
                        "_producer": OPENLINEAGE_PRODUCER,
                        "_schemaURL": "https://ai-healthcare-system.local/openlineage/facets/dataQualityRun",
                        "facilityIdPresent": facility_id is not None,
                    }
                },
            },
            "job": {
                "namespace": OPENLINEAGE_NAMESPACE,
                "name": f"data_quality.{dataset['name']}",
            },
            "inputs": [
                {"namespace": OPENLINEAGE_NAMESPACE, "name": table}
                for table in dataset["lineage"]["source_tables"]
            ],
            "outputs": [
                {
                    "namespace": OPENLINEAGE_NAMESPACE,
                    "name": f"quality.{dataset['name']}",
                    "facets": {
                        "dataQualityMetrics": {
                            "_producer": OPENLINEAGE_PRODUCER,
                            "_schemaURL": "https://ai-healthcare-system.local/openlineage/facets/dataQualityMetrics",
                            "rowCount": dataset["record_count"],
                            "checkCount": len(dataset_checks),
                            "failedChecks": failed_checks,
                        },
                        "privacy": {
                            "_producer": OPENLINEAGE_PRODUCER,
                            "_schemaURL": "https://ai-healthcare-system.local/openlineage/facets/privacy",
                            "piiExposed": False,
                            "recordLevelPayloadsExposed": False,
                        },
                    },
                }
            ],
        })
    return events


def _quarantine_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed_checks = [check for check in checks if check["status"] == "failed"]
    return {
        "enabled": True,
        "record_level_payloads_exposed": False,
        "datasets": [
            {
                "dataset": check["dataset"],
                "check_id": check["id"],
                "severity": check["severity"],
                "failed_count": check["failed_count"],
                "quarantine_table": f"quarantine_{check['dataset']}",
                "pii_exposed": False,
            }
            for check in failed_checks
        ],
    }


def generate_quality_report(db: Session, facility_id: int | None = None) -> dict[str, Any]:
    checks = _quality_checks(db, facility_id)
    generated_at = datetime.now(timezone.utc).isoformat()
    run_id = f"data-quality-{uuid4()}"
    datasets = [
        _dataset_summary(db, "patient_accounts", models.User, facility_id, models.User.role == "patient"),
        _dataset_summary(db, "encounters", models.Encounter, facility_id),
        _dataset_summary(db, "vital_observations", models.VitalObservation, facility_id),
        _dataset_summary(db, "diagnostic_results", models.DiagnosticResult, facility_id),
        _dataset_summary(db, "prescriptions", models.Prescription, facility_id),
        _dataset_summary(db, "invoices", models.Invoice, facility_id),
        _dataset_summary(db, "interoperability_exports", models.InteroperabilityExport, facility_id),
    ]
    return {
        "source": "backend.data_quality",
        "generated_at": generated_at,
        "facility_id": facility_id,
        "overall_score": _overall_score(checks),
        "failed_checks": [check["id"] for check in checks if check["status"] == "failed"],
        "datasets": datasets,
        "checks": checks,
        "lineage_events": _lineage_events(
            datasets=datasets,
            checks=checks,
            generated_at=generated_at,
            facility_id=facility_id,
            run_id=run_id,
        ),
        "quarantine": _quarantine_summary(checks),
        "privacy_note": "Aggregate quality report only; no patient names, contact details, or clinical free text are returned.",
    }
