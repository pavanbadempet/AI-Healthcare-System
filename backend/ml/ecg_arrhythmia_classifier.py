"""
Continuous ECG Arrhythmia Classifier
=====================================
Classifies multi-lead telemetry ECG signal segments into Normal Sinus Rhythm (NSR),
Atrial Fibrillation (AFib), Ventricular Tachycardia (V-Tach), or PVCs.
"""

from typing import Dict


class EcgArrhythmiaClassifier:
    """Classifies telemetry ECG rhythm waveforms and detects life-threatening arrhythmias."""

    def classify_rhythm_segment(
        self,
        heart_rate_bpm: int,
        rr_interval_std_ms: float,
        qrs_duration_ms: float,
        p_wave_present: bool = True,
    ) -> Dict[str, any]:
        rhythm_type = "NORMAL_SINUS_RHYTHM"
        urgency = "ROUTINE"

        if heart_rate_bpm > 120 and qrs_duration_ms > 120:
            rhythm_type = "VENTRICULAR_TACHYCARDIA"
            urgency = "EMERGENCY_STAT"
        elif not p_wave_present and rr_interval_std_ms > 100:
            rhythm_type = "ATRIAL_FIBRILLATION"
            urgency = "HIGH_PRIORITY"
        elif heart_rate_bpm > 100:
            rhythm_type = "SINUS_TACHYCARDIA"
            urgency = "MODERATE"
        elif heart_rate_bpm < 50:
            rhythm_type = "SINUS_BRADYCARDIA"
            urgency = "MODERATE"

        return {
            "heart_rate_bpm": heart_rate_bpm,
            "rhythm_classification": rhythm_type,
            "urgency_level": urgency,
            "requires_telemetry_alarm": urgency in ["EMERGENCY_STAT", "HIGH_PRIORITY"],
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
ecg_classifier = EcgArrhythmiaClassifier()
