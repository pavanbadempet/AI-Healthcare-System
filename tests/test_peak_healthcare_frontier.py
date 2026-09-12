"""
Comprehensive Test Suite for Level 4 Autonomous Cyber-Physical Health OS Capabilities:
1. Cybernetics Unscented Kalman Filter (UKF) Telemetry Assimilation
2. Causal Structural Causal Models & do-Calculus Counterfactuals
3. Formally Verified Safe Clinical Control Guards
4. Multimodal Clinical Coordinate Fusion
5. FastAPI Peak Healthcare v1 REST Endpoints
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.causal_engine import causal_engine
from backend.clinical_cybernetics import cybernetics_engine
from backend.clinical_guardrails import clinical_guardrails
from backend.main import app
from backend.multimodal_fusion import multimodal_engine
from backend.schemas.peak_healthcare import (
    CausalCounterfactualRequest,
    CyberneticAssimilationRequest,
    FormalSafetyVerificationRequest,
    MultimodalPatientProfile,
    TelemetryObservationVector,
)


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Cybernetics & Unscented Kalman Filter Tests
# =====================================================================

def test_ukf_telemetry_assimilation_stable():
    """Test UKF dynamic assimilation on normal stable telemetry."""
    obs = TelemetryObservationVector(
        heart_rate=72.0,
        mean_arterial_pressure=92.0,
        spo2=98.0,
        blood_glucose=95.0,
        egfr_proxy=88.0,
    )
    req = CyberneticAssimilationRequest(
        patient_id="PT-UKF-001",
        observation=obs,
        elapsed_time_hours=2.0,
        active_interventions=["sglt2i", "statin"],
    )

    resp = cybernetics_engine.assimilate_telemetry(req)

    assert resp.patient_id == "PT-UKF-001"
    assert resp.hemodynamic_instability_detected is False
    assert resp.posterior_estimate.system_stability_status == "STABLE"
    assert "cardiovascular" in resp.posterior_estimate.estimated_organ_reserves
    assert resp.posterior_estimate.estimated_organ_reserves["cardiovascular"] > 60.0
    assert resp.recommended_sampling_interval_sec == 60


def test_ukf_telemetry_assimilation_critical_shock():
    """Test UKF correctly flags severe hypotension and increases sampling frequency."""
    obs = TelemetryObservationVector(
        heart_rate=128.0,
        mean_arterial_pressure=54.0,  # Critical shock (< 65 mmHg)
        spo2=87.0,                   # Critical hypoxia (< 90%)
        blood_glucose=240.0,
        egfr_proxy=35.0,
    )
    req = CyberneticAssimilationRequest(
        patient_id="PT-UKF-SHOCK",
        observation=obs,
        elapsed_time_hours=0.5,
    )

    resp = cybernetics_engine.assimilate_telemetry(req)

    assert resp.hemodynamic_instability_detected is True
    assert resp.posterior_estimate.system_stability_status == "CRITICAL_INSTABILITY"
    assert resp.recommended_sampling_interval_sec == 10
    assert resp.clinical_alert is not None
    assert "Shock" in resp.clinical_alert or "Hypoxemic" in resp.clinical_alert


# =====================================================================
# 2. Causal Structural Causal Model & do-Calculus Tests
# =====================================================================

def test_causal_counterfactual_evaluation():
    """Test Pearl Level-3 counterfactual estimation on SGLT2i + GLP-1 dual therapy."""
    req = CausalCounterfactualRequest(
        patient_id="PT-CAUSAL-100",
        age=64.0,
        baseline_egfr=52.0,
        baseline_sbp=142.0,
        baseline_hba1c=8.2,
        bmi=31.5,
        factual_treatment="standard_of_care",
        factual_10yr_mace_percent=24.5,
        factual_egfr_slope_per_year=-3.2,
        counterfactual_intervention="sglt2i_plus_glp1",
    )

    resp = causal_engine.evaluate_counterfactual(req)

    assert resp.patient_id == "PT-CAUSAL-100"
    assert resp.counterfactual_intervention == "sglt2i_plus_glp1"
    # MACE risk under counterfactual should be lower than factual
    assert resp.counterfactual_10yr_mace_percent < req.factual_10yr_mace_percent
    assert resp.individual_treatment_effect_mace > 0.0
    # Annual eGFR decline slope should be significantly preserved
    assert resp.counterfactual_egfr_slope_per_year > req.factual_egfr_slope_per_year
    assert resp.individual_treatment_effect_egfr_slope > 1.0
    # E-value sensitivity score should be >= 1.2
    assert resp.e_value_sensitivity >= 1.2


# =====================================================================
# 3. Formally Verified Safe Clinical Control Guards Tests
# =====================================================================

def test_formal_guard_proves_safe_regimen():
    """Test formal verifier successfully proves and certifies a safe medication regimen."""
    req = FormalSafetyVerificationRequest(
        patient_id="PT-SAFE-001",
        proposed_medications=["Lisinopril 10mg", "Empagliflozin 10mg", "Atorvastatin 20mg"],
        egfr=78.0,
        serum_potassium=4.4,
        systolic_bp=132.0,
        diastolic_bp=84.0,
        qtc_interval_ms=410.0,
        fib4_score=1.1,
    )

    resp = clinical_guardrails.verify_regimen(req)

    assert resp.is_safe_to_administer is True
    assert resp.verification_status in ["PROVEN_SAFE", "CONDITIONAL_SAFE"]
    assert len(resp.violated_invariants) == 0
    assert resp.safety_proof_token.startswith("PROOF-SEC-")


def test_formal_guard_rejects_lethal_renal_metformin():
    """Test formal verifier rejects Metformin when eGFR < 30 mL/min (MALA risk)."""
    req = FormalSafetyVerificationRequest(
        patient_id="PT-LETHAL-RENAL",
        proposed_medications=["Metformin 1000mg", "Amlodipine 5mg"],
        egfr=22.0,  # Lethal threshold (< 30)
        serum_potassium=4.2,
        systolic_bp=130.0,
        diastolic_bp=80.0,
    )

    resp = clinical_guardrails.verify_regimen(req)

    assert resp.is_safe_to_administer is False
    assert resp.verification_status == "REJECTED_LETHAL_VIOLATION"
    assert "INVARIANT_1_RENAL_METFORMIN_LETHAL_FLOOR" in resp.violated_invariants
    assert "metformin" in resp.safe_auto_clamped_alternatives


def test_formal_guard_rejects_hyperkalemic_mra():
    """Test formal verifier blocks Spironolactone when K+ >= 5.5 mEq/L (fatal arrhythmia hazard)."""
    req = FormalSafetyVerificationRequest(
        patient_id="PT-HYPER-K",
        proposed_medications=["Spironolactone 25mg", "Lisinopril 20mg"],
        egfr=55.0,
        serum_potassium=5.8,  # Hyperkalemia (>= 5.5)
        systolic_bp=135.0,
        diastolic_bp=82.0,
    )

    resp = clinical_guardrails.verify_regimen(req)

    assert resp.is_safe_to_administer is False
    assert resp.verification_status == "REJECTED_LETHAL_VIOLATION"
    assert "INVARIANT_2_HYPERKALEMIA_LETHAL_ARRHYTHMIA_GATE" in resp.violated_invariants
    assert "mra" in resp.safe_auto_clamped_alternatives


def test_formal_guard_rejects_hypotensive_vasodilator():
    """Test formal verifier blocks vasodilators when MAP < 65 mmHg."""
    req = FormalSafetyVerificationRequest(
        patient_id="PT-SHOCK-BP",
        proposed_medications=["Amlodipine 10mg", "Metoprolol 50mg"],
        egfr=60.0,
        serum_potassium=4.0,
        systolic_bp=82.0,  # Shock SBP
        diastolic_bp=50.0, # Shock MAP = 60.6 mmHg
    )

    resp = clinical_guardrails.verify_regimen(req)

    assert resp.is_safe_to_administer is False
    assert resp.verification_status == "REJECTED_LETHAL_VIOLATION"
    assert "INVARIANT_3_HEMODYNAMIC_SHOCK_FLOOR" in resp.violated_invariants


def test_formal_guard_rejects_cumulative_qtc_torsades():
    """Test formal verifier blocks high-risk QTc prolonging combinations."""
    req = FormalSafetyVerificationRequest(
        patient_id="PT-QTC-HAZARD",
        proposed_medications=["Amiodarone 200mg", "Azithromycin 500mg", "Haloperidol 5mg"],
        egfr=80.0,
        serum_potassium=4.1,
        systolic_bp=125.0,
        diastolic_bp=78.0,
        qtc_interval_ms=450.0,
    )

    resp = clinical_guardrails.verify_regimen(req)

    assert resp.is_safe_to_administer is False
    assert resp.verification_status == "REJECTED_LETHAL_VIOLATION"
    assert "INVARIANT_4_CUMULATIVE_QTC_TORSADES_HAZARD" in resp.violated_invariants


# =====================================================================
# 4. Multimodal Clinical Coordinate Fusion Tests
# =====================================================================

def test_multimodal_clinical_coordinate_projection():
    """Test multimodal coordinate embedding into normalized R^128 latent manifold."""
    profile = MultimodalPatientProfile(
        patient_id="PT-MULTI-42",
        age=58.0,
        gender="male",
        vitals_vector={
            "systolic_bp": 138.0,
            "diastolic_bp": 86.0,
            "heart_rate": 74.0,
            "egfr": 58.0,
            "hba1c": 7.6,
            "fasting_glucose": 135.0,
            "ldl_cholesterol": 125.0,
            "crp_mg_l": 2.4,
        },
        diagnostic_codes=["E11.9", "I10", "N18.3"],
        genomic_variants={"CYP2D6": "*4/*4", "CYP2C19": "*1/*1"},
        morphological_features={
            "cardiothoracic_ratio": 0.54,
            "lvef_percent": 52.0,
            "qtc_interval_ms": 435.0,
        },
    )

    resp = multimodal_engine.embed_patient(profile)

    assert resp.patient_id == "PT-MULTI-42"
    assert resp.embedding_dimension == 128
    assert len(resp.latent_coordinate_vector) == 128
    # Norm of embedding vector should be approximately 1.0 (unit hypersphere)
    vec = np.array(resp.latent_coordinate_vector)
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-2) == 1.0
    assert 0.0 <= resp.latent_manifold_stability_index <= 1.0
    assert len(resp.nearest_phenotypic_cohort) > 0
    assert resp.cohort_euclidean_distance >= 0.0


# =====================================================================
# 5. FastAPI Integration Endpoints Tests
# =====================================================================

def test_fastapi_peak_healthcare_level4_routes(client):
    """Test all four new Level 4 REST endpoints via FastAPI TestClient."""

    # 1. Cybernetics Assimilation Endpoint
    cyber_resp = client.post(
        "/v1/cybernetics/assimilate",
        json={
            "patient_id": "PT-API-CYBER",
            "observation": {
                "heart_rate": 75.0,
                "mean_arterial_pressure": 90.0,
                "spo2": 97.0,
                "blood_glucose": 110.0,
                "egfr_proxy": 82.0,
            },
            "elapsed_time_hours": 1.0,
            "active_interventions": ["sglt2i"],
        },
    )
    assert cyber_resp.status_code == 200
    cyber_data = cyber_resp.json()
    assert cyber_data["patient_id"] == "PT-API-CYBER"
    assert "posterior_estimate" in cyber_data

    # 2. Causal Counterfactual Endpoint
    causal_resp = client.post(
        "/v1/causal/counterfactual",
        json={
            "patient_id": "PT-API-CAUSAL",
            "age": 62.0,
            "baseline_egfr": 60.0,
            "baseline_sbp": 138.0,
            "baseline_hba1c": 7.4,
            "bmi": 29.0,
            "factual_treatment": "standard_of_care",
            "factual_10yr_mace_percent": 20.0,
            "factual_egfr_slope_per_year": -2.8,
            "counterfactual_intervention": "quad_therapy",
        },
    )
    assert causal_resp.status_code == 200
    causal_data = causal_resp.json()
    assert causal_data["patient_id"] == "PT-API-CAUSAL"
    assert causal_data["individual_treatment_effect_mace"] > 0.0

    # 3. Formal Safety Verification Endpoint
    safety_resp = client.post(
        "/v1/safety/verify-regimen",
        json={
            "patient_id": "PT-API-SAFETY",
            "proposed_medications": ["Metformin 1000mg"],
            "egfr": 18.0,  # Severe CKD
            "serum_potassium": 4.5,
            "systolic_bp": 125.0,
            "diastolic_bp": 80.0,
        },
    )
    assert safety_resp.status_code == 200
    safety_data = safety_resp.json()
    assert safety_data["is_safe_to_administer"] is False
    assert safety_data["verification_status"] == "REJECTED_LETHAL_VIOLATION"

    # 4. Multimodal Coordinate Embedding Endpoint
    multi_resp = client.post(
        "/v1/multimodal/embed-patient",
        json={
            "patient_id": "PT-API-MULTI",
            "age": 55.0,
            "vitals_vector": {"systolic_bp": 120.0, "egfr": 95.0, "hba1c": 5.4},
            "diagnostic_codes": ["Z00.00"],
            "genomic_variants": {"CYP2D6": "*1/*1"},
            "morphological_features": {"lvef_percent": 60.0},
        },
    )
    assert multi_resp.status_code == 200
    multi_data = multi_resp.json()
    assert multi_data["embedding_dimension"] == 128
    assert len(multi_data["latent_coordinate_vector"]) == 128
