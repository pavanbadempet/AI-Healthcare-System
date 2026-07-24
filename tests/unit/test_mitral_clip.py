"""
Unit tests for Percutaneous MitraClip Engine
"""

from backend.ml.mitral_clip_mitraclip_engine import mitraclip_engine


def test_evaluate_mitraclip_eligibility_coapt():
    res = mitraclip_engine.evaluate_mitraclip_eligibility(
        effective_regurgitant_orifice_area_eroa_cm2=0.42,
        left_ventricular_ejection_fraction_lvef_percent=35.0,
        left_ventricular_end_systolic_volume_index_lvesvi_mL_m2=75.0,
        mitral_valve_area_mva_cm2=4.5,
    )
    assert res["coapt_trial_eligible"] is True
    assert res["mitraclip_teer_indicated"] is True
    assert res["teer_phenotype"] == "COAPT_OPTIMAL_TEER_CANDIDATE"
    assert "Optimal Candidate for MitraClip TEER" in res["clinical_recommendation"]


def test_evaluate_mitraclip_eligibility_suboptimal():
    res = mitraclip_engine.evaluate_mitraclip_eligibility(
        effective_regurgitant_orifice_area_eroa_cm2=0.25,
        left_ventricular_ejection_fraction_lvef_percent=18.0,
        left_ventricular_end_systolic_volume_index_lvesvi_mL_m2=110.0,
        mitral_valve_area_mva_cm2=3.8,
    )
    assert res["coapt_trial_eligible"] is False
    assert res["mitraclip_teer_indicated"] is False
    assert res["teer_phenotype"] == "SUBOPTIMAL_TEER_PROFILE_SEVERE_LV_DILATATION"
