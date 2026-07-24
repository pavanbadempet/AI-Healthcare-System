"""
Multiple Sclerosis MS-PROgnosis 10-Year Disability Predictor
=============================================================
Predicts 10-year probability of reaching EDSS 6.0 based on clinical and MRI baseline biomarkers.
"""

from typing import Dict


class MsPrognosisDisabilityEngine:
    """Predicts 10-year disability progression (EDSS >= 6.0) for Multiple Sclerosis."""

    def predict_10yr_edss6_risk(
        self,
        age_at_onset_years: int,
        relapse_count_first_2_years: int,
        t2_lesions_count_mri: int,
        spinal_cord_lesions_present: bool = False,
        csf_oligoclonal_bands_positive: bool = True,
    ) -> Dict[str, any]:
        risk_score = 0

        if age_at_onset_years >= 40:
            risk_score += 2
        elif age_at_onset_years >= 30:
            risk_score += 1

        if relapse_count_first_2_years >= 3:
            risk_score += 3
        elif relapse_count_first_2_years >= 1:
            risk_score += 1

        if t2_lesions_count_mri >= 10:
            risk_score += 2
        elif t2_lesions_count_mri >= 3:
            risk_score += 1

        if spinal_cord_lesions_present:
            risk_score += 2

        if csf_oligoclonal_bands_positive:
            risk_score += 1

        ten_year_edss6_risk_pct = 12.0
        if risk_score >= 7:
            ten_year_edss6_risk_pct = 68.0
        elif risk_score >= 4:
            ten_year_edss6_risk_pct = 36.0

        high_efficacy_dmt_indicated = risk_score >= 4

        recommendation = "Moderate risk: Standard Disease Modifying Therapy (Dimethyl Fumarate / Glatiramer Acetate)"
        if high_efficacy_dmt_indicated:
            recommendation = "High Progression Risk (>=36% 10-Yr EDSS 6.0): Initiate High-Efficacy Monoclonal Antibody DMT (Ocrelizumab / Ofatumumab / Kesimpta)"

        return {
            "prognostic_risk_score": risk_score,
            "ten_year_edss6_disability_risk_percent": ten_year_edss6_risk_pct,
            "high_efficacy_dmt_indicated": high_efficacy_dmt_indicated,
            "clinical_recommendation": recommendation,
            "status": "PREDICTION_COMPLETE",
        }


# Singleton engine instance
ms_prognosis_engine = MsPrognosisDisabilityEngine()
