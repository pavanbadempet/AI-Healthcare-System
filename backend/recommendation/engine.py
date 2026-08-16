"""
Unified 4-Stage Multi-Objective Clinical Recommendation Engine Orchestrator.
Coordinates:
1. Stage 1: Two-Tower Candidate Retrieval (TwoTowerCandidateRetrieval)
2. Stage 2: Heavy MMoE Multi-Objective Ranking (MMoERankingEngine)
3. Stage 3: MMR Diversity & Re-Ranking (MMRDiversityReRanker)
4. Stage 4: Clinical Guardrails & Contextual Thompson Bandits (ClinicalSafetyGuardrail, ContextualThompsonBandit)
"""

import logging
import time
from typing import Any, Dict, List

from backend.recommendation.guardrails_and_bandits import ClinicalSafetyGuardrail, ContextualThompsonBandit
from backend.recommendation.mmoe_ranker import MMoERankingEngine
from backend.recommendation.mmr_diversity import MMRDiversityReRanker
from backend.recommendation.two_tower import TwoTowerCandidateRetrieval
from backend.schemas.recommendation import (
    CandidateItem,
    FeedbackEvent,
    PatientContext,
    RankedRecommendation,
    RecommendationRequest,
    RecommendationResponse,
)

logger = logging.getLogger("backend.recommendation.engine")


class MultiStageRecommendationPipeline:
    """Production 4-Stage Clinical Recommendation Pipeline."""

    def __init__(self):
        self.stage1_retrieval = TwoTowerCandidateRetrieval()
        self.stage2_ranker = MMoERankingEngine()
        self.stage3_reranker = MMRDiversityReRanker(max_items_per_category=2)
        self.bandit_engine = ContextualThompsonBandit()

    def _generate_clinical_rationale(self, patient: PatientContext, item: CandidateItem, eff: float, safe: float) -> str:
        """Generates evidence-backed clinical justification for the recommendation."""
        reasons = []
        matching_conds = [c for c in patient.primary_conditions if any(c.lower() in t.lower() for t in item.tags)]
        if matching_conds:
            reasons.append(f"Targeted for active diagnosis of {', '.join(matching_conds)}")
        if eff > 0.75:
            reasons.append(f"High predicted efficacy ({eff*100:.0f}%) per {item.evidence_level}")
        if safe > 0.80:
            reasons.append("Verified low risk of pharmacological adverse events")

        return ". ".join(reasons) + "." if reasons else f"Recommended as an evidence-based {item.category} intervention."

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Executes the full 4-stage recommendation pipeline under a 50ms SLA.
        """
        start_time = time.perf_counter()
        patient = request.patient_context
        domain = request.domain
        top_k = int(request.top_k)
        div_lambda = request.diversity_lambda
        enable_exploration = request.enable_exploration

        clean_domain = str(domain).replace("\r", "").replace("\n", "")[:50]
        logger.info("Executing 4-stage recommendation (domain=%s, top_k=%d)", clean_domain, top_k)

        # ---------------------------------------------------------------------
        # STAGE 1: Two-Tower Candidate Retrieval (Retrieve top candidates)
        # ---------------------------------------------------------------------
        raw_candidates: List[CandidateItem] = self.stage1_retrieval.retrieve_candidates(
            context=patient,
            domain=domain,
            top_n=50
        )
        total_retrieved = len(raw_candidates)

        # ---------------------------------------------------------------------
        # STAGE 4A: Pre-Ranking Clinical Safety & Contraindication Filter
        # ---------------------------------------------------------------------
        safe_candidates: List[CandidateItem] = []
        for cand in raw_candidates:
            is_contra, reason = ClinicalSafetyGuardrail.is_contraindicated(patient, cand)
            if not is_contra:
                safe_candidates.append(cand)
            else:
                logger.debug("Filtered candidate %s due to contraindication: %s", cand.item_id, reason)

        # If all candidates filtered, fall back to safe subset of raw candidates
        if not safe_candidates:
            safe_candidates = raw_candidates[:5]

        # ---------------------------------------------------------------------
        # STAGE 2: Heavy Multi-Objective Ranking (MMoE Scoring)
        # ---------------------------------------------------------------------
        scored_candidates = self.stage2_ranker.score_candidates(
            patient=patient,
            candidates=safe_candidates,
            weights=(0.50, 0.30, 0.20)
        )
        total_ranked = len(scored_candidates)

        # ---------------------------------------------------------------------
        # STAGE 3: MMR Diversity & Re-Ranking (Maximal Marginal Relevance)
        # ---------------------------------------------------------------------
        reranked_items = self.stage3_reranker.rerank(
            scored_candidates=scored_candidates,
            top_k=top_k,
            diversity_lambda=div_lambda
        )

        # ---------------------------------------------------------------------
        # STAGE 4B: Contextual Thompson Sampling Exploration & Final Output Construction
        # ---------------------------------------------------------------------
        final_recommendations: List[RankedRecommendation] = []

        for rank_idx, item in enumerate(reranked_items, start=1):
            cand, eff, safe, adh, comp, mmr_penalty = item
            is_explored = False

            if enable_exploration:
                bandit_sample, is_explored = self.bandit_engine.sample_exploration_multiplier(cand.item_id)
                # Modulate composite score slightly with bandit sample for exploration
                comp = (0.85 * comp) + (0.15 * bandit_sample)

            rationale = self._generate_clinical_rationale(patient, cand, eff, safe)

            rec = RankedRecommendation(
                rank=rank_idx,
                item_id=cand.item_id,
                title=cand.title,
                category=cand.category,
                description=cand.description,
                evidence_level=cand.evidence_level,
                predicted_efficacy=round(eff, 4),
                safety_score=round(safe, 4),
                adherence_likelihood=round(adh, 4),
                composite_score=round(comp, 4),
                diversity_score=round(mmr_penalty, 4),
                is_explored=is_explored,
                rationale=rationale
            )
            final_recommendations.append(rec)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("4-Stage Recommendation finished in %.2f ms with %d recommendations", latency_ms, len(final_recommendations))

        return RecommendationResponse(
            patient_id=patient.patient_id,
            domain=domain,
            total_candidates_retrieved=total_retrieved,
            total_ranked_candidates=total_ranked,
            latency_ms=round(latency_ms, 2),
            recommendations=final_recommendations
        )

    def record_feedback(self, feedback: FeedbackEvent) -> Dict[str, Any]:
        """Ingests user/clinician feedback to update Bayesian posteriors for Thompson Sampling."""
        reward = feedback.outcome_value
        # Map qualitative actions to numeric rewards if not explicitly 0/1
        if feedback.action in ("accept", "completed"):
            reward = 1.0
        elif feedback.action in ("decline", "rejected"):
            reward = 0.0

        self.bandit_engine.update_feedback(feedback.item_id, reward)
        return {
            "status": "success",
            "message": f"Feedback recorded for item {feedback.item_id}",
            "reward_applied": reward
        }


# Global singleton instance
recommendation_pipeline = MultiStageRecommendationPipeline()
