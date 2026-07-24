"""
Multi-Omics & Genomic Variant Risk Analysis Engine
===================================================
Parses Variant Call Format (VCF) files and maps Single Nucleotide Polymorphisms (SNPs)
and genomic risk alleles (e.g., APOE4, TCF7L2, BRCA1, LPL) to quantitative polygenic risk scores (PRS).
Completely local, privacy-first, zero external API dependency.
"""

from typing import Dict, List

# Key Clinical Variant Polygenic Risk Map (rsID -> Disease Risk Impact)
CLINICAL_VARIANT_CATALOG: Dict[str, Dict[str, any]] = {
    "rs7903146": {
        "gene": "TCF7L2",
        "condition": "diabetes",
        "risk_allele": "T",
        "odds_ratio": 1.45,
        "description": "Transcription factor 7-like 2 variant strongly associated with Type 2 Diabetes Mellitus.",
    },
    "rs429358": {
        "gene": "APOE",
        "condition": "heart",
        "risk_allele": "C",
        "odds_ratio": 1.68,
        "description": "Apolipoprotein E e4 allele conferring increased risk of dyslipidemia and cardiovascular events.",
    },
    "rs10757278": {
        "gene": "CDKN2A/B",
        "condition": "heart",
        "risk_allele": "G",
        "odds_ratio": 1.28,
        "description": "Chromosome 9p21 locus associated with early-onset coronary artery disease.",
    },
    "rs1801282": {
        "gene": "PPARG",
        "condition": "diabetes",
        "risk_allele": "C",
        "odds_ratio": 1.22,
        "description": "Peroxisome proliferator-activated receptor gamma Pro12Ala metabolic variant.",
    },
    "rs738409": {
        "gene": "PNPLA3",
        "condition": "liver",
        "risk_allele": "G",
        "odds_ratio": 1.85,
        "description": "Patatin-like phospholipase domain-containing 3 variant linked to non-alcoholic fatty liver disease (NAFLD).",
    },
    "rs6025": {
        "gene": "F5",
        "condition": "lungs",
        "risk_allele": "T",
        "odds_ratio": 2.10,
        "description": "Factor V Leiden variant associated with pulmonary embolism and venous thromboembolism.",
    },
}


class GenomicRiskEngine:
    """Evaluates VCF genomic variant files and computes polygenic risk scores."""

    def __init__(self):
        self.catalog = CLINICAL_VARIANT_CATALOG

    def parse_vcf_content(self, vcf_text: str) -> List[Dict[str, str]]:
        """Parses raw VCF text content into structured variant dicts."""
        variants = []
        lines = vcf_text.strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 5:
                chrom, pos, rsid, ref, alt = parts[0], parts[1], parts[2], parts[3], parts[4]
                variants.append({
                    "chrom": chrom,
                    "pos": pos,
                    "rsid": rsid,
                    "ref": ref,
                    "alt": alt,
                })
        return variants

    def evaluate_polygenic_risk(self, vcf_text: str) -> Dict[str, any]:
        """Computes polygenic risk scores across clinical conditions based on detected variants."""
        parsed_variants = self.parse_vcf_content(vcf_text)
        detected_variants = []
        risk_multipliers = {
            "diabetes": 1.0,
            "heart": 1.0,
            "liver": 1.0,
            "lungs": 1.0,
            "kidney": 1.0,
        }

        for v in parsed_variants:
            rsid = v["rsid"]
            if rsid in self.catalog:
                entry = self.catalog[rsid]
                condition = entry["condition"]
                alt_alleles = v["alt"].split(",")
                if entry["risk_allele"] in alt_alleles:
                    detected_variants.append({
                        "rsid": rsid,
                        "gene": entry["gene"],
                        "condition": condition,
                        "detected_allele": entry["risk_allele"],
                        "odds_ratio": entry["odds_ratio"],
                        "description": entry["description"],
                    })
                    risk_multipliers[condition] *= entry["odds_ratio"]

        # Calculate normalized polygenic risk percentiles
        prs_scores = {}
        for cond, mult in risk_multipliers.items():
            prs_percentile = min(99.9, round((mult - 1.0) * 50 + 50, 1)) if mult > 1.0 else 50.0
            prs_scores[cond] = {
                "risk_multiplier": round(mult, 2),
                "polygenic_risk_percentile": prs_percentile,
                "risk_category": "HIGH" if prs_percentile >= 75 else ("ELEVATED" if prs_percentile >= 60 else "NORMAL"),
            }

        return {
            "total_variants_parsed": len(parsed_variants),
            "clinical_variants_identified": len(detected_variants),
            "detected_variants": detected_variants,
            "polygenic_risk_scores": prs_scores,
        }


# Singleton engine instance
genomics_engine = GenomicRiskEngine()
