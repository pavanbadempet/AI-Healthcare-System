"""
Unit tests for Primary Progressive Aphasia Variant Classifier Engine
"""

from backend.ml.ppa_variant_classifier_engine import ppa_classifier_engine


def test_classify_nfvppa():
    res = ppa_classifier_engine.classify_ppa_variant(
        agrammatic_speech=True,
        effortful_speech_halting=True,
        impaired_single_word_comprehension=False,
    )
    assert res["ppa_variant"] == "NON_FLUENT_AGRAMMATIC_PPA_NFVPPA"
    assert "TAU_OPATHY" in res["associated_pathology"]


def test_classify_svppa():
    res = ppa_classifier_engine.classify_ppa_variant(
        surface_dyslexia_present=True,
        impaired_single_word_comprehension=True,
        impaired_confrontational_naming=True,
    )
    assert res["ppa_variant"] == "SEMANTIC_VARIANT_PPA_SVPPA"
    assert "TDP43" in res["associated_pathology"]
