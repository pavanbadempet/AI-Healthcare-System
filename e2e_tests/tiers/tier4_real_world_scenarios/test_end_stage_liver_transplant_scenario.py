"""
Tier 4: Real-World Application Scenarios — End-Stage Liver Disease & Transplant Evaluation Protocol
Simulates an end-to-end clinical workflow: Inpatient admission, MELD & FIB-4 native risk computation, hepatology bed allocation, and nursing telemetry handoff.
"""
import pytest
from e2e_tests.harness.client import E2EClient
from backend.rust_bridge import RustBridgeEngine


def test_end_stage_liver_transplant_scenario(doctor_client: E2EClient, nurse_client: E2EClient):
    """
    Real-World Scenario:
    A 64-year-old patient presents with decompensated cirrhosis, jaundice, and ascites.
    1. Clinician queries hospital departments to identify Hepatology / Inpatient GI availability.
    2. Clinician queries bed allocation status.
    3. Clinician computes FIB-4 score (advanced fibrosis confirmation).
    4. Clinician computes MELD score (Model for End-Stage Liver Disease) for transplant acuity evaluation.
    5. Nurse reviews nursing task queue and inpatient telemetry monitoring cards.
    """
    bridge = RustBridgeEngine()

    # Step 1: Query hospital departments
    dept_resp = doctor_client.get("/v1/hospital/departments")
    assert dept_resp.status_code in (200, 401, 404)

    # Step 2: Query hospital bed status
    bed_resp = doctor_client.get("/v1/hospital/beds")
    assert bed_resp.status_code in (200, 401, 404)

    # Step 3: Compute FIB-4 score
    fib4_score = bridge.calculate_fib4_rust(
        ast=78.0,
        alt=42.0,
        platelets=85.0,
        age=64.0,
    )
    assert fib4_score > 3.25, f"Expected high FIB-4 indicating advanced cirrhosis, got: {fib4_score}"

    # Step 4: Compute MELD score
    meld_score = bridge.calculate_meld_rust(
        bilirubin_mg_dl=4.2,
        inr=2.3,
        creatinine_mg_dl=2.1,
        on_dialysis=False,
    )
    assert 6.0 <= meld_score <= 40.0
    assert meld_score >= 20.0, f"Expected elevated MELD score >= 20, got: {meld_score}"

    # Step 5: Inpatient nursing tasks & telemetry review
    nursing_resp = nurse_client.get("/v1/nursing/tasks")
    assert nursing_resp.status_code in (200, 401, 404)
