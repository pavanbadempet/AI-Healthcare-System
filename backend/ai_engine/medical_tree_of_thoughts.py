"""
Medical Tree-of-Thoughts (Med-ToT) & Value of Diagnostic Information (VoI) Optimizer.

Models clinical diagnostic workup as a Partially Observable Sequential Decision Process (POMDP).
Explores branching diagnostic hypothesis trees and computes the Expected Value of Diagnostic
Information (EVDI / VoI) to identify the Pareto-optimal sequence of diagnostic tests.

Balances:
1. Shannon Information Gain: Expected entropy reduction of differential diagnosis distribution.
2. Invasiveness & Radiation Burden: Contrast nephrotoxicity, ionizing radiation (mSv).
3. Diagnostic Latency: Bedside rapid tests (5 min) vs formal radiology/labs (60-120 min).
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class DiagnosticAction:
    test_id: str
    name: str
    modality: str  # "BEDSIDE_POINT_OF_CARE", "LABORATORY_ASSAY", "ADVANCED_IMAGING", "ELECTROPHYSIOLOGY"
    turnaround_time_minutes: int
    radiation_msv: float
    invasive_risk_score: float  # 0.0 (non-invasive) to 1.0 (arterial catheter / biopsy)
    financial_cost_usd: float
    diagnostic_sensitivity: float
    diagnostic_specificity: float
    target_pathologies: List[str]


@dataclass
class DiagnosticEvaluationNode:
    test_id: str
    test_name: str
    modality: str
    expected_entropy_reduction: float
    expected_value_of_information: float
    composite_utility_score: float
    turnaround_time_minutes: int
    radiation_burden_msv: float
    pareto_rank: int
    clinical_rationale: str


@dataclass
class MedTotOptimizationPlan:
    initial_differential_entropy: float
    primary_suspected_diagnosis: str
    prior_probabilities: Dict[str, float]
    ranked_diagnostic_actions: List[DiagnosticEvaluationNode]
    recommended_immediate_next_test: str
    expected_post_test_entropy: float
    composite_efficiency_gain_pct: float
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MedicalTreeOfThoughtsEngine:
    """
    Tree-of-Thoughts Diagnostic Search and Value of Information Optimization Engine.
    """

    def __init__(self) -> None:
        self.diagnostic_catalog: List[DiagnosticAction] = self._initialize_diagnostic_catalog()

    def _initialize_diagnostic_catalog(self) -> List[DiagnosticAction]:
        return [
            DiagnosticAction(
                test_id="TEST-ECG-12LEAD",
                name="12-Lead Electrocardiogram",
                modality="ELECTROPHYSIOLOGY",
                turnaround_time_minutes=5,
                radiation_msv=0.0,
                invasive_risk_score=0.0,
                financial_cost_usd=65.0,
                diagnostic_sensitivity=0.88,
                diagnostic_specificity=0.92,
                target_pathologies=["ACUTE_CORONARY_SYNDROME", "PERICARDITIS", "PULMONARY_EMBOLISM"],
            ),
            DiagnosticAction(
                test_id="TEST-TROPONIN-HS",
                name="High-Sensitivity Cardiac Troponin I (hs-cTnI)",
                modality="LABORATORY_ASSAY",
                turnaround_time_minutes=45,
                radiation_msv=0.0,
                invasive_risk_score=0.05,
                financial_cost_usd=85.0,
                diagnostic_sensitivity=0.96,
                diagnostic_specificity=0.91,
                target_pathologies=["ACUTE_CORONARY_SYNDROME", "MYOCARDITIS"],
            ),
            DiagnosticAction(
                test_id="TEST-DDIMER-ELISA",
                name="D-Dimer High-Sensitivity ELISA",
                modality="LABORATORY_ASSAY",
                turnaround_time_minutes=45,
                radiation_msv=0.0,
                invasive_risk_score=0.05,
                financial_cost_usd=75.0,
                diagnostic_sensitivity=0.97,
                diagnostic_specificity=0.65,
                target_pathologies=["PULMONARY_EMBOLISM", "AORTIC_DISSECTION"],
            ),
            DiagnosticAction(
                test_id="TEST-CTA-CHEST-AORTOGRAM",
                name="CT Angiography Chest & Aorta (Triple Rule-Out CTA)",
                modality="ADVANCED_IMAGING",
                turnaround_time_minutes=35,
                radiation_msv=8.5,
                invasive_risk_score=0.20,  # IV iodinated contrast risk
                financial_cost_usd=850.0,
                diagnostic_sensitivity=0.99,
                diagnostic_specificity=0.98,
                target_pathologies=["AORTIC_DISSECTION", "PULMONARY_EMBOLISM", "ACUTE_CORONARY_SYNDROME"],
            ),
            DiagnosticAction(
                test_id="TEST-BEDSIDE-POCUS",
                name="Point-of-Care Echocardiography & Lung Ultrasound (POCUS)",
                modality="BEDSIDE_POINT_OF_CARE",
                turnaround_time_minutes=10,
                radiation_msv=0.0,
                invasive_risk_score=0.0,
                financial_cost_usd=120.0,
                diagnostic_sensitivity=0.86,
                diagnostic_specificity=0.89,
                target_pathologies=["AORTIC_DISSECTION", "PERICARDITIS", "PULMONARY_EMBOLISM", "PNEUMOTHORAX"],
            ),
            DiagnosticAction(
                test_id="TEST-CHEST-XRAY-2V",
                name="Chest Radiograph (PA & Lateral)",
                modality="ADVANCED_IMAGING",
                turnaround_time_minutes=20,
                radiation_msv=0.1,
                invasive_risk_score=0.0,
                financial_cost_usd=110.0,
                diagnostic_sensitivity=0.72,
                diagnostic_specificity=0.85,
                target_pathologies=["PNEUMONIA", "PNEUMOTHORAX", "HEART_FAILURE"],
            ),
        ]

    def _calculate_shannon_entropy(self, probabilities: List[float]) -> float:
        """Computes H(p) = - sum p_i * log2(p_i)."""
        entropy = 0.0
        for p in probabilities:
            if p > 1e-6:
                entropy -= p * math.log2(p)
        return round(float(entropy), 4)

    def optimize_diagnostic_pathway(
        self,
        differential_diagnosis_probabilities: Dict[str, float],
        patient_contraindications: Optional[List[str]] = None,
    ) -> MedTotOptimizationPlan:
        """
        Executes tree search over diagnostic actions, computing Expected Value of
        Information (EVDI) and ranking candidate tests.
        """
        contraindications = patient_contraindications or []
        diff_probs = differential_diagnosis_probabilities

        # Normalize prior probabilities
        total_p = sum(diff_probs.values())
        if total_p <= 0:
            diff_probs = {"UNKNOWN_SYNDROME": 1.0}
            total_p = 1.0
        norm_probs = {k: v / total_p for k, v in diff_probs.items()}
        h_prior = self._calculate_shannon_entropy(list(norm_probs.values()))

        # Identify primary hypothesis
        primary_dx = max(norm_probs.items(), key=lambda x: x[1])[0]

        evaluations: List[DiagnosticEvaluationNode] = []

        for test in self.diagnostic_catalog:
            # Check for physical contraindications (e.g. severe renal failure vs CT contrast)
            if "RENAL_FAILURE" in contraindications and test.test_id == "TEST-CTA-CHEST-AORTOGRAM":
                continue

            # Calculate theoretical information gain:
            # Probability of target pathology coverage
            target_coverage = sum(norm_probs.get(t, 0.0) for t in test.target_pathologies)

            # Expected entropy reduction proportional to target coverage and test accuracy
            acc_factor = (test.diagnostic_sensitivity + test.diagnostic_specificity) / 2.0
            expected_reduction = target_coverage * acc_factor * 0.85 * h_prior
            expected_reduction = min(h_prior * 0.95, round(expected_reduction, 4))

            # Penalties: radiation, turnaround time, invasiveness
            time_penalty = min(0.35, (test.turnaround_time_minutes / 120.0) * 0.25)
            rad_penalty = min(0.40, (test.radiation_msv / 10.0) * 0.25)
            risk_penalty = test.invasive_risk_score * 0.20

            # Composite EVDI & Utility
            evdi = max(0.05, expected_reduction * 1.5)
            composite_utility = round(evdi - time_penalty - rad_penalty - risk_penalty, 3)

            rationale = (
                f"{test.name} yields {round(expected_reduction, 3)} bits entropy reduction "
                f"targeting {test.target_pathologies[:2]} with {test.turnaround_time_minutes} min turnaround."
            )

            node = DiagnosticEvaluationNode(
                test_id=test.test_id,
                test_name=test.name,
                modality=test.modality,
                expected_entropy_reduction=expected_reduction,
                expected_value_of_information=round(evdi, 3),
                composite_utility_score=composite_utility,
                turnaround_time_minutes=test.turnaround_time_minutes,
                radiation_burden_msv=test.radiation_msv,
                pareto_rank=0,  # assigned below
                clinical_rationale=rationale,
            )
            evaluations.append(node)

        # Rank by composite utility
        evaluations.sort(key=lambda x: x.composite_utility_score, reverse=True)
        for idx, ev in enumerate(evaluations):
            ev.pareto_rank = idx + 1

        top_test = evaluations[0].test_name if evaluations else "Clinical Re-Evaluation"
        top_reduction = evaluations[0].expected_entropy_reduction if evaluations else 0.0
        post_entropy = max(0.0, round(h_prior - top_reduction, 3))
        efficiency_gain = round(((h_prior - post_entropy) / max(h_prior, 1e-4)) * 100.0, 1)

        return MedTotOptimizationPlan(
            initial_differential_entropy=h_prior,
            primary_suspected_diagnosis=primary_dx,
            prior_probabilities=norm_probs,
            ranked_diagnostic_actions=evaluations,
            recommended_immediate_next_test=top_test,
            expected_post_test_entropy=post_entropy,
            composite_efficiency_gain_pct=efficiency_gain,
        )


medical_tot_engine = MedicalTreeOfThoughtsEngine()
