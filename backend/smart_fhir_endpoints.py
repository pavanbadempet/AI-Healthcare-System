"""SMART on FHIR API endpoints for application registration and launch workflow."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import auth, database, models, schemas

router = APIRouter(prefix="/smart", tags=["SMART on FHIR"])


@router.post(
    "/apps",
    response_model=schemas.SmartAppResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_smart_app(
    payload: schemas.SmartAppCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.SmartApp:
    """Register a new third-party SMART on FHIR application."""
    if not auth.is_admin(current_user) and current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or clinicians can register applications",
        )

    # Check for duplicate name
    existing = (
        db.query(models.SmartApp)
        .filter(models.SmartApp.app_name == payload.app_name)
        .first()
    )
    if existing:
        if not existing.is_active:
            # Reactivate soft-deleted app
            existing.is_active = True
            existing.redirect_uri = payload.redirect_uri
            existing.launch_url = payload.launch_url
            existing.scopes = payload.scopes
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An application with this name is already registered",
        )

    client_id = str(uuid4())
    db_app = models.SmartApp(
        app_name=payload.app_name,
        client_id=client_id,
        redirect_uri=payload.redirect_uri,
        launch_url=payload.launch_url,
        scopes=payload.scopes,
        is_active=True,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


@router.get("/apps", response_model=list[schemas.SmartAppResponse])
def list_smart_apps(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> list[models.SmartApp]:
    """Retrieve all active registered SMART applications."""
    return db.query(models.SmartApp).filter(models.SmartApp.is_active == True).all()


@router.delete("/apps/{app_id}")
def delete_smart_app(
    app_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> dict[str, str]:
    """Soft-delete a registered SMART application by ID."""
    if not auth.is_admin(current_user) and current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or clinicians can delete applications",
        )

    db_app = (
        db.query(models.SmartApp)
        .filter(models.SmartApp.id == app_id, models.SmartApp.is_active == True)
        .first()
    )
    if not db_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    db_app.is_active = False
    db.commit()
    return {"status": "deleted"}


@router.post("/launch", response_model=schemas.SmartLaunchResponse)
def launch_smart_app(
    payload: schemas.SmartLaunchRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
) -> models.SmartLaunchContext:
    """Generate a patient-scoped launch context and tokens for a SMART app."""
    # Verify app exists
    db_app = (
        db.query(models.SmartApp)
        .filter(models.SmartApp.id == payload.app_id, models.SmartApp.is_active == True)
        .first()
    )
    if not db_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Verify patient exists
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

    # Generate launch tokens (valid for 10 minutes)
    launch_token = str(uuid4())
    auth_code = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    db_launch = models.SmartLaunchContext(
        app_id=payload.app_id,
        patient_id=payload.patient_id,
        user_id=current_user.id,
        launch_token=launch_token,
        auth_code=auth_code,
        scope=db_app.scopes,
        expires_at=expires_at,
    )
    db.add(db_launch)
    db.commit()
    db.refresh(db_launch)
    return db_launch
