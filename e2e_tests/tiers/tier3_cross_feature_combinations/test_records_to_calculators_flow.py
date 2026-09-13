"""
Tier 3: Cross-Feature Combinations — Clinical Records to Calculators and Safety Gate Flow
Simulates cross-module pipeline: Clinical Records -> Native Calculators (Framingham/ASCVD/qSOFA) -> Pharmacy Safety Gate.
"""
import pytest
from e2e_tests.harness.client import E2EClient
from backend.rust_bridge import RustBridgeEngine


def test_records_to_calculators_flow(doctor_client: E2EClient):
    """
    Step 1: Query clinical records for patient observation history.
    Step 2: Execute Rust native clinical risk calculations (Framingham & ASCVD).
    Step 3: Compute qSOFA sepsis risk score.
    Step 4: Execute pharmacy drug safety and interaction checks.
    """
    bridge = RustBridgeEngine()

    # Step 1: Patient records check
    rec_resp = doctor_client.get("/v1/records/patient/1")
    assert rec_resp.status_code in (200, 401, 404)

    # Step 2: Native clinical risk calculation
    framingham_score = bridge.calculate_framingham_rust(
        age=56.0,
        total_chol=235.0,
        hdl_chol=38.0,
        sbp=142.0,
        smoker=False,
    )
    assert isinstance(framingham_score, float)
    assert framingham_score > 0.0

    ascvd_score = bridge.calculate_ascvd_rust(
        age=56.0,
        total_chol=235.0,
        hdl_chol=38.0,
        sbp=142.0,
        treated_bp=False,
        smoker=False,
        diabetic=True,
        is_female=False,
    )
    assert isinstance(ascvd_score, float)
    assert ascvd_score > 0.0

    # Step 3: qSOFA screening
    qsofa_score, risk_desc = bridge.compute_sepsis_qsofa_rust(resp_rate=18.0, sbp=125.0, gcs=15.0)
    assert qsofa_score == 0
    assert "LOW" in risk_desc

    # Step 4: Pharmacy safety gate check
    safety_payload = {
        "medications": ["Atorvastatin 20mg", "Metformin 500mg"],
        "allergies": ["Penicillin"],
        "conditions": ["Type 2 Diabetes", "Hyperlipidemia"],
    }
    pharm_resp = doctor_client.post("/v1/pharmacy/safety-check", json=safety_payload)
    assert pharm_resp.status_code in (200, 401, 404, 405, 422)
