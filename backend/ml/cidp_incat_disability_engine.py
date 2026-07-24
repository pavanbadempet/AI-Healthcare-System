"""
Chronic Inflammatory Demyelinating Polyneuropathy (CIDP) INCAT Disability Engine
================================================================================
Evaluates INCAT disability score (0-10), nerve conduction study electrophysiology
(conduction block, temporal dispersion), and CSF protein (> 0.45 g/L) to stage CIDP
and recommend IVIG vs Subcutaneous Immunoglobulin (SCIG) vs FcRn blockers.
"""

from typing import Dict


class CidpIncatDisabilityEngine:
    """Evaluates INCAT disability score and electrophysiological demyelination in CIDP."""

    def stage_cidp_disability(
        self,
        arm_incat_score: int,  # 0-5
        leg_incat_score: int,  # 0-5
        csf_protein_g_L: float,
        ncs_demyelinating_features_present: bool = True,
        refractory_to_ivig: bool = False,
    ) -> Dict[str, any]:
        total_incat = arm_incat_score + leg_incat_score
        cytoalbuminologic_dissociation = csf_protein_g_L > 0.45

        cidp_confirmed = ncs_demyelinating_features_present and cytoalbuminologic_dissociation and total_incat >= 1

        first_line_therapy = "IVIG_OR_CORTICOSTEROIDS"
        if refractory_to_ivig:
            first_line_therapy = "FCRN_BLOCKER_EFGARTIGIMOD_OR_RITUXIMAB"
        elif total_incat >= 2:
            first_line_therapy = "IVIG_2G_KG_INDUCTION_THEN_SCIG_MAINTENANCE"

        severity = "MILD_CIDP_DISABILITY"
        if total_incat >= 6:
            severity = "SEVERE_CIDP_DISABILITY"
        elif total_incat >= 3:
            severity = "MODERATE_CIDP_DISABILITY"

        recommendation = "Incomplete criteria for CIDP diagnosis; evaluate alternative causes of demyelinating neuropathy (e.g., POEMS syndrome, MMN)"
        if cidp_confirmed:
            if refractory_to_ivig:
                recommendation = f"Refractory CIDP (INCAT Score {total_incat}): Transition to Efgartigimod alfa-fcab (FcRn receptor inhibitor) or Rituximab therapy"
            else:
                recommendation = f"Confirmed CIDP ({severity}, INCAT Score {total_incat}): Initiate IVIG induction (2 g/kg split over 2-5 days); transition to maintenance SCIG (0.2-0.4 g/kg weekly)"

        return {
            "total_incat_score": total_incat,
            "csf_protein_g_L": csf_protein_g_L,
            "cytoalbuminologic_dissociation": cytoalbuminologic_dissociation,
            "cidp_confirmed": cidp_confirmed,
            "cidp_severity": severity,
            "recommended_therapy": first_line_therapy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
cidp_engine = CidpIncatDisabilityEngine()
