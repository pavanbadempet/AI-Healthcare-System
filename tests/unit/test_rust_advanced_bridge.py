"""
Unit tests for Advanced Rust Execution Engines:
- ECG Pan-Tompkins R-Peak Detection & HRV
- DICOM Pixel Matrix Normalization (HU + VOI LUT)
- FHIR Base85 Binary Compression & Decompression
"""

import math
from backend.rust_bridge import rust_bridge


def test_rust_ecg_pan_tompkins_and_hrv():
    # Generate 5 seconds of synthetic 250Hz ECG with 5 simulated QRS spikes
    sampling_rate = 250.0
    duration_s = 4.0
    total_samples = int(duration_s * sampling_rate)
    t = [i / sampling_rate for i in range(total_samples)]

    # Baseline sine + 4 sharp peaks at 0.8s, 1.6s, 2.4s, 3.2s
    signal = [0.1 * math.sin(2 * math.pi * 1.0 * ti) for ti in t]
    spike_times = [0.8, 1.6, 2.4, 3.2]
    for st in spike_times:
        idx = int(st * sampling_rate)
        if 0 <= idx < len(signal):
            signal[idx] = 2.5
            if idx > 0: signal[idx-1] = 0.8
            if idx + 1 < len(signal): signal[idx+1] = 0.8

    r_peaks = rust_bridge.detect_ecg_r_peaks_rust(signal, sampling_rate)
    assert len(r_peaks) >= 3

    hr, sdnn, rmssd, pnn50 = rust_bridge.compute_hrv_metrics_rust(r_peaks, sampling_rate)
    assert 50.0 <= hr <= 100.0
    assert sdnn >= 0.0
    assert rmssd >= 0.0


def test_rust_dicom_pixel_normalization():
    raw_pixels = [0.0, 100.0, 500.0, 1000.0]
    # Rescale slope = 1.0, intercept = -1000 (standard CT HU)
    # Window Center = 40, Window Width = 400 (Standard Soft Tissue Window)
    # Lower = 40 - 200 = -160, Upper = 40 + 200 = 240
    normalized = rust_bridge.normalize_dicom_pixels_rust(
        raw_pixels, rescale_slope=1.0, rescale_intercept=-1000.0,
        window_center=40.0, window_width=400.0
    )
    assert len(normalized) == 4
    for val in normalized:
        assert 0.0 <= val <= 1.0


def test_rust_fhir_bundle_compression_and_decompression():
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "PATIENT-RUST-001",
                    "gender": "female",
                    "birthDate": "1980-05-12"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"code": "8867-4", "display": "Heart rate"}]},
                    "valueQuantity": {"value": 74, "unit": "beats/minute"}
                }
            }
        ]
    }

    b85_str, orig_sz, comp_sz, ratio = rust_bridge.compress_fhir_bundle_rust(fhir_bundle)
    assert isinstance(b85_str, str)
    assert len(b85_str) > 0
    assert comp_sz < orig_sz

    decompressed = rust_bridge.decompress_fhir_bundle_rust(b85_str)
    assert decompressed["resourceType"] == "Bundle"
    assert decompressed["entry"][0]["resource"]["id"] == "PATIENT-RUST-001"
