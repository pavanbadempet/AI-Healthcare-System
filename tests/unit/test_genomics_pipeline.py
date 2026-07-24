"""
Unit tests for Multi-Omics & Genomic Variant Risk Pipeline
"""

from backend.ml.genomics_variant_pipeline import genomics_engine

SAMPLE_VCF_DATA = """##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr10	114758349	rs7903146	C	T	99	PASS	GENE=TCF7L2
chr19	45411941	rs429358	T	C	99	PASS	GENE=APOE
chr22	50364718	rs6025	C	T	99	PASS	GENE=F5
chr1	1234567	rs999999	A	G	99	PASS	GENE=UNKNOWN
"""


def test_parse_vcf_content():
    variants = genomics_engine.parse_vcf_content(SAMPLE_VCF_DATA)
    assert len(variants) == 4
    assert variants[0]["rsid"] == "rs7903146"
    assert variants[0]["alt"] == "T"


def test_evaluate_polygenic_risk():
    res = genomics_engine.evaluate_polygenic_risk(SAMPLE_VCF_DATA)
    assert res["total_variants_parsed"] == 4
    assert res["clinical_variants_identified"] == 3
    assert "diabetes" in res["polygenic_risk_scores"]
    assert res["polygenic_risk_scores"]["diabetes"]["risk_category"] in ["ELEVATED", "HIGH"]
    assert res["polygenic_risk_scores"]["heart"]["risk_multiplier"] > 1.0
