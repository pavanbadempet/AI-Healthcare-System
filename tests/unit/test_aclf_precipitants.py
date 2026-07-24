"""
Unit tests for Gastroenterology ACLF Precipitants Engine
"""

from backend.ml.aclf_precipitants_trigger_engine import aclf_precipitants_engine


def test_evaluate_aclf_sbp_trigger():
    res = aclf_precipitants_engine.evaluate_aclf_triggers(
        cirrhosis_confirmed=True,
        ascites_polymorphonuclear_count_per_uL=380.0,
        fever_or_leukocytosis=True,
        recent_heavy_alcohol_use=False,
    )
    assert res["sbp_confirmed"] is True
    assert "SPONTANEOUS_BACTERIAL_PERITONITIS" in res["identified_triggers"]
    assert "Ceftriaxone" in res["clinical_recommendation"]
    assert "Albumin" in res["clinical_recommendation"]


def test_evaluate_aclf_alcoholic_hepatitis_trigger():
    res = aclf_precipitants_engine.evaluate_aclf_triggers(
        cirrhosis_confirmed=True,
        ascites_polymorphonuclear_count_per_uL=80.0,
        fever_or_leukocytosis=False,
        recent_heavy_alcohol_use=True,
        maddrey_discriminant_function=45.2,
    )
    assert res["severe_alcoholic_hepatitis"] is True
    assert "SEVERE_ACUTE_ALCOHOLIC_HEPATITIS" in res["identified_triggers"]
    assert "Prednisolone" in res["clinical_recommendation"]
