"""
Comprehensive Test Suite for Level 5 Autonomous Clinical Frontier:
1. In Silico Molecular Docking & Binding Free Energy Estimation
2. Lyapunov-Constrained Closed-Loop Infusion Actuation
3. Zero-Knowledge Sovereign Health Assertion & Verification
4. FastAPI Peak Healthcare v1 Endpoints Integration
"""

import pytest
from fastapi.testclient import TestClient

from backend.closed_loop_actuator import closed_loop_actuator
from backend.generative_therapeutics import generative_therapeutics_engine
from backend.main import app
from backend.schemas.peak_healthcare import (
    ClosedLoopTitrationRequest,
    MolecularAffinityRequest,
    ZkHealthAssertionRequest,
    ZkProofVerificationRequest,
)
from backend.zk_health_passport import zk_health_engine


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Generative Molecular Docking Tests
# =====================================================================

def test_molecular_docking_small_molecule():
    """Test in silico docking of small molecule candidate against SGLT2 pocket."""
    req = MolecularAffinityRequest(
        target_receptor="SGLT2",
        ligand_identifier="CANDIDATE-SGLT2-ALPHA",
        chemical_smiles="CC1=CC(=C(C=C1)CC2=CC=C(C=C2)OC3C(C(C(C(O3)CO)O)O)O)Cl",  # Dapagliflozin-like SMILES
    )

    resp = generative_therapeutics_engine.dock_candidate(req)

    assert resp.target_receptor == "Sodium-Glucose Transport Protein 2 (SGLT2)"
    assert resp.ligand_identifier == "CANDIDATE-SGLT2-ALPHA"
    assert resp.predicted_delta_g_kcal_mol < -5.0  # Favorable spontaneous binding
    assert resp.predicted_kd_nanomolar > 0.0
    assert resp.binding_affinity_tier in ["PICOMOLAR_ULTRA", "LOW_NANOMOLAR_POTENT", "SUB_MICROMOLAR"]
    assert "human_intestinal_absorption" in resp.admet_safety_profile
    assert "herg_cardiotoxicity_risk" in resp.admet_safety_profile


def test_molecular_docking_peptide():
    """Test docking of candidate peptide therapeutic against GLP-1R pocket."""
    req = MolecularAffinityRequest(
        target_receptor="GLP1R",
        ligand_identifier="PEPTIDE-GLP1-MIMETIC",
        peptide_sequence="HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
    )

    resp = generative_therapeutics_engine.dock_candidate(req)

    assert "GLP-1R" in resp.target_receptor
    assert resp.predicted_delta_g_kcal_mol < -6.0
    assert resp.lipinski_rule_of_5_compliant is False  # Large biologic bypasses small-molecule Lipinski rules
    assert resp.admet_safety_profile["blood_brain_barrier_penetration"] == "Non-Penetrating (CNS Sparing)"


# =====================================================================
# 2. Lyapunov Closed-Loop Infusion Actuator Tests
# =====================================================================

def test_closed_loop_norepinephrine_titration():
    """Test vasopressor titration for hypotensive patient verifies Lyapunov stability."""
    req = ClosedLoopTitrationRequest(
        patient_id="PT-ICU-SHOCK",
        medication_channel="norepinephrine",
        current_state_measurement=62.0,  # Hypotensive MAP (target is 85.0 mmHg)
        target_setpoint=85.0,
        current_infusion_rate=8.0,
        elapsed_time_sec=60.0,
    )

    resp = closed_loop_actuator.titrate(req)

    assert resp.medication_channel == "norepinephrine"
    assert resp.rate_delta > 0.0  # Must increase vasopressor to raise MAP
    assert resp.recommended_infusion_rate > req.current_infusion_rate
    assert resp.lyapunov_candidate_value > 0.0
    # Lyapunov derivative dV/dt must be strictly negative proving asymptotic convergence
    assert resp.lyapunov_derivative_v_dot < 0.0
    assert resp.is_lyapunov_stable is True
    assert resp.actuator_status == "NORMAL_REGULATION"


def test_closed_loop_insulin_titration():
    """Test insulin titration for hyperglycemic patient verifies Lyapunov stability."""
    req = ClosedLoopTitrationRequest(
        patient_id="PT-ICU-GLUC",
        medication_channel="insulin",
        current_state_measurement=210.0,  # Hyperglycemia (target is 110.0 mg/dL)
        target_setpoint=110.0,
        current_infusion_rate=2.0,
        elapsed_time_sec=60.0,
    )

    resp = closed_loop_actuator.titrate(req)

    assert resp.rate_delta > 0.0  # Must increase insulin infusion to lower glucose
    assert resp.lyapunov_derivative_v_dot < 0.0
    assert resp.is_lyapunov_stable is True


def test_closed_loop_target_convergence():
    """Test controller holds rate when state error is within physiological deadband."""
    req = ClosedLoopTitrationRequest(
        patient_id="PT-ICU-STABLE",
        medication_channel="norepinephrine",
        current_state_measurement=84.5,  # Within 2 mmHg of target 85.0
        target_setpoint=85.0,
        current_infusion_rate=6.0,
        elapsed_time_sec=60.0,
    )

    resp = closed_loop_actuator.titrate(req)

    assert resp.rate_delta == 0.0
    assert resp.recommended_infusion_rate == 6.0
    assert resp.actuator_status == "CONVERGED_AT_TARGET"


def test_closed_loop_safety_clamp():
    """Test controller engages emergency clamp when exceeding maximum rate bound."""
    req = ClosedLoopTitrationRequest(
        patient_id="PT-ICU-MAX",
        medication_channel="norepinephrine",
        current_state_measurement=45.0,  # Profound shock
        target_setpoint=85.0,
        current_infusion_rate=34.0,     # Near ceiling (35 mcg/min)
        elapsed_time_sec=60.0,
    )

    resp = closed_loop_actuator.titrate(req)

    assert resp.recommended_infusion_rate <= 35.0  # Strictly bounded by safety ceiling
    assert resp.safety_clamp_engaged is True
    assert resp.actuator_status == "EMERGENCY_CLAMP"


# =====================================================================
# 3. Zero-Knowledge Sovereign Health Passport Tests
# =====================================================================

def test_zk_health_assertion_valid():
    """Test generating and verifying a valid ZK assertion (eGFR >= 60 mL/min)."""
    # Prover generates proof for real eGFR = 82.0
    prove_req = ZkHealthAssertionRequest(
        patient_id="PT-ZK-ALICE",
        biomarker_name="egfr",
        secret_value=82.0,
        public_threshold=60.0,
        assertion_operator=">=",
    )

    proof_resp = zk_health_engine.generate_assertion_proof(prove_req)

    assert proof_resp.assertion_satisfied is True
    assert proof_resp.public_commitment != ""
    assert proof_resp.proof_token != ""

    # Independent verifier verifies proof using ONLY public fields
    verify_req = ZkProofVerificationRequest(
        public_commitment=proof_resp.public_commitment,
        proof_token=proof_resp.proof_token,
        biomarker_name=proof_resp.biomarker_name,
        public_threshold=proof_resp.public_threshold,
        assertion_operator=proof_resp.assertion_operator,
    )

    verify_resp = zk_health_engine.verify_assertion_proof(verify_req)

    assert verify_resp.is_valid_proof is True
    assert verify_resp.verification_status == "VERIFIED_VALID"


def test_zk_health_assertion_false_claim_rejected():
    """Test that attempting to prove a false claim (eGFR >= 90 when real is 55) is rejected."""
    prove_req = ZkHealthAssertionRequest(
        patient_id="PT-ZK-BOB",
        biomarker_name="egfr",
        secret_value=55.0,
        public_threshold=90.0,
        assertion_operator=">=",
    )

    proof_resp = zk_health_engine.generate_assertion_proof(prove_req)

    assert proof_resp.assertion_satisfied is False
    assert "failed" in proof_resp.statement.lower()


def test_zk_tampered_proof_rejected():
    """Test that a modified commitment or tampered token is detected and rejected."""
    prove_req = ZkHealthAssertionRequest(
        patient_id="PT-ZK-EVE",
        biomarker_name="mace_10yr_risk",
        secret_value=4.5,
        public_threshold=7.5,
        assertion_operator="<=",
    )
    proof_resp = zk_health_engine.generate_assertion_proof(prove_req)

    # Verifier with altered commitment
    verify_req = ZkProofVerificationRequest(
        public_commitment="TAMPERED_HASH_1234567890ABCDEF",
        proof_token=proof_resp.proof_token,
        biomarker_name="mace_10yr_risk",
        public_threshold=7.5,
        assertion_operator="<=",
    )
    verify_resp = zk_health_engine.verify_assertion_proof(verify_req)

    assert verify_resp.is_valid_proof is False
    assert "REJECTED" in verify_resp.verification_status


# =====================================================================
# 4. FastAPI Integration Tests for Level 5 Routes
# =====================================================================

def test_fastapi_level5_routes(client):
    """Test all four Level 5 Peak Healthcare REST endpoints."""

    # 1. Docking endpoint
    dock_resp = client.post(
        "/v1/therapeutics/dock",
        json={
            "target_receptor": "ACE2",
            "ligand_identifier": "CANDIDATE-ACE2-INHIBITOR",
            "chemical_smiles": "CC(C)CC(C(=O)NC(CCC(=O)O)C(=O)N1CCCC1C(=O)O)NC(=O)C",
        },
    )
    assert dock_resp.status_code == 200
    dock_data = dock_resp.json()
    assert "predicted_delta_g_kcal_mol" in dock_data
    assert dock_data["predicted_delta_g_kcal_mol"] < 0.0

    # 2. Closed-loop titration endpoint
    act_resp = client.post(
        "/v1/actuator/titrate",
        json={
            "patient_id": "PT-API-ACT",
            "medication_channel": "norepinephrine",
            "current_state_measurement": 68.0,
            "target_setpoint": 85.0,
            "current_infusion_rate": 5.0,
            "elapsed_time_sec": 60.0,
        },
    )
    assert act_resp.status_code == 200
    act_data = act_resp.json()
    assert act_data["is_lyapunov_stable"] is True
    assert act_data["rate_delta"] > 0.0

    # 3. ZK Prove endpoint
    zk_prove = client.post(
        "/v1/zk-passport/prove",
        json={
            "patient_id": "PT-API-ZK",
            "biomarker_name": "hba1c",
            "secret_value": 6.4,
            "public_threshold": 7.0,
            "assertion_operator": "<=",
        },
    )
    assert zk_prove.status_code == 200
    prove_data = zk_prove.json()
    assert prove_data["assertion_satisfied"] is True

    # 4. ZK Verify endpoint
    zk_verify = client.post(
        "/v1/zk-passport/verify",
        json={
            "public_commitment": prove_data["public_commitment"],
            "proof_token": prove_data["proof_token"],
            "biomarker_name": "hba1c",
            "public_threshold": 7.0,
            "assertion_operator": "<=",
        },
    )
    assert zk_verify.status_code == 200
    verify_data = zk_verify.json()
    assert verify_data["is_valid_proof"] is True
    assert verify_data["verification_status"] == "VERIFIED_VALID"
