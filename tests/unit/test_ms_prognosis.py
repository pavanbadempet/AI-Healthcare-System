"""
Unit tests for Multiple Sclerosis 10-Year Disability Predictor
"""

from backend.ml.ms_prognosis_disability_engine import ms_prognosis_engine


def test_predict_10yr_edss6_risk_high():
    res = ms_prognosis_engine.predict_10yr_edss6_risk(
        age_at_onset_years=42,
        relapse_count_first_2_years=3,
        t2_lesions_count_mri=14,
        spinal_cord_lesions_present=True,
        csf_oligoclonal_bands_positive=True,
    )
    assert res["prognostic_risk_score"] == 10
    assert res["ten_year_edss6_disability_risk_percent"] == 68.0
    assert res["high_efficacy_dmt_indicated"] is True
    assert "High-Efficacy Monoclonal Antibody" in res["clinical_recommendation"]


def test_predict_10yr_edss6_risk_low():
    res = ms_prognosis_engine.predict_10yr_edss6_risk(
        age_at_onset_years=24,
        relapse_count_first_2_years=0,
        t2_lesions_count_mri=1,
        csf_oligoclonal_bands_positive=False,
    )
    assert res["prognostic_risk_score"] == 0
    assert res["ten_year_edss6_disability_risk_percent"] == 12.0
    assert res["high_efficacy_dmt_indicated"] is False
