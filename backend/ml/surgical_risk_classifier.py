"""
Surgical Risk & ASA Physical Status Classifier
===============================================
Computes NSQIP 30-day perioperative mortality and cardiac complication risk scores (RCRI index)
for preoperative surgical clearance.
"""

from typing import Dict


class SurgicalRiskClassifier:
    """Evaluates preoperative cardiac and mortality surgical risk scores."""

    def evaluate_surgical_risk(
        self,
        asa_class: int,  # 1 to 5
        high_risk_surgery: bool,
        history_ischemic_heart_disease: bool,
        history_congestive_heart_failure: bool,
        history_cerebrovascular_disease: bool,
        preop_creatinine_mg_dL: float,
    ) -> Dict[str, any]:
        # Revised Cardiac Risk Index (RCRI) score computation
        rcri_score = 0
        if high_risk_surgery:
            rcri_score += 1
        if history_ischemic_heart_disease:
            rcri_score += 1
        if history_congestive_heart_failure:
            rcri_score += 1
        if history_cerebrovascular_disease:
            rcri_score += 1
        if preop_creatinine_mg_dL > 2.0:
            rcri_score += 1

        cardiac_risk_pct = 0.4 if rcri_score == 0 else (1.0 if rcri_score == 1 else (2.4 if rcri_score == 2 else 5.4))

        return {
            "asa_physical_status_class": f"ASA_CLASS_{asa_class}",
            "rcri_score": rcri_score,
            "estimated_30day_cardiac_event_risk_percent": cardiac_risk_pct,
            "clearance_status": "HIGH_PERIOPERATIVE_RISK_CARDIOLOGY_CONSULT_REQUIRED" if rcri_score >= 2 or asa_class >= 3 else "CLEARED_FOR_SURGERY",
        }


# Singleton classifier instance
surgical_risk_classifier = SurgicalRiskClassifier()
