"""Structured Clinical Intent & Semantic Attribution Tracker.

Moves beyond 'who changed what' to 'why was this clinical action taken'.
Captures structured medical rationales, diagnostic evidence linkages, and
Four-Eye dual clinician quorum sign-offs for high-risk interventions.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class ClinicalIntentCategory(str, Enum):
    """Standardized taxonomy of clinical motivations for medical decisions."""

    PHARMACOGENOMIC_GUIDELINE = "PHARMACOGENOMIC_GUIDELINE"
    RENAL_DOSE_ADJUSTMENT = "RENAL_DOSE_ADJUSTMENT"
    HEMODYNAMIC_INSTABILITY = "HEMODYNAMIC_INSTABILITY"
    DRUG_INTERACTION_OVERRIDE = "DRUG_INTERACTION_OVERRIDE"
    ALLERGIC_REACTION_RESPONSE = "ALLERGIC_REACTION_RESPONSE"
    PALLIATIVE_PIVOT = "PALLIATIVE_PIVOT"
    TRANSCRIPTION_CORRECTION = "TRANSCRIPTION_CORRECTION"
    DIAGNOSTIC_CONFIRMATION = "DIAGNOSTIC_CONFIRMATION"
    ROUTINE_MONITORING = "ROUTINE_MONITORING"


# Categories that strictly require dual-clinician quorum sign-off
QUORUM_REQUIRED_CATEGORIES = {
    ClinicalIntentCategory.DRUG_INTERACTION_OVERRIDE,
    ClinicalIntentCategory.PHARMACOGENOMIC_GUIDELINE,
    ClinicalIntentCategory.PALLIATIVE_PIVOT,
}


class EvidenceLink:
    """Links clinical decisions to objective diagnostic or genetic evidence."""

    def __init__(
        self,
        evidence_type: str,
        evidence_id: str,
        description: str,
    ) -> None:
        self.evidence_type = evidence_type  # 'LAB_SPECIMEN', 'GENOMIC_VARIANT', 'VITAL_TREND', 'NOTE'
        self.evidence_id = evidence_id
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "evidence_id": self.evidence_id,
            "description": self.description,
        }


class ClinicianSignature:
    """Cryptographically verifiable digital attribution signature."""

    def __init__(
        self,
        clinician_id: str,
        clinician_name: str,
        role: str,
        signed_at: datetime.datetime,
        intent_id: str,
    ) -> None:
        self.clinician_id = clinician_id
        self.clinician_name = clinician_name
        self.role = role
        self.signed_at = signed_at
        self.signature_hash = self._generate_hash(intent_id)

    def _generate_hash(self, intent_id: str) -> str:
        payload = f"{self.clinician_id}:{self.role}:{self.signed_at.isoformat()}:{intent_id}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clinician_id": self.clinician_id,
            "clinician_name": self.clinician_name,
            "role": self.role,
            "signed_at": self.signed_at.isoformat(),
            "signature_hash": self.signature_hash,
        }


class ClinicalIntentRecord:
    """Represents the complete semantic attribution context for a chart modification."""

    def __init__(
        self,
        intent_id: str,
        patient_id: str,
        category: ClinicalIntentCategory,
        rationale: str,
        primary_clinician: ClinicianSignature,
        evidence_links: Optional[List[EvidenceLink]] = None,
        countersignatures: Optional[List[ClinicianSignature]] = None,
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.intent_id = intent_id
        self.patient_id = patient_id
        self.category = category
        self.rationale = rationale
        self.primary_clinician = primary_clinician
        self.evidence_links = evidence_links or []
        self.countersignatures = countersignatures or []
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)

    @property
    def is_quorum_verified(self) -> bool:
        """Evaluate if the record satisfies dual-signoff quorum for high-risk decisions."""
        if self.category not in QUORUM_REQUIRED_CATEGORIES:
            return True
        return len(self.countersignatures) >= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "patient_id": self.patient_id,
            "category": self.category.value,
            "rationale": self.rationale,
            "primary_clinician": self.primary_clinician.to_dict(),
            "countersignatures": [cs.to_dict() for cs in self.countersignatures],
            "evidence_links": [ev.to_dict() for ev in self.evidence_links],
            "is_quorum_verified": self.is_quorum_verified,
            "created_at": self.created_at.isoformat(),
        }


class ClinicalIntentTracker:
    """Repository and verifier for structured clinical intent records."""

    def __init__(self) -> None:
        self._intents: Dict[str, ClinicalIntentRecord] = {}  # intent_id -> record

    def record_intent(
        self,
        patient_id: str,
        category: ClinicalIntentCategory | str,
        rationale: str,
        clinician_id: str,
        clinician_name: str,
        role: str,
        evidence: Optional[List[Dict[str, str]]] = None,
        intent_id: Optional[str] = None,
    ) -> ClinicalIntentRecord:
        """Create and register a new structured clinical intent record."""
        iid = intent_id or str(uuid.uuid4())
        cat = ClinicalIntentCategory(category) if isinstance(category, str) else category
        now = datetime.datetime.now(datetime.timezone.utc)

        sig = ClinicianSignature(
            clinician_id=clinician_id,
            clinician_name=clinician_name,
            role=role,
            signed_at=now,
            intent_id=iid,
        )

        ev_links: List[EvidenceLink] = []
        if evidence:
            for item in evidence:
                ev_links.append(
                    EvidenceLink(
                        evidence_type=item.get("evidence_type", "CLINICAL_NOTE"),
                        evidence_id=item.get("evidence_id", "REF-0"),
                        description=item.get("description", ""),
                    )
                )

        record = ClinicalIntentRecord(
            intent_id=iid,
            patient_id=patient_id,
            category=cat,
            rationale=rationale,
            primary_clinician=sig,
            evidence_links=ev_links,
            created_at=now,
        )

        self._intents[iid] = record
        return record

    def add_countersignature(
        self,
        intent_id: str,
        clinician_id: str,
        clinician_name: str,
        role: str,
    ) -> Optional[ClinicalIntentRecord]:
        """Add Four-Eye dual signoff countersignature from another clinician."""
        record = self._intents.get(intent_id)
        if not record:
            return None

        # Prevent self-countersigning
        if record.primary_clinician.clinician_id == clinician_id:
            raise ValueError("Countersignature cannot be performed by the primary clinician")

        now = datetime.datetime.now(datetime.timezone.utc)
        counter_sig = ClinicianSignature(
            clinician_id=clinician_id,
            clinician_name=clinician_name,
            role=role,
            signed_at=now,
            intent_id=intent_id,
        )

        record.countersignatures.append(counter_sig)
        return record

    def get_intent(self, intent_id: str) -> Optional[ClinicalIntentRecord]:
        """Fetch intent record by unique identifier."""
        return self._intents.get(intent_id)

    def get_patient_intents(self, patient_id: str) -> List[ClinicalIntentRecord]:
        """Fetch all clinical intent rationales recorded for a patient."""
        return [
            rec for rec in self._intents.values()
            if rec.patient_id == patient_id
        ]

    def clear(self) -> None:
        """Reset internal store (for testing)."""
        self._intents.clear()
