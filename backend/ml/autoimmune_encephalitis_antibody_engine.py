"""
Autoimmune Encephalitis Anti-NMDA / LGI1 / CASPR2 Score Engine
================================================================
Evaluates Clinical Assessment Scale in Autoimmune Encephalitis (CASE score), CSF pleocytosis (> 5 cells/uL),
limbic MRI hyperintensity, and NMDAR / LGI1 / CASPR2 antibody serology to select 1st-line IVIG/PLEX
vs 2nd-line Rituximab / Cyclophosphamide.
"""

from typing import Dict


class AutoimmuneEncephalitisAntibodyEngine:
    """Evaluates Autoimmune Encephalitis antibody panel and immunotherapy escalation."""

    def evaluate_encephalitis(
        self,
        nmdar_antibody_positive: bool = False,
        lgi1_antibody_positive: bool = False,
        caspr2_antibody_positive: bool = False,
        csf_pleocytosis_cells_uL: float = 2.0,
        mri_limbic_t2_flair_hyperintensity: bool = False,
        case_severity_score: int = 4,  # 0 to 27
        refractory_to_first_line_immunotherapy: bool = False,
    ) -> Dict[str, any]:
        antibody_detected = nmdar_antibody_positive or lgi1_antibody_positive or caspr2_antibody_positive
        csf_abnormal = csf_pleocytosis_cells_uL > 5.0

        encephalitis_confirmed = antibody_detected or (csf_abnormal and mri_limbic_t2_flair_hyperintensity and case_severity_score >= 3)

        specific_subtype = "SERONEGATIVE_AUTOIMMUNE_ENCEPHALITIS"
        if nmdar_antibody_positive:
            specific_subtype = "ANTI_NMDAR_ENCEPHALITIS"
        elif lgi1_antibody_positive:
            specific_subtype = "ANTI_LGI1_LIMBIC_ENCEPHALITIS"
        elif caspr2_antibody_positive:
            specific_subtype = "ANTI_CASPR2_ENCEPHALITIS_MORVAN_SYNDROME"

        immunotherapy = "HIGH_DOSE_IV_METHYLPREDNISOLONE_PLUS_IVIG_OR_PLEX"
        if refractory_to_first_line_immunotherapy:
            immunotherapy = "SECOND_LINE_RITUXIMAB_375MG_M2_OR_CYCLOPHOSPHAMIDE"

        recommendation = "Incomplete criteria for Autoimmune Encephalitis; evaluate viral encephalitis (HSV PCR) & metabolic encephalopathy"
        if encephalitis_confirmed:
            if nmdar_antibody_positive:
                recommendation = f"Confirmed {specific_subtype}: Initiate {immunotherapy}; perform pelvic MRI/US screening for ovarian teratoma"
            else:
                recommendation = f"Confirmed {specific_subtype}: Initiate {immunotherapy}; monitor CASE score longitudinally"

        return {
            "encephalitis_confirmed": encephalitis_confirmed,
            "encephalitis_subtype": specific_subtype,
            "recommended_immunotherapy": immunotherapy,
            "refractory_to_first_line": refractory_to_first_line_immunotherapy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
encephalitis_engine = AutoimmuneEncephalitisAntibodyEngine()
