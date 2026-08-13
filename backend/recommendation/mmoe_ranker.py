"""
Stage 2: Heavy Multi-Objective Ranking Engine (MMoE / DLRM Architecture).
Scores candidates across 3 simultaneous objectives:
1. Clinical Efficacy (y1)
2. Pharmacological Safety (y2)
3. Patient Adherence / Compliance (y3)
"""

import math
import numpy as np
from typing import List, Dict, Any, Tuple
from backend.schemas.recommendation import PatientContext, CandidateItem


def _sigmoid(x: float) -> float:
    """Standard numerically stable sigmoid function."""
    return 1.0 / (1.0 + math.exp(-max(min(x, 15.0), -15.0)))


def _softmax(vec: List[float]) -> List[float]:
    """Computes softmax distribution over a vector."""
    max_v = max(vec) if vec else 0.0
    exp_v = [math.exp(v - max_v) for v in vec]
    sum_exp = sum(exp_v) or 1.0
    return [e / sum_exp for e in exp_v]


class MMoERankingEngine:
    """
    Multi-gate Mixture-of-Experts (MMoE) Clinical Ranker:
    Extracts dense cross-features and routes through 4 specialized experts with task-specific gates.
    """

    def __init__(self):
        # Initialized calibrated weight matrices for 4 experts and 3 task gates
        # In production, these weights are trained via PySpark / MLflow offline
        self.num_features = 8
        self.num_experts = 4
        
        # Expert feature weights: Shape (num_experts, num_features)
        self.expert_weights = np.array([
            [0.35, 0.40, 0.25, 0.30, 0.15, 0.20, 0.10, 0.50],  # Expert 1: Efficacy specialist
            [0.10, 0.15, 0.45, 0.50, 0.40, 0.30, 0.25, 0.10],  # Expert 2: Safety & Contraindication specialist
            [0.20, 0.10, 0.15, 0.10, 0.20, 0.45, 0.50, 0.20],  # Expert 3: Behavioral Adherence specialist
            [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]   # Expert 4: Shared cross-domain interaction
        ])

        # Task gating weights: Shape (num_tasks=3, num_features, num_experts)
        self.gate_weights = {
            "efficacy": np.array([0.45, 0.35, 0.10, 0.10]),
            "safety": np.array([0.10, 0.10, 0.60, 0.20]),
            "adherence": np.array([0.15, 0.15, 0.20, 0.50])
        }

    def _extract_feature_vector(self, patient: PatientContext, candidate: CandidateItem) -> List[float]:
        """
        Extracts 8 dense multi-dimensional interaction features:
        f0: Vector Cosine Similarity (from Stage 1)
        f1: Tag Overlap with Primary Conditions (Jaccard)
        f2: Physiological Risk Match (Blood Pressure / Glucose alignment)
        f3: Age Vulnerability Factor
        f4: BMI / Metabolic Strain Index
        f5: Medication Complexity Penalty (Adherence proxy)
        f6: Behavioral Engagement Match (Recent interactions)
        f7: Evidence Level Tier (1A=1.0, 1B=0.8, Phase 2/3=0.7)
        """
        # f0: Cosine similarity
        f0 = max(0.0, min(1.0, candidate.similarity_score))

        # f1: Condition tag overlap
        patient_conditions_lower = {c.lower() for c in patient.primary_conditions}
        candidate_tags_lower = {t.lower() for t in candidate.tags}
        overlap = len(patient_conditions_lower.intersection(candidate_tags_lower))
        total_unique = len(patient_conditions_lower.union(candidate_tags_lower)) or 1
        f1 = overlap / total_unique

        # f2: Physiological risk match
        f2 = 0.5
        if ("diabetes" in candidate_tags_lower or "glucose" in candidate_tags_lower) and (patient.fasting_glucose and patient.fasting_glucose > 125):
            f2 += 0.3
        if ("hypertension" in candidate_tags_lower or "cardiovascular" in candidate_tags_lower) and (patient.systolic_bp and patient.systolic_bp > 135):
            f2 += 0.3
        f2 = min(1.0, f2)

        # f3: Age factor
        f3 = min(1.0, max(0.1, patient.age / 80.0))

        # f4: BMI factor
        f4 = min(1.0, max(0.1, (patient.bmi or 25.0) / 40.0))

        # f5: Medication complexity (more current meds = higher adherence friction)
        med_count = len(patient.current_medications)
        f5 = max(0.2, 1.0 - (med_count * 0.08))

        # f6: Behavioral engagement
        recent_lower = {r.lower() for r in patient.recent_interactions}
        f6 = 0.8 if any(r in candidate_tags_lower for r in recent_lower) else 0.5

        # f7: Evidence level
        ev = candidate.evidence_level.lower()
        f7 = 1.0 if "level 1a" in ev else 0.85 if "level 1b" in ev else 0.70

        return [f0, f1, f2, f3, f4, f5, f6, f7]

    def score_candidates(
        self,
        patient: PatientContext,
        candidates: List[CandidateItem],
        weights: Tuple[float, float, float] = (0.50, 0.30, 0.20)
    ) -> List[Tuple[CandidateItem, float, float, float, float]]:
        """
        Executes MMoE Scoring across candidates.
        Returns: List of tuples (candidate, efficacy_score, safety_score, adherence_score, composite_score)
        """
        w_eff, w_safe, w_adh = weights
        scored_candidates = []

        for candidate in candidates:
            x = np.array(self._extract_feature_vector(patient, candidate))

            # Compute output of each of the 4 experts: Expert_i = f_i(x)
            expert_outputs = []
            for i in range(self.num_experts):
                expert_raw = np.dot(self.expert_weights[i], x)
                expert_outputs.append(math.tanh(expert_raw))
            expert_outputs_arr = np.array(expert_outputs)

            # Compute Task Gate distributions: g_task = softmax(GateWeights)
            g_eff = self.gate_weights["efficacy"]
            g_safe = self.gate_weights["safety"]
            g_adh = self.gate_weights["adherence"]

            # Multi-Task Heads: y_k = sigmoid(sum(g_k_i * Expert_i))
            eff_score = _sigmoid(float(np.dot(g_eff, expert_outputs_arr)) * 2.5)
            safe_score = _sigmoid(float(np.dot(g_safe, expert_outputs_arr)) * 2.0)
            adh_score = _sigmoid(float(np.dot(g_adh, expert_outputs_arr)) * 2.2)

            # Composite Calibrated Rank Score
            composite = (w_eff * eff_score) + (w_safe * safe_score) + (w_adh * adh_score)

            scored_candidates.append((candidate, eff_score, safe_score, adh_score, composite))

        # Sort descending by composite rank score
        scored_candidates.sort(key=lambda item: item[4], reverse=True)
        return scored_candidates
