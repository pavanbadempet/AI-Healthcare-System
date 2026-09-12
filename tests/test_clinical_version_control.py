"""Tests for Level 13 Clinical Version Control, Care Protocol Branching & Simulation OS.

Verifies:
1. Copy-on-Write (CoW) chart branching, isolated hypothetical simulation, and 3-way merge.
2. 3-way merge conflict detection on concurrent medication modifications.
3. Clinical Care Protocol VCS with SemVer 2.0.0, safety linter, and unit-scoped canary rollouts.
4. Model-Data-Code triad cryptographic lineage, HMAC seals, and inference attestations.
5. Semantic medical ontology deprecation scanning and non-destructive migration patching.
6. FastAPI /v1/versioning endpoints integration.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from backend.history.clinical_event_store import ClinicalEventStore, EventType
from backend.main import app
from backend.routes.history_routes import event_store as route_event_store
from backend.routes.versioning_routes import (
    branch_engine as route_branch_engine,
)
from backend.routes.versioning_routes import (
    ontology_engine as route_ontology_engine,
)
from backend.routes.versioning_routes import (
    protocol_engine as route_protocol_engine,
)
from backend.routes.versioning_routes import (
    triad_registry as route_triad_registry,
)
from backend.versioning.chart_branch_engine import ChartBranchEngine
from backend.versioning.ontology_version_engine import (
    OntologyVersionEngine,
    TerminologySystem,
)
from backend.versioning.protocol_vcs import (
    ClinicalProtocol,
    ProtocolSafetyLinter,
    ProtocolStatus,
    ProtocolStep,
    ProtocolVCSEngine,
    SemanticVersion,
)
from backend.versioning.triad_lineage_registry import (
    ModelDataTriadRegistry,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_versioning_stores():
    """Ensure clean isolated state across tests."""
    route_event_store.clear()
    route_branch_engine.clear()
    route_protocol_engine.clear()
    route_triad_registry.clear()
    route_ontology_engine.clear()
    yield
    route_event_store.clear()
    route_branch_engine.clear()
    route_protocol_engine.clear()
    route_triad_registry.clear()
    route_ontology_engine.clear()


# =========================================================================
# 1. Patient Record Branching & CoW Simulation Tests
# =========================================================================

def test_chart_branching_cow_isolation_and_merge():
    """Verify Copy-on-Write isolation between trunk chart and simulation branch."""
    store = ClinicalEventStore()
    engine = ChartBranchEngine(event_store=store)

    # Seed baseline patient chart in trunk
    store.append(
        patient_id="PT-SIM-01",
        event_type=EventType.PATIENT_ADMITTED,
        payload={"unit": "ONCOLOGY_DAY_WARD", "attending_id": "DR-ONC"},
    )
    store.append(
        patient_id="PT-SIM-01",
        event_type=EventType.CONDITION_DIAGNOSED,
        payload={"code": "C34.90", "name": "Non-Small Cell Lung Cancer", "severity": "STAGE_IV"},
    )

    # Create simulation branch for Regimen A (Immunotherapy)
    branch = engine.create_branch(
        patient_id="PT-SIM-01",
        branch_name="sim-pembrolizumab-chemo",
        author_id="DR-ONC",
        author_name="Dr. Gregory House",
        purpose="Simulate 3-week course of Pembrolizumab plus Carboplatin",
    )

    assert branch.status == "ACTIVE"

    # Mutate branch with hypothetical orders
    engine.mutate_branch(
        branch_id=branch.branch_id,
        event_type=EventType.MEDICATION_PRESCRIBED,
        payload={"name": "Pembrolizumab", "dose": 200, "unit": "mg", "frequency": "Q3W"},
    )
    engine.mutate_branch(
        branch_id=branch.branch_id,
        event_type=EventType.MEDICATION_PRESCRIBED,
        payload={"name": "Carboplatin", "dose": 500, "unit": "mg", "frequency": "CYCLE_DAY_1"},
    )

    # 1. Verify branch state contains simulated medications
    sim_state = engine.get_branch_state(branch.branch_id)
    assert len(sim_state["medications"]) == 2
    assert "Pembrolizumab" in sim_state["medications"]

    # 2. Verify canonical trunk chart remains completely untouched (CoW isolation!)
    trunk_before = store.project_patient_chart("PT-SIM-01")
    assert len(trunk_before["medications"]) == 0

    # 3. Merge branch to trunk with clinical quorum attribution
    merge_res = engine.three_way_merge(
        branch_id=branch.branch_id,
        merging_clinician_id="DR-CUDDY",
        merging_clinician_name="Dr. Lisa Cuddy",
    )

    assert merge_res["success"] is True
    assert merge_res["status"] == "MERGED_TO_TRUNK"
    assert merge_res["applied_events_count"] == 2

    # 4. Canonical trunk now contains the merged chemotherapy orders
    trunk_after = store.project_patient_chart("PT-SIM-01")
    assert len(trunk_after["medications"]) == 2
    assert "Pembrolizumab" in trunk_after["medications"]
    assert branch.status == "MERGED"


def test_three_way_merge_concurrent_conflict_detection():
    """Verify 3-way merge detects concurrent medication modifications between trunk and branch."""
    store = ClinicalEventStore()
    engine = ChartBranchEngine(event_store=store)

    # Base patient setup
    store.append(
        patient_id="PT-CONF-02",
        event_type=EventType.MEDICATION_PRESCRIBED,
        payload={"name": "Warfarin", "dose": 5, "unit": "mg", "status": "ACTIVE"},
    )

    # Fork simulation branch
    branch = engine.create_branch(
        patient_id="PT-CONF-02",
        branch_name="sim-dose-escalation",
        author_id="DR-FELLOW",
        author_name="Dr. Eric Foreman",
        purpose="Simulate dose escalation to 7.5mg",
    )

    # Branch modifies Warfarin to 7.5mg
    engine.mutate_branch(
        branch_id=branch.branch_id,
        event_type=EventType.DOSAGE_ADJUSTED,
        payload={"name": "Warfarin", "new_dose": 7.5},
    )

    # Concurrently in trunk, attending physician independently reduced Warfarin to 2.5mg due to high INR!
    store.append(
        patient_id="PT-CONF-02",
        event_type=EventType.DOSAGE_ADJUSTED,
        payload={"name": "Warfarin", "new_dose": 2.5, "reason": "INR elevated to 3.8"},
    )

    # Attempt merge without override -> Conflict must be detected!
    res = engine.three_way_merge(
        branch_id=branch.branch_id,
        merging_clinician_id="DR-HOUSE",
        merging_clinician_name="Dr. Gregory House",
        allow_conflict_override=False,
    )

    assert res["success"] is False
    assert res["status"] == "MERGE_CONFLICT"
    assert len(res["conflicts"]) == 1
    conflict = res["conflicts"][0]
    assert conflict["entity_id"] == "Warfarin"
    assert conflict["trunk_value"]["dose"] == 2.5
    assert conflict["branch_value"]["dose"] == 7.5

    # With clinician override, merge proceeds
    res_override = engine.three_way_merge(
        branch_id=branch.branch_id,
        merging_clinician_id="DR-HOUSE",
        merging_clinician_name="Dr. Gregory House",
        allow_conflict_override=True,
    )
    assert res_override["success"] is True


# =========================================================================
# 2. Care Protocol & Order Set VCS Tests
# =========================================================================

def test_protocol_semver_lifecycle_and_canary_rollout():
    """Verify SemVer protocol progression, safety linting, and canary unit scoping."""
    engine = ProtocolVCSEngine()

    # Step definition
    steps = [
        {"step_id": "step_1", "name": "Initial Blood Cultures", "action_type": "LAB_DRAW", "parameters": {}},
        {"step_id": "step_2", "name": "Broad-Spectrum Antibiotics", "action_type": "MEDICATION_ORDER", "parameters": {"drug": "Ceftriaxone", "dose": 2, "max_dose": 4, "route": "IV"}},
    ]

    # 1. Create v1.0.0 draft
    proto = engine.create_protocol(
        protocol_id="PROTO-SEPSIS-1HR",
        title="Surviving Sepsis 1-Hour Bundle",
        version_str="1.0.0",
        steps_data=steps,
        author_id="DR-COMMITTEE",
    )
    assert proto.status == ProtocolStatus.DRAFT

    # 2. Transition to STAGED with canary unit
    proto_staged = engine.transition_status(
        protocol_id="PROTO-SEPSIS-1HR",
        version_str="1.0.0",
        target_status=ProtocolStatus.STAGED,
        user_id="DR-CHAIR",
        canary_units=["ED_TRAUMA_BAY"],
    )
    assert proto_staged.status == ProtocolStatus.STAGED

    # In ED_TRAUMA_BAY, the staged canary is active
    eff_canary = engine.resolve_effective_protocol("PROTO-SEPSIS-1HR", unit_name="ED_TRAUMA_BAY")
    assert eff_canary is not None
    assert str(eff_canary.version) == "1.0.0"

    # In GENERAL_MEDICINE, no active protocol exists yet
    eff_gen = engine.resolve_effective_protocol("PROTO-SEPSIS-1HR", unit_name="GENERAL_MEDICINE")
    assert eff_gen is None

    # 3. Promote to hospital-wide ACTIVE
    proto_active = engine.transition_status(
        protocol_id="PROTO-SEPSIS-1HR",
        version_str="1.0.0",
        target_status=ProtocolStatus.ACTIVE,
        user_id="CHIEF-MEDICAL-OFFICER",
    )
    assert proto_active.status == ProtocolStatus.ACTIVE

    # Now active hospital-wide
    eff_hospital = engine.resolve_effective_protocol("PROTO-SEPSIS-1HR", unit_name="GENERAL_MEDICINE")
    assert eff_hospital is not None
    assert str(eff_hospital.version) == "1.0.0"


def test_protocol_safety_linter_rejection():
    """Verify safety linter catches dosage violations and missing administration routes."""
    bad_steps = [
        ProtocolStep(
            step_id="s1",
            name="Acetaminophen Overdose",
            action_type="MEDICATION_ORDER",
            parameters={"drug": "Acetaminophen", "dose": 8000, "max_dose": 4000, "route": "ORAL"},
        ),
        ProtocolStep(
            step_id="s2",
            name="Missing Route Medication",
            action_type="MEDICATION_ORDER",
            parameters={"drug": "Morphine", "dose": 4},
        ),
    ]

    bad_proto = ClinicalProtocol(
        protocol_id="PROTO-DANGEROUS",
        title="Dangerous Order Set",
        version=SemanticVersion(1, 0, 0),
        steps=bad_steps,
        author_id="BAD-INPUT",
    )

    issues = ProtocolSafetyLinter.lint(bad_proto)
    assert len(issues) == 2
    assert "exceeds ceiling max_dose" in issues[0]
    assert "missing administration route" in issues[1]


# =========================================================================
# 3. Model-Data-Code Triad Cryptographic Provenance Tests
# =========================================================================

def test_model_data_triad_and_attestation():
    """Verify cryptographic HMAC lineage registration and inference attestation validation."""
    registry = ModelDataTriadRegistry()

    # Register triad
    triad = registry.register_triad(
        model_id="sepsis_shock_xgb_v3",
        weights_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        dataset_digest="7d1a54127b222502f5b79b5fb0803061152a44f92b37e23c65dd0e336d329aa2",
        code_commit_hash="55b25b16e87fbc",
        framework="XGBoost 2.0.3",
    )

    assert triad.verify_integrity() is True

    # Attest prediction
    att = registry.attest_inference(
        patient_id="PT-AI-99",
        prediction_id="PRED-8801",
        triad_id=triad.triad_id,
        input_features={"lactate": 3.8, "wbc": 14.5, "map": 58},
        output_prediction={"sepsis_risk_percent": 87.4, "tier": "CRITICAL"},
    )

    # Verify provenance certificate
    cert = registry.verify_provenance(att.attestation_id)
    assert cert["valid"] is True
    assert cert["patient_id"] == "PT-AI-99"
    assert cert["triad"]["model_id"] == "sepsis_shock_xgb_v3"

    # Tamper test: Alter prediction payload in attestation
    att.output_prediction["sepsis_risk_percent"] = 12.0  # Fraudulent tampering
    cert_tampered = registry.verify_provenance(att.attestation_id)
    assert cert_tampered["valid"] is False
    assert "mismatch" in cert_tampered["reason"]


# =========================================================================
# 4. Semantic Ontology Deprecation Scanner Tests
# =========================================================================

def test_ontology_deprecation_scanning_and_patching():
    """Verify detection of retired SNOMED/LOINC codes and synthesis of migration patches."""
    engine = OntologyVersionEngine()

    # Patient chart containing retired SNOMED code '59621000'
    chart: Dict[str, Any] = {
        "patient_id": "PT-ONT-01",
        "conditions": {
            "c1": {"code": "59621000", "name": "Essential hypertension", "status": "ACTIVE"},
        },
        "labs": {
            "Serum Sodium": {"code": "2951-2", "value": 140, "unit": "mmol/L"},
        },
    }

    findings = engine.scan_chart_for_deprecations(chart=chart, target_release="2026-06")
    assert len(findings) == 2

    snomed_finding = next(f for f in findings if f.system == TerminologySystem.SNOMED_CT.value)
    assert snomed_finding.obsolete_code == "59621000"
    assert snomed_finding.recommended_code == "38341003"

    # Generate non-destructive migration patch
    patch = engine.generate_migration_patch(chart, findings)
    assert patch["findings_count"] == 2
    assert len(patch["patch_operations"]) == 2
    assert patch["requires_clinician_signoff"] is True


# =========================================================================
# 5. FastAPI /v1/versioning Endpoints Integration Tests
# =========================================================================

def test_api_versioning_health(client: TestClient):
    """Verify /v1/versioning/health endpoint."""
    resp = client.get("/v1/versioning/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["engine"] == "CLINICAL_VCS_SIMULATION_OS"


def test_api_branch_lifecycle_http(client: TestClient):
    """Verify creating, mutating, querying, and merging branches over HTTP."""
    # Seed baseline patient
    client.post(
        "/v1/history/events/append",
        json={
            "patient_id": "PT-HTTP-VCS-1",
            "event_type": "PatientAdmitted",
            "payload": {"unit": "ICU_STEPDOWN"},
        },
    )

    # 1. Create branch
    r1 = client.post(
        "/v1/versioning/branches/create",
        json={
            "patient_id": "PT-HTTP-VCS-1",
            "branch_name": "sim-anticoagulation",
            "author_id": "DR-HTTP",
            "author_name": "Dr. Allison Cameron",
            "purpose": "Simulate Enoxaparin bridging",
        },
    )
    assert r1.status_code == 200
    bid = r1.json()["branch_id"]

    # 2. Mutate branch
    r2 = client.post(
        f"/v1/versioning/branches/{bid}/mutate",
        json={
            "event_type": "MedicationPrescribed",
            "payload": {"name": "Enoxaparin", "dose": 40, "unit": "mg", "frequency": "DAILY"},
        },
    )
    assert r2.status_code == 200

    # 3. Query branch state
    r3 = client.get(f"/v1/versioning/branches/{bid}/state")
    assert r3.status_code == 200
    assert "Enoxaparin" in r3.json()["medications"]

    # 4. Merge branch
    r4 = client.post(
        f"/v1/versioning/branches/{bid}/merge",
        json={
            "merging_clinician_id": "DR-CHIEF",
            "merging_clinician_name": "Chief Medical Officer",
            "allow_conflict_override": False,
        },
    )
    assert r4.status_code == 200
    assert r4.json()["success"] is True


def test_api_triad_register_and_attest_http(client: TestClient):
    """Verify triad registration and inference attestation over HTTP."""
    # Register Triad
    r1 = client.post(
        "/v1/versioning/triad/register",
        json={
            "model_id": "cardiac_arrest_rf_v1",
            "weights_digest": "aaaa1111bbbb2222cccc3333dddd4444eeee5555ffff66660000111122223333",
            "dataset_digest": "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "code_commit_hash": "commit_123456",
            "framework": "Scikit-Learn 1.4",
        },
    )
    assert r1.status_code == 200
    tid = r1.json()["triad_id"]

    # Attest Inference
    r2 = client.post(
        "/v1/versioning/triad/attest",
        json={
            "patient_id": "PT-PRED-01",
            "prediction_id": "PRED-CARD-01",
            "triad_id": tid,
            "input_features": {"troponin": 0.45, "ef": 35},
            "output_prediction": {"risk": "HIGH", "score": 0.82},
        },
    )
    assert r2.status_code == 200
    att_id = r2.json()["attestation_id"]

    # Verify Provenance
    r3 = client.get(f"/v1/versioning/triad/verify/{att_id}")
    assert r3.status_code == 200
    assert r3.json()["valid"] is True


def test_api_protocol_endpoints_http(client: TestClient):
    """Verify care protocol creation and canary resolution over HTTP."""
    r1 = client.post(
        "/v1/versioning/protocols/create",
        json={
            "protocol_id": "PROTO-STROKE-FAST",
            "title": "Hyperacute Stroke Protocol",
            "version": "2.0.0",
            "steps": [
                {"step_id": "ct_angio", "name": "Emergency CTA Head/Neck", "action_type": "IMAGING", "parameters": {}},
            ],
            "author_id": "NEURO-COMMITTEE",
        },
    )
    assert r1.status_code == 200
    assert r1.json()["version"] == "2.0.0"

    # Transition to ACTIVE
    r2 = client.post(
        "/v1/versioning/protocols/PROTO-STROKE-FAST/transition",
        json={
            "version": "2.0.0",
            "target_status": "ACTIVE",
            "user_id": "DR-DIRECTOR",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "ACTIVE"

    # Get effective protocol
    r3 = client.get("/v1/versioning/protocols/PROTO-STROKE-FAST/effective")
    assert r3.status_code == 200
    assert r3.json()["version"] == "2.0.0"
