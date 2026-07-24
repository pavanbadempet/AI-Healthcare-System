"""
Unit tests for Genomic Variant Annotation Engine
"""

from backend.ml.variant_annotation_engine import variant_annotation_engine


def test_annotate_variant_actionable():
    res = variant_annotation_engine.annotate_variant("chr7:55259515:T>G")
    assert res["gene"] == "EGFR"
    assert res["pathogenicity"] == "Pathogenic"
    assert res["actionable"] is True
    assert "Osimertinib" in res["recommended_therapies"]


def test_annotate_variant_vus():
    res = variant_annotation_engine.annotate_variant("chr1:10000:A>G")
    assert res["actionable"] is False
    assert res["status"] == "ANNOTATED_VUS"
