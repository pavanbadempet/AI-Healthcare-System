"""
Parkinson's Disease Movement Disorder Society UPDRS Part III Engine
====================================================================
Scores MDS-UPDRS Part III Motor Examination (0 to 132 points) for motor symptom severity and levodopa response.
"""

from typing import Dict


class MdsUpdrsPart3Engine:
    """Calculates MDS-UPDRS Part III motor score for Parkinson's Disease staging."""

    def evaluate_mds_updrs_part3_score(
        self,
        speech_score_0_to_4: int,
        facial_expression_score_0_to_4: int,
        rigidity_score_0_to_4: int,
        finger_tapping_bradykinesia_score_0_to_4: int,
        rest_tremor_score_0_to_4: int,
        gait_postural_instability_score_0_to_4: int,
        levodopa_on_state: bool = True,
    ) -> Dict[str, any]:
        total_motor_score = (
            speech_score_0_to_4
            + facial_expression_score_0_to_4
            + rigidity_score_0_to_4
            + finger_tapping_bradykinesia_score_0_to_4
            + rest_tremor_score_0_to_4
            + gait_postural_instability_score_0_to_4
        )

        motor_severity = "MILD_MOTOR_SYMPTOMS"
        dbs_evaluation_indicated = False

        if total_motor_score >= 18:
            motor_severity = "SEVERE_MOTOR_DISABILITY"
            dbs_evaluation_indicated = True
        elif total_motor_score >= 10:
            motor_severity = "MODERATE_MOTOR_IMPAIRMENT"

        recommendation = "Mild motor symptoms: Initiate MAO-B inhibitor (Rasagiline) or Dopamine Agonist (Pramipexole)"
        if dbs_evaluation_indicated:
            recommendation = "Severe Motor Disability: Optimize Levodopa/Carbidopa dosage & refer for Deep Brain Stimulation (DBS) evaluation"
        elif motor_severity == "MODERATE_MOTOR_IMPAIRMENT":
            recommendation = "Moderate Motor Impairment: Initiate Levodopa/Carbidopa (Sinemet 100/25 TID) & physical therapy"

        return {
            "mds_updrs_part3_score": total_motor_score,
            "levodopa_on_state": levodopa_on_state,
            "motor_severity_stage": motor_severity,
            "deep_brain_stimulation_dbs_indicated": dbs_evaluation_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mds_updrs_engine = MdsUpdrsPart3Engine()
