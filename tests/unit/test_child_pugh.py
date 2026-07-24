"""
Unit tests for Child-Pugh Calculator
"""

from backend.ml.child_pugh_calculator import child_pugh_calculator


def test_calculate_child_pugh_score_class_c():
    res = child_pugh_calculator.calculate_child_pugh_score(
        bilirubin_mg_dL=3.5,
        albumin_g_dL=2.4,
        inr=2.5,
        ascites_severity="MODERATE_SEVERE",
        encephalopathy_grade=3,
    )
    assert res["child_pugh_score"] == 15
    assert res["child_pugh_class"] == "CLASS_C"
    assert res["liver_transplantation_eval_indicated"] is True
    assert res["one_year_survival_percent"] == 45.0


def test_calculate_child_pugh_score_class_a():
    res = child_pugh_calculator.calculate_child_pugh_score(
        bilirubin_mg_dL=1.2,
        albumin_g_dL=4.0,
        inr=1.1,
        ascites_severity="NONE",
        encephalopathy_grade=0,
    )
    assert res["child_pugh_score"] == 5
    assert res["child_pugh_class"] == "CLASS_A"
    assert res["liver_transplantation_eval_indicated"] is False
