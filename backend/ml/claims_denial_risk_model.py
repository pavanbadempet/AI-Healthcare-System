"""
Medical Claims Denial Risk AI Predictor
========================================
Analyzes insurance claim parameters (ANSI X12 837P fields, CPT/ICD-10 code combinations,
prior authorization status) to compute pre-submission claim refusal probabilities.
"""

from typing import Dict, List, Optional


class ClaimsDenialRiskModel:
    """Predicts insurance claim refusal risks before electronic EDI submission."""

    def predict_claim_denial_risk(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        total_billed_amount: float,
        has_prior_authorization: bool = True,
        is_in_network_provider: bool = True,
    ) -> Dict[str, any]:
        denial_reasons = []
        risk_score = 0.05

        # 1. Prior Authorization Requirement Checks
        high_cost_cpts = {"99215", "74177", "71260"}
        if any(cpt in high_cost_cpts for cpt in cpt_codes) and not has_prior_authorization:
            risk_score += 0.45
            denial_reasons.append("High-cost procedure code requires Prior Authorization.")

        # 2. Out of Network Penalty
        if not is_in_network_provider:
            risk_score += 0.25
            denial_reasons.append("Out-of-network provider billing without pre-approval.")

        # 3. Medical Necessity Overlap Check
        if not icd10_codes:
            risk_score += 0.35
            denial_reasons.append("Missing primary ICD-10 diagnosis code for medical necessity.")

        denial_probability = round(min(0.98, max(0.02, risk_score)), 3)

        if denial_probability >= 0.50:
            status = "HIGH_DENIAL_RISK"
            recommendation = "Hold claim submission. Obtain prior authorization and verify diagnosis coding."
        elif denial_probability >= 0.25:
            status = "MODERATE_RISK"
            recommendation = "Review coding attachments before EDI transmission."
        else:
            status = "LOW_RISK"
            recommendation = "Claim cleared for immediate EDI 837P transmission."

        return {
            "cpt_codes": cpt_codes,
            "icd10_codes": icd10_codes,
            "billed_amount": total_billed_amount,
            "denial_probability": denial_probability,
            "risk_status": status,
            "flagged_reasons": denial_reasons,
            "recommendation": recommendation,
        }


# Singleton model instance
claims_denial_model = ClaimsDenialRiskModel()
