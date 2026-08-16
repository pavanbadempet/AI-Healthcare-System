"""
Pharmacogenomics (PGx) Drug-Gene Interaction Engine
=====================================================
Evaluates patient genotype variants (CYP2D6, CYP2C19, TPMT, HLA-B*5701) against
FDA CPIC PGx guidelines to flag poor/ultrafast metabolizer risks and dosing changes.
"""

from typing import Dict

PGX_GENE_RULES = {
    ("clopidogrel", "CYP2C19"): {
        "*2/*2": {"metabolizer": "POOR", "action": "CONTRAINDICATED", "recommendation": "Use Prasugrel or Ticagrelor. High risk of stent thrombosis."},
        "*1/*1": {"metabolizer": "EXTENSIVE", "action": "STANDARD_DOSING", "recommendation": "Standard Clopidogrel 75mg daily."},
    },
    ("codeine", "CYP2D6"): {
        "*1/*1xN": {"metabolizer": "ULTRAFAST", "action": "CONTRAINDICATED", "recommendation": "High risk of severe morphine toxicity/respiratory depression."},
        "*4/*4": {"metabolizer": "POOR", "action": "INEFFECTIVE", "recommendation": "Analgesic failure due to lack of conversion to morphine. Use alternative."},
    },
}


from backend.rust_bridge import rust_bridge


class PharmacogenomicsEngine:
    """Evaluates drug-gene interactions and metabolizer phenotype risks via Rust / Fallback."""

    def evaluate_pgx_dosing(
        self,
        medication_name: str,
        gene: str,
        diplotype: str,
    ) -> Dict[str, any]:
        return rust_bridge.match_pgx_diplotype_rust(medication_name, gene, diplotype, PGX_GENE_RULES)


# Singleton engine instance
pgx_engine = PharmacogenomicsEngine()
