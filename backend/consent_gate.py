"""EULA Consent Gate — Enforces Terms of Service acceptance.

Requires users to accept the End User License Agreement before accessing
clinical features. Records consent with version tracking for audit compliance.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from . import database, models

logger = logging.getLogger(__name__)

CURRENT_EULA_VERSION = "1.0"

router = APIRouter(prefix="/consent", tags=["Consent"])

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token", auto_error=False)


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------
class ConsentRecord(database.Base):
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    eula_version = Column(String, nullable=False)
    accepted_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ConsentAcceptRequest(BaseModel):
    eula_version: str = CURRENT_EULA_VERSION


class ConsentStatusResponse(BaseModel):
    accepted: bool
    eula_version: str
    current_version: str
    accepted_at: Optional[str] = None
    requires_reaccept: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_user(token: Optional[str], db: Session) -> models.User:
    """Resolve the current user from a bearer token, with lazy auth import."""
    from . import auth

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return auth.get_current_user(token=token, db=db)


def _get_user_consent(db: Session, user_id: int) -> Optional[ConsentRecord]:
    """Get the latest consent record for a user."""
    return (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user_id)
        .order_by(ConsentRecord.accepted_at.desc())
        .first()
    )


def has_valid_consent(db: Session, user_id: int) -> bool:
    """Check if user has accepted the current EULA version."""
    record = _get_user_consent(db, user_id)
    if record is None:
        return False
    return record.eula_version == CURRENT_EULA_VERSION


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------
def require_consent():
    """Dependency that blocks clinical endpoints until EULA is accepted."""

    def _check(
        request: Request,
        token: Optional[str] = Depends(_oauth2_scheme),
        db: Session = Depends(database.get_db),
    ):
        user = _resolve_user(token, db)
        if has_valid_consent(db, user.id):
            return user

        raise HTTPException(
            status_code=451,
            detail=(
                f"You must accept the End User License Agreement (EULA) v{CURRENT_EULA_VERSION} "
                "before accessing clinical features. POST /v1/consent/accept to proceed."
            ),
        )

    return _check


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/accept")
def accept_eula(
    body: ConsentAcceptRequest,
    request: Request,
    token: Optional[str] = Depends(_oauth2_scheme),
    db: Session = Depends(database.get_db),
):
    """Accept the EULA. Requires authentication."""
    current_user = _resolve_user(token, db)

    record = ConsentRecord(
        user_id=current_user.id,
        eula_version=body.eula_version,
        accepted_at=datetime.now(timezone.utc),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:512],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "EULA v%s accepted by user %d from %s",
        body.eula_version,
        current_user.id,
        record.ip_address or "unknown",
    )

    return {
        "status": "accepted",
        "eula_version": body.eula_version,
        "accepted_at": record.accepted_at.isoformat(),
    }


@router.get("/status")
def consent_status(
    request: Request,
    token: Optional[str] = Depends(_oauth2_scheme),
    db: Session = Depends(database.get_db),
):
    """Check current EULA consent status for the authenticated user."""
    current_user = _resolve_user(token, db)

    record = _get_user_consent(db, current_user.id)
    if record is None:
        return ConsentStatusResponse(
            accepted=False,
            eula_version="none",
            current_version=CURRENT_EULA_VERSION,
            requires_reaccept=True,
        )

    requires_reaccept = record.eula_version != CURRENT_EULA_VERSION
    return ConsentStatusResponse(
        accepted=not requires_reaccept,
        eula_version=record.eula_version,
        current_version=CURRENT_EULA_VERSION,
        accepted_at=record.accepted_at.isoformat() if record.accepted_at else None,
        requires_reaccept=requires_reaccept,
    )
