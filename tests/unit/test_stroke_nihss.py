"""
Unit tests for Stroke NIHSS Evaluator
"""

from backend.ml.stroke_nihss_evaluator import stroke_evaluator


def test_evaluate_stroke_tpa_eligible():
    res = stroke_evaluator.evaluate_stroke_tpa_eligibility(
        nihss_score=14,
        symptom_onset_hours_ago=2.0,
        has_intracranial_hemorrhage_on_ct=False,
        systolic_bp_mmHg=160,
    )
    assert res["stroke_severity_tier"] == "MODERATE_STROKE"
    assert res["tpa_thrombolysis_eligible"] is True
    assert res["mechanical_thrombectomy_eligible"] is True


def test_evaluate_stroke_tpa_contraindicated():
    res = stroke_evaluator.evaluate_stroke_tpa_eligibility(
        nihss_score=22,
        symptom_onset_hours_ago=5.0,
        has_intracranial_hemorrhage_on_ct=False,
    )
    assert res["tpa_thrombolysis_eligible"] is False
    assert "Symptom onset > 4.5 hours" in res["tpa_contraindications"][0]
