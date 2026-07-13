"""FHIR R4 scope-guarded endpoints for Patient and Observation resources."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import auth, database, models

router = APIRouter(prefix="/fhir", tags=["FHIR R4"])
security = HTTPBearer(auto_error=False)


def validate_fhir_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(database.get_db),
) -> Dict[str, Any]:
    """Validate token and extract patient context.

    Supports both:
    1. Standard user access tokens (doctor, admin, or patient)
    2. SMART Launch launch_tokens / auth_codes passed as Bearer tokens
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials required",
        )

    token = credentials.credentials

    # 1. Check if token is a SMART launch token
    launch_context = (
        db.query(models.SmartLaunchContext)
        .filter(models.SmartLaunchContext.launch_token == token)
        .first()
    )
    if launch_context:
        if launch_context.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SMART launch token has expired",
            )
        return {
            "patient_id": launch_context.patient_id,
            "scopes": launch_context.scope.split(),
            "smart": True,
        }

    # 2. Check if token is a standard JWT access token
    try:
        current_user = auth.get_current_user(token=token, db=db)
        return {
            "patient_id": current_user.id if current_user.role == "patient" else None,
            "user": current_user,
            "scopes": ["*"],
            "smart": False,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authorization token: {str(exc)}",
        )


def _check_patient_access(
    patient_id: int,
    context: Dict[str, Any],
) -> None:
    """Enforce that the requesting context has permission to access patient_id."""
    if context.get("smart"):
        # SMART context is strictly bound to its launch patient
        if context["patient_id"] != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SMART context token is not authorized for this patient ID",
            )
        # Ensure read scope
        has_read = any(
            s in context["scopes"]
            for s in ("patient/*.read", "patient/Patient.read", "patient/Observation.read", "*")
        )
        if not has_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient SMART scopes for this resource",
            )
    else:
        user = context.get("user")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User context missing",
            )
        # Patients can only read their own file
        if user.role == "patient" and user.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to other patient's record",
            )


@router.get("/Patient/{patient_id}")
def get_fhir_patient(
    patient_id: int,
    context: Dict[str, Any] = Depends(validate_fhir_token),
    db: Session = Depends(database.get_db),
) -> Dict[str, Any]:
    """Retrieve FHIR R4 Patient resource."""
    _check_patient_access(patient_id, context)

    patient = (
        db.query(models.User)
        .filter(models.User.id == patient_id, models.User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found",
        )

    # Build FHIR R4 Patient JSON
    names = [{"use": "official", "text": patient.full_name}]
    parts = patient.full_name.split()
    if len(parts) > 1:
        names[0]["family"] = parts[-1]
        names[0]["given"] = parts[:-1]
    else:
        names[0]["given"] = [patient.full_name]

    return {
        "resourceType": "Patient",
        "id": str(patient.id),
        "active": True,
        "name": names,
        "telecom": [
            {"system": "email", "value": patient.email, "use": "home"}
        ],
        "gender": "unknown",
    }


@router.get("/Observation")
def get_fhir_observations(
    patient: int = Query(..., description="Target patient ID"),
    context: Dict[str, Any] = Depends(validate_fhir_token),
    db: Session = Depends(database.get_db),
) -> List[Dict[str, Any]]:
    """Retrieve FHIR R4 Observation resources (vitals) for a patient."""
    _check_patient_access(patient, context)

    vitals_list = (
        db.query(models.VitalObservation)
        .filter(models.VitalObservation.patient_id == patient)
        .order_by(models.VitalObservation.observed_at.desc())
        .limit(50)
        .all()
    )

    fhir_obs_list = []
    for v in vitals_list:
        observed_time = v.observed_at.isoformat() if v.observed_at else datetime.now().isoformat()

        # 1. Heart Rate
        if v.heart_rate is not None:
            fhir_obs_list.append({
                "resourceType": "Observation",
                "id": f"hr-{v.id}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate",
                        }
                    ],
                    "text": "Heart rate",
                },
                "subject": {"reference": f"Patient/{patient}"},
                "effectiveDateTime": observed_time,
                "valueQuantity": {
                    "value": float(v.heart_rate),
                    "unit": "beats/minute",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min",
                },
            })

        # 2. SpO2
        if v.spo2 is not None:
            fhir_obs_list.append({
                "resourceType": "Observation",
                "id": f"spo2-{v.id}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "2708-6",
                            "display": "Oxygen saturation in Arterial blood",
                        }
                    ],
                    "text": "Oxygen saturation",
                },
                "subject": {"reference": f"Patient/{patient}"},
                "effectiveDateTime": observed_time,
                "valueQuantity": {
                    "value": float(v.spo2),
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%",
                },
            })

        # 3. Blood Pressure
        if v.systolic_bp is not None or v.diastolic_bp is not None:
            components = []
            if v.systolic_bp is not None:
                components.append({
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure",
                            }
                        ]
                    },
                    "valueQuantity": {
                        "value": float(v.systolic_bp),
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]",
                    },
                })
            if v.diastolic_bp is not None:
                components.append({
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure",
                            }
                        ]
                    },
                    "valueQuantity": {
                        "value": float(v.diastolic_bp),
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]",
                    },
                })

            fhir_obs_list.append({
                "resourceType": "Observation",
                "id": f"bp-{v.id}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure panel with all children optional",
                        }
                    ],
                    "text": "Blood pressure",
                },
                "subject": {"reference": f"Patient/{patient}"},
                "effectiveDateTime": observed_time,
                "component": components,
            })

    return fhir_obs_list


@router.get("/AuditEvent", response_model=Dict[str, Any])
def get_fhir_audit_events(
    db: Session = Depends(database.get_db),
    context: Dict[str, Any] = Depends(validate_fhir_token),
) -> Dict[str, Any]:
    """Retrieve system audit logs mapped to FHIR R4 AuditEvent resource bundles."""
    user = context.get("user")
    if context.get("smart") or not user or user.role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access FHIR AuditEvent records"
        )

    logs = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )

    from .fhir import audit_event_resource, build_bundle
    resources = []
    for log in logs:
        try:
            resources.append(audit_event_resource(log))
        except Exception:
            continue

    return build_bundle(resources)

