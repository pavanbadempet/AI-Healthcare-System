"""
Unit tests for MSA UMSARS Engine
"""

from backend.ml.msa_umsars_engine import msa_umsars_engine


def test_evaluate_umsars_score_severe():
    res = msa_umsars_engine.evaluate_umsars_score(
        part_1_adl_score_0_to_48=32,
        part_2_motor_exam_score_0_to_56=38,
        parkinsonism_bradykinesia_predominant=True,
    )
    assert res["umsars_total_score"] == 70
    assert res["msa_phenotype"] == "MSA_P_PARKINSONIAN_SUBTYPE"
    assert res["disease_stage"] == "SEVERE_STAGE_IV_BEDRIDDEN"
    assert res["autonomic_pharmacotherapy_indicated"] is True


def test_evaluate_umsars_score_mild():
    res = msa_umsars_engine.evaluate_umsars_score(
        part_1_adl_score_0_to_48=4,
        part_2_motor_exam_score_0_to_56=5,
        cerebellar_ataxia_predominant=True,
    )
    assert res["umsars_total_score"] == 9
    assert res["msa_phenotype"] == "MSA_C_CEREBELLAR_SUBTYPE"
    assert res["disease_stage"] == "MILD_STAGE_I"
