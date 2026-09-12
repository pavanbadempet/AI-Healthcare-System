"""
Unit & Integration Tests for Level 8 Frontier Clinical AI & Neuro-Symbolic Reasoning:
- Multi-Agent Clinical Consensus Delphi Swarm with Adversarial Falsification
- Neuro-Symbolic Clinical Ontology Reasoner & Axiomatic Proof Engine
- Clinical Semantic Uncertainty & Epistemic Hallucination Guard
- Medical Tree-of-Thoughts (Med-ToT) with Expected Value of Diagnostic Information (EVDI)
- FastAPI /v1/clinical-ai/ REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.ai_engine.adversarial_delphi_swarm import delphi_swarm_engine
from backend.ai_engine.clinical_semantic_uncertainty import semantic_uncertainty_engine
from backend.ai_engine.medical_tree_of_thoughts import medical_tot_engine
from backend.ai_engine.neurosymbolic_clinical_reasoner import neurosymbolic_reasoner
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Multi-Agent Delphi Swarm Tests
# =====================================================================

def test_delphi_swarm_chest_pain_consensus_and_adversarial_critique():
    """Verify Delphi swarm reaches consensus and adversarial agent flags anchoring bias."""
    case = {
        "patient_id": "PT-ACS-001",
        "symptoms": ["Severe central crushing chest pain", "Diaphoresis", "Dyspnea"],
        "vitals": {"systolic_bp": 155, "heart_rate": 96, "spo2": 95},
        "labs": {"egfr": 78.0, "potassium": 4.1},
        "current_medications": ["Atorvastatin 20mg", "Aspirin 81mg"],
    }

    res = delphi_swarm_engine.execute_delphi_deliberation(case, max_rounds=3)

    assert res.consensus_reached is True
    assert 0.5 <= res.final_kendall_w <= 1.0
    assert res.calibrated_consensus_confidence > 0.70
    assert "Acute Coronary Syndrome" in res.primary_unified_diagnosis

    # Verify Adversarial Skeptic identified Anchoring Bias
    assert len(res.cognitive_bias_warnings) > 0
    bias = res.cognitive_bias_warnings[0]
    assert bias.bias_type == "ANCHORING_BIAS"
    assert "Stanford Type A Aortic Dissection" in bias.high_acuity_mimickers

    # Verify mandatory falsification tests
    assert len(res.mandatory_falsification_tests) > 0
    assert any("CT" in t or "aortic" in t.lower() or "arterial" in t.lower() for t in res.mandatory_falsification_tests)


def test_delphi_swarm_fever_cough_premature_closure():
    """Verify adversarial agent flags premature closure in respiratory infection cases."""
    case = {
        "patient_id": "PT-RESP-002",
        "symptoms": ["High fever", "Productive cough with purulent sputum", "Chills and rigors"],
        "vitals": {"systolic_bp": 115, "heart_rate": 105, "spo2": 91},
        "labs": {"egfr": 65.0, "potassium": 4.0},
        "current_medications": [],
    }

    res = delphi_swarm_engine.execute_delphi_deliberation(case, max_rounds=2)
    assert len(res.cognitive_bias_warnings) > 0
    assert res.cognitive_bias_warnings[0].bias_type == "PREMATURE_CLOSURE"


def test_delphi_swarm_api_endpoint(client):
    """Verify FastAPI /v1/clinical-ai/delphi-swarm/deliberate endpoint."""
    res = client.post(
        "/v1/clinical-ai/delphi-swarm/deliberate",
        json={
            "patient_id": "PT-API-TEST",
            "symptoms": ["Acute chest tightness"],
            "vitals": {"systolic_bp": 140, "heart_rate": 88},
            "max_rounds": 2,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["consensus_reached"] is True
    assert len(data["prioritized_care_plan"]) > 0
    assert len(data["cognitive_bias_warnings"]) > 0


# =====================================================================
# 2. Neuro-Symbolic Clinical Reasoner Tests
# =====================================================================

def test_neurosymbolic_proves_safe_plan():
    """Verify compliant clinical plan yields valid mathematical proof certificate."""
    patient = {
        "pharmacogenomics": ["CYP2C19*1/*1 (Normal Metabolizer)"],
        "labs": {"egfr": 95.0, "potassium": 4.2, "qtc_ms": 410.0},
        "conditions": ["Essential Hypertension", "Dyslipidemia"],
    }
    actions = ["Amlodipine 5mg", "Atorvastatin 20mg"]

    cert = neurosymbolic_reasoner.verify_treatment_plan(patient, actions)
    assert cert.is_provably_safe is True
    assert cert.proof_token.startswith("PROOF-FOL-")
    assert len(cert.unsat_core_violations) == 0


def test_neurosymbolic_rejects_cyp2c19_clopidogrel_pgx():
    """Verify FOL reasoner rejects clopidogrel in CYP2C19 poor metabolizers with CPIC Level A proof."""
    patient = {
        "pharmacogenomics": ["CYP2C19*2/*3 (Poor Metabolizer)"],
        "labs": {"egfr": 80.0, "potassium": 4.1},
        "conditions": ["Recent NSTEMI / Post-PCI"],
    }
    actions = ["Aspirin 81mg", "Clopidogrel 75mg"]

    cert = neurosymbolic_reasoner.verify_treatment_plan(patient, actions)
    assert cert.is_provably_safe is False
    assert len(cert.unsat_core_violations) == 1
    assert "PGX-CYP2C19-CLOPIDOGREL" in cert.unsat_core_violations[0]
    assert any("Ticagrelor" in r or "Prasugrel" in r for r in cert.remedial_clinical_actions)


def test_neurosymbolic_rejects_severe_ckd_metformin():
    """Verify FOL reasoner rejects metformin when eGFR < 30 mL/min."""
    patient = {
        "pharmacogenomics": [],
        "labs": {"egfr": 24.0, "potassium": 4.5},
        "conditions": ["Type 2 Diabetes Mellitus", "Stage 4 CKD"],
    }
    actions = ["Metformin 1000mg BID"]

    cert = neurosymbolic_reasoner.verify_treatment_plan(patient, actions)
    assert cert.is_provably_safe is False
    assert any("RENAL-METFORMIN-LACTIC-ACIDOSIS" in v for v in cert.unsat_core_violations)
    assert any("Linagliptin" in r or "Insulin" in r for r in cert.remedial_clinical_actions)


def test_neurosymbolic_rejects_hyperkalemia_and_active_bleeding():
    """Verify FOL reasoner rejects K-sparing agents and anticoagulants in high-risk states."""
    patient = {
        "pharmacogenomics": [],
        "labs": {"egfr": 45.0, "potassium": 5.7},
        "conditions": ["Acute Upper Gastrointestinal Bleed", "Heart Failure with reduced EF"],
    }
    actions = ["Spironolactone 25mg", "Apixaban 5mg BID"]

    cert = neurosymbolic_reasoner.verify_treatment_plan(patient, actions)
    assert cert.is_provably_safe is False
    # Expect 2 violations: hyperkalemia gate + active bleeding gate
    assert len(cert.unsat_core_violations) == 2
    assert any("ELECTROLYTE-HYPERKALEMIA-RAAS-GATE" in v for v in cert.unsat_core_violations)
    assert any("HEMOSTATIC-ACTIVE-BLEEDING-ANTICOAGULATION" in v for v in cert.unsat_core_violations)


def test_neurosymbolic_api_endpoint(client):
    """Verify FastAPI /v1/clinical-ai/neurosymbolic/verify-plan endpoint."""
    res = client.post(
        "/v1/clinical-ai/neurosymbolic/verify-plan",
        json={
            "patient_profile": {
                "pharmacogenomics": ["HLA-B*57:01 Positive"],
                "labs": {"egfr": 80.0},
                "conditions": ["HIV-1 Infection"],
            },
            "proposed_medications_and_actions": ["Abacavir 600mg", "Lamivudine 300mg"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_provably_safe"] is False
    assert any("PGX-HLA-B5701-ABACAVIR" in v for v in data["unsat_core_violations"])


# =====================================================================
# 3. Clinical Semantic Uncertainty Tests
# =====================================================================

def test_semantic_entropy_concordant_trajectories():
    """Verify concordant equivalent assertions yield zero semantic entropy."""
    trajectories = [
        "Acute non-ST elevation myocardial infarction",
        "NSTE-ACS requiring urgent coronary angiography",
        "NSTEMI with positive troponin biomarker",
        "Acute coronary syndrome - non-ST elevation",
    ]

    profile = semantic_uncertainty_engine.evaluate_semantic_entropy(trajectories)
    assert profile.semantic_entropy == 0.0
    assert profile.is_epistemically_safe is True
    assert profile.hallucination_risk_level == "LOW"
    assert len(profile.semantic_clusters) == 1


def test_semantic_entropy_divergent_hallucination_hazard():
    """Verify divergent conflicting assertions trigger critical hallucination hazard and CoVe."""
    trajectories = [
        "Acute non-ST elevation myocardial infarction",
        "Stanford Type A acute aortic dissection",
        "Community-acquired bacterial pneumonia",
        "Massive acute pulmonary embolism",
    ]

    profile = semantic_uncertainty_engine.evaluate_semantic_entropy(trajectories)
    # High entropy across 4 completely distinct clinical clusters
    assert profile.semantic_entropy > 0.85
    assert profile.is_epistemically_safe is False
    assert profile.hallucination_risk_level == "CRITICAL_HALLUCINATION_HAZARD"
    assert len(profile.semantic_clusters) == 4
    assert len(profile.chain_of_verification_plan) == 4


def test_semantic_uncertainty_api_endpoint(client):
    """Verify FastAPI /v1/clinical-ai/uncertainty/semantic-entropy endpoint."""
    res = client.post(
        "/v1/clinical-ai/uncertainty/semantic-entropy",
        json={
            "candidate_trajectories": [
                "NSTEMI",
                "Non-ST elevation MI",
                "Pulmonary embolism",
            ],
            "baseline_patient_entropy": 0.15,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "semantic_entropy" in data
    assert len(data["semantic_clusters"]) >= 2


# =====================================================================
# 4. Medical Tree-of-Thoughts (Med-ToT) Tests
# =====================================================================

def test_med_tot_diagnostic_ranking_and_evdi():
    """Verify Med-ToT tree search calculates EVDI and ranks candidate diagnostic actions."""
    diff_probs = {
        "ACUTE_CORONARY_SYNDROME": 0.55,
        "PULMONARY_EMBOLISM": 0.25,
        "AORTIC_DISSECTION": 0.15,
        "PERICARDITIS": 0.05,
    }

    plan = medical_tot_engine.optimize_diagnostic_pathway(diff_probs)

    assert plan.initial_differential_entropy > 1.0
    assert plan.primary_suspected_diagnosis == "ACUTE_CORONARY_SYNDROME"
    assert len(plan.ranked_diagnostic_actions) >= 4
    assert plan.expected_post_test_entropy < plan.initial_differential_entropy
    assert plan.composite_efficiency_gain_pct > 0.0

    # Verify Pareto ranks are sequential starting at 1
    ranks = [a.pareto_rank for a in plan.ranked_diagnostic_actions]
    assert ranks == list(range(1, len(plan.ranked_diagnostic_actions) + 1))


def test_med_tot_contrast_nephrotoxicity_pruning():
    """Verify Med-ToT prunes iodinated contrast CTA when severe renal failure is flagged."""
    diff_probs = {"AORTIC_DISSECTION": 0.70, "PULMONARY_EMBOLISM": 0.30}

    plan_renal = medical_tot_engine.optimize_diagnostic_pathway(
        diff_probs, patient_contraindications=["RENAL_FAILURE"]
    )
    test_ids = [t.test_id for t in plan_renal.ranked_diagnostic_actions]
    assert "TEST-CTA-CHEST-AORTOGRAM" not in test_ids


def test_med_tot_api_and_health(client):
    """Verify FastAPI Med-ToT diagnostic pathway and system health endpoints."""
    # 1. Med-ToT Pathway
    res_tot = client.post(
        "/v1/clinical-ai/med-tot/optimal-diagnostic-path",
        json={
            "differential_diagnosis_probabilities": {
                "ACUTE_CORONARY_SYNDROME": 0.60,
                "PNEUMONIA": 0.40,
            },
        },
    )
    assert res_tot.status_code == 200
    data_tot = res_tot.json()
    assert len(data_tot["ranked_diagnostic_actions"]) > 0
    assert data_tot["composite_efficiency_gain_pct"] > 0.0

    # 2. Health Check
    res_health = client.get("/v1/clinical-ai/health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert data_h["status"] == "HEALTHY"
    assert data_h["tier"] == "LEVEL_8_UNIFIED_CLINICAL_INTELLIGENCE_OS"
    assert data_h["subsystems"]["neurosymbolic_reasoner"] == "ACTIVE"
