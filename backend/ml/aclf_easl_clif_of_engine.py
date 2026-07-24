"""
Acute-on-Chronic Liver Failure (ACLF) EASL-CLIF Consortium Organ Failure Score Engine
======================================================================================
Evaluates CLIF-C Organ Failure Score (CLIF-C OFS across 6 organ systems: Liver, Kidney, Brain, Coagulation, Circulation, Lungs)
to grade ACLF (Grade 1, Grade 2, Grade 3) and predict 28-day/90-day mortality to guide emergency liver transplantation.
"""

from typing import Dict


class AclfEaslClifOfEngine:
    """Evaluates EASL-CLIF Organ Failure Score and ACLF Grade in decompensated cirrhosis."""

    def calculate_clif_c_ofs(
        self,
        total_bilirubin_mg_dL: float,  # <6 = 1, 6-12 = 2, >12 = 3
        creatinine_mg_dL: float,  # <1.5 = 1, 1.5-2.0 = 2, >2.0 or RRT = 3
        hepatic_encephalopathy_grade: int,  # 0 = 1, I-II = 2, III-IV = 3
        inr_coagulation: float,  # <1.5 = 1, 1.5-2.5 = 2, >2.5 = 3
        mean_arterial_pressure_mmHg: float,  # >= 70 = 1, <70 = 2, vasopressors = 3
        vasopressors_required: bool = False,
        pao2_fio2_ratio: float = 350.0,  # > 300 = 1, 200-300 = 2, <= 200 or MV = 3
        dialysis_active: bool = False,
    ) -> Dict[str, any]:
        # Liver subscore
        liver_score = 1
        if total_bilirubin_mg_dL >= 12.0:
            liver_score = 3
        elif total_bilirubin_mg_dL >= 6.0:
            liver_score = 2

        # Kidney subscore
        kidney_score = 1
        if creatinine_mg_dL >= 2.0 or dialysis_active:
            kidney_score = 3
        elif creatinine_mg_dL >= 1.5:
            kidney_score = 2

        # Brain subscore
        brain_score = 1
        if hepatic_encephalopathy_grade in [3, 4]:
            brain_score = 3
        elif hepatic_encephalopathy_grade in [1, 2]:
            brain_score = 2

        # Coagulation subscore
        coag_score = 1
        if inr_coagulation >= 2.5:
            coag_score = 3
        elif inr_coagulation >= 1.5:
            coag_score = 2

        # Circulation subscore
        circ_score = 1
        if vasopressors_required:
            circ_score = 3
        elif mean_arterial_pressure_mmHg < 70.0:
            circ_score = 2

        # Lung subscore
        lung_score = 1
        if pao2_fio2_ratio <= 200.0:
            lung_score = 3
        elif pao2_fio2_ratio <= 300.0:
            lung_score = 2

        # Total Organ Failures (score == 3 counts as an organ failure)
        organ_failures_count = sum([
            1 for s in [liver_score, kidney_score, brain_score, coag_score, circ_score, lung_score] if s == 3
        ])

        aclf_grade = "NO_ACLF"
        if organ_failures_count >= 3:
            aclf_grade = "ACLF_GRADE_3"
        elif organ_failures_count == 2:
            aclf_grade = "ACLF_GRADE_2"
        elif organ_failures_count == 1:
            aclf_grade = "ACLF_GRADE_1"

        clif_c_ofs_total = liver_score + kidney_score + brain_score + coag_score + circ_score + lung_score

        recommendation = f"No ACLF detected (CLIF-C OFS {clif_c_ofs_total}); continue standard cirrhosis care and treat underlying precipitants"
        if aclf_grade == "ACLF_GRADE_3":
            recommendation = f"CRITICAL ACLF GRADE 3 (CLIF-C OFS {clif_c_ofs_total}, {organ_failures_count} Organ Failures): 28-day mortality ~ 75-80%; IMMEDIATE ICU ADMISSION and emergency liver transplant evaluation (high priority MELD-Na exception)"
        elif aclf_grade in ["ACLF_GRADE_1", "ACLF_GRADE_2"]:
            recommendation = f"ACLF {aclf_grade.replace('_', ' ')} DETECTED (CLIF-C OFS {clif_c_ofs_total}, {organ_failures_count} Organ Failures): Transfer to step-down/ICU, initiate broad-spectrum antibiotics, albumin infusions, and target organ support"

        return {
            "clif_c_ofs_total": clif_c_ofs_total,
            "organ_failures_count": organ_failures_count,
            "aclf_grade": aclf_grade,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
aclf_clif_engine = AclfEaslClifOfEngine()
