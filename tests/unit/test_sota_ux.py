"""
Unit tests for SOTA High-Performance UX Engine (backend/sota_ux.py).
"""

from backend.sota_ux import SOTAUserExperienceEngine


def test_optimistic_ui_mutation_and_rollback():
    engine = SOTAUserExperienceEngine()

    mutation = engine.apply_optimistic_update(
        mutation_id="MUT_001",
        component="PatientVitalsCard",
        optimistic_state={"heart_rate": 75, "status": "SAVING"},
        rollback_state={"heart_rate": 70, "status": "SAVED"},
    )

    assert mutation.status == "OPTIMISTICALLY_APPLIED"
    assert mutation.optimistic_state["heart_rate"] == 75

    confirmed = engine.confirm_mutation_success("MUT_001")
    assert confirmed
    assert engine.active_mutations["MUT_001"].status == "CONFIRMED"

    # Test rollback
    engine.apply_optimistic_update(
        mutation_id="MUT_002",
        component="AllergyList",
        optimistic_state={"allergies": ["Penicillin"]},
        rollback_state={"allergies": []},
    )

    rolled_back_state = engine.rollback_mutation("MUT_002")
    assert rolled_back_state == {"allergies": []}
