"""
Chronic Pancreatitis Cambridge Classification Engine
=====================================================
Evaluates ERCP / EUS / MRCP structural criteria (main pancreatic duct caliber, side branch dilation,
intraductal calcifications, cavity formation) to stage chronic pancreatitis (Normal, Equivocal, Mild, Moderate, Severe).
"""

from typing import Dict


class CambridgeChronicPancreatitisEngine:
    """Evaluates Cambridge structural classification for Chronic Pancreatitis."""

    def stage_cambridge_pancreatitis(
        self,
        abnormal_side_branches_count: int,
        main_pancreatic_duct_dilated_over_3mm: bool = False,
        intraductal_calcifications_present: bool = False,
        pancreatic_cavities_or_pseudocysts_present: bool = False,
        pancreatic_parenchymal_heterogeneity: bool = False,
    ) -> Dict[str, any]:
        cambridge_stage = "NORMAL"
        pert_enzyme_replacement_indicated = False

        if intraductal_calcifications_present or pancreatic_cavities_or_pseudocysts_present or (main_pancreatic_duct_dilated_over_3mm and abnormal_side_branches_count >= 3):
            cambridge_stage = "SEVERE_CHRONIC_PANCREATITIS"
            pert_enzyme_replacement_indicated = True
        elif main_pancreatic_duct_dilated_over_3mm or abnormal_side_branches_count >= 3:
            cambridge_stage = "MODERATE_CHRONIC_PANCREATITIS"
            pert_enzyme_replacement_indicated = True
        elif abnormal_side_branches_count == 1 or abnormal_side_branches_count == 2 or pancreatic_parenchymal_heterogeneity:
            cambridge_stage = "MILD_CHRONIC_PANCREATITIS"
        elif abnormal_side_branches_count == 0 and not main_pancreatic_duct_dilated_over_3mm:
            cambridge_stage = "NORMAL"

        recommendation = "Normal pancreatic morphology: No evidence of chronic pancreatitis; monitor symptoms"
        if cambridge_stage == "SEVERE_CHRONIC_PANCREATITIS":
            recommendation = "Severe Chronic Pancreatitis (Cambridge Severe): Initiate Pancreatic Enzyme Replacement Therapy (PERT - Creon 40,000-75,000 units/meal), Fat-Soluble Vitamin Supplementation (A,D,E,K), & Pain Management consult"
        elif cambridge_stage == "MODERATE_CHRONIC_PANCREATITIS":
            recommendation = "Moderate Chronic Pancreatitis: Initiate PERT for steatorrhea / malabsorption & lifestyle intervention (strict alcohol/smoking cessation)"
        elif cambridge_stage == "MILD_CHRONIC_PANCREATITIS":
            recommendation = "Mild Chronic Pancreatitis: Follow-up EUS/MRCP in 12 months; initiate non-opioid pain therapy & dietary fat modulation"

        return {
            "abnormal_side_branches_count": abnormal_side_branches_count,
            "main_duct_dilated": main_pancreatic_duct_dilated_over_3mm,
            "calcifications_present": intraductal_calcifications_present,
            "cambridge_stage": cambridge_stage,
            "pert_enzymes_indicated": pert_enzyme_replacement_indicated,
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
cambridge_pancreatitis_engine = CambridgeChronicPancreatitisEngine()
