"""
Unit tests for Atlanta Pancreatitis Classifier
"""

from backend.ml.atlanta_pancreatitis_classifier import atlanta_classifier


def test_classify_pancreatitis_severity_severe():
    res = atlanta_classifier.classify_pancreatitis_severity(
        transient_organ_failure_under_48h=True,
        persistent_organ_failure_over_48h=True,
        local_complications_necrosis_fluid_collection=True,
    )
    assert res["atlanta_severity_grade"] == "SEVERE_ACUTE_PANCREATITIS"
    assert res["persistent_organ_failure_present"] is True
    assert res["icu_transfer_indicated"] is True


def test_classify_pancreatitis_severity_mild():
    res = atlanta_classifier.classify_pancreatitis_severity(
        transient_organ_failure_under_48h=False,
        persistent_organ_failure_over_48h=False,
        local_complications_necrosis_fluid_collection=False,
    )
    assert res["atlanta_severity_grade"] == "MILD_ACUTE_PANCREATITIS"
    assert res["icu_transfer_indicated"] is False
