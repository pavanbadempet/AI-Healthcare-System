"""Tests for clinical-tabular package."""

import pickle

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# FTTransformerClassifier
# ---------------------------------------------------------------------------

class TestFTTransformerClassifier:
    def test_fit_predict(self):
        from clinical_tabular.models.ft_transformer import FTTransformerClassifier

        rng = np.random.RandomState(42)
        X = rng.randn(100, 5).astype(np.float32)
        y = (X[:, 0] > 0).astype(int)

        model = FTTransformerClassifier(d_embedding=16, depth=1, epochs=3, batch_size=32)
        model.fit(X, y)

        proba = model.predict_proba(X)
        assert proba.shape == (100, 2)
        assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-5)

        preds = model.predict(X)
        assert preds.shape == (100,)
        assert set(preds).issubset({0, 1})

    def test_pickle_roundtrip(self):
        from clinical_tabular.models.ft_transformer import FTTransformerClassifier

        rng = np.random.RandomState(7)
        X = rng.randn(60, 4).astype(np.float32)
        y = np.random.randint(0, 2, 60)

        model = FTTransformerClassifier(d_embedding=8, depth=1, epochs=2, batch_size=32)
        model.fit(X, y)
        p_before = model.predict_proba(X[:5])

        data = pickle.dumps(model)
        restored = pickle.loads(data)
        p_after = restored.predict_proba(X[:5])

        np.testing.assert_allclose(p_before, p_after, atol=1e-5)


# ---------------------------------------------------------------------------
# ClinicalTemporalLSTM
# ---------------------------------------------------------------------------

class TestClinicalTemporalLSTM:
    def test_fit_predict_3d(self):
        from clinical_tabular.models.temporal_lstm import ClinicalTemporalLSTM

        rng = np.random.RandomState(42)
        X = rng.randn(50, 4, 3).astype(np.float32)
        y = (X[:, -1, 0] > 0).astype(int)

        model = ClinicalTemporalLSTM(hidden_dim=16, num_layers=1, epochs=3, batch_size=16, patience=2)
        model.fit(X, y)

        proba = model.predict_proba(X)
        assert proba.shape == (50, 2)
        assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    def test_attention_weights(self):
        from clinical_tabular.models.temporal_lstm import ClinicalTemporalLSTM

        rng = np.random.RandomState(99)
        X = rng.randn(20, 5, 3).astype(np.float32)
        y = np.random.randint(0, 2, 20)

        model = ClinicalTemporalLSTM(hidden_dim=8, num_layers=1, epochs=2, batch_size=10)
        model.fit(X, y)

        probs, attn = model.predict_with_attention(X)
        assert probs.shape == (20,)
        assert attn.shape == (20, 5)
        assert np.allclose(attn.sum(axis=1), 1.0, atol=1e-5)

    def test_pickle_roundtrip(self):
        from clinical_tabular.models.temporal_lstm import ClinicalTemporalLSTM

        rng = np.random.RandomState(1)
        X = rng.randn(30, 3, 4).astype(np.float32)
        y = np.random.randint(0, 2, 30)

        model = ClinicalTemporalLSTM(hidden_dim=8, num_layers=1, epochs=2, batch_size=16)
        model.fit(X, y)
        p_before = model.predict_proba(X[:5])

        data = pickle.dumps(model)
        restored = pickle.loads(data)
        p_after = restored.predict_proba(X[:5])
        np.testing.assert_allclose(p_before, p_after, atol=1e-5)


# ---------------------------------------------------------------------------
# PyTorchTabularMLP
# ---------------------------------------------------------------------------

class TestPyTorchTabularMLP:
    def test_fit_predict(self):
        from clinical_tabular.models.tabular_mlp import PyTorchTabularMLP

        rng = np.random.RandomState(42)
        X = rng.randn(80, 5).astype(np.float32)
        y = (X[:, 0] > 0).astype(int)

        model = PyTorchTabularMLP(hidden_dims=[16, 8], epochs=5, batch_size=32)
        model.fit(X, y)

        proba = model.predict_proba(X)
        assert proba.shape == (80, 2)

        preds = model.predict(X)
        assert set(preds).issubset({0, 1})


# ---------------------------------------------------------------------------
# Clinical Indices
# ---------------------------------------------------------------------------

class TestClinicalIndices:
    def test_egfr_ckd_epi(self):
        from clinical_tabular.indices import calculate_egfr_ckd_epi

        result = calculate_egfr_ckd_epi(age=65, gender=1, creatinine=1.2)
        assert result is not None
        assert "egfr" in result
        assert "stage" in result
        assert result["egfr"] > 0

    def test_egfr_invalid_input(self):
        from clinical_tabular.indices import calculate_egfr_ckd_epi

        assert calculate_egfr_ckd_epi(age=10, gender=1, creatinine=1.0) is None  # too young
        assert calculate_egfr_ckd_epi(age=50, gender=0, creatinine=-1) is None  # negative creatinine

    def test_fib4_index(self):
        from clinical_tabular.indices import calculate_fib4_index

        result = calculate_fib4_index(age=50, ast=45, alt=30, platelets=200)
        assert result is not None
        assert "score" in result
        assert "risk_level" in result

    def test_framingham_risk(self):
        from clinical_tabular.indices import calculate_framingham_risk

        result = calculate_framingham_risk(
            age=55, gender=1, total_chol=240, hdl_chol=45,
            sbp=140, smoker=0, diabetes=0, hyp_treatment=1,
        )
        assert result is not None
        assert "risk_percent" in result
        assert 0 <= result["risk_percent"] <= 100


# ---------------------------------------------------------------------------
# Conformal Prediction
# ---------------------------------------------------------------------------

class TestConformalPrediction:
    def test_compute_threshold(self):
        from clinical_tabular.calibration import compute_conformal_threshold

        rng = np.random.RandomState(42)
        y_true = np.array([0, 0, 0, 1, 1, 1, 0, 1])
        proba = rng.rand(8)

        threshold = compute_conformal_threshold(y_true, proba, alpha=0.05)
        assert isinstance(threshold, float)
        assert 0 <= threshold <= 1

    def test_class_conditional(self):
        from clinical_tabular.calibration import class_conditional_thresholds

        rng = np.random.RandomState(7)
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        proba = rng.rand(8)

        thresholds = class_conditional_thresholds(y_true, proba)
        assert 0 in thresholds
        assert 1 in thresholds

    def test_prediction_set(self):
        from clinical_tabular.calibration import conformal_prediction_set

        result = conformal_prediction_set(proba_positive=0.85, conformal_q=0.5)
        assert "conformal_prediction_set" in result
        assert "uncertainty_status" in result

    def test_triage_recommendation(self):
        from clinical_tabular.calibration import get_triage_recommendation

        rec = get_triage_recommendation(1, [1])
        assert "Urgent" in rec

        rec = get_triage_recommendation(0, [0])
        assert "Routine" in rec

        rec = get_triage_recommendation(1, [0, 1])
        assert "Triage" in rec


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class TestEvaluation:
    def test_evaluate_model(self):
        from clinical_tabular.evaluation import evaluate_model
        from sklearn.ensemble import RandomForestClassifier

        rng = np.random.RandomState(42)
        X = rng.randn(100, 5)
        y = (X[:, 0] > 0).astype(int)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X[:80], y[:80])

        results = evaluate_model(model, X[80:], y[80:], [f"f{i}" for i in range(5)], "test")
        assert "accuracy" in results
        assert "auc_roc" in results
        assert "confusion_matrix" in results
        assert "sensitivity" in results
        assert results["model_name"] == "test"
