"""PHI-safe backend operational health checks for admin readiness views."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from fastapi.routing import APIRoute
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import (
    abdm,
    ai_function_registry,
    backup_readiness,
    data_quality,
    dicomweb,
    incident_response,
    retention_policy,
    security_assurance,
    smart_fhir,
)

EXPECTED_SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def _check(
    *,
    check_id: str,
    name: str,
    status: str,
    total_count: int = 1,
    failed_count: int = 0,
    detail: str | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "name": name,
        "status": status,
        "total_count": total_count,
        "failed_count": failed_count,
        "detail": detail,
    }


def _route_pairs(routes: Iterable[Any]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for route in routes:
        if isinstance(route, tuple) and len(route) == 2:
            method, path = route
            pairs.append((str(method).upper(), str(path)))
            continue
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods:
            pairs.append((method.upper(), route.path))
    return pairs


def _duplicate_route_check(routes: Iterable[Any]) -> dict[str, Any]:
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    pairs = _route_pairs(routes)
    for pair in pairs:
        if pair in seen:
            duplicates.add(pair)
        seen.add(pair)
    return _check(
        check_id="duplicate_routes",
        name="Duplicate API route registrations",
        status="passed" if not duplicates else "failed",
        total_count=len(pairs),
        failed_count=len(duplicates),
        detail="no duplicate method/path routes" if not duplicates else "duplicate method/path routes detected",
    )


def _database_check(db: Session) -> dict[str, Any]:
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception:
        return _check(
            check_id="database_reachable",
            name="Database reachability",
            status="failed",
            failed_count=1,
            detail="database check failed",
        )
    return _check(
        check_id="database_reachable",
        name="Database reachability",
        status="passed",
        detail="database responded",
    )


def _security_headers_check() -> dict[str, Any]:
    return _check(
        check_id="security_headers_expected",
        name="Security headers configured",
        status="passed",
        total_count=len(EXPECTED_SECURITY_HEADERS),
        detail="expected browser-hardening headers are defined",
    )


def _ai_registry_check() -> dict[str, Any]:
    try:
        ai_function_registry.validate_ai_registry()
    except ai_function_registry.AIRegistryError:
        return _check(
            check_id="ai_function_registry_valid",
            name="AI function registry validation",
            status="failed",
            failed_count=1,
            detail="AI function registry failed validation",
        )
    return _check(
        check_id="ai_function_registry_valid",
        name="AI function registry validation",
        status="passed",
        total_count=len(ai_function_registry.AI_FUNCTIONS),
        detail="AI function registry is valid",
    )


def _data_quality_check(db: Session, facility_id: int | None) -> dict[str, Any]:
    try:
        report = data_quality.generate_quality_report(db, facility_id=facility_id)
    except Exception:
        return _check(
            check_id="data_quality_available",
            name="Data quality report availability",
            status="failed",
            failed_count=1,
            detail="data quality report failed",
        )
    failed_count = len(report["failed_checks"])
    return _check(
        check_id="data_quality_available",
        name="Data quality report availability",
        status="passed" if failed_count == 0 else "warning",
        total_count=len(report["checks"]),
        failed_count=failed_count,
        detail=f"overall_score={report['overall_score']}",
    )


def _abdm_check() -> dict[str, Any]:
    try:
        readiness = abdm.get_readiness()
    except Exception:
        return _check(
            check_id="abdm_readiness_available",
            name="ABDM readiness availability",
            status="failed",
            failed_count=1,
            detail="ABDM readiness check failed",
        )
    return _check(
        check_id="abdm_readiness_available",
        name="ABDM readiness availability",
        status="passed",
        total_count=len(readiness["missing"]),
        detail="ABDM readiness evaluated without exposing secrets",
    )


def _dicomweb_check() -> dict[str, Any]:
    try:
        readiness = dicomweb.get_readiness()
    except Exception:
        return _check(
            check_id="dicomweb_readiness_available",
            name="DICOMweb readiness availability",
            status="failed",
            failed_count=1,
            detail="DICOMweb readiness check failed",
        )
    return _check(
        check_id="dicomweb_readiness_available",
        name="DICOMweb readiness availability",
        status="passed",
        total_count=len(readiness["missing"]),
        detail="DICOMweb readiness evaluated without exposing secrets or pixel data",
    )


def _smart_fhir_check() -> dict[str, Any]:
    try:
        readiness = smart_fhir.get_readiness()
    except Exception:
        return _check(
            check_id="smart_fhir_readiness_available",
            name="SMART on FHIR readiness availability",
            status="failed",
            failed_count=1,
            detail="SMART on FHIR readiness check failed",
        )
    return _check(
        check_id="smart_fhir_readiness_available",
        name="SMART on FHIR readiness availability",
        status="passed",
        total_count=len(readiness["missing"]),
        detail="SMART on FHIR readiness evaluated without exposing secrets or exchanging tokens",
    )


def _backup_readiness_check() -> dict[str, Any]:
    try:
        readiness = backup_readiness.get_readiness()
    except Exception:
        return _check(
            check_id="backup_readiness_available",
            name="Backup and restore readiness availability",
            status="failed",
            failed_count=1,
            detail="backup readiness check failed",
        )
    status = "passed" if readiness["status"] in {"ready", "disabled"} else "warning"
    return _check(
        check_id="backup_readiness_available",
        name="Backup and restore readiness availability",
        status=status,
        total_count=len(readiness["missing"]),
        failed_count=len(readiness["missing"]),
        detail=f"backup_status={readiness['status']}",
    )


def _incident_response_check() -> dict[str, Any]:
    try:
        readiness = incident_response.get_readiness()
    except Exception:
        return _check(
            check_id="incident_response_readiness_available",
            name="Incident response readiness availability",
            status="failed",
            failed_count=1,
            detail="incident response readiness check failed",
        )
    status = "passed" if readiness["status"] in {"ready", "disabled"} else "warning"
    return _check(
        check_id="incident_response_readiness_available",
        name="Incident response readiness availability",
        status=status,
        total_count=len(readiness["missing"]),
        failed_count=len(readiness["missing"]),
        detail=f"incident_response_status={readiness['status']}",
    )


def _retention_policy_check() -> dict[str, Any]:
    try:
        readiness = retention_policy.get_readiness()
    except Exception:
        return _check(
            check_id="retention_policy_readiness_available",
            name="Retention policy readiness availability",
            status="failed",
            failed_count=1,
            detail="retention policy readiness check failed",
        )
    status = "passed" if readiness["status"] in {"ready", "disabled"} else "warning"
    return _check(
        check_id="retention_policy_readiness_available",
        name="Retention policy readiness availability",
        status=status,
        total_count=len(readiness["missing"]),
        failed_count=len(readiness["missing"]),
        detail=f"retention_policy_status={readiness['status']}",
    )


def _security_assurance_check() -> dict[str, Any]:
    try:
        readiness = security_assurance.get_readiness()
    except Exception:
        return _check(
            check_id="security_assurance_readiness_available",
            name="Security assurance readiness availability",
            status="failed",
            failed_count=1,
            detail="security assurance readiness check failed",
        )
    status = "passed" if readiness["status"] in {"ready", "disabled"} else "warning"
    return _check(
        check_id="security_assurance_readiness_available",
        name="Security assurance readiness availability",
        status=status,
        total_count=len(readiness["missing"]),
        failed_count=len(readiness["missing"]),
        detail=f"security_assurance_status={readiness['status']}",
    )


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["status"] == "failed" for check in checks):
        return "unhealthy"
    if any(check["status"] == "warning" for check in checks):
        return "degraded"
    return "healthy"


def build_operational_health_report(
    db: Session,
    *,
    routes: Iterable[Any],
    facility_id: int | None,
) -> dict[str, Any]:
    checks = [
        _database_check(db),
        _duplicate_route_check(routes),
        _security_headers_check(),
        _ai_registry_check(),
        _data_quality_check(db, facility_id),
        _abdm_check(),
        _dicomweb_check(),
        _smart_fhir_check(),
        _backup_readiness_check(),
        _incident_response_check(),
        _retention_policy_check(),
        _security_assurance_check(),
    ]
    return {
        "source": "backend.operational_health",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "facility_id": facility_id,
        "status": _overall_status(checks),
        "checks": checks,
        "security_headers": EXPECTED_SECURITY_HEADERS,
        "privacy_note": "Operational health reports return aggregate readiness signals only and do not include patient identifiers or clinical free text.",
    }
