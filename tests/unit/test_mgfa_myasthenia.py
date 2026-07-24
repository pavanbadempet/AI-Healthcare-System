"""
Unit tests for MGFA Myasthenia Gravis Engine
"""

from backend.ml.mgfa_myasthenia_gravis_engine import mgfa_engine


def test_classify_mgfa_grade_crisis():
    res = mgfa_engine.classify_mgfa_grade(
        intubation_respiratory_failure=True,
    )
    assert res["mgfa_class"] == "CLASS_V_MYASTHENIC_CRISIS"
    assert res["myasthenic_crisis_present"] is True
    assert res["plex_or_ivig_indicated"] is True
    assert "Therapeutic Plasma Exchange" in res["clinical_recommendation"]


def test_classify_mgfa_grade_ocular():
    res = mgfa_engine.classify_mgfa_grade(
        ocular_muscle_weakness_only=True,
    )
    assert res["mgfa_class"] == "CLASS_I_OCULAR"
    assert res["myasthenic_crisis_present"] is False
    assert res["plex_or_ivig_indicated"] is False
