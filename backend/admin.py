"""
Admin Dashboard Logic
=====================
Endpoints for system administration, analytics, and user management.
"""
import csv
import io
import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from . import (
    ai_function_registry,
    audit,
    auth,
    backup_readiness,
    breach_notification,
    compliance_check,
    data_quality,
    database,
    incident_response,
    licensing,
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


@router.post("/maintenance", status_code=status.HTTP_200_OK)
def trigger_system_maintenance(
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    """Triggers system database optimization and HIPAA data retention compliance pruning."""
    from backend.maintenance import run_system_maintenance
    report = run_system_maintenance(db, executor_id=current_admin.id)
    return report


@router.post("/agents/billing-audit", status_code=status.HTTP_200_OK)
async def trigger_billing_agent_audit(
    soap_note: str = Query(..., description="The clinical SOAP note to audit"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    """Audits a SOAP note using SOTA Clinical Billing Agent to flag claims denial risk."""
    from backend.agents.billing_agent import ClinicalBillingAgent
    agent = ClinicalBillingAgent(db)
    report = await agent.audit_billing_claim(soap_note)
    return report


@router.post("/agents/maf-billing-audit", status_code=status.HTTP_200_OK)
async def trigger_maf_billing_agent_audit(
    soap_note: str = Query(..., description="The clinical SOAP note to audit"),
    current_admin: models.User = Depends(get_current_admin),
):
    """Audits a SOAP note using Microsoft Agent Framework (MAF) to flag claims denial risk."""
    from backend.maf_orchestrator import run_maf_billing_audit
    report = await run_maf_billing_audit(soap_note)
    return report


@router.post("/agents/maf-handoff-audit", status_code=status.HTTP_200_OK)
async def trigger_maf_handoff_agent_audit(
    soap_note: str = Query(..., description="The clinical SOAP note to audit"),
    current_admin: models.User = Depends(get_current_admin),
):
    """Audits a SOAP note using a multi-agent MAF handoff orchestration (billing & safety compliance)."""
    from backend.maf_orchestrator import run_maf_handoff_audit
    report = await run_maf_handoff_audit(soap_note)
    return report


@router.post("/agents/langgraph-triage", status_code=status.HTTP_200_OK)
async def trigger_langgraph_triage(
    symptoms: str = Query(..., description="The clinical symptoms to triage"),
    patient_id: int = Query(1, description="The patient ID context"),
    current_admin: models.User = Depends(get_current_admin),
):
    """Triages symptoms using a stateful LangGraph workflow (triage, safety, compliance)."""
    from backend.langgraph_orchestrator import run_langgraph_triage
    report = await run_langgraph_triage(symptoms, patient_id)
    return report





@router.post("/agents/discharge-summary", status_code=status.HTTP_200_OK)
async def trigger_discharge_agent_summary(
    patient_id: int = Query(..., description="The patient ID to generate discharge summary for"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    """Generates a transition-of-care summary and discharge instructions using SOTA Discharge Coordinator Agent."""
    from backend.agents.discharge_agent import ClinicalDischargeAgent
    agent = ClinicalDischargeAgent(db)
    report = await agent.generate_discharge_plan(patient_id)
    return report


@router.post("/agents/nursing-handoff", status_code=status.HTTP_200_OK)
async def trigger_nursing_agent_handoff(
    patient_id: int = Query(..., description="The patient ID to generate shift handoff card for"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
):
    """Compiles a shift handoff card and task priority list using SOTA Clinical Nursing Agent."""
    from backend.agents.nursing_agent import ClinicalNursingAgent
    agent = ClinicalNursingAgent(db)
    report = await agent.generate_handoff_card(patient_id)
    return report


@router.post("/agents/security-patch", status_code=status.HTTP_200_OK)
async def trigger_security_patch_agent(
    dependencies: str = Query("FastAPI, jose, passlib, sqlalchemy", description="The list of system dependencies"),
    env_config: str = Query("SECRET_KEY: Set, DEBUG: False, CORS_ORIGIN: *", description="The active environment configuration"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
    _license: None = Depends(licensing.enforce_license_tier("enterprise")),
):
    """Runs a security posture scan and generates recommended and virtual hotpatches using SOTA Patch Agent."""
    from backend.agents.patch_agent import ClinicalPatchAgent
    agent = ClinicalPatchAgent(db)
    report = await agent.audit_and_apply_patches(dependencies, env_config)
    return report


@router.post("/agents/auto-fix", status_code=status.HTTP_200_OK)
async def trigger_auto_fixing_agent(
    error_logs: str = Query("OperationalError: database is locked", description="The active exception/error log signature"),
    health_signals: str = Query("CPU: 92%, Memory: 85%", description="The current host health signals"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
    _license: None = Depends(licensing.enforce_license_tier("enterprise")),
):
    """Executes a diagnostic self-healing session and recovery routine using SOTA Fixing Agent."""
    from backend.agents.fixing_agent import ClinicalFixingAgent
    agent = ClinicalFixingAgent(db)
    report = await agent.diagnose_and_heal(error_logs, health_signals)
    return report


@router.post("/agents/auto-call", status_code=status.HTTP_200_OK)
async def trigger_auto_calling_agent(
    alert_details: str = Query("Alarm: SYS_ALARM_TACHY", description="The active vital alarm details"),
    staff_directory: str = Query("Dr. Sarah Jenkins (+1-555-0199)", description="The on-call medical directory"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
    _license: None = Depends(licensing.enforce_license_tier("enterprise")),
):
    """Triggers an emergency calling and notification broadcast routing session using SOTA Calling Agent."""
    from backend.agents.calling_agent import ClinicalCallingAgent
    agent = ClinicalCallingAgent(db)
    report = await agent.route_emergency_call(alert_details, staff_directory)
    return report


@router.post("/agents/wellness-advisory", status_code=status.HTTP_200_OK)
async def trigger_wellness_agent(
    patient_data: str = Query("Symptom: Mild fatigue", description="The patient-submitted lifestyle and symptoms details"),
    current_admin: models.User = Depends(get_current_admin),
    db: Session = Depends(database.get_db),
    _license: None = Depends(licensing.enforce_license_tier("enterprise")),
):
    """Generates a structured SOTA preventive care and wellness plan using SOTA Wellness Agent."""
    from backend.agents.wellness_agent import ClinicalWellnessAgent
    agent = ClinicalWellnessAgent(db)
    report = await agent.generate_wellness_plan(patient_data)
    return report






def _scope_users_to_admin_facility(query, admin: models.User):
    query = query.filter(models.User.is_deleted == False)
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

@router.get("/analytics/report")
def get_analytics_report(
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Fetch the Gold Layer analyst report."""
    if admin.facility_id is not None:
        raise HTTPException(status_code=403, detail="Global analytics report requires global admin privileges")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_path = os.path.join(base_dir, "data", "gold", "analyst_report.json")

    if not os.path.exists(report_path):
        return {
            "report_generated_at": None,
            "total_records_analyzed": 0,
            "prevalence_rates": {
                "diabetes": 0.0,
                "heart": 0.0,
                "kidney": 0.0,
                "liver": 0.0,
                "lungs": 0.0
            },
            "demographics": {
                "avg_age": 0.0,
                "avg_bmi": 0.0,
                "gender_distribution": {"male_ratio": 50.0, "female_ratio": 50.0}
            },
            "model_performance": {
                "diabetes": 0.0,
                "heart": 0.0,
                "kidney": 0.0,
                "liver": 0.0,
                "lungs": 0.0
            },
            "pipeline_execution": {
                "duration_seconds": 0.0,
                "status": "not_run"
            }
        }

    try:
        with open(report_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Gold analyst report: {str(e)}"
        )


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Get high-level system statistics."""
    facility_id = admin.facility_id or "global"
    cache_key = f"dashboard_statistics:{facility_id}"

    from backend.cache_service import cache
    try:
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return cached_stats
    except Exception as exc:
        logger.debug("Cache fetch exception in get_dashboard_stats: %s", exc)

    user_query = _scope_users_to_admin_facility(db.query(models.User), admin)
    user_ids = [user_id for (user_id,) in user_query.with_entities(models.User.id).all()]
    prediction_query = db.query(models.HealthRecord)
    message_query = db.query(models.ChatLog)
    if admin.facility_id is not None:
        prediction_query = prediction_query.filter(models.HealthRecord.user_id.in_(user_ids))
        message_query = message_query.filter(models.ChatLog.user_id.in_(user_ids))

    stats = {
        "total_users": user_query.count(),
        "total_predictions": prediction_query.count(),
        "total_messages": message_query.count(),
        "server_status": "Online",
        "database_status": "Connected",
        "database_type": "sqlite" if "sqlite" in database.SQLALCHEMY_DATABASE_URL else "postgresql"
    }

    try:
        cache.set(cache_key, stats, ttl=3600)
    except Exception as exc:
        logger.debug("Cache store exception in get_dashboard_stats: %s", exc)

    return stats

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


@router.get("/audit-logs/export")
def export_audit_logs_csv(
    action: Optional[str] = None,
    target_user_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Response:
    """Export facility audit log entries in PHI-safe CSV format."""
    _ensure_admin_can_filter_target_user(db, admin, target_user_id)
    query = _scope_audit_logs_to_admin_facility(db.query(models.AuditLog), admin)
    if action:
        query = query.filter(models.AuditLog.action == action)
    if target_user_id is not None:
        query = query.filter(models.AuditLog.target_user_id == target_user_id)

    entries = (
        query.order_by(models.AuditLog.timestamp.desc(), models.AuditLog.id.desc())
        .limit(1000)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Actor User ID", "Target User ID", "Facility ID", "Action", "IP Address", "Details"])

    for entry in entries:
        resp = audit.audit_log_to_response(entry)
        writer.writerow([
            resp.get("id"),
            resp.get("timestamp"),
            resp.get("actor_user_id"),
            resp.get("target_user_id"),
            resp.get("facility_id"),
            resp.get("action"),
            resp.get("ip_address"),
            json.dumps(resp.get("details", {})),
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs_export.csv"},
    )


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


@router.get("/attribution-drift")
def get_attribution_drift_report(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Return a model feature attribution drift analysis report compared to baseline profiles."""
    if admin.facility_id is not None:
        raise HTTPException(status_code=403, detail="Global drift report requires global admin privileges")

    import numpy as np

    from .models import DbFeatureAttributionLog

    # Define baseline feature importance dictionaries (e.g. key: baseline_shap_weight)
    # These represent the baseline training SHAP profiles for our models.
    baselines = {
        "kidney": {
            "age": 0.05, "bp": 0.08, "sg": 0.15, "al": 0.20, "su": 0.02,
            "rbc": 0.05, "pc": 0.05, "pcc": 0.02, "ba": 0.01, "bgr": 0.08,
            "bu": 0.06, "sc": 0.22, "sod": 0.04, "pot": 0.03, "hemo": 0.12,
            "pcv": 0.08, "wc": 0.04, "rc": 0.05, "htn": 0.10, "dm": 0.08,
            "cad": 0.02, "appet": 0.03, "pe": 0.02, "ane": 0.01
        },
        "lungs": {
            "age": 0.08, "gender": 0.02, "smoker": 0.25, "yellow_fingers": 0.05,
            "anxiety": 0.04, "peer_pressure": 0.03, "chronic_disease": 0.12,
            "fatigue": 0.08, "allergy": 0.15, "wheezing": 0.18,
            "alcohol_consuming": 0.05, "coughing": 0.22, "shortness_of_breath": 0.20,
            "swallowing_difficulty": 0.10, "chest_pain": 0.18
        },
        "diabetes": {
            "pregnancies": 0.05, "glucose": 0.35, "bloodpressure": 0.08,
            "skinthickness": 0.03, "insulin": 0.10, "bmi": 0.22,
            "diabetespedigreefunction": 0.15, "age": 0.12
        },
        "heart": {
            "age": 0.10, "sex": 0.05, "cp": 0.22, "trestbps": 0.08, "chol": 0.08,
            "fbs": 0.02, "restecg": 0.03, "thalach": 0.18, "exang": 0.12,
            "oldpeak": 0.15, "slope": 0.08, "ca": 0.18, "thal": 0.20
        },
        "liver": {
            "age": 0.08, "gender": 0.02, "total_bilirubin": 0.18, "direct_bilirubin": 0.12,
            "alkaline_phosphotase": 0.10, "alamine_aminotransferase": 0.22,
            "aspartate_aminotransferase": 0.20, "total_proteins": 0.05,
            "albumin": 0.08, "albumin_and_globulin_ratio": 0.10
        }
    }

    report = {}

    for model_name, baseline_dict in baselines.items():
        # Query logs for this model
        logs = db.query(DbFeatureAttributionLog).filter(
            DbFeatureAttributionLog.model_name == model_name
        ).order_by(DbFeatureAttributionLog.timestamp.desc()).limit(100).all()

        if not logs:
            report[model_name] = {
                "status": "Insufficient Data",
                "drift_score": 0.0,
                "message": "No production predictions logged yet for this model.",
                "features_logged": 0
            }
            continue

        # Compute mean absolute attribution for each feature in logged production data
        prod_attributions = {}
        for feature in baseline_dict.keys():
            vals = []
            for log in logs:
                attr_dict = log.attributions or {}
                val = attr_dict.get(feature)
                if val is not None:
                    vals.append(abs(float(val)))

            if vals:
                prod_attributions[feature] = float(np.mean(vals))
            else:
                prod_attributions[feature] = 0.0

        # Convert to vectors for similarity calculation
        features = list(baseline_dict.keys())
        base_vec = np.array([baseline_dict[f] for f in features])
        prod_vec = np.array([prod_attributions[f] for f in features])

        # Normalize baseline to represent relative importances
        sum_base = np.sum(base_vec)
        if sum_base > 0:
            base_vec = base_vec / sum_base

        # Normalize production relative importances
        sum_prod = np.sum(prod_vec)
        if sum_prod > 0:
            prod_vec = prod_vec / sum_prod

        # Compute cosine similarity
        norm_b = np.linalg.norm(base_vec)
        norm_p = np.linalg.norm(prod_vec)

        if norm_b > 0 and norm_p > 0:
            cosine_sim = np.dot(base_vec, prod_vec) / (norm_b * norm_p)
            drift_score = float(np.round(1.0 - cosine_sim, 4))
        else:
            drift_score = 1.0

        # Determine status
        if drift_score < 0.15:
            status = "Low Drift"
        elif drift_score < 0.25:
            status = "Moderate Drift Warning"
        else:
            status = "High Drift Alert"

        report[model_name] = {
            "status": status,
            "drift_score": drift_score,
            "sample_count": len(logs),
            "production_relative_attributions": {f: float(np.round(prod_attributions[f], 4)) for f in features},
            "baseline_relative_attributions": {f: float(np.round(baseline_dict[f], 4)) for f in features}
        }

    return {
        "status": "success",
        "models": report
    }


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


@router.post("/privacy/execute-deletion/{patient_id}")
def execute_patient_deletion(
    patient_id: int,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Execute patient deletion propagation in reverse dependency order."""
    patient = db.query(models.User).filter(
        models.User.id == patient_id,
        models.User.role == "patient",
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    _ensure_admin_can_access_user(admin, patient)
    patient_facility_id = patient.facility_id
    try:
        result = privacy_operations.execute_patient_deletion(db, patient_id)
    except privacy_operations.PrivacyOperationNotFound:
        raise HTTPException(status_code=404, detail="Patient not found") from None

    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=patient_id,
        facility_id=patient_facility_id,
        action="EXECUTE_PATIENT_DELETION",
        details={
            "resource_type": "privacy_deletion_execution",
            "resource_id": patient_id,
            "deleted_records": result["database"]["total_records_deleted"],
        },
    )
    return result


@router.post("/backups/execute")
def execute_database_backup(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    try:
        connection = db.connection().connection
        raw_conn = getattr(connection, "driver_connection", None) or getattr(connection, "dbapi_connection", None) or getattr(connection, "connection", None)
        if raw_conn is None:
            raise AttributeError("Could not find underlying DBAPI connection on SQLAlchemy Connection object")
        backup_file = backup_readiness.run_sqlite_backup(raw_conn)
    except Exception as e:
        db_path = "healthcare.db"
        if not os.path.exists(db_path):
            if os.path.exists("backend/healthcare.db"):
                db_path = "backend/healthcare.db"
        try:
            backup_file = backup_readiness.run_sqlite_backup(db_path)
        except Exception as file_err:
            raise HTTPException(status_code=500, detail=f"Backup failed: connection error ({str(e)}), file error ({str(file_err)})")

    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=admin.id,
        facility_id=admin.facility_id,
        action="EXECUTE_DATABASE_BACKUP",
        details={
            "backup_file": backup_file,
        },
    )
    return {
        "status": "success",
        "backup_file": backup_file,
        "message": "Database backup completed successfully."
    }


@router.post("/retention/execute-cleanup")
def execute_retention_cleanup(
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(get_current_admin),
) -> Dict:
    """Execute a data retention cleanup sweep according to policy thresholds."""
    try:
        deleted_counts = retention_policy.execute_retention_cleanup(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retention cleanup failed: {str(e)}")

    audit.record_audit_event(
        db,
        actor_user_id=admin.id,
        target_user_id=admin.id,
        facility_id=admin.facility_id,
        action="EXECUTE_RETENTION_CLEANUP",
        details=deleted_counts,
    )
    return {
        "status": "success",
        "deleted_records": deleted_counts,
        "message": "Data retention sweep completed successfully."
    }

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
        models.User.is_deleted == False,
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
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
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
    """Soft delete a user and their data."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _ensure_admin_can_access_user(admin, user)

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")

    from datetime import datetime, timezone
    deleted_user_id = user.id
    deleted_user_facility_id = user.facility_id
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
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


@router.get("/semantic-cache")
def get_semantic_cache_stats(
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Retrieve runtime telemetry and entry auditing metadata from the LLM semantic cache."""
    from .core_ai import semantic_cache
    return {
        "status": "success",
        "stats": semantic_cache.get_stats()
    }


@router.delete("/semantic-cache")
def clear_semantic_cache(
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Evict all items in the semantic cache to handle stale narratives or policy updates."""
    if admin.facility_id is not None:
        raise HTTPException(status_code=403, detail="Clearing the semantic cache requires global admin privileges")

    from .core_ai import semantic_cache
    semantic_cache.clear()
    return {
        "status": "success",
        "message": "Semantic cache evicted successfully"
    }


@router.post("/federated-sim")
def run_federated_simulation(
    epochs: int = Query(10, ge=1, le=50),
    epsilon: float = Query(1.5, gt=0.0, le=10.0),
    admin: models.User = Depends(get_current_admin)
) -> Dict:
    """Run the federated learning simulation with custom epochs and privacy budget epsilon."""
    if admin.facility_id is not None:
        raise HTTPException(status_code=403, detail="Federated simulation requires global admin privileges")

    import os
    import sys

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    try:
        from scripts.training.run_federated_sim import run_simulation
        results = run_simulation(epochs=epochs, epsilon=epsilon)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Federated simulation failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# HIPAA Compliance Self-Check
# ---------------------------------------------------------------------------
@router.get("/compliance/hipaa")
def hipaa_compliance_check(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Run HIPAA technical safeguard compliance self-check."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return compliance_check.get_hipaa_compliance_report()


# ---------------------------------------------------------------------------
# Breach Notification Management
# ---------------------------------------------------------------------------
@router.get("/breaches")
def list_breaches(
    include_resolved: bool = Query(False),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    """List all security breach incidents."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "incidents": breach_notification.breach_manager.list_incidents(include_resolved=include_resolved),
        "overdue": breach_notification.breach_manager.get_overdue_incidents(),
    }


@router.post("/breaches/report")
def report_breach(
    description: str = Query(..., min_length=10),
    severity: str = Query("medium"),
    affected_records: int = Query(0, ge=0),
    phi_involved: bool = Query(False),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Report a new security breach incident."""
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        sev = breach_notification.BreachSeverity(severity)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}. Use: low, medium, high, critical")
    report = breach_notification.breach_manager.report_breach(
        description=description,
        reporter=current_user.username,
        severity=sev,
        affected_records=affected_records,
        phi_involved=phi_involved,
    )
    return report.to_dict()
