"""
Unit tests for ALS King's & MiToS Staging Engine
"""

from backend.ml.als_kings_mitos_staging_engine import als_staging_engine


def test_calculate_als_kings_stage_3():
    res = als_staging_engine.calculate_als_staging(
        bulbar_involvement=True,
        cervical_upper_limb_involvement=True,
        lumbosacral_lower_limb_involvement=True,
    )
    assert res["kings_stage"] == "STAGE_3_THREE_REGIONS"
    assert res["peg_indicated"] is True


def test_calculate_als_kings_stage_4b_niv():
    res = als_staging_engine.calculate_als_staging(
        bulbar_involvement=True,
        niv_ventilation_required=True,
    )
    assert res["kings_stage"] == "STAGE_4B_NIV_VENTILATION"
    assert "ADVANCED ALS" in res["clinical_recommendation"]
