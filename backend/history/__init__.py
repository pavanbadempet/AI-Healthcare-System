"""Level 12 Bi-Temporal Event-Sourced Clinical History & Time-Travel OS.

Exposes:
- BiTemporalEngine: ISO/IEC 9075:2011 dual-time clinical reality vs system knowledge.
- ClinicalEventStore: CQRS event sourcing with Lamport vector clocks & hash chaining.
- ClinicalIntentTracker: Semantic attribution, diagnostic evidence linkage, & Four-Eye quorum.
- TemporalDiffEngine: Clinical state differential engine & shift handoff generator.
"""

from backend.history.bitemporal_engine import (
    BiTemporalEngine,
    BiTemporalRecord,
)
from backend.history.clinical_event_store import (
    ClinicalDomainEvent,
    ClinicalEventStore,
    EventType,
    LamportVectorClock,
)
from backend.history.clinical_intent_tracker import (
    ClinicalIntentCategory,
    ClinicalIntentRecord,
    ClinicalIntentTracker,
    ClinicianSignature,
    EvidenceLink,
)
from backend.history.temporal_diff_engine import (
    TemporalDiffEngine,
    diff_patient_states,
)

__all__ = [
    "BiTemporalEngine",
    "BiTemporalRecord",
    "ClinicalDomainEvent",
    "ClinicalEventStore",
    "EventType",
    "LamportVectorClock",
    "ClinicalIntentCategory",
    "ClinicalIntentRecord",
    "ClinicalIntentTracker",
    "ClinicianSignature",
    "EvidenceLink",
    "TemporalDiffEngine",
    "diff_patient_states",
]
