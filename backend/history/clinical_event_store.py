"""Immutable Event-Sourced Clinical Store (CQRS).

Patient charts are never mutated in place. State is a deterministic mathematical
fold projection over an append-only, cryptographically chained sequence of strongly
typed clinical domain events with Lamport Vector Clocks for causal ordering.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """Strongly typed clinical domain events."""

    PATIENT_ADMITTED = "PatientAdmitted"
    CONDITION_DIAGNOSED = "ConditionDiagnosed"
    CONDITION_RESOLVED = "ConditionResolved"
    MEDICATION_PRESCRIBED = "MedicationPrescribed"
    DOSAGE_ADJUSTED = "DosageAdjusted"
    MEDICATION_DISCONTINUED = "MedicationDiscontinued"
    VITAL_RECORDED = "VitalRecorded"
    ALLERGY_FLAGGED = "AllergyFlagged"
    ALLERGY_REVOKED = "AllergyRevoked"
    LAB_RESULT_RECORDED = "LabResultRecorded"


class LamportVectorClock:
    """Lamport Vector Clock ensuring causal order across distributed clinical nodes.

    Prevents wall-clock skew anomalies between ambulances, telemetry nodes, and hospital servers.
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._clock: Dict[str, int] = {node_id: 0}

    def tick(self) -> Dict[str, int]:
        """Increment local logical clock."""
        self._clock[self.node_id] = self._clock.get(self.node_id, 0) + 1
        return dict(self._clock)

    def merge(self, other_clock: Dict[str, int]) -> Dict[str, int]:
        """Merge another node's vector clock and tick local."""
        for node, val in other_clock.items():
            self._clock[node] = max(self._clock.get(node, 0), val)
        self._clock[self.node_id] = self._clock.get(self.node_id, 0) + 1
        return dict(self._clock)

    @property
    def clock(self) -> Dict[str, int]:
        return dict(self._clock)

    @staticmethod
    def is_causally_before(a: Dict[str, int], b: Dict[str, int]) -> bool:
        """Return True if vector clock A strictly happened-before vector clock B."""
        all_less_or_equal = True
        at_least_one_less = False
        all_nodes = set(a.keys()).union(set(b.keys()))

        for node in all_nodes:
            va = a.get(node, 0)
            vb = b.get(node, 0)
            if va > vb:
                return False
            if va < vb:
                at_least_one_less = True

        return all_less_or_equal and at_least_one_less


class ClinicalDomainEvent:
    """Immutable domain event recorded in the clinical event stream."""

    def __init__(
        self,
        event_id: str,
        patient_id: str,
        event_type: EventType | str,
        timestamp: datetime.datetime,
        valid_time: datetime.datetime,
        node_id: str,
        vector_clock: Dict[str, int],
        causal_sequence: int,
        payload: Dict[str, Any],
        intent_id: Optional[str] = None,
        prev_hash: Optional[str] = None,
        event_hash: Optional[str] = None,
    ) -> None:
        self.event_id = event_id
        self.patient_id = patient_id
        self.event_type = EventType(event_type) if isinstance(event_type, str) else event_type
        self.timestamp = timestamp
        self.valid_time = valid_time
        self.node_id = node_id
        self.vector_clock = vector_clock
        self.causal_sequence = causal_sequence
        self.payload = payload
        self.intent_id = intent_id
        self.prev_hash = prev_hash
        self.event_hash = event_hash or self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA-256 hash chaining over prior event hash and canonical payload."""
        content = {
            "prev_hash": self.prev_hash or "GENESIS",
            "event_id": self.event_id,
            "patient_id": self.patient_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "valid_time": self.valid_time.isoformat(),
            "node_id": self.node_id,
            "vector_clock": self.vector_clock,
            "causal_sequence": self.causal_sequence,
            "payload": self.payload,
            "intent_id": self.intent_id,
        }
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary representation."""
        return {
            "event_id": self.event_id,
            "patient_id": self.patient_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "valid_time": self.valid_time.isoformat(),
            "node_id": self.node_id,
            "vector_clock": self.vector_clock,
            "causal_sequence": self.causal_sequence,
            "payload": self.payload,
            "intent_id": self.intent_id,
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
        }


class ClinicalEventStore:
    """Append-only, cryptographically verified Event Store for patient state projection."""

    def __init__(self, default_node_id: str = "core_node_1") -> None:
        self.default_node_id = default_node_id
        self._events: Dict[str, List[ClinicalDomainEvent]] = {}  # patient_id -> list
        self._vector_clocks: Dict[str, LamportVectorClock] = {}  # node_id -> clock
        self._global_sequence = 0

    def _get_clock(self, node_id: str) -> LamportVectorClock:
        if node_id not in self._vector_clocks:
            self._vector_clocks[node_id] = LamportVectorClock(node_id)
        return self._vector_clocks[node_id]

    def append(
        self,
        patient_id: str,
        event_type: EventType | str,
        payload: Dict[str, Any],
        valid_time: Optional[datetime.datetime] = None,
        node_id: Optional[str] = None,
        intent_id: Optional[str] = None,
        timestamp: Optional[datetime.datetime] = None,
        incoming_clock: Optional[Dict[str, int]] = None,
    ) -> ClinicalDomainEvent:
        """Append an immutable clinical domain event to the patient's event stream."""
        node = node_id or self.default_node_id
        clock_mgr = self._get_clock(node)

        if incoming_clock:
            v_clock = clock_mgr.merge(incoming_clock)
        else:
            v_clock = clock_mgr.tick()

        self._global_sequence += 1
        t_now = timestamp or datetime.datetime.now(datetime.timezone.utc)
        v_time = valid_time or t_now

        patient_stream = self._events.setdefault(patient_id, [])
        prev_hash = patient_stream[-1].event_hash if patient_stream else "GENESIS"

        event = ClinicalDomainEvent(
            event_id=str(uuid.uuid4()),
            patient_id=patient_id,
            event_type=event_type,
            timestamp=t_now,
            valid_time=v_time,
            node_id=node,
            vector_clock=v_clock,
            causal_sequence=self._global_sequence,
            payload=payload,
            intent_id=intent_id,
            prev_hash=prev_hash,
        )

        patient_stream.append(event)
        return event

    def get_events(
        self,
        patient_id: str,
        as_of_time: Optional[datetime.datetime] = None,
        by_valid_time: bool = False,
    ) -> List[ClinicalDomainEvent]:
        """Retrieve chronological event stream for a patient, optionally filtering as-of time."""
        stream = self._events.get(patient_id, [])
        if not as_of_time:
            return list(stream)

        cutoff = as_of_time.astimezone(datetime.timezone.utc).replace(tzinfo=None) if as_of_time.tzinfo else as_of_time
        filtered: List[ClinicalDomainEvent] = []

        for ev in stream:
            target_time = ev.valid_time if by_valid_time else ev.timestamp
            t_norm = target_time.astimezone(datetime.timezone.utc).replace(tzinfo=None) if target_time.tzinfo else target_time
            if t_norm <= cutoff:
                filtered.append(ev)

        return filtered

    def verify_event_chain(self, patient_id: str) -> bool:
        """Verify the cryptographic integrity of the patient's event hash chain."""
        stream = self._events.get(patient_id, [])
        if not stream:
            return True

        expected_prev = "GENESIS"
        for ev in stream:
            if ev.prev_hash != expected_prev:
                return False
            if ev.event_hash != ev.compute_hash():
                return False
            expected_prev = ev.event_hash

        return True

    def project_patient_chart(
        self,
        patient_id: str,
        as_of_time: Optional[datetime.datetime] = None,
        by_valid_time: bool = False,
    ) -> Dict[str, Any]:
        """Deterministic mathematical fold projection: State(T) = fold(Initial, Events[0..T])."""
        events = self.get_events(patient_id, as_of_time=as_of_time, by_valid_time=by_valid_time)

        # Initial state baseline
        chart: Dict[str, Any] = {
            "patient_id": patient_id,
            "admitted": False,
            "admission": None,
            "conditions": {},
            "medications": {},
            "vitals": [],
            "allergies": {},
            "labs": {},
            "event_count": len(events),
            "as_of_time": as_of_time.isoformat() if as_of_time else None,
            "last_event_hash": events[-1].event_hash if events else None,
        }

        for ev in events:
            ev_type = ev.event_type
            p = ev.payload

            if ev_type == EventType.PATIENT_ADMITTED:
                chart["admitted"] = True
                chart["admission"] = {
                    "admitted_at": ev.valid_time.isoformat(),
                    "unit": p.get("unit", "GENERAL_WARD"),
                    "attending_id": p.get("attending_id"),
                }

            elif ev_type == EventType.CONDITION_DIAGNOSED:
                code = p.get("code", str(uuid.uuid4()))
                chart["conditions"][code] = {
                    "code": code,
                    "name": p.get("name", "Unknown Condition"),
                    "severity": p.get("severity", "MODERATE"),
                    "status": "ACTIVE",
                    "diagnosed_at": ev.valid_time.isoformat(),
                    "intent_id": ev.intent_id,
                }

            elif ev_type == EventType.CONDITION_RESOLVED:
                code = p.get("code")
                if code and code in chart["conditions"]:
                    chart["conditions"][code]["status"] = "RESOLVED"
                    chart["conditions"][code]["resolved_at"] = ev.valid_time.isoformat()

            elif ev_type == EventType.MEDICATION_PRESCRIBED:
                med_id = p.get("medication_id", p.get("name", str(uuid.uuid4())))
                chart["medications"][med_id] = {
                    "medication_id": med_id,
                    "name": p.get("name", "Unknown Medication"),
                    "dose": p.get("dose"),
                    "unit": p.get("unit", "mg"),
                    "route": p.get("route", "ORAL"),
                    "frequency": p.get("frequency", "DAILY"),
                    "status": "ACTIVE",
                    "prescribed_at": ev.valid_time.isoformat(),
                    "intent_id": ev.intent_id,
                    "adjustments": [],
                }

            elif ev_type == EventType.DOSAGE_ADJUSTED:
                med_id = p.get("medication_id", p.get("name"))
                if med_id and med_id in chart["medications"]:
                    med = chart["medications"][med_id]
                    med["adjustments"].append({
                        "previous_dose": med["dose"],
                        "new_dose": p.get("new_dose"),
                        "adjusted_at": ev.valid_time.isoformat(),
                        "intent_id": ev.intent_id,
                        "reason": p.get("reason"),
                    })
                    med["dose"] = p.get("new_dose")

            elif ev_type == EventType.MEDICATION_DISCONTINUED:
                med_id = p.get("medication_id", p.get("name"))
                if med_id and med_id in chart["medications"]:
                    chart["medications"][med_id]["status"] = "DISCONTINUED"
                    chart["medications"][med_id]["discontinued_at"] = ev.valid_time.isoformat()
                    chart["medications"][med_id]["discontinue_reason"] = p.get("reason")

            elif ev_type == EventType.VITAL_RECORDED:
                chart["vitals"].append({
                    "vital_type": p.get("type"),
                    "value": p.get("value"),
                    "unit": p.get("unit"),
                    "recorded_at": ev.valid_time.isoformat(),
                    "device_id": p.get("device_id", ev.node_id),
                })

            elif ev_type == EventType.ALLERGY_FLAGGED:
                allergen = p.get("allergen", "Unknown")
                chart["allergies"][allergen] = {
                    "allergen": allergen,
                    "severity": p.get("severity", "MODERATE"),
                    "reaction": p.get("reaction", "RASH"),
                    "status": "ACTIVE",
                    "flagged_at": ev.valid_time.isoformat(),
                }

            elif ev_type == EventType.ALLERGY_REVOKED:
                allergen = p.get("allergen")
                if allergen and allergen in chart["allergies"]:
                    chart["allergies"][allergen]["status"] = "REVOKED"
                    chart["allergies"][allergen]["revoked_at"] = ev.valid_time.isoformat()
                    chart["allergies"][allergen]["reason"] = p.get("reason")

            elif ev_type == EventType.LAB_RESULT_RECORDED:
                test_name = p.get("test_name", "Unknown Lab")
                chart["labs"][test_name] = {
                    "test_name": test_name,
                    "value": p.get("value"),
                    "unit": p.get("unit"),
                    "reference_range": p.get("reference_range"),
                    "flag": p.get("flag", "NORMAL"),
                    "resulted_at": ev.valid_time.isoformat(),
                }

        return chart

    def clear(self) -> None:
        """Reset internal store (for testing)."""
        self._events.clear()
        self._vector_clocks.clear()
        self._global_sequence = 0
