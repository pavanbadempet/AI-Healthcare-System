"""
Unit tests for Histopathology Analyzer
"""

from backend.ml.histopathology_analyzer import histopathology_analyzer


def test_analyze_biopsy_patches_grade3():
    res = histopathology_analyzer.analyze_biopsy_patches(
        slide_id="WSI-2026-99",
        patch_count=500,
        mean_nuclear_atypia_score=0.85,
        ki67_positive_ratio=0.55,
        til_density_per_mm2=320.0,
    )
    assert res["histological_grade"] == "GRADE_3_POORLY_DIFFERENTIATED"
    assert res["tumor_microenvironment"] == "HIGH_IMMUNE_INFILTRATE"
    assert res["ki67_index_percent"] == 55.0


def test_analyze_biopsy_patches_grade1():
    res = histopathology_analyzer.analyze_biopsy_patches(
        slide_id="WSI-2026-01",
        patch_count=200,
        mean_nuclear_atypia_score=0.2,
        ki67_positive_ratio=0.08,
        til_density_per_mm2=50.0,
    )
    assert res["histological_grade"] == "GRADE_1_WELL_DIFFERENTIATED"
    assert res["tumor_microenvironment"] == "LOW_IMMUNE_INFILTRATE"
