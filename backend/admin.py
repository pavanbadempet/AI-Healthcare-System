"""
Admin Dashboard Logic
=====================
Endpoints for system administration, analytics, and user management.
"""
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from . import (
    ai_function_registry,
    audit,
    auth,
    backup_readiness,
    data_quality,
    database,
    incident_response,
    model_cards,
    models,
    operational_health,
    privacy_operations,
    retention_policy,
    security_assurance,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
ADMIN_FACILITY_ACCESS_DETAIL = "Admin resource is outside the user's facility"

# --- Dependencies ---

def _safe_user_response(user: models.User) -> Dict:
    return {
        "id": user.id,
        "facility_id": user.facility_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "2024-01-01",
        "gender": user.gender,
        "dob": user.dob,
        "blood_type": user.blood_type,
        "height": user.height,
        "weight": user.weight,
        "plan_tier": user.plan_tier,
    }


def get_current_admin(current_user: models.User = Depends(auth.get_current_user)):
    """Dependency to ensure the authenticated user has the admin role."""
    if not auth.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def _scope_users_to_admin_facility(query, admin: models.User):
    if admin.facility_id is None:
        return query
    return query.filter(models.User.facility_id == admin.facility_id)


def _ensure_admin_can_access_user(admin: models.User, user: models.User) -> None:
    if admin.facility_id is None:
        return
    if user.facility_id != admin.facility_id:
        raise HTTPException(status_code=403, detail=ADMIN_FACILITY_ACCESS_DETAIL)


def _ensure_admin_can_manage_facility(admin: models.User, facility_id: int) -> None:
    if admin.facility_id is None:
        return
    if admin.facility_id != facility_id:
        raise HTTPException(status_code=403, detail=ADMIN_FACILITY_ACCESS_DETAIL)


def _ensure_admin_can_filter_target_user(
    db: Session,
    admin: models.User,
    target_user_id: Optional[int],
) -> None:
    if admin.facility_id is None or target_user_id is None:
        return
    target_user = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target_user is not None:
        _ensure_admin_can_access_user(admin, target_user)


def _scope_audit_logs_to_admin_facility(query, admin: models.User):
    if admin.facility_id is None:
        return query
    return query.filter(models.AuditLog.facility_id == admin.facility_id)

# --- Endpoints ---

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Get high-level system statistics."""
    user_query = _scope_users_to_admin_facility(db.query(models.User), admin)
    user_ids = [user_id for (user_id,) in user_query.with_entities(models.User.id).all()]
    prediction_query = db.query(models.HealthRecord)
    message_query = db.query(models.ChatLog)
    if admin.facility_id is not None:
        prediction_query = prediction_query.filter(models.HealthRecord.user_id.in_(user_ids))
        message_query = message_query.filter(models.ChatLog.user_id.in_(user_ids))

    return {
        "total_users": user_query.count(),
        "total_predictions": prediction_query.count(),
        "total_messages": message_query.count(),
        "server_status": "Online",
        "database_status": "Connected"
    }

@router.get("/audit-logs")
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    target_user_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> list[Dict]:
    """Review PHI-safe audit trail entries."""
    _ensure_admin_can_filter_target_user(db, admin, target_user_id)
    query = _scope_audit_logs_to_admin_facility(db.query(models.AuditLog), admin)
    if action:
        query = query.filter(models.AuditLog.action == action)
    if target_user_id is not None:
        query = query.filter(models.AuditLog.target_user_id == target_user_id)

    entries = (
        query.order_by(models.AuditLog.timestamp.desc(), models.AuditLog.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [audit.audit_log_to_response(entry) for entry in entries]


@router.get("/ai-functions")
def get_ai_function_registry(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return the admin-visible AI function governance inventory."""
    return ai_function_registry.registry_response()


@router.get("/model-cards")
def get_model_cards(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return admin-visible model and dataset evidence cards."""
    return model_cards.registry_response()


@router.get("/data-quality")
def get_data_quality_report(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe aggregate data quality and lineage report."""
    return data_quality.generate_quality_report(db, facility_id=admin.facility_id)


@router.get("/operational-health")
def get_operational_health_report(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe backend operational health report."""
    return operational_health.build_operational_health_report(
        db,
        routes=request.app.routes,
        facility_id=admin.facility_id,
    )


@router.get("/backup-readiness")
def get_backup_readiness_report(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe backup and restore readiness report."""
    return backup_readiness.get_readiness()


@router.get("/incident-readiness")
def get_incident_readiness_report(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe incident response and alert readiness report."""
    return incident_response.get_readiness()


@router.get("/retention-readiness")
def get_retention_readiness_report(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe retention policy readiness report."""
    return retention_policy.get_readiness()


@router.get("/security-assurance")
def get_security_assurance_report(
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a PHI-safe security assurance readiness report."""
    return security_assurance.get_readiness()


@router.get("/privacy/deletion-plan/{patient_id}")
def get_patient_deletion_plan(
    patient_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a non-destructive, PHI-safe deletion propagation plan."""
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    _ensure_admin_can_access_user(admin, patient)
    try:
        plan = privacy_operations.build_patient_deletion_plan(db, patient_id)
    except privacy_operations.PrivacyOperationNotFound:
        raise HTTPException(status_code=404, detail="Patient not found") from None
    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=patient.id,
        facility_id=patient.facility_id,
        action="VIEW_PATIENT_DELETION_PLAN",
        details={
            "resource_type": "privacy_deletion_plan",
            "resource_id": patient.id,
            "db_rows": plan["database"]["total_records"],
            "vector_rows": plan["vector_store"]["record_ids_pending_delete"],
        },
    )
    return plan

@router.get("/users")
def get_recent_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
):
    """List recent users for management."""
    users = (
        _scope_users_to_admin_facility(db.query(models.User), admin)
        .order_by(models.User.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_safe_user_response(user) for user in users]


@router.get("/patients")
def get_admin_patients(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> list[Dict]:
    """List patient accounts only for admin patient registry views."""
    patients = (
        _scope_users_to_admin_facility(db.query(models.User), admin)
        .filter(models.User.role == "patient")
        .order_by(models.User.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_safe_user_response(patient) for patient in patients]


@router.get("/patients/{patient_id}")
def get_admin_patient_profile(
    patient_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Fetch one patient profile for admin patient-detail views."""
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    _ensure_admin_can_access_user(admin, patient)
    return _safe_user_response(patient)

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Update a user's system role."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _ensure_admin_can_access_user(admin, user)

    allowed_roles = {"patient", "doctor", "nurse", "pharmacist", "billing", "admin"}
    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be patient, doctor, nurse, pharmacist, billing, or admin.",
        )
    if user.id == admin.id and role != "admin":
        raise HTTPException(status_code=400, detail="Cannot change your own admin role.")

    previous_role = user.role
    user.role = role
    db.commit()
    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=user.id,
        action="UPDATE_USER_ROLE",
        details={
            "resource_type": "user",
            "resource_id": user.id,
            "previous_role": previous_role,
            "new_role": role,
        },
    )
    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/facility")
def assign_user_facility(
    user_id: int,
    facility_id: int,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    """Assign a user to a hospital or clinic facility boundary."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    facility = db.query(models.HospitalFacility).filter(models.HospitalFacility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    _ensure_admin_can_manage_facility(admin, facility.id)
    _ensure_admin_can_access_user(admin, user)

    previous_facility_id = user.facility_id
    user.facility_id = facility.id
    db.commit()
    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=user.id,
        action="ASSIGN_USER_FACILITY",
        details={
            "resource_type": "user",
            "resource_id": user.id,
            "previous_facility_id": previous_facility_id,
            "new_facility_id": facility.id,
        },
    )
    return {"message": "User facility updated", "user_id": user.id, "facility_id": facility.id}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Permanently delete a user and their data."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _ensure_admin_can_access_user(admin, user)

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")

    deleted_user_id = user.id
    deleted_user_facility_id = user.facility_id
    db.delete(user)
    db.commit()
    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=deleted_user_id,
        facility_id=deleted_user_facility_id,
        action="DELETE_USER",
        details={"resource_type": "user", "resource_id": deleted_user_id},
    )
    return {"message": "User deleted successfully"}
