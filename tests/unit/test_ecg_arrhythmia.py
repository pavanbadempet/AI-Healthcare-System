"""
Unit tests for Continuous ECG Arrhythmia Classifier
"""

from backend.ml.ecg_arrhythmia_classifier import ecg_classifier


def test_classify_vtach():
    res = ecg_classifier.classify_rhythm_segment(
        heart_rate_bpm=160,
        rr_interval_std_ms=45.0,
        qrs_duration_ms=140.0,
        p_wave_present=False,
    )
    assert res["rhythm_classification"] == "VENTRICULAR_TACHYCARDIA"
    assert res["urgency_level"] == "EMERGENCY_STAT"
    assert res["requires_telemetry_alarm"] is True


def test_classify_normal():
    res = ecg_classifier.classify_rhythm_segment(
        heart_rate_bpm=72,
        rr_interval_std_ms=30.0,
        qrs_duration_ms=90.0,
        p_wave_present=True,
    )
    assert res["rhythm_classification"] == "NORMAL_SINUS_RHYTHM"
    assert res["requires_telemetry_alarm"] is False
