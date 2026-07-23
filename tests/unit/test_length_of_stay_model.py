"""
Unit tests for Length of Stay Predictor Model
"""

import pytest
from backend.ml.length_of_stay_model import LengthOfStayModel, los_model


def test_predict_length_of_stay_low():
    res = los_model.predict_length_of_stay(
        age=35,
        is_icu_admission=False,
        charlson_comorbidity_index=0,
    )
    assert res["predicted_los_days"] < 4.0
    assert res["complexity_tier"] == "LOW"


def test_predict_length_of_stay_high():
    res = los_model.predict_length_of_stay(
        age=75,
        is_icu_admission=True,
        charlson_comorbidity_index=4,
        admission_systolic_bp=190.0,
    )
    assert res["predicted_los_days"] >= 7.0
    assert res["complexity_tier"] == "HIGH"
    assert res["discharge_planning_flag"] is True
