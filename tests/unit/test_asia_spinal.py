"""
Unit tests for ASIA Spinal Injury Engine
"""

from backend.ml.asia_spinal_injury_engine import asia_spinal_engine


def test_classify_asia_impairment_scale_complete():
    res = asia_spinal_engine.classify_asia_impairment_scale(
        sacral_sensory_sparing_s4_s5=False,
        deep_anal_pressure_present=False,
        voluntary_anal_sphincter_contraction=False,
        motor_function_spared_below_neurological_level=False,
        more_than_half_key_muscles_grade_3_or_more=False,
        neurological_level_of_injury="C5",
    )
    assert res["asia_impairment_grade"] == "ASIA_GRADE_A_COMPLETE"
    assert res["sacral_sparing_present"] is False
    assert res["urgent_spinal_decompression_indicated"] is True
    assert "ASIA Grade A" in res["clinical_recommendation"]


def test_classify_asia_impairment_scale_incomplete_d():
    res = asia_spinal_engine.classify_asia_impairment_scale(
        sacral_sensory_sparing_s4_s5=True,
        deep_anal_pressure_present=True,
        voluntary_anal_sphincter_contraction=True,
        motor_function_spared_below_neurological_level=True,
        more_than_half_key_muscles_grade_3_or_more=True,
        neurological_level_of_injury="L1",
    )
    assert res["asia_impairment_grade"] == "ASIA_GRADE_D_INCOMPLETE"
    assert res["sacral_sparing_present"] is True
