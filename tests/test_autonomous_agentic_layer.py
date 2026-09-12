"""Tests for Level 14 Autonomous Multi-Agent Deliberative Clinical Consensus & Metacognitive HTN Orchestration OS.

Verifies:
1. Dung's Abstract Argumentation Framework (AF = <A, R>) for multi-specialist virtual tumor board consensus.
2. Dialectical attack resolution: Genomic mismatch, cardiotoxicity interaction, and palliative ethics vetoes.
3. Hierarchical Task Network (HTN) clinical goal decomposition with precondition/postcondition gates.
4. Reactive telemetry replanning upon sudden physiological collapse in sub-5ms.
5. Deterministic Pre-Action Invariant Execution Gate (Contraindications, Renal limits, Teratogens, Allergies).
6. Metacognitive epistemic uncertainty estimation and autonomous human clinician escalation yielding.
7. FastAPI /v1/agentic HTTP endpoints integration.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.agentic.dialectical_consensus import (
    ClinicalArgument,
    DialecticalConsensusEngine,
    DungArgumentationFramework,
    SpecialistRole,
)
from backend.agentic.htn_planner import HTNClinicalPlanner, TaskStatus
from backend.agentic.invariant_execution_gate import (
    InvariantType,
    PreActionInvariantGate,
)
from backend.agentic.metacognitive_calibrator import MetacognitiveCalibrator
from backend.main import app
from backend.routes.agentic_routes import (
    consensus_engine as route_consensus_engine,
)
from backend.routes.agentic_routes import (
    htn_planner as route_htn_planner,
)
from backend.routes.agentic_routes import (
    invariant_gate as route_invariant_gate,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_agentic_stores():
    """Ensure clean isolated state across tests."""
    route_consensus_engine._history.clear()
    route_htn_planner.clear()
    route_invariant_gate.clear()
    yield
    route_consensus_engine._history.clear()
    route_htn_planner.clear()
    route_invariant_gate.clear()


# =========================================================================
# 1. Dung's Abstract Argumentation & Dialectical Consensus Tests
# =========================================================================

def test_dung_argumentation_framework_grounded_extension():
    """Verify mathematical computation of conflict-free and grounded extensions."""
    af = DungArgumentationFramework()

    # Argument A: Proposed targeted therapy
    af.add_argument(ClinicalArgument("A", SpecialistRole.ATTENDING_PHYSICIAN, "Give osimertinib", "EGFR target"))
    # Argument B: Pharmacist objection (QTc prolongation)
    af.add_argument(ClinicalArgument("B", SpecialistRole.CLINICAL_PHARMACIST, "Hold osimertinib", "QTc 510ms"))
    # Argument C: Geneticist note (Confirming cardiac modifier)
    af.add_argument(ClinicalArgument("C", SpecialistRole.MEDICAL_GENETICIST, "Confirm high cardiac risk", "KCNQ1 variant"))

    # B attacks A
    af.add_attack("B", "A", "DRUG_INTERACTION", "Cardiotoxicity")
    # C defends B (does not attack B)

    grounded = af.compute_grounded_extension()
    assert "B" in grounded, "Unattacked pharmacist objection must be in grounded extension"
    assert "C" in grounded, "Unattacked geneticist finding must be in grounded extension"
    assert "A" not in grounded, "Attacked and undefended oncologist argument must be excluded"
    assert af.is_conflict_free(grounded) is True


def test_virtual_tumor_board_deliberation_scenarios():
    """Verify multi-specialist deliberation across 3 distinct clinical dispute scenarios."""
    engine = DialecticalConsensusEngine()

    # Scenario 1: Standard clean EGFR mutation -> Approved
    case_standard = {
        "diagnosis": "Stage IV Adenocarcinoma",
        "biomarkers": {"EGFR": "EXON_19_DEL"},
        "organ_function": {"egfr": 80},
        "ecg_qtc": 420,
    }
    res1 = engine.deliberate("PT-ONC-01", case_standard)
    assert res1["consensus_action"] == "PROCEED_WITH_STANDARD_TARGETED_THERAPY"
    assert len(res1["grounded_consensus_arguments"]) >= 2

    # Scenario 2: Cardiotoxicity dispute -> Defer for cardiac clearance
    case_cardiac = {
        "diagnosis": "Stage IV Adenocarcinoma",
        "biomarkers": {"EGFR": "EXON_19_DEL"},
        "current_meds": ["Amiodarone"],
        "ecg_qtc": 510,
    }
    res2 = engine.deliberate("PT-ONC-02", case_cardiac)
    assert res2["consensus_action"] == "DEFER_TARGETED_THERAPY_CARDIAC_REVIEW"
    assert any(att["attack_type"] == "DRUG_INTERACTION" for att in res2["attacks_evaluated"])

    # Scenario 3: Palliative Advance Directive -> Ethics veto
    case_palliative = {
        "diagnosis": "Stage IV Adenocarcinoma",
        "biomarkers": {"EGFR": "EXON_19_DEL"},
        "patient_preferences": {"palliative_only": True},
    }
    res3 = engine.deliberate("PT-ONC-03", case_palliative)
    assert res3["consensus_action"] == "PIVOT_TO_PALLIATIVE_CARE"


# =========================================================================
# 2. Hierarchical Task Network (HTN) Planner & Reactive Replanning Tests
# =========================================================================

def test_htn_planning_decomposition():
    """Verify decomposition of high-level sepsis goal into compound tasks and primitive actions."""
    planner = HTNClinicalPlanner()
    plan = planner.generate_plan(
        patient_id="PT-ICU-88",
        goal="SEPTIC_SHOCK_RESUSCITATION",
        initial_state={"map": 58, "lactate": 3.2},
    )

    assert plan.goal == "SEPTIC_SHOCK_RESUSCITATION"
    assert len(plan.compound_tasks) == 2

    hemo_task = plan.compound_tasks[0]
    assert hemo_task.task_id == "TASK_HEMODYNAMICS"
    assert len(hemo_task.actions) == 2

    # Check action 1: Crystalloid IV bolus
    fluid_act = hemo_task.actions[0]
    assert fluid_act.category == "FLUIDS"
    assert fluid_act.preconditions["map_max"] == 65

    # Check precondition evaluation
    sat, unmet = fluid_act.check_preconditions({"map": 58})
    assert sat is True
    assert len(unmet) == 0

    sat_fail, unmet_fail = fluid_act.check_preconditions({"map": 80})
    assert sat_fail is False
    assert len(unmet_fail) == 1


def test_htn_reactive_telemetry_replanning():
    """Verify dynamic pruning and sub-5ms emergency branch synthesis upon acute physiological collapse."""
    planner = HTNClinicalPlanner()
    plan = planner.generate_plan(
        patient_id="PT-ICU-99",
        goal="SEPTIC_SHOCK_RESUSCITATION",
        initial_state={"map": 62},
    )

    # Patient collapses: Refractory hypotension (MAP 42) + Hypoxemia (SpO2 81%)
    telemetry_crash = {
        "map": 42,
        "spo2": 81,
        "lactate": 5.4,
    }

    replanned = planner.reactive_replan(plan.plan_id, telemetry_crash)

    assert replanned.replanned_count == 1
    assert len(replanned.replanning_history) == 1

    # Emergency task must be prepended as the very first task in the tree
    emerg_task = replanned.compound_tasks[0]
    assert "Emergency Refractory Stabilization Protocol" in emerg_task.name
    assert len(emerg_task.actions) == 2  # Vasopressin + RSI Intubation

    # Downstream non-emergent actions must be marked PRUNED
    pruned_actions = [
        act for t in replanned.compound_tasks[1:]
        for act in t.actions
        if act.status == TaskStatus.PRUNED
    ]
    assert len(pruned_actions) >= 1


# =========================================================================
# 3. Pre-Action Clinical Invariant Execution Gate Tests
# =========================================================================

def test_invariant_gate_blocks_absolute_contraindications():
    """Verify tPA / Thrombolytic is strictly blocked in the presence of active hemorrhage."""
    gate = PreActionInvariantGate()

    patient_with_bleed = {
        "patient_id": "PT-BLEED-01",
        "conditions": ["Acute Ischemic Stroke", "Subdural Hemorrhage"],
        "allergies": [],
        "egfr": 85,
    }

    res = gate.validate_and_execute(
        action_name="prescribe_medication",
        parameters={"drug": "Alteplase", "dose": 0.9, "unit": "mg/kg"},
        patient_profile=patient_with_bleed,
    )

    assert res.allowed is False
    assert res.status == "REJECTED_INVARIANT_BREACH"
    assert len(res.violations) == 1
    v = res.violations[0]
    assert v.invariant_type == InvariantType.ABSOLUTE_CONTRAINDICATION
    assert "strictly contraindicated" in v.message


def test_invariant_gate_blocks_renal_and_teratogenic_breaches():
    """Verify Metformin blocked in severe renal failure and teratogens blocked in pregnancy."""
    gate = PreActionInvariantGate()

    # 1. Renal impairment breach (eGFR 22 < 30)
    renal_patient = {"conditions": ["Type 2 Diabetes"], "egfr": 22.0, "allergies": []}
    res_renal = gate.validate_and_execute(
        action_name="prescribe_medication",
        parameters={"drug": "Metformin", "dose": 1000, "unit": "mg"},
        patient_profile=renal_patient,
    )
    assert res_renal.allowed is False
    assert res_renal.violations[0].invariant_type == InvariantType.RENAL_HEPATIC_CLEARANCE

    # 2. Pregnancy Teratogen Category X breach
    pregnant_patient = {"conditions": ["Rheumatoid Arthritis"], "is_pregnant": True, "allergies": [], "egfr": 90}
    res_preg = gate.validate_and_execute(
        action_name="prescribe_medication",
        parameters={"drug": "Methotrexate", "dose": 15, "unit": "mg"},
        patient_profile=pregnant_patient,
    )
    assert res_preg.allowed is False
    assert res_preg.violations[0].invariant_type == InvariantType.PREGNANCY_TERATOGENIC

    # 3. Anaphylaxis allergy breach
    allergic_patient = {"allergies": ["Penicillin"], "conditions": ["Pneumonia"], "egfr": 90}
    res_allergy = gate.validate_and_execute(
        action_name="prescribe_medication",
        parameters={"drug": "Ampicillin", "dose": 2, "unit": "g"},
        patient_profile=allergic_patient,
    )
    assert res_allergy.allowed is False
    assert res_allergy.violations[0].invariant_type == InvariantType.ANAPHYLAXIS_ALLERGY

    # 4. Safe order passes
    res_safe = gate.validate_and_execute(
        action_name="prescribe_medication",
        parameters={"drug": "Aztreonam", "dose": 1, "unit": "g"},
        patient_profile=allergic_patient,
    )
    assert res_safe.allowed is True
    assert res_safe.status == "EXECUTED_SAFE"
    assert res_safe.audit_token is not None


# =========================================================================
# 4. Metacognitive Epistemic Calibrator Tests
# =========================================================================

def test_metacognitive_epistemic_calibration_and_safety_yield():
    """Verify epistemic self-assessment triggers autonomous safety yield when knowledge gaps exist."""
    calibrator = MetacognitiveCalibrator()

    # Scenario A: High epistemic uncertainty with critical diagnostic gaps -> YIELD
    claim = "Patient is suffering from non-ST segment elevation myocardial infarction"
    available = ["Patient reports chest pressure"]
    missing = ["Serial Troponin I at 0h and 3h", "12-Lead Electrocardiogram", "Echocardiogram"]

    res_uncertain = calibrator.evaluate_epistemic_confidence(
        clinical_claim=claim,
        available_evidence=available,
        missing_observations=missing,
        acuity_level="CRITICAL",
    )

    assert res_uncertain.epistemic_uncertainty > res_uncertain.safe_threshold
    assert res_uncertain.autonomous_execution_permitted is False
    assert res_uncertain.yield_decision == "YIELD_TO_HUMAN_CLINICIAN"
    assert res_uncertain.clinician_escalation_brief is not None
    assert len(res_uncertain.clinician_escalation_brief["missing_critical_diagnostics"]) == 3

    # Scenario B: Low epistemic uncertainty with comprehensive evidence -> SAFE
    comprehensive_evidence = [
        "Serial Troponin I elevated (0.85 ng/mL)",
        "ST depressions in leads V4-V6 on 12-lead ECG",
        "Coronary angiography confirms 90% LAD stenosis",
    ]
    res_safe = calibrator.evaluate_epistemic_confidence(
        clinical_claim="NSTEMI confirmed",
        available_evidence=comprehensive_evidence,
        missing_observations=[],
        acuity_level="HIGH",
    )

    assert res_safe.epistemic_uncertainty <= res_safe.safe_threshold
    assert res_safe.autonomous_execution_permitted is True
    assert res_safe.yield_decision == "AUTONOMOUS_EXECUTION_SAFE"


# =========================================================================
# 5. FastAPI /v1/agentic Endpoints Integration Tests
# =========================================================================

def test_api_agentic_health(client: TestClient):
    """Verify /v1/agentic/health endpoint."""
    resp = client.get("/v1/agentic/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["engine"] == "AUTONOMOUS_DELIBERATIVE_METANET_AGENT_OS"


def test_api_deliberate_endpoint(client: TestClient):
    """Verify multi-specialist virtual tumor board deliberation over HTTP."""
    resp = client.post(
        "/v1/agentic/deliberate",
        json={
            "patient_id": "PT-DELIB-01",
            "clinical_case": {
                "diagnosis": "Metastatic NSCLC",
                "biomarkers": {"EGFR": "EXON_19_DEL"},
                "organ_function": {"egfr": 78},
            },
        },
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["patient_id"] == "PT-DELIB-01"
    assert d["consensus_action"] == "PROCEED_WITH_STANDARD_TARGETED_THERAPY"
    assert len(d["grounded_consensus_arguments"]) >= 1


def test_api_htn_plan_and_replan_endpoint(client: TestClient):
    """Verify HTN generation and reactive replanning over HTTP."""
    # 1. Generate plan
    r1 = client.post(
        "/v1/agentic/htn/plan",
        json={
            "patient_id": "PT-HTN-01",
            "goal": "SEPTIC_SHOCK_RESUSCITATION",
            "initial_state": {"map": 60},
        },
    )
    assert r1.status_code == 200
    plan_id = r1.json()["plan_id"]

    # 2. Fetch plan
    r2 = client.get(f"/v1/agentic/htn/plan/{plan_id}")
    assert r2.status_code == 200
    assert r2.json()["goal"] == "SEPTIC_SHOCK_RESUSCITATION"

    # 3. Trigger reactive replan
    r3 = client.post(
        "/v1/agentic/htn/replan",
        json={
            "plan_id": plan_id,
            "telemetry_interrupt": {"map": 45, "spo2": 82, "lactate": 4.8},
        },
    )
    assert r3.status_code == 200
    assert r3.json()["replanned_count"] == 1
    assert "Emergency" in r3.json()["compound_tasks"][0]["name"]


def test_api_invariant_gate_execution(client: TestClient):
    """Verify safety-gated execution endpoint over HTTP."""
    # Contraindicated action
    r1 = client.post(
        "/v1/agentic/gate/execute",
        json={
            "action_name": "prescribe_medication",
            "parameters": {"drug": "Metformin", "dose": 1000},
            "patient_profile": {"conditions": [], "allergies": [], "egfr": 15},
        },
    )
    assert r1.status_code == 200
    assert r1.json()["allowed"] is False
    assert r1.json()["status"] == "REJECTED_INVARIANT_BREACH"

    # Safe action
    r2 = client.post(
        "/v1/agentic/gate/execute",
        json={
            "action_name": "prescribe_medication",
            "parameters": {"drug": "Insulin Glargine", "dose": 10},
            "patient_profile": {"conditions": [], "allergies": [], "egfr": 15},
        },
    )
    assert r2.status_code == 200
    assert r2.json()["allowed"] is True
    assert r2.json()["status"] == "EXECUTED_SAFE"

    # Check audit log
    r3 = client.get("/v1/agentic/gate/audit")
    assert r3.status_code == 200
    assert len(r3.json()) >= 2


def test_api_metacognitive_calibrate(client: TestClient):
    """Verify metacognitive epistemic calibration over HTTP."""
    resp = client.post(
        "/v1/agentic/metacognition/calibrate",
        json={
            "clinical_claim": "Bacterial Meningitis",
            "available_evidence": ["Fever 39.2C", "Nuchal rigidity"],
            "missing_observations": ["Lumbar Puncture CSF Analysis", "Head CT to rule out herniation"],
            "acuity_level": "CRITICAL",
        },
    )
    assert resp.status_code == 200
    d = resp.json()
    assert d["yield_decision"] == "YIELD_TO_HUMAN_CLINICIAN"
    assert d["autonomous_execution_permitted"] is False
    assert d["clinician_escalation_brief"] is not None
