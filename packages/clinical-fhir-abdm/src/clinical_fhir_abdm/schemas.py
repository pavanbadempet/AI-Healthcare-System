"""Strongly-typed FHIR action proposals and clinical agent response models.

Provides strongly-typed, serialization-ready dataclasses for clinical specialist swarms:
- FHIRMedicationRequestProposal: Prescription and drug therapy orders.
- FHIRServiceRequestProposal: Diagnostic, procedural, laboratory, and consult requests.
- FHIRFlagProposal: Clinical safety alerts, allergy flags, and critical warnings.
- ClinicalAgentResponse: Unified response emitted by autonomous clinical agents.
"""

from __future__ import annotations

import datetime
import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

try:
    from clinical_fhir_abdm.fhir import fhir_datetime
except (ImportError, ModuleNotFoundError):
    from .fhir import fhir_datetime


@dataclass
class FHIRMedicationRequestProposal:
    """Strongly-typed proposal for a FHIR MedicationRequest resource."""

    patient_id: str
    medication_name: str
    dosage: str = ""
    route: str = "oral"
    frequency: str = "once daily"
    indication: str = ""
    clinical_evidence: Optional[List[str]] = None
    requester: Optional[str] = None
    intent: str = "order"
    priority: str = "routine"  # routine | urgent | stat | asap
    dose: Optional[float] = None
    unit: Optional[str] = None
    countersigned_by: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = f"medreq-{uuid.uuid4().hex[:10]}"
        if self.created_at is None:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)
        if self.clinical_evidence is None:
            self.clinical_evidence = []
        if not self.dosage and self.dose is not None:
            self.dosage = f"{self.dose} {self.unit or ''}".strip()
        elif self.dosage and self.dose is None:
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(self.dosage))
            if match:
                try:
                    self.dose = float(match.group(1))
                except (ValueError, TypeError):
                    pass

    @property
    def numeric_dose(self) -> Optional[float]:
        """Extract numeric dose in standard units."""
        if self.dose is not None:
            return float(self.dose)
        if not self.dosage:
            return None
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(self.dosage))
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to standard dictionary."""
        data = asdict(self)
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FHIRMedicationRequestProposal:
        """Construct a proposal from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except Exception:
                created_at = None

        med_name = str(data.get("medication_name") or data.get("drug") or data.get("name") or "")
        dose_val = data.get("dose")
        unit_val = data.get("unit")
        dosage_val = str(data.get("dosage", ""))
        if not dosage_val and dose_val is not None:
            dosage_val = f"{dose_val} {unit_val or ''}".strip()

        return cls(
            patient_id=str(data.get("patient_id", "")),
            medication_name=med_name,
            dosage=dosage_val,
            route=str(data.get("route", "oral")),
            frequency=str(data.get("frequency", "once daily")),
            indication=str(data.get("indication", "")),
            clinical_evidence=list(data.get("clinical_evidence") or []),
            requester=data.get("requester"),
            intent=str(data.get("intent", "order")),
            priority=str(data.get("priority", "routine")),
            dose=float(dose_val) if dose_val is not None else None,
            unit=str(unit_val) if unit_val is not None else None,
            countersigned_by=data.get("countersigned_by"),
            id=data.get("id"),
            created_at=created_at,
        )

    def to_fhir(self) -> Dict[str, Any]:
        """Serialize proposal into a valid FHIR R4 MedicationRequest resource."""
        resource: Dict[str, Any] = {
            "resourceType": "MedicationRequest",
            "id": self.id,
            "status": "active",
            "intent": self.intent,
            "priority": self.priority,
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "authoredOn": fhir_datetime(self.created_at),
            "medicationCodeableConcept": {
                "text": self.medication_name,
            },
            "dosageInstruction": [
                {
                    "text": f"{self.dosage}, {self.route}, {self.frequency}".strip(", "),
                    "route": {"text": self.route},
                }
            ],
        }

        if self.indication:
            resource["reasonCode"] = [{"text": self.indication}]
        if self.requester:
            resource["requester"] = {"display": self.requester}
        if self.clinical_evidence:
            resource["note"] = [{"text": ev} for ev in self.clinical_evidence]

        return resource


@dataclass
class FHIRServiceRequestProposal:
    """Strongly-typed proposal for a FHIR ServiceRequest resource."""

    patient_id: str
    category: str  # diagnostic | procedure | consult | laboratory | imaging
    code: str  # LOINC or SNOMED CT code
    description: str
    urgency: str = "routine"  # routine | urgent | stat | asap
    indication: str = ""
    requester: Optional[str] = None
    supporting_info: Optional[List[str]] = None
    countersigned_by: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = f"sr-{uuid.uuid4().hex[:10]}"
        if self.created_at is None:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)
        if self.supporting_info is None:
            self.supporting_info = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to standard dictionary."""
        data = asdict(self)
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FHIRServiceRequestProposal:
        """Construct a proposal from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except Exception:
                created_at = None

        return cls(
            patient_id=str(data.get("patient_id", "")),
            category=str(data.get("category", "diagnostic")),
            code=str(data.get("code", "")),
            description=str(data.get("description", data.get("name", ""))),
            urgency=str(data.get("urgency", data.get("priority", "routine"))),
            indication=str(data.get("indication", data.get("reason", ""))),
            requester=data.get("requester"),
            supporting_info=list(data.get("supporting_info") or []),
            countersigned_by=data.get("countersigned_by"),
            id=data.get("id"),
            created_at=created_at,
        )

    def to_fhir(self) -> Dict[str, Any]:
        """Serialize proposal into a valid FHIR R4 ServiceRequest resource."""
        # Map urgency to FHIR priority
        priority_map = {
            "routine": "routine",
            "urgent": "urgent",
            "stat": "stat",
            "asap": "asap",
        }
        fhir_priority = priority_map.get(self.urgency.lower(), "routine")

        # Determine coding system if known
        system = "http://loinc.org" if any(c.isdigit() for c in self.code) and "-" in self.code else "http://snomed.info/sct"

        resource: Dict[str, Any] = {
            "resourceType": "ServiceRequest",
            "id": self.id,
            "status": "active",
            "intent": "order",
            "priority": fhir_priority,
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "108252007",
                            "display": self.category.title(),
                        }
                    ],
                    "text": self.category,
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": system,
                        "code": self.code,
                        "display": self.description,
                    }
                ],
                "text": self.description,
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "authoredOn": fhir_datetime(self.created_at),
        }

        if self.indication:
            resource["reasonCode"] = [{"text": self.indication}]
        if self.requester:
            resource["requester"] = {"display": self.requester}
        if self.supporting_info:
            resource["supportingInfo"] = [{"display": info} for info in self.supporting_info]

        return resource


@dataclass
class FHIRFlagProposal:
    """Strongly-typed proposal for a FHIR Flag resource (safety alerts, warnings)."""

    patient_id: str
    status: str = "active"  # active | inactive | entered-in-error
    category: str = "clinical_alert"  # clinical_alert | allergy | safety_risk | behavioral | advance_directive
    severity: str = "warning"  # critical | high | warning | moderate | low
    code: str = ""
    details: str = ""
    author: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = f"flag-{uuid.uuid4().hex[:10]}"
        if self.created_at is None:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to standard dictionary."""
        data = asdict(self)
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FHIRFlagProposal:
        """Construct a proposal from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except Exception:
                created_at = None

        return cls(
            patient_id=str(data.get("patient_id", "")),
            status=str(data.get("status", "active")),
            category=str(data.get("category", "clinical_alert")),
            severity=str(data.get("severity", "warning")),
            code=str(data.get("code", "")),
            details=str(data.get("details", data.get("message", ""))),
            author=data.get("author"),
            id=data.get("id"),
            created_at=created_at,
        )

    def to_fhir(self) -> Dict[str, Any]:
        """Serialize proposal into a valid FHIR R4 Flag resource."""
        cat_code_map = {
            "clinical_alert": "clinical",
            "safety_risk": "safety",
            "allergy": "safety",
            "behavioral": "behavioral",
            "advance_directive": "advance-directive",
        }
        fhir_cat_code = cat_code_map.get(self.category.lower(), "clinical")

        resource: Dict[str, Any] = {
            "resourceType": "Flag",
            "id": self.id,
            "status": self.status,
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                            "code": fhir_cat_code,
                            "display": self.category.replace("_", " ").title(),
                        }
                    ],
                    "text": self.category,
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": self.code or "404684003",
                        "display": self.details[:60] if self.details else "Clinical finding",
                    }
                ],
                "text": self.details or self.code,
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "period": {
                "start": fhir_datetime(self.created_at),
            },
        }

        if self.author:
            resource["author"] = {"display": self.author}

        # Extensions or tags for severity
        if self.severity:
            resource["extension"] = [
                {
                    "url": "http://ai-healthcare-system.io/fhir/StructureDefinition/flag-severity",
                    "valueString": self.severity.lower(),
                }
            ]

        return resource


FHIRActionProposal = Union[
    FHIRMedicationRequestProposal,
    FHIRServiceRequestProposal,
    FHIRFlagProposal,
]


@dataclass
class ClinicalAgentResponse:
    """Unified standard response emitted by autonomous clinical agents."""

    recommendations: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    proposed_fhir_actions: List[FHIRActionProposal] = field(default_factory=list)
    epistemic_confidence: float = 1.0  # Range [0.0, 1.0]
    agent_name: Optional[str] = None
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __post_init__(self) -> None:
        # Clamp confidence to [0.0, 1.0]
        self.epistemic_confidence = max(0.0, min(1.0, float(self.epistemic_confidence)))

    def add_action(self, action: FHIRActionProposal) -> None:
        """Add a strongly-typed FHIR proposal to the agent's action plan."""
        self.proposed_fhir_actions.append(action)

    def get_medication_requests(self) -> List[FHIRMedicationRequestProposal]:
        """Filter actions to MedicationRequest proposals."""
        return [a for a in self.proposed_fhir_actions if isinstance(a, FHIRMedicationRequestProposal)]

    def get_service_requests(self) -> List[FHIRServiceRequestProposal]:
        """Filter actions to ServiceRequest proposals."""
        return [a for a in self.proposed_fhir_actions if isinstance(a, FHIRServiceRequestProposal)]

    def get_flags(self) -> List[FHIRFlagProposal]:
        """Filter actions to Flag proposals."""
        return [a for a in self.proposed_fhir_actions if isinstance(a, FHIRFlagProposal)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert clinical response to dictionary format."""
        actions = []
        for act in self.proposed_fhir_actions:
            if hasattr(act, "to_dict"):
                actions.append(act.to_dict())
            elif isinstance(act, dict):
                actions.append(act)
            else:
                actions.append(str(act))

        return {
            "agent_name": self.agent_name,
            "epistemic_confidence": round(self.epistemic_confidence, 4),
            "recommendations": self.recommendations,
            "proposed_fhir_actions": actions,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClinicalAgentResponse:
        """Construct response from dictionary, parsing FHIR proposals."""
        raw_actions = data.get("proposed_fhir_actions", [])
        parsed_actions: List[FHIRActionProposal] = []

        for item in raw_actions:
            if isinstance(item, (FHIRMedicationRequestProposal, FHIRServiceRequestProposal, FHIRFlagProposal)):
                parsed_actions.append(item)
            elif isinstance(item, dict):
                if "medication_name" in item:
                    parsed_actions.append(FHIRMedicationRequestProposal.from_dict(item))
                elif "category" in item and "code" in item and "description" in item:
                    parsed_actions.append(FHIRServiceRequestProposal.from_dict(item))
                elif "category" in item and ("details" in item or "severity" in item):
                    parsed_actions.append(FHIRFlagProposal.from_dict(item))
                else:
                    parsed_actions.append(item)  # type: ignore
            else:
                parsed_actions.append(item)  # type: ignore

        timestamp_raw = data.get("timestamp")
        ts = datetime.datetime.now(datetime.timezone.utc)
        if isinstance(timestamp_raw, str):
            try:
                ts = datetime.datetime.fromisoformat(timestamp_raw)
            except Exception:
                pass

        return cls(
            recommendations=list(data.get("recommendations", [])),
            proposed_fhir_actions=parsed_actions,
            epistemic_confidence=float(data.get("epistemic_confidence", 1.0)),
            agent_name=data.get("agent_name"),
            reasoning=data.get("reasoning"),
            metadata=dict(data.get("metadata", {})),
            timestamp=ts,
        )
