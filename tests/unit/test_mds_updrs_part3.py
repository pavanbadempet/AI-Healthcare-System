"""
Unit tests for MDS-UPDRS Part III Engine
"""

from backend.ml.mds_updrs_part3_engine import mds_updrs_engine


def test_evaluate_mds_updrs_part3_score_severe():
    res = mds_updrs_engine.evaluate_mds_updrs_part3_score(
        speech_score_0_to_4=3,
        facial_expression_score_0_to_4=3,
        rigidity_score_0_to_4=4,
        finger_tapping_bradykinesia_score_0_to_4=4,
        rest_tremor_score_0_to_4=3,
        gait_postural_instability_score_0_to_4=3,
    )
    assert res["mds_updrs_part3_score"] == 20
    assert res["motor_severity_stage"] == "SEVERE_MOTOR_DISABILITY"
    assert res["deep_brain_stimulation_dbs_indicated"] is True
    assert "Deep Brain Stimulation" in res["clinical_recommendation"]


def test_evaluate_mds_updrs_part3_score_mild():
    res = mds_updrs_engine.evaluate_mds_updrs_part3_score(
        speech_score_0_to_4=0,
        facial_expression_score_0_to_4=1,
        rigidity_score_0_to_4=1,
        finger_tapping_bradykinesia_score_0_to_4=1,
        rest_tremor_score_0_to_4=0,
        gait_postural_instability_score_0_to_4=0,
    )
    assert res["mds_updrs_part3_score"] == 3
    assert res["motor_severity_stage"] == "MILD_MOTOR_SYMPTOMS"
    assert res["deep_brain_stimulation_dbs_indicated"] is False
