"""
Unit tests for Clinical Trial Matching Agent
"""

from backend.agents.trial_matching_agent import trial_matching_agent


def test_match_patient_to_trials():
    matches = trial_matching_agent.match_patient_to_trials(
        age=55,
        primary_condition="diabetes",
        egfr=45.0,
        icd10_codes=["E11.9"],
    )
    assert len(matches) > 0
    assert matches[0]["nct_id"] == "NCT04253123"
    assert matches[0]["match_score"] >= 70
    assert matches[0]["status"] == "ELIGIBLE"
