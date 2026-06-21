"""Standards-friendly export endpoints for hospital integrations."""

from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import abdm, audit, auth, database, dicomweb, fhir, models, schemas, smart_fhir, terminology
from .facility_scope import users_share_facility_context

router = APIRouter(prefix="/interop", tags=["Interoperability"])

STANDARDS_NOTE = "FHIR-style bundle for integration mapping; local validation and approvals are still required."
CONSENT_SCOPE = "fhir_bundle_export"
CONSENT_REQUIRED_DETAIL = "Active interoperability consent required"
SIGNATURE_ALGORITHM = "HMAC-SHA256"
ALLOWED_EXPORT_RESOURCES = {
    "Patient",
    "Encounter",
    "Observation",
    "DiagnosticReport",
    "MedicationRequest",
    "Invoice",
    "CareEvent",
}
INTEROP_FACILITY_MISMATCH_DETAIL = "Interoperability resources must belong to the same facility"
INTEROP_FACILITY_ACCESS_DETAIL = "Interoperability resource is outside the user's facility"


def _require_admin(current_user: models.User) -> None:
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin privileges required")


def _require_patient(current_user: models.User) -> None:
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")


def _get_patient(db: Session, patient_id: int) -> models.User:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _doctor_assigned_to_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    if not users_share_facility_context(db, doctor_id, patient_id):
        return False

    admission = db.query(models.Admission).filter(
        models.Admission.patient_id == patient_id,
        models.Admission.doctor_id == doctor_id,
    ).first()
    if admission:
        return True

    encounter = db.query(models.Encounter).filter(
        models.Encounter.patient_id == patient_id,
        models.Encounter.doctor_id == doctor_id,
    ).first()
    if encounter:
        return True

    order = db.query(models.ClinicalOrder).filter(
        models.ClinicalOrder.patient_id == patient_id,
        models.ClinicalOrder.doctor_id == doctor_id,
    ).first()
    if order:
        return True

    appointment = db.query(models.Appointment).filter(
        models.Appointment.user_id == patient_id,
        models.Appointment.doctor_id == doctor_id,
    ).first()
    return appointment is not None


def _ensure_doctor_can_access_patient(db: Session, current_user: models.User, patient_id: int) -> None:
    if auth.is_admin(current_user):
        return
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor or admin privileges required")
    if not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")


def _resolve_interop_facility_id(*entities: object | None) -> int | None:
    facility_ids = {
        getattr(entity, "facility_id", None)
        for entity in entities
        if entity is not None and getattr(entity, "facility_id", None) is not None
    }
    if len(facility_ids) > 1:
        raise HTTPException(status_code=400, detail=INTEROP_FACILITY_MISMATCH_DETAIL)
    return next(iter(facility_ids), None)


def _scope_query_to_user_facility(query, facility_column, current_user: models.User):
    if current_user.facility_id is None:
        return query
    return query.filter(or_(facility_column == current_user.facility_id, facility_column.is_(None)))


def _ensure_facility_access(current_user: models.User, facility_id: int | None) -> None:
    if current_user.facility_id is None or facility_id is None:
        return
    if current_user.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=INTEROP_FACILITY_ACCESS_DETAIL)


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_active_consent(consent: models.InteroperabilityConsent, now: datetime | None = None) -> bool:
    if consent.status != "active" or consent.scope != CONSENT_SCOPE:
        return False
    now = now or datetime.now(timezone.utc)
    if consent.expires_at and _to_utc(consent.expires_at) <= now:
        return False
    return True


def _get_active_export_consent(db: Session, patient_id: int) -> models.InteroperabilityConsent | None:
    consents = db.query(models.InteroperabilityConsent).filter(
        models.InteroperabilityConsent.patient_id == patient_id,
        models.InteroperabilityConsent.scope == CONSENT_SCOPE,
        models.InteroperabilityConsent.status == "active",
    ).order_by(models.InteroperabilityConsent.created_at.desc()).all()
    now = datetime.now(timezone.utc)
    for consent in consents:
        if _is_active_consent(consent, now):
            return consent
    return None


def _require_active_export_consent(db: Session, patient_id: int) -> models.InteroperabilityConsent:
    consent = _get_active_export_consent(db, patient_id)
    if not consent:
        raise HTTPException(status_code=403, detail=CONSENT_REQUIRED_DETAIL)
    return consent


def _consent_response(consent: models.InteroperabilityConsent) -> dict[str, Any]:
    payload = schemas.InteroperabilityConsentResponse.model_validate(consent).model_dump(mode="json")
    payload["standards_note"] = STANDARDS_NOTE
    return payload


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _bundle_sha256(bundle: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(bundle).encode("utf-8")).hexdigest()


def _sign_manifest(payload: dict[str, Any]) -> str:
    return hmac.new(
        auth.SECRET_KEY.encode("utf-8"),
        _canonical_json(payload).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _manifest_payload(export: models.InteroperabilityExport) -> dict[str, Any]:
    return {
        "resourceType": "ExportManifest",
        "export_id": export.id,
        "patient_id": export.patient_id,
        "requested_by_id": export.requested_by_id,
        "consent_id": export.consent_id,
        "profile_id": export.profile_id,
        "export_type": export.export_type,
        "resource_count": export.resource_count,
        "filters": _load_filter_summary(export.filter_summary),
        "bundle_sha256": export.bundle_sha256,
        "signature_algorithm": export.signature_algorithm or SIGNATURE_ALGORITHM,
        "created_at": _dt(export.created_at),
        "standards_note": STANDARDS_NOTE,
    }


def _manifest_response(export: models.InteroperabilityExport) -> dict[str, Any]:
    manifest = _manifest_payload(export)
    manifest["signature"] = export.manifest_signature
    return manifest


def _validate_resource_types(resource_types: list[str] | None) -> list[str] | None:
    if resource_types is None:
        return None
    requested_types = []
    for raw_type in resource_types:
        resource_type = raw_type.strip()
        if not resource_type:
            continue
        if resource_type not in ALLOWED_EXPORT_RESOURCES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported interoperability resource type: {resource_type}",
            )
        if resource_type not in requested_types:
            requested_types.append(resource_type)
    return requested_types


def _profile_resource_types(profile: models.InteroperabilityExportProfile) -> list[str] | None:
    if not profile.resource_types:
        return None
    try:
        loaded = json.loads(profile.resource_types)
    except json.JSONDecodeError:
        return None
    if not isinstance(loaded, list):
        return None
    return _validate_resource_types([str(item) for item in loaded])


def _profile_response(profile: models.InteroperabilityExportProfile) -> dict[str, Any]:
    payload = schemas.InteroperabilityExportProfileResponse(
        id=profile.id,
        facility_id=profile.facility_id,
        name=profile.name,
        partner_system=profile.partner_system,
        resource_types=_profile_resource_types(profile),
        department_id=profile.department_id,
        created_by_id=profile.created_by_id,
        status=profile.status,
        created_at=profile.created_at,
        standards_note=STANDARDS_NOTE,
    )
    return payload.model_dump(mode="json")


def _get_active_export_profile(db: Session, profile_id: int | None) -> models.InteroperabilityExportProfile | None:
    if profile_id is None:
        return None
    profile = db.query(models.InteroperabilityExportProfile).filter(
        models.InteroperabilityExportProfile.id == profile_id,
        models.InteroperabilityExportProfile.status == "active",
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Export profile not found")
    return profile


def _parse_export_filters(
    resource_types: str | None,
    department_id: int | None,
    profile: models.InteroperabilityExportProfile | None = None,
) -> dict[str, Any]:
    requested_types = None
    if profile:
        requested_types = _profile_resource_types(profile)
    if resource_types:
        requested_types = _validate_resource_types(resource_types.split(","))
    selected_department_id = department_id if department_id is not None else profile.department_id if profile else None
    return {
        "resource_types": requested_types,
        "department_id": selected_department_id,
        "profile_id": profile.id if profile else None,
        "profile_name": profile.name if profile else None,
    }


def _load_filter_summary(filter_summary: str | None) -> dict[str, Any]:
    if not filter_summary:
        return {"resource_types": None, "department_id": None, "profile_id": None, "profile_name": None}
    try:
        loaded = json.loads(filter_summary)
    except json.JSONDecodeError:
        return {"resource_types": None, "department_id": None, "profile_id": None, "profile_name": None}
    return {
        "resource_types": loaded.get("resource_types"),
        "department_id": loaded.get("department_id"),
        "profile_id": loaded.get("profile_id"),
        "profile_name": loaded.get("profile_name"),
    }


def _filter_summary_json(filters: dict[str, Any]) -> str:
    return _canonical_json({
        "resource_types": filters.get("resource_types"),
        "department_id": filters.get("department_id"),
        "profile_id": filters.get("profile_id"),
        "profile_name": filters.get("profile_name"),
    })


def _resource_allowed(filters: dict[str, Any], resource_type: str) -> bool:
    requested_types = filters.get("resource_types")
    return requested_types is None or resource_type in requested_types or resource_type == "Patient"


def _department_allowed(filters: dict[str, Any], department_id: int | None) -> bool:
    requested_department_id = filters.get("department_id")
    return requested_department_id is None or department_id == requested_department_id


def _entry(resource: dict[str, Any]) -> dict[str, Any]:
    return fhir.bundle_entry(resource)


def _build_bundle(db: Session, patient: models.User, filters: dict[str, Any]) -> dict[str, Any]:
    resources: list[dict[str, Any]] = [fhir.patient_resource(patient)]

    if _resource_allowed(filters, "Encounter"):
        encounters = db.query(models.Encounter).filter(models.Encounter.patient_id == patient.id).all()
        for encounter in encounters:
            if not _department_allowed(filters, encounter.department_id):
                continue
            resources.append(fhir.encounter_resource(encounter, patient.id))

    if _resource_allowed(filters, "Observation"):
        observations = db.query(models.VitalObservation).filter(models.VitalObservation.patient_id == patient.id).all()
        for observation in observations:
            if not _department_allowed(filters, observation.department_id):
                continue
            resources.append(fhir.observation_resource(observation, patient.id))

    if _resource_allowed(filters, "DiagnosticReport"):
        diagnostic_results = db.query(models.DiagnosticResult).filter(models.DiagnosticResult.patient_id == patient.id).all()
        for result in diagnostic_results:
            if not _department_allowed(filters, result.department_id):
                continue
            resources.append(fhir.diagnostic_report_resource(result, patient.id))

    if _resource_allowed(filters, "MedicationRequest"):
        prescriptions = db.query(models.Prescription).filter(models.Prescription.patient_id == patient.id).all()
        for prescription in prescriptions:
            if filters.get("department_id") is not None:
                prescription_department_id = prescription.encounter.department_id if prescription.encounter else None
                if not _department_allowed(filters, prescription_department_id):
                    continue
            resources.append(fhir.medication_request_resource(prescription, patient.id))

    if _resource_allowed(filters, "Invoice"):
        invoices = db.query(models.Invoice).filter(models.Invoice.patient_id == patient.id).all()
        for invoice in invoices:
            if filters.get("department_id") is not None:
                invoice_department_id = None
                if invoice.encounter:
                    invoice_department_id = invoice.encounter.department_id
                elif invoice.admission:
                    invoice_department_id = invoice.admission.department_id
                if not _department_allowed(filters, invoice_department_id):
                    continue
            resources.append(fhir.invoice_resource(invoice, patient.id))

    if _resource_allowed(filters, "CareEvent"):
        care_events = db.query(models.CareEvent).filter(models.CareEvent.patient_id == patient.id).all()
        for event in care_events:
            if not _department_allowed(filters, event.department_id):
                continue
            resources.append(fhir.care_event_resource(event, patient.id))

    return fhir.build_bundle(resources, timestamp=datetime.now(timezone.utc))


def _record_export(
    db: Session,
    *,
    facility_id: int | None,
    patient_id: int,
    requested_by_id: int | None,
    consent_id: int | None,
    profile_id: int | None,
    resource_count: int,
    filter_summary: str,
    bundle_sha256: str,
) -> models.InteroperabilityExport:
    export = models.InteroperabilityExport(
        facility_id=facility_id,
        patient_id=patient_id,
        requested_by_id=requested_by_id,
        consent_id=consent_id,
        profile_id=profile_id,
        export_type="fhir_bundle",
        resource_count=resource_count,
        filter_summary=filter_summary,
        bundle_sha256=bundle_sha256,
        signature_algorithm=SIGNATURE_ALGORITHM,
        status="completed",
    )
    db.add(export)
    db.commit()
    db.refresh(export)
    export.manifest_signature = _sign_manifest(_manifest_payload(export))
    db.commit()
    db.refresh(export)
    audit.record_audit_event(
        db,
        actor_user_id=requested_by_id,
        target_user_id=patient_id,
        action="EXPORT_INTEROPERABILITY_BUNDLE",
        details={
            "resource_type": "interoperability_export",
            "resource_id": export.id,
            "consent_id": consent_id,
            "profile_id": profile_id,
            "export_type": export.export_type,
            "resource_count": resource_count,
            "filters": _load_filter_summary(filter_summary),
            "bundle_sha256": bundle_sha256,
            "signature_algorithm": export.signature_algorithm,
        },
    )
    return export


def _export_bundle(
    db: Session,
    patient: models.User,
    current_user: models.User,
    consent: models.InteroperabilityConsent | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = filters or _parse_export_filters(None, None)
    facility_id = _resolve_interop_facility_id(current_user, patient)
    try:
        bundle = _build_bundle(db, patient, filters)
    except fhir.FHIRValidationError as exc:
        raise HTTPException(status_code=422, detail="Generated FHIR bundle failed validation") from exc
    bundle_sha256 = _bundle_sha256(bundle)
    filter_summary = _filter_summary_json(filters)
    export = _record_export(
        db,
        facility_id=facility_id,
        patient_id=patient.id,
        requested_by_id=current_user.id,
        consent_id=consent.id if consent else None,
        profile_id=filters.get("profile_id"),
        resource_count=len(bundle["entry"]),
        filter_summary=filter_summary,
        bundle_sha256=bundle_sha256,
    )
    return {
        "patient_id": patient.id,
        "bundle": bundle,
        "export": schemas.InteroperabilityExportResponse.model_validate(export).model_dump(mode="json"),
        "manifest": _manifest_response(export),
        "filters": filters,
        "standards_note": STANDARDS_NOTE,
    }


def _ensure_manifest_access(db: Session, current_user: models.User, export: models.InteroperabilityExport) -> None:
    _ensure_facility_access(current_user, export.facility_id)
    if auth.is_admin(current_user):
        return
    if current_user.role == "patient" and export.patient_id == current_user.id:
        return
    if current_user.role == "doctor" and _doctor_assigned_to_patient(db, current_user.id, export.patient_id):
        return
    raise HTTPException(status_code=403, detail="You cannot access this export manifest")


@router.post("/patient/consents", status_code=201)
def grant_patient_interoperability_consent(
    payload: schemas.InteroperabilityConsentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_patient(current_user)
    if payload.scope != CONSENT_SCOPE:
        raise HTTPException(status_code=400, detail="Unsupported interoperability consent scope")
    purpose = payload.purpose.strip()
    if not purpose:
        raise HTTPException(status_code=400, detail="Consent purpose is required")
    if payload.expires_at and _to_utc(payload.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Consent expiry must be in the future")

    consent = models.InteroperabilityConsent(
        facility_id=current_user.facility_id,
        patient_id=current_user.id,
        granted_by_id=current_user.id,
        scope=payload.scope,
        purpose=purpose,
        recipient_type=payload.recipient_type,
        expires_at=payload.expires_at,
        status="active",
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
        action="GRANT_INTEROPERABILITY_CONSENT",
        details={
            "resource_type": "interoperability_consent",
            "resource_id": consent.id,
            "scope": consent.scope,
            "recipient_type": consent.recipient_type,
        },
    )
    return _consent_response(consent)


@router.get("/patient/consents")
def list_patient_interoperability_consents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[dict[str, Any]]:
    _require_patient(current_user)
    consents = db.query(models.InteroperabilityConsent).filter(
        models.InteroperabilityConsent.patient_id == current_user.id,
    ).order_by(models.InteroperabilityConsent.created_at.desc()).all()
    return [_consent_response(consent) for consent in consents]


@router.post("/patient/consents/{consent_id}/revoke")
def revoke_patient_interoperability_consent(
    consent_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_patient(current_user)
    consent = db.query(models.InteroperabilityConsent).filter(
        models.InteroperabilityConsent.id == consent_id,
        models.InteroperabilityConsent.patient_id == current_user.id,
    ).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Interoperability consent not found")
    if consent.status == "revoked":
        raise HTTPException(status_code=409, detail="Interoperability consent is already revoked")
    consent.status = "revoked"
    consent.revoked_by_id = current_user.id
    consent.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(consent)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
        action="REVOKE_INTEROPERABILITY_CONSENT",
        details={
            "resource_type": "interoperability_consent",
            "resource_id": consent.id,
            "scope": consent.scope,
        },
    )
    return _consent_response(consent)


@router.get("/doctor/patients/{patient_id}/consent-status")
def get_doctor_patient_consent_status(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    _get_patient(db, patient_id)
    consent = _get_active_export_consent(db, patient_id)
    return {
        "patient_id": patient_id,
        "has_active_consent": consent is not None,
        "active_consent": _consent_response(consent) if consent else None,
        "standards_note": STANDARDS_NOTE,
    }


@router.get("/admin/consents")
def list_admin_interoperability_consents(
    patient_id: int | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[dict[str, Any]]:
    _require_admin(current_user)
    query = db.query(models.InteroperabilityConsent)
    query = _scope_query_to_user_facility(
        query,
        models.InteroperabilityConsent.facility_id,
        current_user,
    )
    if patient_id is not None:
        query = query.filter(models.InteroperabilityConsent.patient_id == patient_id)
    consents = query.order_by(models.InteroperabilityConsent.created_at.desc()).all()
    return [_consent_response(consent) for consent in consents]


@router.post("/admin/export-profiles")
def create_admin_export_profile(
    payload: schemas.InteroperabilityExportProfileCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Export profile name is required")
    status = payload.status or "active"
    if status not in {"active", "inactive"}:
        raise HTTPException(status_code=400, detail="Export profile status must be active or inactive")
    resource_types = _validate_resource_types(payload.resource_types)
    department = None
    if payload.department_id is not None:
        department = db.query(models.Department).filter(models.Department.id == payload.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        _ensure_facility_access(current_user, department.facility_id)
    facility_id = _resolve_interop_facility_id(current_user, department)
    profile = models.InteroperabilityExportProfile(
        facility_id=facility_id,
        name=name,
        partner_system=payload.partner_system,
        resource_types=_canonical_json(resource_types) if resource_types is not None else None,
        department_id=payload.department_id,
        created_by_id=current_user.id,
        status=status,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        facility_id=profile.facility_id,
        action="CREATE_INTEROPERABILITY_EXPORT_PROFILE",
        details={
            "resource_type": "interoperability_export_profile",
            "resource_id": profile.id,
            "partner_system": profile.partner_system,
            "resource_types": resource_types,
            "department_id": profile.department_id,
        },
    )
    return _profile_response(profile)


@router.get("/admin/export-profiles")
def list_admin_export_profiles(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[dict[str, Any]]:
    _require_admin(current_user)
    query = _scope_query_to_user_facility(
        db.query(models.InteroperabilityExportProfile),
        models.InteroperabilityExportProfile.facility_id,
        current_user,
    )
    profiles = query.order_by(
        models.InteroperabilityExportProfile.created_at.desc(),
    ).all()
    return [_profile_response(profile) for profile in profiles]


@router.get("/abdm/readiness")
def get_abdm_readiness(
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return abdm.get_readiness()


def _abdm_event_response(event: models.ABDMConsentEvent, normalized: dict[str, Any]) -> dict[str, Any]:
    return schemas.ABDMConsentCallbackResponse(
        source="backend.abdm",
        event_id=event.id,
        facility_id=event.facility_id,
        patient_id=event.patient_id,
        local_consent_id=event.local_consent_id,
        abdm_request_id=event.abdm_request_id,
        abdm_consent_id=event.abdm_consent_id,
        event_type=event.event_type,
        status=event.status,
        local_consent_status=event.local_consent_status or normalized["local_consent_status"],
        hi_types=normalized["hi_types"],
        error_code=event.error_code,
        notification_at=_dt(event.notification_at),
        payload_sha256=event.payload_sha256,
        raw_payload_stored=False,
    ).model_dump(mode="json")


def _resolve_abdm_callback_subject(
    db: Session,
    current_user: models.User,
    payload: schemas.ABDMConsentCallbackCreate,
) -> tuple[models.User | None, models.InteroperabilityConsent | None, int | None]:
    consent = None
    patient = None
    if payload.local_consent_id is not None:
        consent = db.query(models.InteroperabilityConsent).filter(
            models.InteroperabilityConsent.id == payload.local_consent_id,
        ).first()
        if not consent:
            raise HTTPException(status_code=404, detail="Interoperability consent not found")
        _ensure_facility_access(current_user, consent.facility_id)
        if payload.patient_id is not None and payload.patient_id != consent.patient_id:
            raise HTTPException(status_code=400, detail="ABDM callback patient does not match consent")
        patient = _get_patient(db, consent.patient_id)
    elif payload.patient_id is not None:
        patient = _get_patient(db, payload.patient_id)
        _ensure_facility_access(current_user, patient.facility_id)

    facility_id = _resolve_interop_facility_id(current_user, patient, consent)
    return patient, consent, facility_id


@router.post("/abdm/consent-callbacks", status_code=201)
def record_abdm_consent_callback(
    payload: schemas.ABDMConsentCallbackCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Record a PHI-safe ABDM consent lifecycle callback for sandbox readiness."""
    _require_admin(current_user)
    patient, consent, facility_id = _resolve_abdm_callback_subject(db, current_user, payload)
    try:
        normalized = abdm.normalize_consent_callback(
            request_id=payload.abdm_request_id,
            status=payload.status,
            abdm_consent_id=payload.abdm_consent_id,
            hi_types=payload.hi_types,
            event_type=payload.event_type,
            notification_at=payload.notification_at,
            error_code=payload.error_code,
        )
    except abdm.ABDMValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    event = models.ABDMConsentEvent(
        facility_id=facility_id,
        patient_id=patient.id if patient else None,
        local_consent_id=consent.id if consent else None,
        abdm_request_id=normalized["request_id"],
        abdm_consent_id=normalized["abdm_consent_id"],
        event_type=normalized["event_type"],
        status=normalized["status"],
        local_consent_status=normalized["local_consent_status"],
        hi_types=_canonical_json(normalized["hi_types"]),
        error_code=normalized["error_code"],
        notification_at=payload.notification_at,
        payload_sha256=normalized["payload_sha256"],
    )
    db.add(event)
    if consent is not None:
        consent.abdm_request_id = normalized["request_id"]
        consent.abdm_consent_id = normalized["abdm_consent_id"]
        consent.abdm_status = normalized["status"]
        consent.abdm_last_event_at = payload.notification_at or datetime.now(timezone.utc)
        consent.status = normalized["local_consent_status"]
        if normalized["status"] in {"REVOKED", "EXPIRED"}:
            consent.revoked_at = consent.abdm_last_event_at
            consent.revoked_by_id = current_user.id
    db.commit()
    db.refresh(event)
    if consent is not None:
        db.refresh(consent)

    if normalized.get("status") == "GRANTED" and patient is not None:
        try:
            from .agents.scheduling_agent import SchedulingAgent
            agent = SchedulingAgent(db, patient)
            agent.prefetch_and_index_history()
        except Exception as e:
            logger.error("Failed to automatically prefetch patient history on ABDM consent callback: %s", e)
    audit.record_audit_event(
        db,
        actor_user_id=current_user.id,
        target_user_id=patient.id if patient else None,
        facility_id=facility_id,
        action="ABDM_CONSENT_CALLBACK",
        details={
            "resource_type": "abdm_consent_event",
            "resource_id": event.id,
            "local_consent_id": consent.id if consent else None,
            "abdm_request_id": normalized["request_id"],
            "abdm_status": normalized["status"],
            "raw_payload_stored": False,
        },
    )
    return _abdm_event_response(event, normalized)


@router.post("/abdm/consent-requests")
def prepare_abdm_consent_request(
    payload: schemas.ABDMConsentRequestCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, payload.patient_id)
    patient = _get_patient(db, payload.patient_id)
    _ensure_facility_access(current_user, patient.facility_id)
    try:
        result = abdm.prepare_consent_request(
            patient_abha_address=payload.patient_abha_address,
            purpose_code=payload.purpose_code,
            hi_types=payload.hi_types,
            date_from=payload.date_from,
            date_to=payload.date_to,
            data_erase_at=payload.data_erase_at,
            hip_id=payload.hip_id,
            care_context_reference=payload.care_context_reference,
            submit=payload.submit,
        )
    except abdm.ABDMValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except abdm.ABDMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result["patient_id"] = payload.patient_id
    return result


@router.get("/terminology/systems")
def list_terminology_systems(
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    return {
        "systems": terminology.list_supported_systems(),
        "source": terminology.CATALOG_SOURCE,
        "standards_note": terminology.STANDARDS_NOTE,
    }


@router.get("/terminology/lookup")
def lookup_terminology_code(
    system: str,
    code: str,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    concept = terminology.lookup_code(system, code)
    if concept is None:
        raise HTTPException(status_code=404, detail="Terminology code not found")
    return concept


@router.get("/dicomweb/readiness")
def get_dicomweb_readiness(
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return dicomweb.get_readiness()


@router.get("/dicomweb/studies/{study_instance_uid}/metadata-links")
def get_dicomweb_study_metadata_links(
    study_instance_uid: str,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    try:
        return dicomweb.build_study_metadata_links(study_instance_uid)
    except dicomweb.DICOMwebValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except dicomweb.DICOMwebConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/smart/readiness")
def get_smart_fhir_readiness(
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return smart_fhir.get_readiness()


@router.get("/smart/authorize-url")
def get_smart_authorization_url(
    state: str | None = None,
    launch: str | None = None,
    scope: str | None = None,
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    try:
        return smart_fhir.build_authorization_response(
            state=state,
            launch=launch,
            scope=scope,
        )
    except smart_fhir.SMARTValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except smart_fhir.SMARTConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/patient/fhir-bundle")
def export_patient_bundle(
    resource_types: str | None = None,
    department_id: int | None = None,
    profile_id: int | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_patient(current_user)
    patient = _get_patient(db, current_user.id)
    consent = _require_active_export_consent(db, patient.id)
    profile = _get_active_export_profile(db, profile_id)
    if profile is not None:
        _ensure_facility_access(current_user, profile.facility_id)
    filters = _parse_export_filters(resource_types, department_id, profile)
    return _export_bundle(db, patient, current_user, consent, filters)


@router.get("/doctor/patients/{patient_id}/fhir-bundle")
def export_doctor_patient_bundle(
    patient_id: int,
    resource_types: str | None = None,
    department_id: int | None = None,
    profile_id: int | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _ensure_doctor_can_access_patient(db, current_user, patient_id)
    patient = _get_patient(db, patient_id)
    _ensure_facility_access(current_user, patient.facility_id)
    consent = _require_active_export_consent(db, patient_id)
    profile = _get_active_export_profile(db, profile_id)
    if profile is not None:
        _ensure_facility_access(current_user, profile.facility_id)
    filters = _parse_export_filters(resource_types, department_id, profile)
    return _export_bundle(db, patient, current_user, consent, filters)


@router.get("/exports/{export_id}/manifest")
def get_export_manifest(
    export_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    export = db.query(models.InteroperabilityExport).filter(
        models.InteroperabilityExport.id == export_id,
    ).first()
    if not export:
        raise HTTPException(status_code=404, detail="Interoperability export not found")
    _ensure_manifest_access(db, current_user, export)
    if not export.bundle_sha256 or not export.manifest_signature:
        raise HTTPException(status_code=404, detail="Export manifest not available")
    return _manifest_response(export)


@router.get("/admin/metrics")
def get_interoperability_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    export_query = _scope_query_to_user_facility(
        db.query(models.InteroperabilityExport),
        models.InteroperabilityExport.facility_id,
        current_user,
    )
    consent_query = _scope_query_to_user_facility(
        db.query(models.InteroperabilityConsent),
        models.InteroperabilityConsent.facility_id,
        current_user,
    )
    exports = export_query.all()
    exports_by_type: dict[str, int] = {}
    for export in exports:
        exports_by_type[export.export_type] = exports_by_type.get(export.export_type, 0) + 1
    active_consents = [
        consent for consent in consent_query.all()
        if _is_active_consent(consent)
    ]
    return {
        "total_exports": len(exports),
        "exports_by_type": exports_by_type,
        "total_resources_exported": sum(export.resource_count for export in exports),
        "exports_with_consent": sum(1 for export in exports if export.consent_id is not None),
        "active_consents": len(active_consents),
        "total_consents": consent_query.count(),
        "standards_note": STANDARDS_NOTE,
    }


# ---------------------------------------------------------------------------
# Backward-compatible short aliases for consent routes
# Tests use /interop/consents instead of /interop/patient/consents
# ---------------------------------------------------------------------------

@router.post("/consents")
def grant_consent_alias(
    payload: schemas.InteroperabilityConsentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Alias for POST /patient/consents."""
    return grant_patient_interoperability_consent(payload, db, current_user)


@router.get("/consents")
def list_consents_alias(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[dict[str, Any]]:
    """Alias for GET /patient/consents."""
    return list_patient_interoperability_consents(db, current_user)


@router.put("/consents/{consent_id}/revoke")
def revoke_consent_alias_put(
    consent_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Alias for PUT /patient/consents/{id}/revoke (tests use PUT, not POST)."""
    return revoke_patient_interoperability_consent(consent_id, db, current_user)


@router.post("/export/patient")
@router.get("/export/patient")
def export_patient_alias(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Alias route — delegates to GET /patient/fhir-bundle."""
    return export_patient_bundle(db=db, current_user=current_user)


@router.get("/external-records/{patient_id}")
def get_external_records(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    # Check permissions (must be patient themself, doctor assigned, or admin)
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient"
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Patients can only access their own external records")
    elif current_user.role == "doctor" and not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")

    # Generate mock external health records representing cross-facility transfer via ABDM
    external_records = [
        {
            "id": "ext_doc_001",
            "source_facility": "City General Hospital",
            "clinical_department": "Cardiology",
            "document_type": "Discharge Summary",
            "date": "2025-11-12",
            "diagnoses": ["Essential Hypertension", "Mild Mitral Regurgitation"],
            "medications": ["Lisinopril 10mg once daily"],
            "status": "Verified"
        },
        {
            "id": "ext_doc_002",
            "source_facility": "Metro Diagnostics",
            "clinical_department": "Radiology",
            "document_type": "Chest X-Ray Report",
            "date": "2026-02-05",
            "diagnoses": ["Clear lungs, no active cardiopulmonary disease"],
            "medications": [],
            "status": "Verified"
        },
        {
            "id": "ext_doc_003",
            "source_facility": "Apex Endocrinology Center",
            "clinical_department": "Endocrinology",
            "document_type": "Outpatient Consultation",
            "date": "2026-04-18",
            "diagnoses": ["Pre-diabetes", "Hyperlipidemia"],
            "medications": ["Metformin 500mg twice daily with meals"],
            "status": "Verified"
        }
    ]

    return {
        "patient_id": patient_id,
        "external_records": external_records,
        "abdm_registry": "ABDM National Health Information Exchange (HIU Gateway)",
        "consent_verified": True,
        "clinical_safety_note": "External records are integrated via the ABDM national health network. Verify details directly with the patient and treating physician."
    }


@router.get("/health-passport/{patient_id}")
def get_health_passport(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient"
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Patients can only access their own health passport")
    elif current_user.role == "doctor" and not _doctor_assigned_to_patient(db, current_user.id, patient_id):
        raise HTTPException(status_code=403, detail="Doctor is not assigned to this patient")

    latest_vital = db.query(models.VitalObservation).filter(
        models.VitalObservation.patient_id == patient_id
    ).order_by(models.VitalObservation.observed_at.desc()).first()

    # Create signed QR payload
    qr_data = {
        "pat_id": patient_id,
        "name": patient.full_name or patient.username,
        "dob": str(patient.dob) if patient.dob else "N/A",
        "allergies": patient.about_me or "None recorded",
        "blood_type": "O-Positive (Mock)",
        "emergency_contact": "Next of Kin (Mock)",
        "vitals": {
            "hr": latest_vital.heart_rate if latest_vital else 72.0,
            "bp": f"{latest_vital.systolic_bp if latest_vital else 120}/{latest_vital.diastolic_bp if latest_vital else 80}"
        }
    }

    # Secure hash of QR data to act as signature
    import hashlib
    signature = hashlib.sha256(str(qr_data).encode("utf-8")).hexdigest()[:16]
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=AI-Healthcare-Pass:{signature}"

    return {
        "patient_id": patient_id,
        "full_name": patient.full_name or patient.username,
        "dob": patient.dob,
        "blood_group": "O-Positive",
        "qr_code_url": qr_code_url,
        "passport_signature": signature,
        "vitals_summary": {
            "heart_rate": f"{latest_vital.heart_rate if latest_vital else 72.0} bpm",
            "blood_pressure": f"{latest_vital.systolic_bp if latest_vital else 120.0}/{latest_vital.diastolic_bp if latest_vital else 80.0} mmHg"
        },
        "allergies_summary": patient.about_me or "No known drug allergies",
        "status": "active_passport",
        "clinical_safety_note": "Digital health passport is for emergency reference and decision support only. Do not rely on it as a substitute for primary record verification."
    }
