"""
Unit tests for MG Cholinergic vs Myasthenic Crisis Engine
"""

from backend.ml.mg_cholinergic_vs_myasthenic_crisis_engine import crisis_diff_engine


def test_evaluate_cholinergic_crisis():
    res = crisis_diff_engine.differentiate_crisis(
        daily_pyridostigmine_dose_mg=600.0,
        sludge_muscarinic_symptoms_present=True,
        miosis_pinpoint_pupils=True,
        muscle_fasciculations_present=True,
    )
    assert res["crisis_type"] == "CHOLINERGIC_CRISIS"
    assert res["pyridostigmine_action"] == "TEMPORARILY_HOLD_PYRIDOSTIGMINE_AND_GIVE_ATROPINE"
    assert "HOLD ALL PYRIDOSTIGMINE" in res["clinical_recommendation"]


def test_evaluate_myasthenic_crisis():
    res = crisis_diff_engine.differentiate_crisis(
        daily_pyridostigmine_dose_mg=240.0,
        fever_or_active_infection_present=True,
    )
    assert res["crisis_type"] == "MYASTHENIC_CRISIS"
    assert res["pyridostigmine_action"] == "CONTINUE_OR_INCREASE_PYRIDOSTIGMINE"
