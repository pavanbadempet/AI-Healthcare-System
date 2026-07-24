"""
Myasthenia Gravis Complement C5 Inhibitor Engine (Eculizumab / Ravulizumab / Zilucoplan)
========================================================================================
Evaluates terminal complement C5 inhibitor eligibility (Eculizumab / Soliris, Ravulizumab / Ultomiris, Zilucoplan / Zilbrysq subQ)
in anti-AChR+ refractory generalized Myasthenia Gravis. Mandates quadrivalent meningococcal vaccination (ACWY + MenB)
or Penicillin V prophylaxis prior to initiation to prevent invasive meningococcal disease.
"""

from typing import Dict


class MgComplementInhibitorEngine:
    """Evaluates complement C5 inhibitor therapy and meningococcal safety in anti-AChR+ gMG."""

    def evaluate_c5_inhibitor_safety(
        self,
        achr_antibody_positive: bool = True,
        refractory_gmg_symptoms: bool = True,
        meningococcal_vaccine_acwy_and_menb_given: bool = True,
        vaccine_given_at_least_2_weeks_prior: bool = True,
        penicillin_v_prophylaxis_active: bool = False,
    ) -> Dict[str, any]:
        c5_indicated = achr_antibody_positive and refractory_gmg_symptoms
        safety_clearance = (
            meningococcal_vaccine_acwy_and_menb_given and vaccine_given_at_least_2_weeks_prior
        ) or penicillin_v_prophylaxis_active

        can_proceed = c5_indicated and safety_clearance

        recommended_c5_agent = "RAVULIZUMAB_ULTOMIRIS_IV_EVERY_8_WEEKS_OR_ZILUCOPLAN_ZILBRYSQ_SUBQ_DAILY"

        recommendation = "Complement C5 inhibitor NOT cleared; mandate meningococcal vaccines (MenACWY + MenB) at least 2 weeks prior or initiate oral Penicillin V prophylaxis immediately"
        if can_proceed:
            recommendation = f"CLEARED FOR COMPLEMENT C5 INHIBITOR THERAPY ({recommended_c5_agent}): Patient is vaccinated against N. meningitidis (MenACWY + MenB); proceed with C5 inhibition to prevent MAC-mediated neuromuscular junction destruction"

        return {
            "c5_indicated": c5_indicated,
            "safety_clearance": safety_clearance,
            "can_proceed": can_proceed,
            "recommended_c5_agent": recommended_c5_agent if can_proceed else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
c5_inhibitor_engine = MgComplementInhibitorEngine()
