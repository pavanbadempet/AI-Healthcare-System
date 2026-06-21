"""Federated Sync Bridge API — differential-privacy gradient aggregation."""
from __future__ import annotations

import json
import math
import random
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import auth, database, models, schemas

router = APIRouter(prefix="/federated", tags=["Federated Learning"])


def apply_laplace_dp(
    gradients: dict[str, float],
    epsilon: float,
    sensitivity: float,
    num_records: int,
) -> dict[str, float]:
    """Clip gradients and add Laplace noise for Differential Privacy.

    Formula:
      noise_scale = sensitivity / (num_records * epsilon)
      noise ~ Laplace(0, noise_scale)
    """
    if num_records <= 0:
        return {k: 0.0 for k in gradients}

    # 1. L2-norm clipping of gradients
    l2_norm = math.sqrt(sum(g * g for g in gradients.values()))
    clip_factor = 1.0
    if l2_norm > sensitivity:
        clip_factor = sensitivity / l2_norm

    clipped_gradients = {k: v * clip_factor for k, v in gradients.items()}

    # 2. Add Laplace noise
    # Laplace scale: b = sensitivity / (n * epsilon)
    scale = sensitivity / (num_records * epsilon)

    noisy_gradients = {}
    for k, v in clipped_gradients.items():
        # Sample from Laplace distribution using inverse transform sampling:
        # u ~ Uniform(-0.5, 0.5)
        # noise = -scale * sgn(u) * ln(1 - 2*|u|)
        u = random.random() - 0.5
        sign = 1.0 if u >= 0 else -1.0
        noise = -scale * sign * math.log(1.0 - 2.0 * abs(u))
        noisy_gradients[k] = v + noise

    return noisy_gradients


@router.post(
    "/feedback",
    response_model=schemas.ModelFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_model_feedback(
    payload: schemas.ModelFeedbackCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.ModelFeedback:
    """Submit clinician correction for a model prediction to the federated mesh."""
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinicians or admins can submit model feedback",
        )

    # Validate patient exists
    patient = (
        db.query(models.User)
        .filter(models.User.id == payload.patient_id, models.User.role == "patient")
        .first()
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    db_feedback = models.ModelFeedback(
        patient_id=payload.patient_id,
        model_name=payload.model_name,
        input_features=json.dumps(payload.input_features),
        prediction_result=json.dumps(payload.prediction_result),
        corrected_label=payload.corrected_label,
        clinician_id=current_user.id,
        status="pending_sync",
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


@router.post("/sync", response_model=schemas.FederatedSyncResponse)
def trigger_federated_sync(
    payload: schemas.FederatedSyncRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Execute a differential-privacy gradient sync for a model."""
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinicians or admins can trigger sync runs",
        )

    if payload.epsilon <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Epsilon must be greater than zero",
        )

    # 1. Privacy Budget Exhaustion Guard (Global / Model-specific threshold <= 10.0)
    total_epsilon_spent = (
        db.query(func.sum(models.FederatedSyncAudit.epsilon_consumed))
        .filter(models.FederatedSyncAudit.status == "completed")
        .scalar()
    ) or 0.0

    if total_epsilon_spent + payload.epsilon > 10.0:
        # Log failed audit record
        sync_run_id = str(uuid4())
        db_audit = models.FederatedSyncAudit(
            sync_run_id=sync_run_id,
            node_id="hospital-node-01",
            model_name=payload.model_name,
            records_synced=0,
            epsilon_consumed=0.0,
            delta_consumed=0.0,
            status="rejected",
            error_message="Privacy budget exhausted. Cumulative epsilon exceeds 10.0 limit.",
        )
        db.add(db_audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privacy budget exhausted. Epsilon limit of 10.0 exceeded.",
        )

    # 2. Gather pending feedback records for the model
    feedbacks = (
        db.query(models.ModelFeedback)
        .filter(
            models.ModelFeedback.model_name == payload.model_name,
            models.ModelFeedback.status == "pending_sync",
        )
        .all()
    )

    records_count = len(feedbacks)
    sync_run_id = str(uuid4())

    if records_count == 0:
        # Create completed audit with 0 records
        db_audit = models.FederatedSyncAudit(
            sync_run_id=sync_run_id,
            node_id="hospital-node-01",
            model_name=payload.model_name,
            records_synced=0,
            epsilon_consumed=payload.epsilon,
            delta_consumed=0.0,
            status="completed",
            error_message="No pending records to sync",
        )
        db.add(db_audit)
        db.commit()

        return {
            "sync_run_id": sync_run_id,
            "records_synced": 0,
            "epsilon_consumed": payload.epsilon,
            "noisy_gradients": {},
            "status": "success",
        }

    # 3. Simulate gradient computation and apply LDP
    # We aggregate dummy gradients derived from feedback labels for demo/verification.
    # In a full ML system, this would be computed by running backprop on the corrected labels.
    base_gradients = {
        "weight_0": 0.05 * records_count,
        "weight_1": -0.12 * records_count,
        "weight_2": 0.02 * records_count,
        "bias": -0.01 * records_count,
    }

    noisy_gradients = apply_laplace_dp(
        gradients=base_gradients,
        epsilon=payload.epsilon,
        sensitivity=payload.sensitivity,
        num_records=records_count,
    )

    # 4. Update feedbacks status to synced
    for f in feedbacks:
        f.status = "synced"

    # 5. Log audit trail
    db_audit = models.FederatedSyncAudit(
        sync_run_id=sync_run_id,
        node_id="hospital-node-01",
        model_name=payload.model_name,
        records_synced=records_count,
        epsilon_consumed=payload.epsilon,
        delta_consumed=0.0,
        status="completed",
    )
    db.add(db_audit)
    db.commit()

    return {
        "sync_run_id": sync_run_id,
        "records_synced": records_count,
        "epsilon_consumed": payload.epsilon,
        "noisy_gradients": noisy_gradients,
        "status": "success",
    }


@router.get("/stats")
def get_federated_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, Any]:
    """Get count of pending feedbacks and total epsilon privacy budget consumed."""
    pending_count = (
        db.query(models.ModelFeedback)
        .filter(models.ModelFeedback.status == "pending_sync")
        .count()
    )

    total_epsilon = (
        db.query(func.sum(models.FederatedSyncAudit.epsilon_consumed))
        .filter(models.FederatedSyncAudit.status == "completed")
        .scalar()
    ) or 0.0

    return {
        "pending_count": pending_count,
        "total_epsilon_spent": total_epsilon,
    }


@router.get("/audits", response_model=list[schemas.FederatedSyncAuditResponse])
def get_sync_audits(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[models.FederatedSyncAudit]:
    """Retrieve all sync audit history logs."""
    return (
        db.query(models.FederatedSyncAudit)
        .order_by(models.FederatedSyncAudit.created_at.desc())
        .all()
    )
