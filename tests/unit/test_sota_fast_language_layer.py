"""
Unit tests for SOTA Fast Language Engine (backend/sota_fast_language_layer.py).
"""

from backend.sota_fast_language_layer import SOTAFastLanguageLayerEngine


def test_clinical_tokenization_and_medical_term_matching():
    engine = SOTAFastLanguageLayerEngine()

    clinical_note = "Patient presents with acute hypertension and fever."
    output = engine.tokenize_clinical_text(clinical_note)

    assert output.token_count == 7
    assert "hypertension" in output.matched_medical_terms
    assert "fever" in output.matched_medical_terms
