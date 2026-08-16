"""
Comprehensive Test Suite for 4-Stage Multi-Objective Clinical Recommendation Engine.
Tests:
1. Stage 1: Two-Tower Candidate Retrieval & Dense Embeddings
2. Stage 2: MMoE Multi-Objective Ranker (Efficacy, Safety, Adherence)
3. Stage 3: MMR Diversity Re-Ranking & Category Capping
4. Stage 4: Safety Guardrails (Contraindication & Allergy Filters)
5. Stage 4: Contextual Thompson Sampling Bandits (Beta Distributions)
6. End-to-End FastAPI Recommendation Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.recommendation.engine import recommendation_pipeline
from backend.recommendation.guardrails_and_bandits import ClinicalSafetyGuardrail, ContextualThompsonBandit
from backend.recommendation.mmoe_ranker import MMoERankingEngine
from backend.recommendation.mmr_diversity import MMRDiversityReRanker
from backend.recommendation.two_tower import TwoTowerCandidateRetrieval
from backend.schemas.recommendation import CandidateItem, PatientContext, RecommendationRequest


@pytest.fixture
def sample_diabetic_patient():
    return PatientContext(
        patient_id="PAT-9912",
        age=58.0,
        gender="male",
        bmi=31.4,
        systolic_bp=142.0,
        diastolic_bp=88.0,
        fasting_glucose=155.0,
        hba1c=8.2,
        primary_conditions=["Type 2 Diabetes Mellitus", "Essential Hypertension", "Stage 2 CKD"],
        allergies=["penicillin"],
        current_medications=["Metformin 1000mg", "Amlodipine 5mg"],
        recent_interactions=["kidney_protection", "glycemic_control"]
    )


@pytest.fixture
def sample_allergic_patient():
    return PatientContext(
        patient_id="PAT-8811",
        age=45.0,
        gender="female",
        primary_conditions=["Hyperlipidemia"],
        allergies=["statin", "atorvastatin"],
        current_medications=["Ezetimibe 10mg"]
    )


def test_stage1_two_tower_retrieval(sample_diabetic_patient):
    """Verifies that Stage 1 Two-Tower retrieves relevant candidates with valid cosine similarities."""
    retriever = TwoTowerCandidateRetrieval()
    candidates = retriever.retrieve_candidates(sample_diabetic_patient, domain="clinical_intervention", top_n=10)

    assert len(candidates) > 0
    for cand in candidates:
        assert isinstance(cand, CandidateItem)
        assert cand.item_id is not None
        assert 0.0 <= cand.similarity_score <= 1.0


def test_stage2_mmoe_multi_objective_ranking(sample_diabetic_patient):
    """Verifies that Stage 2 MMoE outputs calibrated multi-objective probabilities."""
    retriever = TwoTowerCandidateRetrieval()
    ranker = MMoERankingEngine()

    candidates = retriever.retrieve_candidates(sample_diabetic_patient, domain="clinical_intervention", top_n=5)
    scored = ranker.score_candidates(sample_diabetic_patient, candidates)

    assert len(scored) == len(candidates)
    for cand, eff, safe, adh, comp in scored:
        assert 0.0 <= eff <= 1.0
        assert 0.0 <= safe <= 1.0
        assert 0.0 <= adh <= 1.0
        assert 0.0 <= comp <= 1.0

    # Scored candidates must be sorted descending by composite score
    for i in range(len(scored) - 1):
        assert scored[i][4] >= scored[i+1][4]


def test_stage3_mmr_diversity_reranker(sample_diabetic_patient):
    """Verifies that MMR re-ranking prevents category flooding and applies diversity penalty."""
    retriever = TwoTowerCandidateRetrieval()
    ranker = MMoERankingEngine()
    reranker = MMRDiversityReRanker(max_items_per_category=2)

    candidates = retriever.retrieve_candidates(sample_diabetic_patient, domain="clinical_intervention", top_n=8)
    scored = ranker.score_candidates(sample_diabetic_patient, candidates)
    reranked = reranker.rerank(scored, top_k=5, diversity_lambda=0.60)

    assert len(reranked) <= 5
    categories = [item[0].category for item in reranked]
    for cat in set(categories):
        assert categories.count(cat) <= 2  # Respects max category quota


def test_stage4_safety_guardrails(sample_allergic_patient):
    """Verifies that deterministic guardrails filter out contraindicated medications."""
    statin_candidate = CandidateItem(
        item_id="MED-STATIN-TEST",
        title="High-Intensity Statin Therapy (Atorvastatin 80mg)",
        category="pharmacotherapy",
        description="Lowers LDL cholesterol in cardiovascular risk.",
        contraindications=["active liver failure"]
    )

    is_contra, reason = ClinicalSafetyGuardrail.is_contraindicated(sample_allergic_patient, statin_candidate)
    assert is_contra is True
    assert "statin" in reason.lower() or "atorvastatin" in reason.lower()


def test_stage4_thompson_sampling_bandits():
    """Verifies Bayesian Beta posterior updates upon feedback ingestion."""
    bandit = ContextualThompsonBandit()
    item_id = "TEST-BANDIT-01"

    # Initial sampling
    sample_initial, _ = bandit.sample_exploration_multiplier(item_id)
    assert 0.0 <= sample_initial <= 1.0

    # Ingest positive rewards (1.0)
    for _ in range(5):
        bandit.update_feedback(item_id, 1.0)

    alpha_after, beta_after = bandit._get_posterior(item_id)
    assert alpha_after == 10.0  # 5 prior + 5 updates
    assert beta_after == 2.0


@pytest.mark.asyncio
async def test_end_to_end_recommendation_pipeline(sample_diabetic_patient):
    """Verifies full 4-stage pipeline execution and response schema."""
    req = RecommendationRequest(
        patient_context=sample_diabetic_patient,
        domain="clinical_intervention",
        top_k=4,
        diversity_lambda=0.70
    )

    resp = await recommendation_pipeline.recommend(req)
    assert resp.patient_id == "PAT-9912"
    assert len(resp.recommendations) > 0
    assert len(resp.recommendations) <= 4
    assert resp.latency_ms > 0.0

    for rec in resp.recommendations:
        assert rec.rank >= 1
        assert rec.predicted_efficacy > 0.0
        assert rec.safety_score > 0.0
        assert rec.adherence_likelihood > 0.0
        assert len(rec.rationale) > 0


def test_fastapi_recommendation_endpoints():
    """Verifies HTTP endpoints for clinical, lifestyle, and trial recommendations."""
    client = TestClient(app)

    payload = {
        "patient_context": {
            "patient_id": "PAT-HTTP-01",
            "age": 62.0,
            "gender": "female",
            "bmi": 28.5,
            "systolic_bp": 138.0,
            "diastolic_bp": 84.0,
            "fasting_glucose": 130.0,
            "primary_conditions": ["Type 2 Diabetes Mellitus", "Hypertension"],
            "allergies": [],
            "current_medications": ["Metformin 500mg"]
        },
        "domain": "clinical_intervention",
        "top_k": 3
    }

    # 1. Clinical interventions endpoint
    res_clin = client.post("/v1/recommendations/clinical-interventions", json=payload)
    assert res_clin.status_code == 200
    data_clin = res_clin.json()
    assert data_clin["domain"] == "clinical_intervention"
    assert len(data_clin["recommendations"]) == 3

    # 2. Lifestyle pathways endpoint
    payload["domain"] = "lifestyle_pathway"
    res_life = client.post("/v1/recommendations/lifestyle-pathways", json=payload)
    assert res_life.status_code == 200
    data_life = res_life.json()
    assert data_life["domain"] == "lifestyle_pathway"

    # 3. Clinical trials endpoint
    payload["domain"] = "clinical_trial"
    res_trials = client.post("/v1/recommendations/clinical-trials", json=payload)
    assert res_trials.status_code == 200
    data_trials = res_trials.json()
    assert data_trials["domain"] == "clinical_trial"

    # 4. Feedback ingestion endpoint
    feedback_payload = {
        "patient_id": "PAT-HTTP-01",
        "item_id": "MED-SGLT2-01",
        "action": "accept",
        "outcome_value": 1.0
    }
    res_fb = client.post("/v1/recommendations/feedback", json=feedback_payload)
    assert res_fb.status_code == 200
    assert res_fb.json()["status"] == "success"
