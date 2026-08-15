"""
Stage 4: Deterministic Clinical Guardrails & Contextual Multi-Armed Bandits (Thompson Sampling).
Enforces hard safety constraints and dynamically explores high-potential clinical actions.
"""

import logging
import random
from typing import Dict, Tuple

from backend.schemas.recommendation import CandidateItem, PatientContext

logger = logging.getLogger("backend.recommendation.guardrails")


class ClinicalSafetyGuardrail:
    """Deterministic clinical safety rules and contraindication filter."""

    # Explicit drug-drug or mechanism interaction pairs
    KNOWN_INTERACTION_PAIRS = [
        ({"ace inhibitor", "lisinopril", "ramipril"}, {"arb", "losartan", "valsartan"}),  # Dual RAS blockade
        ({"statin", "atorvastatin", "simvastatin"}, {"gemfibrozil"}),                      # Rhabdomyolysis risk
        ({"sglt2", "empagliflozin"}, {"loop diuretic high dose", "furosemide 80mg"})      # Severe dehydration
    ]

    @classmethod
    def is_contraindicated(cls, patient: PatientContext, candidate: CandidateItem) -> Tuple[bool, str]:
        """
        Evaluates deterministic clinical contraindications.
        Returns: (is_contraindicated: bool, reason: str)
        """
        cand_title_lower = candidate.title.lower()
        cand_desc_lower = candidate.description.lower()
        contraindications_lower = [c.lower() for c in candidate.contraindications]

        # 1. Allergy Checking
        for allergy in patient.allergies:
            allergy_clean = allergy.lower().strip()
            if allergy_clean and (allergy_clean in cand_title_lower or allergy_clean in cand_desc_lower):
                return True, f"Patient documented allergy to '{allergy}'"

        # 2. Condition-specific contraindication matching
        for condition in patient.primary_conditions:
            cond_lower = condition.lower()
            for contra in contraindications_lower:
                if cond_lower in contra or contra in cond_lower:
                    return True, f"Contraindicated by active diagnosis '{condition}': {contra}"

        # 3. High-risk drug-drug interaction pairs
        curr_meds_lower = {m.lower() for m in patient.current_medications}
        for set_a, set_b in cls.KNOWN_INTERACTION_PAIRS:
            a_in_meds = any(any(alias in m for alias in set_a) for m in curr_meds_lower)
            b_in_cand = any(alias in cand_title_lower for alias in set_b)
            b_in_meds = any(any(alias in m for alias in set_b) for m in curr_meds_lower)
            a_in_cand = any(alias in cand_title_lower for alias in set_a)

            if (a_in_meds and b_in_cand) or (b_in_meds and a_in_cand):
                return True, "Potential high-risk pharmacological interaction with current medication regimen"

        return False, ""


class ContextualThompsonBandit:
    """
    Contextual Multi-Armed Bandit using Beta-Bernoulli Thompson Sampling.
    Maintains Bayesian posterior distributions (Alpha, Beta) per candidate item.
    """

    def __init__(self):
        # In-memory Bayesian parameters: item_id -> {"alpha": int, "beta": int}
        # alpha = successful engagements/adherences, beta = declines/non-adherences
        self._posteriors: Dict[str, Dict[str, float]] = {}

    def _get_posterior(self, item_id: str) -> Tuple[float, float]:
        if item_id not in self._posteriors:
            # Informative empirical prior: Alpha=5, Beta=2 (initial prior mean = 0.71)
            self._posteriors[item_id] = {"alpha": 5.0, "beta": 2.0}
        p = self._posteriors[item_id]
        return p["alpha"], p["beta"]

    def sample_exploration_multiplier(self, item_id: str) -> Tuple[float, bool]:
        """
        Samples a probability from the item's Beta posterior distribution.
        Returns: (sampled_score: float, is_explored: bool)
        """
        alpha, beta = self._get_posterior(item_id)
        # Draw Thompson sample from Beta(alpha, beta)
        sample = random.betavariate(alpha, beta)

        # An item is considered explored if the sample deviates substantially (> 15%) from its prior mean
        prior_mean = alpha / (alpha + beta)
        is_explored = abs(sample - prior_mean) > 0.15

        return sample, is_explored

    def update_feedback(self, item_id: str, outcome_reward: float):
        """
        Updates Bayesian Beta posterior with observed reward:
        reward = 1.0 (positive engagement / completed intervention) -> alpha += 1.0
        reward = 0.0 (rejected / discontinued intervention) -> beta += 1.0
        """
        alpha, beta = self._get_posterior(item_id)
        if outcome_reward >= 0.5:
            self._posteriors[item_id]["alpha"] = alpha + 1.0
        else:
            self._posteriors[item_id]["beta"] = beta + 1.0
        logger.info("Bandit updated for %s: Alpha=%.1f, Beta=%.1f", item_id, self._posteriors[item_id]["alpha"], self._posteriors[item_id]["beta"])
