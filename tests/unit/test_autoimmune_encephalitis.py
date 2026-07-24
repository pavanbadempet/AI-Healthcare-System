"""
Unit tests for Autoimmune Encephalitis Antibody Engine
"""

from backend.ml.autoimmune_encephalitis_antibody_engine import encephalitis_engine


def test_evaluate_nmdar_encephalitis():
    res = encephalitis_engine.evaluate_encephalitis(
        nmdar_antibody_positive=True,
        csf_pleocytosis_cells_uL=24.0,
        case_severity_score=8,
    )
    assert res["encephalitis_confirmed"] is True
    assert res["encephalitis_subtype"] == "ANTI_NMDAR_ENCEPHALITIS"
    assert "ovarian teratoma" in res["clinical_recommendation"]


def test_evaluate_refractory_rituximab():
    res = encephalitis_engine.evaluate_encephalitis(
        lgi1_antibody_positive=True,
        refractory_to_first_line_immunotherapy=True,
    )
    assert res["encephalitis_confirmed"] is True
    assert "SECOND_LINE_RITUXIMAB" in res["recommended_immunotherapy"]
