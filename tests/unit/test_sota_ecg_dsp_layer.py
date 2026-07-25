"""
Unit tests for SOTA ECG DSP Engine (backend/sota_ecg_dsp_layer.py).
"""

from backend.sota_ecg_dsp_layer import SOTAECGDSPCompilerEngine


def test_ecg_qrs_peak_detection_and_arrhythmia_filtering():
    engine = SOTAECGDSPCompilerEngine()

    raw_ecg = [0.1, 0.2, 1.5, 0.1, 0.1, 0.2, 1.4, 0.1]
    result = engine.process_ecg_stream(raw_ecg)

    assert result.sample_count == 8
    assert len(result.detected_qrs_peaks) >= 1
    assert result.heart_rate_bpm > 0.0
    assert result.processing_time_us >= 0.0
