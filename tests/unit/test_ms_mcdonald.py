"""
Unit tests for MS McDonald 2017 Engine
"""

from backend.ml.ms_mcdonald_2017_engine import ms_mcdonald_engine


def test_evaluate_mcdonald_criteria_definite():
    res = ms_mcdonald_engine.evaluate_mcdonald_criteria(
        clinical_attacks_count=1,
        cns_regions_with_t2_lesions_dis_count=3,
        csf_oligoclonal_bands_positive=True,
    )
    assert res["dissemination_in_space_dis"] is True
    assert res["dissemination_in_time_dit"] is True
    assert res["mcdonald_2017_diagnosis"] == "DEFINITE_MULTIPLE_SCLEROSIS"
    assert res["disease_modifying_therapy_dmt_indicated"] is True
    assert "Disease-Modifying Therapy" in res["clinical_recommendation"]


def test_evaluate_mcdonald_criteria_cis():
    res = ms_mcdonald_engine.evaluate_mcdonald_criteria(
        clinical_attacks_count=1,
        cns_regions_with_t2_lesions_dis_count=2,
        csf_oligoclonal_bands_positive=False,
        simultaneous_gd_enhancing_and_non_enhancing_lesions_dit=False,
    )
    assert res["dissemination_in_space_dis"] is True
    assert res["dissemination_in_time_dit"] is False
    assert res["mcdonald_2017_diagnosis"] == "CLINICALLY_ISOLATED_SYNDROME_CIS"
    assert res["disease_modifying_therapy_dmt_indicated"] is True
