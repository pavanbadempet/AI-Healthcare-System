"""
Acute Liver Failure (ALF) King's College Criteria & Transplant Engine
======================================================================
Evaluates King's College Criteria for Acetaminophen (APAP) vs Non-APAP acute liver failure
(arterial pH < 7.30, INR > 6.5, Cr > 3.4 mg/dL, Encephalopathy III/IV) to trigger emergency
UNOS Status 1A liver transplantation listing.
"""

from typing import Dict, Optional


class AlfKingsCollegeCriteriaEngine:
    """Evaluates King's College Criteria for Emergency Liver Transplantation in ALF."""

    def evaluate_kings_college_criteria(
        self,
        acetaminophen_etiology: bool,
        arterial_ph: float,
        inr: float,
        serum_creatinine_mg_dL: float,
        hepatic_encephalopathy_grade: int,  # 0 to 4
        serum_bilirubin_mg_dL: Optional[float] = None,
        age_years: Optional[float] = None,
        jaundice_to_encephalopathy_days: Optional[float] = None,
    ) -> Dict[str, any]:
        criteria_met = False

        if acetaminophen_etiology:
            if arterial_ph < 7.30:
                criteria_met = True
            elif inr > 6.5 and serum_creatinine_mg_dL > 3.4 and hepatic_encephalopathy_grade >= 3:
                criteria_met = True
        else:
            # Non-Acetaminophen etiology
            if inr > 6.5:
                criteria_met = True
            else:
                minor_points = 0
                if age_years is not None and (age_years < 10 or age_years > 40):
                    minor_points += 1
                if jaundice_to_encephalopathy_days is not None and jaundice_to_encephalopathy_days > 7:
                    minor_points += 1
                if inr > 3.5:
                    minor_points += 1
                if serum_bilirubin_mg_dL is not None and serum_bilirubin_mg_dL > 17.5:
                    minor_points += 1

                if minor_points >= 3:
                    criteria_met = True

        status_1a_listing_indicated = criteria_met and hepatic_encephalopathy_grade >= 2

        recommendation = "King's College Criteria NOT met; continue ICU supportive care (N-Acetylcysteine infusion, hypertonic saline for cerebral edema target Na 145-150 mEq/L)"
        if criteria_met:
            recommendation = f"CRITICAL ALF (King's College Criteria MET, Encephalopathy Grade {hepatic_encephalopathy_grade}): High 90-day mortality without transplant; list patient immediately for UNOS Status 1A Emergency Liver Transplantation & initiate MARS artificial liver support"

        return {
            "acetaminophen_etiology": acetaminophen_etiology,
            "arterial_ph": arterial_ph,
            "inr": inr,
            "serum_creatinine_mg_dL": serum_creatinine_mg_dL,
            "kings_college_criteria_met": criteria_met,
            "status_1a_transplant_indicated": status_1a_listing_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
alf_engine = AlfKingsCollegeCriteriaEngine()
