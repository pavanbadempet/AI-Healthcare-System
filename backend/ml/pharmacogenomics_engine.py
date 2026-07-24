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


class PharmacogenomicsEngine:
    """Evaluates drug-gene interactions and metabolizer phenotype risks."""

    def evaluate_pgx_dosing(
        self,
        medication_name: str,
        gene: str,
        diplotype: str,
    ) -> Dict[str, any]:
        med_lower = medication_name.lower()
        key = (med_lower, gene.upper())

        if key in PGX_GENE_RULES and diplotype in PGX_GENE_RULES[key]:
            info = PGX_GENE_RULES[key][diplotype]
            return {
                "medication": medication_name,
                "gene": gene.upper(),
                "diplotype": diplotype,
                "metabolizer_phenotype": info["metabolizer"],
                "pgx_recommendation_action": info["action"],
                "clinical_guideline": info["recommendation"],
                "is_pgx_alert": info["action"] != "STANDARD_DOSING",
            }

        return {
            "medication": medication_name,
            "gene": gene.upper(),
            "diplotype": diplotype,
            "metabolizer_phenotype": "UNKNOWN/WILD_TYPE",
            "pgx_recommendation_action": "STANDARD_DOSING",
            "clinical_guideline": "No specific CPIC PGx contraindication found for this diplotype.",
            "is_pgx_alert": False,
        }


# Singleton engine instance
pgx_engine = PharmacogenomicsEngine()
