"""Tests for Level 12 Bi-Temporal Event-Sourced Clinical History & Time-Travel OS.

Verifies:
1. ISO/IEC 9075:2011 Bi-Temporal clinical modeling separating Valid Time from Transaction Time.
2. Resolving the 'retroactive knowledge' paradox in medical audits and legal discovery.
3. CQRS event sourcing with deterministic state projection and fold reducer.
4. Lamport Vector Clocks and causal ordering across distributed clinical nodes.
5. Cryptographic SHA-256 event hash chain integrity and tamper detection.
6. Structured clinical intent, diagnostic evidence linkage, and Four-Eye dual-clinician quorum sign-offs.
7. Temporal differential engine computing structural deltas and shift handoff summaries.
8. FastAPI /v1/history HTTP API integration.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from backend.history.bitemporal_engine import (
    BiTemporalEngine,
)
from backend.history.clinical_event_store import (
    ClinicalEventStore,
    EventType,
    LamportVectorClock,
)
from backend.history.clinical_intent_tracker import (
    ClinicalIntentCategory,
    ClinicalIntentTracker,
)
from backend.history.temporal_diff_engine import (
    diff_patient_states,
)
from backend.main import app
from backend.routes.history_routes import (
    bitemporal_engine as route_bitemporal_engine,
)
from backend.routes.history_routes import (
    event_store as route_event_store,
)
from backend.routes.history_routes import (
    intent_tracker as route_intent_tracker,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_history_stores():
    """Ensure clean state across test runs."""
    route_event_store.clear()
    route_bitemporal_engine.clear()
    route_intent_tracker.clear()
    yield
    route_event_store.clear()
    route_bitemporal_engine.clear()
    route_intent_tracker.clear()


# =========================================================================
# 1. Bi-Temporal Clinical Modeling & Retroactive Knowledge Paradox Tests
# =========================================================================

def test_bitemporal_retroactive_knowledge_paradox():
    """Verify that Valid Time (clinical reality) and Transaction Time (EHR awareness)

    accurately distinguish what was true in the patient vs what was known to clinicians.
    Scenario:
    - 08:00 (T1): Blood drawn from patient showing critical hyperkalemia (K+ = 6.2).
    - 10:00 (T2): Attending physician rounds and checks chart. Lab is still pending.
    - 14:00 (T3): Lab completes analysis and enters result into EHR.
    - 15:00 (T4): Retrospective medical review queries what was known at T2.
    """
    engine = BiTemporalEngine()
    t1 = datetime.datetime(2026, 6, 1, 8, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc)
    t3 = datetime.datetime(2026, 6, 1, 14, 0, tzinfo=datetime.timezone.utc)
    t4 = datetime.datetime(2026, 6, 1, 15, 0, tzinfo=datetime.timezone.utc)

    # Insert record: Valid from 08:00 (T1), but Transaction time is 14:00 (T3)
    engine.insert(
        entity_type="lab",
        entity_id="LAB-K-001",
        patient_id="PT-901",
        valid_from=t1,
        valid_to=None,
        payload={"test": "Potassium", "value": 6.2, "unit": "mmol/L", "flag": "CRITICAL_HIGH"},
        transaction_time=t3,
    )

    # Query 1: As of 10:00 (T2) clinical reality, based on system knowledge at 10:00 (T2)
    # The clinician at 10:00 DID NOT KNOW the hyperkalemia result because it was recorded at 14:00.
    known_at_t2 = engine.query_as_of(
        patient_id="PT-901",
        valid_time=t2,
        transaction_time=t2,
    )
    assert len(known_at_t2) == 0, "EHR should reflect lab was NOT known to clinician at 10:00"

    # Query 2: As of 10:00 (T2) clinical reality, based on system knowledge at 15:00 (T4)
    # In retrospect, we now know that at 10:00 the patient did indeed have hyperkalemia.
    known_retrospectively = engine.query_as_of(
        patient_id="PT-901",
        valid_time=t2,
        transaction_time=t4,
    )
    assert len(known_retrospectively) == 1
    assert known_retrospectively[0].payload["value"] == 6.2


def test_bitemporal_correction_and_revocation():
    """Verify that corrections close the transaction window on old records rather than deleting them."""
    engine = BiTemporalEngine()
    t_start = datetime.datetime(2026, 5, 1, 12, 0, tzinfo=datetime.timezone.utc)
    t_corr = datetime.datetime(2026, 5, 2, 9, 0, tzinfo=datetime.timezone.utc)

    # Initial assertion: Dose 100mg
    engine.insert(
        entity_type="medication",
        entity_id="MED-WARFARIN",
        patient_id="PT-100",
        valid_from=t_start,
        valid_to=None,
        payload={"drug": "Warfarin", "dose": 100, "unit": "mg"},
        transaction_time=t_start,
    )

    # Transcription correction: It was actually 10mg, corrected the next day
    old_rec, new_rec = engine.correct(
        entity_type="medication",
        entity_id="MED-WARFARIN",
        patient_id="PT-100",
        new_valid_from=t_start,
        new_valid_to=None,
        new_payload={"drug": "Warfarin", "dose": 10, "unit": "mg"},
        transaction_time=t_corr,
    )

    assert old_rec is not None
    assert old_rec.transaction_to is not None
    assert new_rec.payload["dose"] == 10

    # Complete audit trail shows both the historic mistake and the correction
    audit = engine.query_entity_audit(patient_id="PT-100", entity_id="MED-WARFARIN")
    assert len(audit) == 2


# =========================================================================
# 2. CQRS Event Sourcing & Deterministic Projections
# =========================================================================

def test_clinical_event_store_projection_fold():
    """Verify deterministic mathematical fold projection from an immutable event stream."""
    store = ClinicalEventStore(default_node_id="icu_cluster_01")
    t0 = datetime.datetime(2026, 7, 10, 8, 0, tzinfo=datetime.timezone.utc)
    t1 = datetime.datetime(2026, 7, 10, 9, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 7, 10, 10, 0, tzinfo=datetime.timezone.utc)
    t3 = datetime.datetime(2026, 7, 10, 11, 0, tzinfo=datetime.timezone.utc)

    # Event 1: Patient Admitted
    store.append(
        patient_id="PT-500",
        event_type=EventType.PATIENT_ADMITTED,
        payload={"unit": "NEURO_ICU", "attending_id": "DR-HOUSE"},
        timestamp=t0,
        valid_time=t0,
    )

    # Event 2: Condition Diagnosed
    store.append(
        patient_id="PT-500",
        event_type=EventType.CONDITION_DIAGNOSED,
        payload={"code": "I63.9", "name": "Ischemic Stroke", "severity": "SEVERE"},
        timestamp=t1,
        valid_time=t1,
    )

    # Event 3: Medication Prescribed
    store.append(
        patient_id="PT-500",
        event_type=EventType.MEDICATION_PRESCRIBED,
        payload={"name": "Alteplase", "dose": 0.9, "unit": "mg/kg", "route": "IV"},
        timestamp=t2,
        valid_time=t2,
    )

    # Event 4: Dose Adjusted
    store.append(
        patient_id="PT-500",
        event_type=EventType.DOSAGE_ADJUSTED,
        payload={"name": "Alteplase", "new_dose": 0.45, "reason": "Partial infusion completed"},
        timestamp=t3,
        valid_time=t3,
    )

    # Time-travel projection at t1 (before medication)
    chart_t1 = store.project_patient_chart(patient_id="PT-500", as_of_time=t1)
    assert chart_t1["admitted"] is True
    assert "I63.9" in chart_t1["conditions"]
    assert len(chart_t1["medications"]) == 0
    assert chart_t1["event_count"] == 2

    # Final projection at t3
    chart_final = store.project_patient_chart(patient_id="PT-500", as_of_time=t3)
    assert len(chart_final["medications"]) == 1
    alteplase = chart_final["medications"]["Alteplase"]
    assert alteplase["dose"] == 0.45
    assert len(alteplase["adjustments"]) == 1


def test_lamport_vector_clock_causality():
    """Verify Lamport vector clocks establish unambiguous happens-before ordering across distributed nodes."""
    ambulance_clock = LamportVectorClock("ambulance_unit_4")
    hospital_clock = LamportVectorClock("hospital_ed_node")

    # Ambulance records vitals en route
    c1 = ambulance_clock.tick()
    assert c1["ambulance_unit_4"] == 1

    c2 = ambulance_clock.tick()
    assert c2["ambulance_unit_4"] == 2

    # Hospital receives ambulance telemetry and merges
    c3 = hospital_clock.merge(c2)
    assert c3["ambulance_unit_4"] == 2
    assert c3["hospital_ed_node"] == 1

    # Causality verification: c1 and c2 strictly happened before c3
    assert LamportVectorClock.is_causally_before(c1, c3) is True
    assert LamportVectorClock.is_causally_before(c2, c3) is True
    assert LamportVectorClock.is_causally_before(c3, c1) is False


def test_cryptographic_hash_chain_tamper_detection():
    """Verify SHA-256 event chaining detects unauthorized tampering with historic clinical facts."""
    store = ClinicalEventStore()
    store.append("PT-777", EventType.ALLERGY_FLAGGED, {"allergen": "Penicillin", "reaction": "ANAPHYLAXIS"})
    store.append("PT-777", EventType.VITAL_RECORDED, {"type": "HEART_RATE", "value": 88, "unit": "bpm"})

    assert store.verify_event_chain("PT-777") is True

    # Malicious or accidental in-place mutation of first event's allergen payload
    store._events["PT-777"][0].payload["allergen"] = "Amoxicillin"

    # Integrity verification must immediately detect the hash mismatch
    assert store.verify_event_chain("PT-777") is False


# =========================================================================
# 3. Structured Clinical Intent & Quorum Attribution Tests
# =========================================================================

def test_clinical_intent_and_four_eye_quorum():
    """Verify structured clinical intent tracking, evidence linkages, and Four-Eye dual signoff."""
    tracker = ClinicalIntentTracker()

    # Record high-risk drug interaction override
    intent = tracker.record_intent(
        patient_id="PT-202",
        category=ClinicalIntentCategory.DRUG_INTERACTION_OVERRIDE,
        rationale="Benefits of Amiodarone with Warfarin outweigh bleeding risk under strict INR monitoring",
        clinician_id="DR-CARTER",
        clinician_name="Dr. John Carter",
        role="ATTENDING_CARDIOLOGIST",
        evidence=[
            {"evidence_type": "LAB_SPECIMEN", "evidence_id": "INR-992", "description": "Baseline INR 2.1"},
            {"evidence_type": "NOTE", "evidence_id": "NOTE-401", "description": "Cardiology consult agreement"},
        ],
    )

    assert intent.is_quorum_verified is False, "High-risk category requires dual signoff"
    assert len(intent.evidence_links) == 2

    # Prevent primary clinician from countersigning their own order
    with pytest.raises(ValueError, match="Countersignature cannot be performed by the primary clinician"):
        tracker.add_countersignature(
            intent_id=intent.intent_id,
            clinician_id="DR-CARTER",
            clinician_name="Dr. John Carter",
            role="ATTENDING_CARDIOLOGIST",
        )

    # Countersignature by Clinical Pharmacist satisfies quorum
    tracker.add_countersignature(
        intent_id=intent.intent_id,
        clinician_id="PHARM-WEAVER",
        clinician_name="Kerry Weaver, PharmD",
        role="CLINICAL_PHARMACIST",
    )

    assert intent.is_quorum_verified is True
    assert len(intent.countersignatures) == 1
    assert intent.countersignatures[0].clinician_id == "PHARM-WEAVER"


# =========================================================================
# 4. Temporal Differential Engine Tests
# =========================================================================

def test_temporal_differential_engine():
    """Verify structural delta calculation between two patient states."""
    state_t1: Dict[str, Any] = {
        "conditions": {
            "E11.9": {"code": "E11.9", "name": "Type 2 Diabetes", "severity": "MILD", "status": "ACTIVE"},
        },
        "medications": {
            "Metformin": {"name": "Metformin", "dose": 500, "unit": "mg", "status": "ACTIVE"},
        },
        "allergies": {
            "Sulfa": {"allergen": "Sulfa", "reaction": "Rash", "status": "ACTIVE"},
        },
        "labs": {},
        "vitals": [{"vital_type": "HR", "value": 72, "unit": "bpm"}],
    }

    state_t2: Dict[str, Any] = {
        "conditions": {
            "E11.9": {"code": "E11.9", "name": "Type 2 Diabetes", "severity": "MILD", "status": "ACTIVE"},
            "I10": {"code": "I10", "name": "Essential Hypertension", "severity": "MODERATE", "status": "ACTIVE"},
        },
        "medications": {
            "Metformin": {"name": "Metformin", "dose": 1000, "unit": "mg", "status": "ACTIVE"},
            "Lisinopril": {"name": "Lisinopril", "dose": 10, "unit": "mg", "status": "ACTIVE"},
        },
        "allergies": {
            "Sulfa": {"allergen": "Sulfa", "reaction": "Rash", "status": "REVOKED"},
        },
        "labs": {
            "HbA1c": {"test_name": "HbA1c", "value": 7.4, "unit": "%", "flag": "HIGH"},
        },
        "vitals": [
            {"vital_type": "HR", "value": 72, "unit": "bpm"},
            {"vital_type": "BP", "value": "140/90", "unit": "mmHg"},
        ],
    }

    diff = diff_patient_states(state_t1, state_t2)

    assert len(diff["added"]["conditions"]) == 1
    assert diff["added"]["conditions"][0]["code"] == "I10"

    assert len(diff["added"]["medications"]) == 1
    assert diff["added"]["medications"][0]["name"] == "Lisinopril"

    assert len(diff["modified"]["medications"]) == 1
    assert diff["modified"]["medications"][0]["from_dose"] == 500
    assert diff["modified"]["medications"][0]["to_dose"] == 1000

    assert len(diff["resolved_or_revoked"]["allergies"]) == 1
    assert diff["resolved_or_revoked"]["allergies"][0]["allergen"] == "Sulfa"

    assert len(diff["added"]["labs"]) == 1
    assert diff["new_vitals_count"] == 1
    assert len(diff["clinical_narrative"]) >= 5


# =========================================================================
# 5. FastAPI /v1/history Endpoints Integration Tests
# =========================================================================

def test_api_history_health(client: TestClient):
    """Verify /v1/history/health operational check."""
    resp = client.get("/v1/history/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["engine"] == "BI_TEMPORAL_EVENT_SOURCED_TIME_TRAVEL_OS"


def test_api_event_append_and_projection(client: TestClient):
    """Verify appending events and retrieving as-of chart projections over HTTP."""
    # Append Admission
    r1 = client.post(
        "/v1/history/events/append",
        json={
            "patient_id": "PT-HTTP-01",
            "event_type": "PatientAdmitted",
            "payload": {"unit": "CARDIAC_ICU", "attending_id": "DR-SMITH"},
            "valid_time": "2026-08-01T08:00:00Z",
        },
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "EVENT_COMMITTED"

    # Append Diagnosis
    r2 = client.post(
        "/v1/history/events/append",
        json={
            "patient_id": "PT-HTTP-01",
            "event_type": "ConditionDiagnosed",
            "payload": {"code": "I21.0", "name": "STEMI", "severity": "CRITICAL"},
            "valid_time": "2026-08-01T08:30:00Z",
        },
    )
    assert r2.status_code == 200

    # Query As-Of Projection
    r3 = client.get("/v1/history/patient/PT-HTTP-01/as-of")
    assert r3.status_code == 200
    chart = r3.json()
    assert chart["patient_id"] == "PT-HTTP-01"
    assert chart["admitted"] is True
    assert "I21.0" in chart["conditions"]
    assert chart["chain_verified"] is True

    # Query Timeline
    r4 = client.get("/v1/history/patient/PT-HTTP-01/timeline")
    assert r4.status_code == 200
    assert len(r4.json()) == 2


def test_api_bitemporal_insert_and_query(client: TestClient):
    """Verify bi-temporal insertion and as-of queries over HTTP."""
    # Insert diagnosis known at 12:00 but clinically valid from 06:00
    r1 = client.post(
        "/v1/history/bitemporal/insert",
        json={
            "entity_type": "diagnosis",
            "entity_id": "DX-PNEUMO",
            "patient_id": "PT-BITEMP-99",
            "valid_from": "2026-09-01T06:00:00Z",
            "payload": {"name": "Pneumonia", "icd": "J18.9"},
            "transaction_time": "2026-09-01T12:00:00Z",
        },
    )
    assert r1.status_code == 200

    # Query as of 08:00 with transaction time 10:00 (should return empty because entered at 12:00)
    r2 = client.post(
        "/v1/history/bitemporal/query?patient_id=PT-BITEMP-99",
        json={
            "valid_time": "2026-09-01T08:00:00Z",
            "transaction_time": "2026-09-01T10:00:00Z",
        },
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 0

    # Query as of 08:00 with transaction time 13:00 (should return the diagnosis)
    r3 = client.post(
        "/v1/history/bitemporal/query?patient_id=PT-BITEMP-99",
        json={
            "valid_time": "2026-09-01T08:00:00Z",
            "transaction_time": "2026-09-01T13:00:00Z",
        },
    )
    assert r3.status_code == 200
    assert len(r3.json()) == 1
    assert r3.json()[0]["payload"]["name"] == "Pneumonia"


def test_api_clinical_intent_and_countersign(client: TestClient):
    """Verify recording and countersigning clinical intent over HTTP."""
    # Record intent
    r1 = client.post(
        "/v1/history/intents",
        json={
            "patient_id": "PT-INT-55",
            "category": "PHARMACOGENOMIC_GUIDELINE",
            "rationale": "Abacavir contraindicated due to HLA-B*5701 positivity",
            "clinician_id": "DR-FAUCI",
            "clinician_name": "Dr. Anthony Fauci",
            "role": "INFECTIOUS_DISEASE_SPECIALIST",
            "evidence": [{"evidence_type": "GENOMIC_VARIANT", "evidence_id": "HLA-B*5701", "description": "Positive"}],
        },
    )
    assert r1.status_code == 200
    intent_data = r1.json()
    assert intent_data["is_quorum_verified"] is False
    intent_id = intent_data["intent_id"]

    # Countersign
    r2 = client.post(
        f"/v1/history/intents/{intent_id}/countersign",
        json={
            "clinician_id": "PHARM-CHEN",
            "clinician_name": "Dr. Lucy Chen",
            "role": "PHARMACOGENOMICS_PHARMACIST",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["is_quorum_verified"] is True
    assert len(r2.json()["countersignatures"]) == 1

    # Fetch patient intents
    r3 = client.get("/v1/history/patient/PT-INT-55/intents")
    assert r3.status_code == 200
    assert len(r3.json()) == 1


def test_api_temporal_diff_endpoint(client: TestClient):
    """Verify the /patient/{id}/diff endpoint computes differential between events."""
    # Seed two events with different timestamps
    client.post(
        "/v1/history/events/append",
        json={
            "patient_id": "PT-DIFF-88",
            "event_type": "MedicationPrescribed",
            "payload": {"name": "Aspirin", "dose": 81, "unit": "mg"},
            "timestamp": "2026-09-05T08:00:00Z",
            "valid_time": "2026-09-05T08:00:00Z",
        },
    )
    client.post(
        "/v1/history/events/append",
        json={
            "patient_id": "PT-DIFF-88",
            "event_type": "MedicationPrescribed",
            "payload": {"name": "Clopidogrel", "dose": 75, "unit": "mg"},
            "timestamp": "2026-09-05T12:00:00Z",
            "valid_time": "2026-09-05T12:00:00Z",
        },
    )

    diff_resp = client.post(
        "/v1/history/patient/PT-DIFF-88/diff",
        json={
            "t1": "2026-09-05T09:00:00Z",
            "t2": "2026-09-05T13:00:00Z",
        },
    )
    assert diff_resp.status_code == 200
    d = diff_resp.json()
    assert d["patient_id"] == "PT-DIFF-88"
    assert len(d["added"]["medications"]) == 1
    assert d["added"]["medications"][0]["name"] == "Clopidogrel"
    assert len(d["clinical_narrative"]) >= 1
