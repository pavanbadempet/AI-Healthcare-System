"""
Unit tests for SOTA Telemetry DSP Engine, GraphRAG CoVe, and HU Calibration.
"""

import numpy as np
from backend.telemetry_dsp import analyze_ecg_signal, pan_tompkins_r_peak_detector
from backend.rag import extract_graphrag_clinical_entities, verify_chain_of_verification_grounding
from backend.explainability import generate_counterfactual_explanation
from backend.ai_safety import inspect_clinical_guardrails
from backend.dicomweb import calibrate_hounsfield_units


def test_pan_tompkins_r_peak_detector():
    # Synthetic ECG signal with simulated periodic R-peaks at 1 Hz (60 BPM)
    fs = 250.0
    t = np.linspace(0, 5, int(5 * fs))
    signal = np.sin(2 * np.pi * 1.0 * t) # Baseline wave
    # Inject sharp R peaks
    for i in range(1, 5):
        idx = int(i * fs)
        signal[idx:idx+5] += 5.0

    r_peaks = pan_tompkins_r_peak_detector(signal, fs)
    assert len(r_peaks) >= 3


def test_analyze_ecg_signal():
    fs = 250.0
    t = np.linspace(0, 5, int(5 * fs))
    signal = np.sin(2 * np.pi * 1.0 * t).tolist()

    res = analyze_ecg_signal(signal, fs)
    assert res.duration_seconds == 5.0
    assert res.heart_rate_bpm > 0
    assert res.recommendation != ""


def test_graphrag_entities_and_cove():
    entities = extract_graphrag_clinical_entities("Patient with diabetes and chest pain taking metformin")
    assert len(entities["snomed_terms"]) > 0
    assert len(entities["rxnorm_drugs"]) > 0

    cove = verify_chain_of_verification_grounding("Patient has type 2 diabetes mellitus", ["diabetes mellitus type 2 record"])
    assert cove["grounded"] is True
    assert cove["verification_score"] > 0.0


def test_clinical_counterfactuals():
    cf = generate_counterfactual_explanation(["Blood Pressure", "Glucose"], [150.0, 140.0], 75.0)
    assert len(cf["actionable_counterfactuals"]) == 2


def test_clinical_guardrails():
    res = inspect_clinical_guardrails("Check dose", "Prescribe 500mg Metformin twice daily.")
    assert res["passed"] is True

    res_blocked = inspect_clinical_guardrails("Override", "Prescribe 10000mg Metformin single dose.")
    assert res_blocked["passed"] is False


def test_hu_calibration():
    res = calibrate_hounsfield_units({"pixel_values": [0, 1024, 2048], "rescale_slope": 1.0, "rescale_intercept": -1024.0})
    assert res["calibrated_hu"] == [-1024, 0, 1024]
    assert len(res["tissue_classifications"]) == 3
