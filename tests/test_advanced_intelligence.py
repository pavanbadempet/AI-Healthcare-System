"""
Unit & Integration Tests for Advanced Clinical Intelligence Systems:
- Conformal Prediction
- Clinical Survival Analysis & Competing Risks
- Polypharmacy Graph Interaction Network
- Marked Temporal Point Process (Multivariate Hawkes Process)
- Safe Offline Reinforcement Learning Treatment Optimizer
- Topological Data Analysis (Persistent Homology)
- FastAPI /v1/advanced/ REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.conformal_prediction import conformal_engine
from backend.main import app
from backend.polypharmacy_graph import polypharmacy_engine
from backend.rl_treatment_optimizer import ClinicalStateObservation, rl_optimizer
from backend.survival_engine import survival_engine
from backend.temporal_point_process import ClinicalHistoricalEvent, tpp_engine
from backend.topological_phenotyping import topological_engine


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. Conformal Prediction Engine Tests
# =====================================================================

def test_conformal_interval_guarantee():
    """Verify split conformal intervals obey finite sample width and coverage."""
    res = conformal_engine.predict_interval(
        target_name="egfr",
        point_estimate=60.0,
        confidence_level=0.95,
    )
    assert res.target_name == "egfr"
    assert res.point_estimate == 60.0
    assert res.lower_bound < 60.0 < res.upper_bound
    assert res.confidence_level == 0.95
    assert res.interval_width > 0.0
    assert res.finite_sample_guaranteed is True


def test_conformal_heteroscedastic_scaling():
    """Verify locally weighted conformal bands scale with local spread factor."""
    base_res = conformal_engine.predict_interval("map", 75.0, confidence_level=0.90)
    scaled_res = conformal_engine.predict_interval(
        "map", 75.0, confidence_level=0.90, local_spread_factor=1.8
    )
    assert scaled_res.interval_width > base_res.interval_width
    assert "Heteroscedastic" in scaled_res.method


def test_conformal_adaptive_prediction_set():
    """Verify adaptive prediction sets include top candidates until threshold."""
    probs = {"Sepsis": 0.55, "Pneumonia": 0.30, "Heart_Failure": 0.10, "Other": 0.05}
    res = conformal_engine.predict_classification_set(probs, confidence_level=0.80)
    assert res.diagnostic_category == "Sepsis"
    assert "Sepsis" in res.prediction_set
    assert "Pneumonia" in res.prediction_set
    assert res.set_cardinality >= 2
    assert res.ambiguity_flag is True


def test_conformal_empirical_coverage_evaluation():
    """Verify empirical calibration evaluation on simulated test vectors."""
    y_true = [50.0, 55.0, 62.0, 70.0, 45.0, 80.0]
    y_pred = [51.0, 54.0, 61.0, 68.0, 46.0, 82.0]
    eval_res = conformal_engine.evaluate_calibration_coverage(y_true, y_pred, confidence_level=0.90)
    assert eval_res["sample_size"] == 6
    assert eval_res["empirical_coverage"] >= 0.80


# =====================================================================
# 2. Survival Analysis & Competing Risks Tests
# =====================================================================

def test_kaplan_meier_estimator():
    """Verify Kaplan-Meier estimator produces monotonically decreasing survival."""
    durations = [3.0, 6.0, 12.0, 18.0, 24.0, 30.0]
    events = [1, 0, 1, 1, 0, 1]
    curve = survival_engine.compute_kaplan_meier(durations, events)
    assert len(curve) == 6
    for i in range(len(curve) - 1):
        assert curve[i].survival_probability >= curve[i + 1].survival_probability
        assert 0.0 <= curve[i].lower_ci <= curve[i].upper_ci <= 1.0


def test_cox_proportional_hazards_fit():
    """Verify Cox model estimates hazard ratios and p-values."""
    X = [[60.0, 1.2], [70.0, 2.5], [50.0, 0.8], [65.0, 1.9], [75.0, 3.1]]
    durations = [10.0, 5.0, 25.0, 15.0, 4.0]
    events = [1, 1, 0, 1, 1]
    effects = survival_engine.fit_cox_proportional_hazards(X, durations, events, ["age", "creatinine"])
    assert len(effects) == 2
    assert effects[0].covariate_name == "age"
    assert effects[1].covariate_name == "creatinine"
    assert effects[1].hazard_ratio > 0.0


def test_patient_survival_prediction():
    """Verify individual patient survival projections and competing risks."""
    pred = survival_engine.predict_patient_survival(
        patient_id="PT-SURV-1",
        condition="heart_failure",
        age=66.0,
        biomarkers={"egfr": 45.0, "bnp": 650.0},
        active_therapies=["sglt2_inhibitor"],
    )
    assert pred.patient_id == "PT-SURV-1"
    assert pred.individual_hazard_ratio > 0.0
    assert "1_year" in pred.survival_probabilities
    assert "5_year" in pred.survival_probabilities
    assert pred.survival_probabilities["1_year"] > pred.survival_probabilities["5_year"]
    assert len(pred.competing_risk_probabilities) > 0
    assert len(pred.survival_curve) == 6


# =====================================================================
# 3. Polypharmacy Graph Interaction Network Tests
# =====================================================================

def test_polypharmacy_contraindicated_pair():
    """Verify detection of contraindicated QT prolonging drug pair."""
    report = polypharmacy_engine.evaluate_regimen(["amiodarone", "ciprofloxacin"])
    assert report.is_contraindicated is True
    assert report.highest_severity == "CONTRAINDICATED"
    assert len(report.pairwise_interactions) >= 1
    interaction = report.pairwise_interactions[0]
    assert interaction.interaction_type == "QT_PROLONGATION"
    assert "amiodarone" in report.safer_substitutions or "ciprofloxacin" in report.safer_substitutions


def test_polypharmacy_triple_whammy_synergy():
    """Verify detection of the 3-way Hemodynamic Triple Whammy AKI pathology."""
    report = polypharmacy_engine.evaluate_regimen(["lisinopril", "furosemide", "ibuprofen"])
    assert report.is_contraindicated is True
    assert len(report.high_order_synergies) >= 1
    triple_whammy = report.high_order_synergies[0]
    assert "Triple Whammy" in triple_whammy.synergy_name
    assert report.regimen_toxicity_index >= 5.0
    assert "ibuprofen" in report.safer_substitutions


# =====================================================================
# 4. Marked Temporal Point Process Tests
# =====================================================================

def test_temporal_point_process_intensities():
    """Verify Hawkes process computes positive intensities and tracks excitation."""
    history = [
        ClinicalHistoricalEvent(timestamp_hours=4.0, event_type="SEPSIS_ALERT", severity_mark=1.5),
        ClinicalHistoricalEvent(timestamp_hours=10.0, event_type="ACUTE_DECOMPENSATION", severity_mark=2.0),
    ]
    intensities = tpp_engine.calculate_intensities(current_time_hours=12.0, history=history)
    assert len(intensities) == 5
    assert all(i > 0 for i in intensities)


def test_temporal_point_process_forecast():
    """Verify TPP cascade forecast returns subcritical branching ratio and simulated arrivals."""
    history = [
        ClinicalHistoricalEvent(timestamp_hours=2.0, event_type="LAB_PANIC_VALUE", severity_mark=1.0),
        ClinicalHistoricalEvent(timestamp_hours=8.0, event_type="ARRHYTHMIA", severity_mark=1.2),
    ]
    forecast = tpp_engine.forecast_cascade("PT-TPP-1", current_time_hours=16.0, history=history)
    assert forecast.patient_id == "PT-TPP-1"
    assert forecast.dominant_near_term_threat in tpp_engine._event_types
    assert forecast.branching_ratio_spectral_radius < 1.0
    assert forecast.system_is_subcritical is True
    assert forecast.expected_time_to_next_event_hours > 0.0


# =====================================================================
# 5. Safe Offline Reinforcement Learning Optimizer Tests
# =====================================================================

def test_rl_optimizer_hypotension_resuscitation():
    """Verify RL policy selects vasopressor titration when patient is in shock."""
    shock_state = ClinicalStateObservation(
        map_mmhg=54.0,
        heart_rate_bpm=122.0,
        lactate_mmol_l=4.2,
        serum_creatinine=1.8,
        urine_output_ml_kg_hr=0.4,
        blood_glucose_mg_dl=130.0,
    )
    policy = rl_optimizer.optimize_treatment_policy(
        patient_id="PT-SHOCK-1",
        state=shock_state,
        current_vasopressor_dose=0.0,
        current_fluid_rate=0.0,
        current_insulin_rate=0.0,
    )
    assert policy.patient_id == "PT-SHOCK-1"
    assert policy.norepinephrine_dose_mcg_kg_min > 0.0
    assert policy.expected_counterfactual_gain >= 0.0
    assert policy.safety_interlock_cleared is True


def test_rl_optimizer_hypoglycemia_pruning():
    """Verify RL policy prunes insulin when patient is hypoglycemic (OOD avoidance)."""
    hypo_state = ClinicalStateObservation(
        map_mmhg=75.0,
        heart_rate_bpm=80.0,
        lactate_mmol_l=1.1,
        serum_creatinine=0.9,
        urine_output_ml_kg_hr=1.2,
        blood_glucose_mg_dl=62.0,  # Hypoglycemia
    )
    policy = rl_optimizer.optimize_treatment_policy(
        patient_id="PT-HYPO-1",
        state=hypo_state,
        current_vasopressor_dose=0.0,
        current_fluid_rate=100.0,
        current_insulin_rate=0.0,
    )
    assert policy.insulin_rate_units_hr == 0.0


# =====================================================================
# 6. Topological Data Analysis (Persistent Homology) Tests
# =====================================================================

def test_topological_phenotyping_clustering():
    """Verify persistent homology identifies H0 cluster modes and persistent entropy."""
    features = [
        [60.0, 1.2, 50.0],
        [62.0, 1.4, 48.0],
        [85.0, 0.8, 90.0],
        [88.0, 0.9, 92.0],
        [45.0, 3.5, 25.0],
        [48.0, 3.2, 28.0],
    ]
    report = topological_engine.analyze_phenotypic_manifold("COHORT-TEST", features)
    assert report.cohort_id == "COHORT-TEST"
    assert report.num_samples == 6
    assert report.dimension == 3
    assert report.persistent_entropy > 0.0
    assert len(report.h0_persistence) > 0
    assert len(report.betti_curves) == 10


# =====================================================================
# 7. FastAPI /v1/advanced/ REST Endpoints Tests
# =====================================================================

def test_api_conformal_interval(client: TestClient):
    payload = {"target_name": "map", "point_estimate": 72.0, "confidence_level": 0.95}
    res = client.post("/v1/advanced/conformal-predict-interval", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_name"] == "map"
    assert data["lower_bound"] < 72.0 < data["upper_bound"]


def test_api_conformal_set(client: TestClient):
    payload = {
        "candidate_probabilities": {"Acute_MI": 0.70, "Unstable_Angina": 0.20, "Pericarditis": 0.10},
        "confidence_level": 0.90,
    }
    res = client.post("/v1/advanced/conformal-predict-set", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Acute_MI" in data["prediction_set"]


def test_api_survival_analysis(client: TestClient):
    payload = {
        "patient_id": "PT-API-SURV",
        "condition": "heart_failure",
        "age": 70.0,
        "biomarkers": {"egfr": 42.0, "bnp": 600.0},
        "active_therapies": ["sglt2_inhibitor"],
    }
    res = client.post("/v1/advanced/survival-analysis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "PT-API-SURV"
    assert "5_year" in data["survival_probabilities"]


def test_api_polypharmacy_evaluate(client: TestClient):
    payload = {
        "drug_list": ["spironolactone", "lisinopril", "amiodarone"],
    }
    res = client.post("/v1/advanced/polypharmacy-evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["num_drugs"] == 3
    assert len(data["pairwise_interactions"]) > 0


def test_api_temporal_forecast(client: TestClient):
    payload = {
        "patient_id": "PT-API-TPP",
        "current_time_hours": 24.0,
        "history": [
            {"timestamp_hours": 6.0, "event_type": "SEPSIS_ALERT", "severity_mark": 1.0},
            {"timestamp_hours": 12.0, "event_type": "ACUTE_DECOMPENSATION", "severity_mark": 1.4},
        ],
    }
    res = client.post("/v1/advanced/temporal-forecast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "PT-API-TPP"
    assert data["system_is_subcritical"] is True


def test_api_rl_treatment_optimization(client: TestClient):
    payload = {
        "patient_id": "PT-API-RL",
        "state": {
            "map_mmhg": 58.0,
            "heart_rate_bpm": 115.0,
            "lactate_mmol_l": 3.4,
            "serum_creatinine": 1.7,
            "urine_output_ml_kg_hr": 0.45,
            "blood_glucose_mg_dl": 220.0,
        },
        "current_vasopressor_dose": 0.0,
        "current_fluid_rate": 100.0,
        "current_insulin_rate": 0.0,
    }
    res = client.post("/v1/advanced/rl-optimize-treatment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["patient_id"] == "PT-API-RL"
    assert data["safety_interlock_cleared"] is True


def test_api_topological_phenotype(client: TestClient):
    payload = {
        "cohort_id": "COHORT-API-TOPO",
        "patient_feature_matrix": [
            [70.0, 1.2, 60.0],
            [72.0, 1.4, 58.0],
            [80.0, 0.9, 85.0],
            [82.0, 0.8, 88.0],
        ],
    }
    res = client.post("/v1/advanced/topological-phenotype", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["cohort_id"] == "COHORT-API-TOPO"
    assert data["num_samples"] == 4
