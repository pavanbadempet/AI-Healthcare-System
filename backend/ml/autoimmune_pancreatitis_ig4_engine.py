"""
IgG4-Related Autoimmune Pancreatitis HISORt Criteria Engine
=============================================================
Evaluates Mayo Clinic HISORt criteria (Histology, Imaging, Serology IgG4 >140 mg/dL,
Other organ involvement, Response to Steroid therapy) to diagnose Type 1 vs Type 2 AIP
and differentiate from Pancreatic Adenocarcinoma.
"""

from typing import Dict, Optional


class AutoimmunePancreatitisIg4Engine:
    """Evaluates HISORt criteria for IgG4 Autoimmune Pancreatitis."""

    def evaluate_hisort_criteria(
        self,
        serum_igg4_mg_dL: float,
        ct_mri_diffuse_sausage_shaped_enlargement: bool = False,
        histology_lgpp_dense_igg4_plasma_cells: bool = False,
        other_organ_involvement_retroperitoneal_fibrosis_or_cholangitis: bool = False,
        steroid_response_rapid_resolution: Optional[bool] = None,
    ) -> Dict[str, any]:
        hisort_score = 0

        if serum_igg4_mg_dL > 140.0:
            hisort_score += 1
        if serum_igg4_mg_dL > 280.0:  # 2x ULN strong criterion
            hisort_score += 1
        if ct_mri_diffuse_sausage_shaped_enlargement:
            hisort_score += 1
        if histology_lgpp_dense_igg4_plasma_cells:
            hisort_score += 2
        if other_organ_involvement_retroperitoneal_fibrosis_or_cholangitis:
            hisort_score += 1
        if steroid_response_rapid_resolution is True:
            hisort_score += 1

        diagnosis = "UNLIKELY_AUTOIMMUNE_PANCREATITIS"
        steroids_indicated = False

        if histology_lgpp_dense_igg4_plasma_cells or (hisort_score >= 3):
            diagnosis = "TYPE_1_IGG4_RELATED_AUTOIMMUNE_PANCREATITIS"
            steroids_indicated = True
        elif hisort_score >= 2:
            diagnosis = "POSSIBLE_AUTOIMMUNE_PANCREATITIS"
            steroids_indicated = True

        recommendation = "Low HISORt score: Evaluate for Pancreatic Adenocarcinoma (EUS-FNA biopsy recommended before empirical steroid trial)"
        if diagnosis == "TYPE_1_IGG4_RELATED_AUTOIMMUNE_PANCREATITIS":
            recommendation = "Definite Type 1 IgG4-Related Autoimmune Pancreatitis: Initiate Oral Prednisone 40 mg/day for 4 weeks followed by 5 mg/week taper; monitor IgG4 levels"
        elif steroids_indicated:
            recommendation = "Possible AIP: Perform 2-week empirical Oral Steroid Trial with high-resolution CT/MRI reassessment to confirm diagnostic response"

        return {
            "serum_igg4_mg_dL": serum_igg4_mg_dL,
            "hisort_total_score": hisort_score,
            "aip_diagnosis": diagnosis,
            "prednisone_steroid_therapy_indicated": steroids_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
autoimmune_pancreatitis_engine = AutoimmunePancreatitisIg4Engine()
