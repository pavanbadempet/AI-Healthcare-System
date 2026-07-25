"""
Unit tests for SOTA Genomic VEP Engine (backend/sota_genomic_vep_layer.py).
"""

from backend.sota_genomic_vep_layer import SOTAGenomicVEPLayerEngine


def test_genomic_variant_annotation():
    engine = SOTAGenomicVEPLayerEngine()

    v_id = "chr7:140453136:A>T"
    result = engine.annotate_genomic_variant(v_id)

    assert result.variant_id == v_id
    assert result.gene_symbol == "BRAF"
    assert result.clinical_significance == "PATHOGENIC"
    assert result.is_pathogenic
    assert result.annotation_time_us >= 0.0
