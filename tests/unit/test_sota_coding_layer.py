"""
Unit tests for SOTA Clinical Medical Coding Engine (backend/sota_coding_layer.py).
"""

from backend.sota_coding_layer import SOTACodingLayerEngine


def test_medical_ontology_mapping_and_drg_calculation():
    engine = SOTACodingLayerEngine()

    clinical_note = "Patient has history of hypertension and diabetes."
    codes = engine.map_text_to_codes(clinical_note)

    assert len(codes) == 2
    assert codes[0].code == "I10"
    assert codes[1].code == "E11.9"

    drg_summary = engine.calculate_drg_summary(codes)
    assert drg_summary.drg_code == "DRG-305"
    assert drg_summary.severity_weight == 0.85
