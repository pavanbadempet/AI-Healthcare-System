"""
Multiple Sclerosis McDonald 2017 Diagnostic Criteria Engine
=============================================================
Evaluates 2017 McDonald Criteria for MS diagnosis (Dissemination in Space DIS,
Dissemination in Time DIT, CSF Oligoclonal Bands) to diagnose Relapsing-Remitting MS
and initiate Disease-Modifying Therapy (DMT).
"""

from typing import Dict


class MsMcDonald2017Engine:
    """Evaluates 2017 McDonald Diagnostic Criteria for Multiple Sclerosis."""

    def evaluate_mcdonald_criteria(
        self,
        clinical_attacks_count: int,
        cns_regions_with_t2_lesions_dis_count: int,  # >= 2 out of periventricular, cortical/juxtacortical, infratentorial, spinal cord
        simultaneous_gd_enhancing_and_non_enhancing_lesions_dit: bool = False,
        csf_oligoclonal_bands_positive: bool = False,
        new_t2_lesion_on_follow_up_mri_dit: bool = False,
    ) -> Dict[str, any]:
        dissemination_in_space_dis = cns_regions_with_t2_lesions_dis_count >= 2
        dissemination_in_time_dit = (
            simultaneous_gd_enhancing_and_non_enhancing_lesions_dit
            or csf_oligoclonal_bands_positive
            or new_t2_lesion_on_follow_up_mri_dit
        )

        ms_diagnosis = "NOT_MEETING_MCDONALD_CRITERIA"
        dmt_indicated = False

        if clinical_attacks_count >= 2:
            if dissemination_in_space_dis or cns_regions_with_t2_lesions_dis_count >= 1:
                ms_diagnosis = "DEFINITE_MULTIPLE_SCLEROSIS"
                dmt_indicated = True
        elif clinical_attacks_count == 1:
            if dissemination_in_space_dis and dissemination_in_time_dit:
                ms_diagnosis = "DEFINITE_MULTIPLE_SCLEROSIS"
                dmt_indicated = True
            elif dissemination_in_space_dis or dissemination_in_time_dit:
                ms_diagnosis = "CLINICALLY_ISOLATED_SYNDROME_CIS"
                dmt_indicated = True

        recommendation = "Criteria not fully met; perform serial brain/spine MRI in 6-12 months & evaluate alternative demyelinating etiologies (NMODSD / MOGAD)"
        if ms_diagnosis == "DEFINITE_MULTIPLE_SCLEROSIS":
            recommendation = "Definite Relapsing-Remitting Multiple Sclerosis (2017 McDonald Criteria Met): Initiate High-Efficacy Disease-Modifying Therapy (Ocrelizumab, Ofatumumab, or Natalizumab)"
        elif ms_diagnosis == "CLINICALLY_ISOLATED_SYNDROME_CIS":
            recommendation = "Clinically Isolated Syndrome (CIS): High risk of conversion to MS; initiate Early Disease-Modifying Therapy (DMT) & baseline spine MRI"

        return {
            "clinical_attacks_count": clinical_attacks_count,
            "dissemination_in_space_dis": dissemination_in_space_dis,
            "dissemination_in_time_dit": dissemination_in_time_dit,
            "mcdonald_2017_diagnosis": ms_diagnosis,
            "disease_modifying_therapy_dmt_indicated": dmt_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ms_mcdonald_engine = MsMcDonald2017Engine()
