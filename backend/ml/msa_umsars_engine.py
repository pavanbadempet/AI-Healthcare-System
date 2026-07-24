"""
Multiple System Atrophy (MSA) UMSARS (Unified MSA Rating Scale) Engine
========================================================================
Scores UMSARS Part I (ADL) and Part II (Motor Examination: 0 to 56) to stage MSA-C vs MSA-P.
"""

from typing import Dict


class MsaUmsarsEngine:
    """Scores UMSARS for Multiple System Atrophy phenotype & progression tracking."""

    def evaluate_umsars_score(
        self,
        part_1_adl_score_0_to_48: int,
        part_2_motor_exam_score_0_to_56: int,
        cerebellar_ataxia_predominant: bool = False,
        parkinsonism_bradykinesia_predominant: bool = False,
        severe_autonomic_failure_orthostatic_hypotension: bool = True,
    ) -> Dict[str, any]:
        total_umsars = part_1_adl_score_0_to_48 + part_2_motor_exam_score_0_to_56

        phenotype = "POSSIBLE_MSA"
        if cerebellar_ataxia_predominant:
            phenotype = "MSA_C_CEREBELLAR_SUBTYPE"
        elif parkinsonism_bradykinesia_predominant:
            phenotype = "MSA_P_PARKINSONIAN_SUBTYPE"

        severity = "MILD_STAGE_I"
        if total_umsars >= 60:
            severity = "SEVERE_STAGE_IV_BEDRIDDEN"
        elif total_umsars >= 35:
            severity = "MODERATE_STAGE_III_WHEELCHAIR_BOUND"
        elif total_umsars >= 15:
            severity = "MILD_TO_MODERATE_STAGE_II"

        recommendation = "Standard supportive therapy & orthostatic precautions"
        if severity in ["SEVERE_STAGE_IV_BEDRIDDEN", "MODERATE_STAGE_III_WHEELCHAIR_BOUND"]:
            recommendation = "High-grade neuro-disability: Midodrine/Fludrocortisone for orthostasis, L-DOPA trial (MSA-P), & specialized neuro-palliative care"

        return {
            "umsars_total_score": total_umsars,
            "msa_phenotype": phenotype,
            "disease_stage": severity,
            "autonomic_pharmacotherapy_indicated": severe_autonomic_failure_orthostatic_hypotension,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
msa_umsars_engine = MsaUmsarsEngine()
