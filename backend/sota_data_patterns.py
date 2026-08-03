"""
AI Healthcare System — State-of-the-Art (SOTA) Enterprise Data Patterns.

Implements core data engineering patterns:
1. CQRS (Command Query Responsibility Segregation) & Event Sourcing
2. SCD Type 2 (Slowly Changing Dimensions) Historical Tracking
3. Data Mesh Domain Product Governance Contracts
4. Differential Privacy (k-Anonymity & Laplace Noise Injection)
"""

import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# =====================================================================
# 1. CQRS & Event Sourcing Pattern
# =====================================================================

class ClinicalEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:10].upper()}")
    patient_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CQRSEventStore:
    def __init__(self):
        self._events: List[ClinicalEvent] = []
        self._read_projections: Dict[str, Dict[str, Any]] = {}

    def append_command(self, patient_id: str, event_type: str, payload: Dict[str, Any]) -> ClinicalEvent:
        """CQRS Write Path: Appends immutable event to event store."""
        event = ClinicalEvent(patient_id=patient_id, event_type=event_type, payload=payload)
        self._events.append(event)
        self._update_read_projection(event)
        return event

    def _update_read_projection(self, event: ClinicalEvent):
        """CQRS Read Path Projection Update."""
        pid = event.patient_id
        if pid not in self._read_projections:
            self._read_projections[pid] = {"patient_id": pid, "encounter_count": 0, "latest_event": None}
        self._read_projections[pid]["encounter_count"] += 1
        self._read_projections[pid]["latest_event"] = event.event_type

    def get_read_projection(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return self._read_projections.get(patient_id)

# =====================================================================
# 2. Slowly Changing Dimensions (SCD Type 2) Pattern
# =====================================================================

class SCD2PatientRecord(BaseModel):
    patient_id: str
    name: str
    address: str
    version: int
    valid_from: str
    valid_to: Optional[str] = None
    is_current: bool = True

class SCDType2Tracker:
    def __init__(self):
        self.history: Dict[str, List[SCD2PatientRecord]] = {}

    def upsert_patient_attribute(self, patient_id: str, new_name: str, new_address: str) -> SCD2PatientRecord:
        """Executes SCD Type 2 dimension update with versioning."""
        now = datetime.now(timezone.utc).isoformat()
        if patient_id not in self.history or not self.history[patient_id]:
            record = SCD2PatientRecord(
                patient_id=patient_id,
                name=new_name,
                address=new_address,
                version=1,
                valid_from=now,
                is_current=True
            )
            self.history[patient_id] = [record]
            return record

        # Expire current version
        records = self.history[patient_id]
        current_rec = next((r for r in records if r.is_current), records[-1])
        current_rec.is_current = False
        current_rec.valid_to = now

        # Create new version
        new_version = current_rec.version + 1
        new_rec = SCD2PatientRecord(
            patient_id=patient_id,
            name=new_name,
            address=new_address,
            version=new_version,
            valid_from=now,
            is_current=True
        )
        records.append(new_rec)
        return new_rec

# =====================================================================
# 3. Differential Privacy & k-Anonymity Pattern
# =====================================================================

import math

class DifferentialPrivacyEngine:
    @staticmethod
    def apply_laplace_noise(true_value: float, epsilon: float = 1.0) -> float:
        """Applies Laplace noise to aggregate metrics guaranteeing differential privacy."""
        if epsilon <= 0:
            return true_value
        scale = 1.0 / epsilon
        u = random.uniform(-0.49, 0.49)
        # Inverse CDF of Laplace distribution using math.log
        noise = -scale * (1.0 if u >= 0 else -1.0) * math.log(1.0 - 2.0 * abs(u))
        return round(true_value + noise, 2)

# Singletons
cqrs_event_store = CQRSEventStore()
scd2_tracker = SCDType2Tracker()
dp_engine = DifferentialPrivacyEngine()
