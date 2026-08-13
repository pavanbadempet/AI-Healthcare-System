"""
Precision Pharmacogenomics & CPIC Level A/B Drug-Gene Interaction Engine.
Cross-evaluates patient genetic alleles (CYP2D6, CYP2C19, SLCO1B1, VKORC1, HLA-B*5701)
against proposed pharmacotherapies to determine metabolic clearance rates and safe dosing adjustments.
"""

import logging
from typing import List, Dict, Any, Tuple
from backend.schemas.peak_healthcare import (
    PharmacogenomicProfile,
    PharmacogenomicEvaluationRequest,
    PharmacogenomicEvaluationResponse,
    DrugMetabolismReport
)

logger = logging.getLogger("backend.pharmacogenomics")


class PrecisionPharmacogenomicsEngine:
    """Evaluates CPIC Level A guidelines for gene-drug precision prescribing."""

    # Knowledge base of gene-drug interactions with CPIC recommendations
    CPIC_GENE_DRUG_MAP: Dict[str, Dict[str, Any]] = {
        "clopidogrel": {
            "gene": "CYP2C19",
            "phenotypes": {
                "Poor Metabolizer (*2/*2)": {
                    "implication": "Significantly diminished active metabolite formation; severely reduced platelet inhibition; high risk of stent thrombosis or secondary stroke.",
                    "action": "AVOID CLOPIDOGREL. Recommend alternative antiplatelet agent (Prasugrel or Ticagrelor) with normal platelet inhibition.",
                    "risk": "Critical Thromboembolic Failure Risk",
                    "contraindicated": True
                },
                "Intermediate Metabolizer (*1/*2)": {
                    "implication": "Moderate reduction in active thiol metabolite levels.",
                    "action": "Consider alternative antiplatelet (Ticagrelor) or standard clopidogrel with close P2Y12 platelet function monitoring.",
                    "risk": "Moderate Ischemic Risk",
                    "contraindicated": False
                },
                "Rapid Metabolizer (*1/*17)": {
                    "implication": "Normal to enhanced active metabolite formation.",
                    "action": "Initiate standard recommended dosing (75 mg/day).",
                    "risk": "Standard Safety Profile",
                    "contraindicated": False
                }
            }
        },
        "simvastatin": {
            "gene": "SLCO1B1",
            "phenotypes": {
                "Decreased Function (*5/*5)": {
                    "implication": "Marked reduction in hepatic OATP1B1 statin uptake, resulting in elevated systemic plasma simvastatin acid concentrations.",
                    "action": "HIGH RISK OF SEVERE MYOPATHY / RHABDOMYOLYSIS. Prescribe alternative statin (Rosuvastatin or Pravastatin) or lower dose (<=20 mg).",
                    "risk": "High Rhabdomyolysis Risk",
                    "contraindicated": True
                },
                "Normal Function (*1a/*1a)": {
                    "implication": "Normal hepatic clearance of statin molecules.",
                    "action": "Standard starting dose per clinical indication.",
                    "risk": "Standard Safety Profile",
                    "contraindicated": False
                }
            }
        },
        "codeine": {
            "gene": "CYP2D6",
            "phenotypes": {
                "Ultra-Rapid Metabolizer (*1/*1xN)": {
                    "implication": "Rapid, excessive biotransformation of prodrug codeine into morphine; risk of life-threatening respiratory depression.",
                    "action": "AVOID CODEINE. Risk of severe fatal opioid toxicity. Use non-opioid or non-CYP2D6 metabolized analgesic.",
                    "risk": "Fatal Respiratory Toxicity Risk",
                    "contraindicated": True
                },
                "Poor Metabolizer (*4/*4)": {
                    "implication": "Virtually no conversion to active morphine; complete absence of analgesic efficacy.",
                    "action": "AVOID CODEINE due to therapeutic failure. Use alternative analgesic.",
                    "risk": "Therapeutic Inefficacy",
                    "contraindicated": False
                },
                "Normal Metabolizer (*1/*1)": {
                    "implication": "Standard conversion to morphine.",
                    "action": "Standard age and weight-appropriate dosing.",
                    "risk": "Standard Safety Profile",
                    "contraindicated": False
                }
            }
        },
        "warfarin": {
            "gene": "VKORC1",
            "phenotypes": {
                "A/A (High Sensitivity)": {
                    "implication": "High sensitivity to vitamin K epoxide reductase inhibition; prolonged INR elevation.",
                    "action": "REDUCE INITIAL DOSE BY 50-70%. Frequent INR monitoring required.",
                    "risk": "Major Hemorrhage Risk",
                    "contraindicated": False
                },
                "G/G (Standard Warfarin Sensitivity)": {
                    "implication": "Standard VKORC1 expression.",
                    "action": "Standard titration protocol to target INR 2.0-3.0.",
                    "risk": "Standard Safety Profile",
                    "contraindicated": False
                }
            }
        },
        "abacavir": {
            "gene": "HLA-B*5701",
            "phenotypes": {
                "Positive": {
                    "implication": "Severe, potentially fatal multi-organ hypersensitivity reaction (Stevens-Johnson syndrome, fever, rash, GI toxicity).",
                    "action": "ABSOLUTELY CONTRAINDICATED. Do NOT administer Abacavir under any circumstances.",
                    "risk": "Life-Threatening Hypersensitivity",
                    "contraindicated": True
                },
                "Negative": {
                    "implication": "Low risk of immunological hypersensitivity.",
                    "action": "Standard dosing permitted.",
                    "risk": "Standard Safety Profile",
                    "contraindicated": False
                }
            }
        }
    }

    @classmethod
    def evaluate(cls, req: PharmacogenomicEvaluationRequest) -> PharmacogenomicEvaluationResponse:
        """Evaluates patient medications against genetic profile."""
        reports: List[DrugMetabolismReport] = []
        has_critical = False
        profile = req.genomic_profile

        for raw_drug in req.proposed_medications:
            drug_clean = raw_drug.lower().strip()
            # Match drug key
            matched_key = next((k for k in cls.CPIC_GENE_DRUG_MAP if k in drug_clean), None)

            if matched_key:
                meta = cls.CPIC_GENE_DRUG_MAP[matched_key]
                gene = meta["gene"]
                phenotypes = meta["phenotypes"]

                # Resolve patient phenotype for gene
                if gene == "CYP2C19":
                    pt_pheno = profile.cyp2c19_phenotype
                elif gene == "CYP2D6":
                    pt_pheno = profile.cyp2d6_phenotype
                elif gene == "SLCO1B1":
                    pt_pheno = profile.slco1b1_genotype
                elif gene == "VKORC1":
                    pt_pheno = profile.vkorc1_genotype
                elif gene == "HLA-B*5701":
                    pt_pheno = profile.hla_b5701_status
                else:
                    pt_pheno = "Normal"

                # Find best matching phenotype recommendation
                detail = next((v for k, v in phenotypes.items() if any(p.lower() in pt_pheno.lower() for p in k.split("/"))), None)
                if not detail:
                    detail = list(phenotypes.values())[0]

                if detail.get("contraindicated", False):
                    has_critical = True

                reports.append(DrugMetabolismReport(
                    drug_name=raw_drug,
                    relevant_gene=gene,
                    metabolic_status=pt_pheno,
                    clinical_implication=detail["implication"],
                    recommended_dosage_adjustment=detail["action"],
                    adverse_reaction_risk=detail["risk"],
                    cpic_guideline_level="Level A (Actionable & Validated)"
                ))
            else:
                reports.append(DrugMetabolismReport(
                    drug_name=raw_drug,
                    relevant_gene="Non-variant dependent / Standard Cytochrome",
                    metabolic_status="Wild-Type / Standard Clearance",
                    clinical_implication="No high-risk CPIC Level A/B pharmacogenomic interactions detected for this agent.",
                    recommended_dosage_adjustment="Maintain standard label dosing guidelines.",
                    adverse_reaction_risk="Standard Label Safety Profile",
                    cpic_guideline_level="Standard Guideline"
                ))

        return PharmacogenomicEvaluationResponse(
            patient_id=req.patient_id,
            total_drugs_analyzed=len(reports),
            evaluations=reports,
            has_critical_contraindications=has_critical
        )


pharmacogenomics_engine = PrecisionPharmacogenomicsEngine()
