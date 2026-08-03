"""
AI Healthcare System — ABDM (Ayushman Bharat Digital Mission) Health ID & Consent Manager Sandbox.

Provides zero-configuration local fallback pathways for ABHA creation, OTP verification,
and M1/M2/M3 digital health consent artifacts.
"""

import uuid
import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from backend.schemas.abdm import (
    ABHACreateRequest, ABHAResponse,
    ConsentArtifactCreate, ConsentArtifactResponse
)

router = APIRouter(prefix="/abdm", tags=["abdm-sandbox"])

# In-memory storage for ABDM Sandbox records (zero-config fallback)
_abha_store: Dict[str, Dict[str, Any]] = {}
_consent_store: Dict[str, Dict[str, Any]] = {}

@router.post("/abha/generate", response_model=ABHAResponse)
def generate_abha_health_id(req: ABHACreateRequest) -> Dict[str, Any]:
    """
    Generate an ABHA Health ID & Health Address (ABDM M1 Milestone).
    """
    random_digits = "".join([str(random.randint(0, 9)) for _ in range(12)])
    abha_num = f"91-{random_digits[:4]}-{random_digits[4:8]}-{random_digits[8:]}"
    clean_username = "".join(e for e in req.name.lower() if e.isalnum())
    abha_addr = f"{clean_username}{random.randint(100,999)}@sbx"
    
    record = {
        "abha_number": abha_num,
        "abha_address": abha_addr,
        "name": req.name,
        "status": "ACTIVE",
        "qr_code_token": f"ABDM-QR-{uuid.uuid4().hex[:12].upper()}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _abha_store[abha_num] = record
    return record

@router.get("/abha/{abha_number}", response_model=ABHAResponse)
def get_abha_details(abha_number: str) -> Dict[str, Any]:
    """
    Fetch ABHA Health ID record.
    """
    if abha_number not in _abha_store:
        # Return fallback mock if requested ID not generated in current session
        return {
            "abha_number": abha_number,
            "abha_address": "patient.health@sbx",
            "name": "Verified ABDM Beneficiary",
            "status": "ACTIVE",
            "qr_code_token": f"ABDM-QR-{uuid.uuid4().hex[:12].upper()}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    return _abha_store[abha_number]

@router.post("/consent/request", response_model=ConsentArtifactResponse)
def request_health_consent(req: ConsentArtifactCreate) -> Dict[str, Any]:
    """
    Create an M2/M3 Digital Health Record Consent Artifact.
    """
    consent_id = f"CONSENT-{uuid.uuid4().hex[:10].upper()}"
    artifact = {
        "consent_id": consent_id,
        "patient_abha": req.patient_abha,
        "status": "GRANTED",
        "purpose": req.purpose,
        "hi_types": req.hi_types,
        "granted_at": datetime.now(timezone.utc).isoformat(),
        "valid_until": req.valid_until
    }
    _consent_store[consent_id] = artifact
    return artifact

@router.get("/consent/{consent_id}", response_model=ConsentArtifactResponse)
def get_consent_status(consent_id: str) -> Dict[str, Any]:
    """
    Get Consent Artifact Status.
    """
    if consent_id not in _consent_store:
        raise HTTPException(status_code=404, detail="Consent artifact not found")
    return _consent_store[consent_id]
