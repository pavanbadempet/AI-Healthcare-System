"""
Unit tests for SOTA Clinical AI Layer Engine (backend/sota_ai_layer.py).
"""

from backend.sota_ai_layer import SOTAAILayerEngine


def test_speculative_ai_inference_and_hybrid_rag():
    engine = SOTAAILayerEngine()

    docs = engine.hybrid_rag_retrieve("Hypertension drug treatment")
    assert len(docs) > 0
    assert "Hypertension" in docs[0]

    result = engine.execute_speculative_clinical_inference("What is first line for Hypertension?")

    assert result.speculative_tokens_accepted == 4
    assert result.throughput_tokens_per_sec > 100.0
    assert "DISCLAIMER" in result.safety_disclaimer
    assert "Hypertension" in result.clinical_insight
