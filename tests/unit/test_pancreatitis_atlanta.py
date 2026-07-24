"""
Unit tests for Acute Pancreatitis Atlanta Classification Engine
"""

from backend.ml.acute_pancreatitis_atlanta_classification_engine import pancreatitis_atlanta_engine


def test_classify_severe_pancreatitis():
    res = pancreatitis_atlanta_engine.classify_atlanta_pancreatitis(
        organ_failure_duration_hours=72.0,
        respiratory_pao2_fio2_ratio=210.0,
        renal_serum_creatinine_mg_dL=2.4,
    )
    assert res["organ_failure_present"] is True
    assert res["atlanta_severity"] == "SEVERE_ACUTE_PANCREATITIS"
    assert res["icu_admission_indicated"] is True


def test_classify_mild_pancreatitis():
    res = pancreatitis_atlanta_engine.classify_atlanta_pancreatitis(
        respiratory_pao2_fio2_ratio=380.0,
        renal_serum_creatinine_mg_dL=0.9,
    )
    assert res["organ_failure_present"] is False
    assert res["atlanta_severity"] == "MILD_ACUTE_PANCREATITIS"
