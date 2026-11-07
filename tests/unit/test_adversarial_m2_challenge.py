"""
Adversarial Verification Suite for Milestone 2: Schema Parity & Contract Synchronization.
Empirically stress-tests:
1. HeartInput: Rust 13-feature input vs extra fields vs missing required fields vs boundary values.
2. DiabetesInput: 9 required features, boundary conditions, zero/extreme inputs, missing field validation.
3. KidneyInput: is_female boolean vs gender integer bidirectional translation and edge cases.
4. PredictionReviewCreate: clinician_agree vs decision backwards compatibility, conflicting values, note syncing.
5. AuditLogResponse: admin_id vs actor_user_id mapping, ORM attribute syncing, null details.
6. ExplainabilityResponse: Rust structured format vs legacy format vs hybrid.
7. Data Governance: Float types on DbSchemaContract and DbDatasetEntry.
"""
import json
from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy import Float

from backend.models.data_governance import DbDatasetEntry, DbSchemaContract
from backend.schemas.intelligence import ExplainabilityResponse
from backend.schemas.prediction import (
    DiabetesInput,
    HeartInput,
    KidneyInput,
    PredictionReviewCreate,
)
from backend.schemas.records import AuditLogResponse


# ─────────────────────────────────────────────────────────────────────────────
# 1. HeartInput Adversarial Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHeartInputAdversarial:
    """Stress-tests HeartInput schema validation, extra/missing fields, and boundaries."""

    @pytest.fixture
    def valid_13_payload(self) -> dict[str, float]:
        return {
            "age": 63.0,
            "sex": 1.0,
            "cp": 3.0,
            "trestbps": 145.0,
            "chol": 233.0,
            "fbs": 1.0,
            "restecg": 0.0,
            "thalach": 150.0,
            "exang": 0.0,
            "oldpeak": 2.3,
            "slope": 0.0,
            "ca": 0.0,
            "thal": 1.0,
        }

    def test_exact_13_rust_features_accepted_with_defaults(self, valid_13_payload):
        """Rust provides exactly 13 features without hdl/smoker/hyp_treatment. Python must accept and provide defaults."""
        model = HeartInput(**valid_13_payload)
        assert model.age == 63.0
        assert model.sex == 1.0
        assert model.hdl == 50.0
        assert model.smoker == 0
        assert model.hyp_treatment == 0

    def test_each_of_13_required_features_is_strictly_mandatory(self, valid_13_payload):
        """Omitting any single feature of the 13 required features must raise ValidationError."""
        for key in valid_13_payload.keys():
            incomplete = valid_13_payload.copy()
            del incomplete[key]
            with pytest.raises(ValidationError) as exc_info:
                HeartInput(**incomplete)
            errors = exc_info.value.errors()
            assert any(e["loc"] == (key,) for e in errors), f"Missing {key} did not trigger expected validation error"

    def test_extra_unknown_fields_tolerated(self, valid_13_payload):
        """Extra arbitrary fields in payload should not cause validation failure (matches Serde default behavior)."""
        payload = valid_13_payload.copy()
        payload["unrecognized_clinical_marker"] = 999.9
        payload["metadata_string"] = "batch_test"
        model = HeartInput(**payload)
        assert model.age == 63.0

    def test_explicit_optional_clinical_features(self, valid_13_payload):
        """Client explicitly providing hdl, smoker, and hyp_treatment must be preserved."""
        payload = valid_13_payload.copy()
        payload["hdl"] = 42.5
        payload["smoker"] = 1
        payload["hyp_treatment"] = 1
        model = HeartInput(**payload)
        assert model.hdl == 42.5
        assert model.smoker == 1
        assert model.hyp_treatment == 1

    def test_boundary_and_extreme_float_values(self, valid_13_payload):
        """Extreme numerical floats (zero, high age, high cholesterol) parse correctly."""
        payload = valid_13_payload.copy()
        payload["age"] = 0.0
        payload["chol"] = 1000.0
        payload["oldpeak"] = 0.0
        model = HeartInput(**payload)
        assert model.age == 0.0
        assert model.chol == 1000.0

    def test_invalid_types_raise_validation_error(self, valid_13_payload):
        """Passing non-numeric strings or None for required fields must fail."""
        for invalid_val in ["not_a_number", None, [1, 2], {"nested": 1}]:
            payload = valid_13_payload.copy()
            payload["age"] = invalid_val
            with pytest.raises(ValidationError):
                HeartInput(**payload)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DiabetesInput Adversarial Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDiabetesInputAdversarial:
    """Stress-tests DiabetesInput 9 required features and boundary values."""

    @pytest.fixture
    def valid_9_payload(self) -> dict[str, float]:
        return {
            "hypertension": 1.0,
            "high_chol": 1.0,
            "bmi": 28.5,
            "smoking_history": 0.0,
            "heart_disease": 0.0,
            "physical_activity": 1.0,
            "general_health": 2.0,
            "gender": 1.0,
            "age": 55.0,
        }

    def test_exact_9_features_accepted(self, valid_9_payload):
        model = DiabetesInput(**valid_9_payload)
        assert model.bmi == 28.5
        assert model.age == 55.0

    def test_each_of_9_features_is_strictly_mandatory(self, valid_9_payload):
        for key in valid_9_payload.keys():
            incomplete = valid_9_payload.copy()
            del incomplete[key]
            with pytest.raises(ValidationError) as exc_info:
                DiabetesInput(**incomplete)
            errors = exc_info.value.errors()
            assert any(e["loc"] == (key,) for e in errors)

    def test_zero_and_extreme_boundary_values(self, valid_9_payload):
        payload = valid_9_payload.copy()
        payload["hypertension"] = 0.0
        payload["high_chol"] = 0.0
        payload["bmi"] = 99.9
        payload["age"] = 120.0
        model = DiabetesInput(**payload)
        assert model.bmi == 99.9
        assert model.age == 120.0

    def test_stringified_floats_coerced(self, valid_9_payload):
        """Pydantic V2 default string-to-float coercion."""
        payload = valid_9_payload.copy()
        payload["bmi"] = "31.4"
        payload["age"] = "48"
        model = DiabetesInput(**payload)
        assert model.bmi == 31.4
        assert model.age == 48.0

    def test_non_numeric_values_raise_validation_error(self, valid_9_payload):
        payload = valid_9_payload.copy()
        payload["bmi"] = "invalid_bmi"
        with pytest.raises(ValidationError):
            DiabetesInput(**payload)


# ─────────────────────────────────────────────────────────────────────────────
# 3. KidneyInput is_female / gender Parity Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestKidneyInputAdversarial:
    """Stress-tests KidneyInput bidirectional translation between is_female (Rust) and gender (Python)."""

    def test_gender_0_derives_is_female_true(self):
        k = KidneyInput(gender=0)
        assert k.is_female is True
        assert k.gender == 0

    def test_gender_1_derives_is_female_false(self):
        k = KidneyInput(gender=1)
        assert k.is_female is False
        assert k.gender == 1

    def test_is_female_true_derives_gender_0(self):
        k = KidneyInput(is_female=True)
        assert k.gender == 0
        assert k.is_female is True

    def test_is_female_false_derives_gender_1(self):
        k = KidneyInput(is_female=False)
        assert k.gender == 1
        assert k.is_female is False

    def test_empty_defaults_to_male_none_is_female(self):
        """When neither gender nor is_female is specified in raw dict, gender defaults to 1."""
        k = KidneyInput()
        assert k.gender == 1
        assert k.is_female is None

    def test_both_specified_and_matching(self):
        k_f = KidneyInput(gender=0, is_female=True)
        assert k_f.gender == 0
        assert k_f.is_female is True

        k_m = KidneyInput(gender=1, is_female=False)
        assert k_m.gender == 1
        assert k_m.is_female is False

    def test_arbitrary_gender_integer_falls_back_cleanly(self):
        """Arbitrary non-0 gender integer sets is_female to False."""
        k = KidneyInput(gender=2)
        assert k.is_female is False
        assert k.gender == 2

    def test_serialization_dump_contains_both_fields(self):
        """Serializing KidneyInput produces JSON consumable by both Rust and Python."""
        k = KidneyInput(is_female=True, sc=1.2, age=50.0)
        dump = k.model_dump()
        assert dump["is_female"] is True
        assert dump["gender"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 4. PredictionReviewCreate Backwards Compatibility Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPredictionReviewCreateAdversarial:
    """Stress-tests clinician_agree / decision bidirectional derivation and note syncing."""

    def test_rust_format_derives_decision(self):
        # Rust clinician_agree: false -> decision: overridden
        r1 = PredictionReviewCreate(
            patient_id=1,
            prediction_type="heart",
            clinician_agree=False,
            notes="Requires cardiac catheterization",
        )
        assert r1.decision == "overridden"
        assert r1.review_note == "Requires cardiac catheterization"
        assert r1.clinician_agree is False

        # Rust clinician_agree: true -> decision: accepted
        r2 = PredictionReviewCreate(
            patient_id=2,
            prediction_type="diabetes",
            clinician_agree=True,
        )
        assert r2.decision == "accepted"
        assert r2.clinician_agree is True

    def test_python_format_derives_clinician_agree(self):
        for affirmative in ["accepted", "agree", "approved", "true", "1", "ACCEPTED", "  Agree  "]:
            r = PredictionReviewCreate(
                patient_id=1,
                prediction_type="kidney",
                decision=affirmative,
            )
            assert r.clinician_agree is True, f"Failed to parse affirmative decision: {affirmative}"

        for negative in ["overridden", "disagree", "rejected", "false", "0", "denied"]:
            r = PredictionReviewCreate(
                patient_id=1,
                prediction_type="kidney",
                decision=negative,
            )
            assert r.clinician_agree is False, f"Failed to parse negative decision: {negative}"

    def test_note_and_review_note_bidirectional_sync(self):
        # notes -> review_note
        r1 = PredictionReviewCreate(
            patient_id=10,
            prediction_type="liver",
            notes="Elevated AST/ALT",
        )
        assert r1.notes == "Elevated AST/ALT"
        assert r1.review_note == "Elevated AST/ALT"

        # review_note -> notes
        r2 = PredictionReviewCreate(
            patient_id=11,
            prediction_type="liver",
            review_note="Ultrasound recommended",
        )
        assert r2.notes == "Ultrasound recommended"
        assert r2.review_note == "Ultrasound recommended"

    def test_default_model_prediction_is_empty_string(self):
        r = PredictionReviewCreate(
            patient_id=20,
            prediction_type="stroke",
        )
        assert r.model_prediction == ""


# ─────────────────────────────────────────────────────────────────────────────
# 5. AuditLogResponse admin_id / actor_user_id Parity Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditLogResponseAdversarial:
    """Stress-tests AuditLogResponse admin_id / actor_user_id mapping across dicts and ORM objects."""

    def test_dict_with_admin_id_derives_actor_user_id(self):
        resp = AuditLogResponse(
            id=100,
            admin_id=77,
            action="UPDATE_CONFIG",
            timestamp="2026-11-07T00:00:00Z",
        )
        assert resp.admin_id == 77
        assert resp.actor_user_id == 77

    def test_dict_with_actor_user_id_derives_admin_id(self):
        resp = AuditLogResponse(
            id=101,
            actor_user_id=88,
            action="EXPORT_METRICS",
            timestamp="2026-11-07T00:00:00Z",
        )
        assert resp.admin_id == 88
        assert resp.actor_user_id == 88

    def test_orm_attribute_sync(self):
        class MockOrmAuditLog:
            def __init__(self, id_val, admin_id_val, action_val):
                self.id = id_val
                self.admin_id = admin_id_val
                self.action = action_val
                self.timestamp = datetime.now(timezone.utc)
                self.details = "ORM test"
                self.facility_id = None
                self.target_user_id = None

        mock_obj = MockOrmAuditLog(200, 99, "MOCK_ACTION")
        resp = AuditLogResponse.model_validate(mock_obj)
        assert resp.admin_id == 99
        assert resp.actor_user_id == 99
        assert resp.details == "ORM test"

    def test_nullable_details_preserves_none_and_empty(self):
        resp_none = AuditLogResponse(
            id=1, admin_id=1, action="A", timestamp="2026-11-07T00:00:00Z", details=None
        )
        assert resp_none.details is None

        resp_default = AuditLogResponse(
            id=2, admin_id=1, action="A", timestamp="2026-11-07T00:00:00Z"
        )
        assert resp_default.details == ""


# ─────────────────────────────────────────────────────────────────────────────
# 6. ExplainabilityResponse Parity Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExplainabilityResponseAdversarial:
    """Stress-tests ExplainabilityResponse handling both Rust and legacy Python structures."""

    def test_rust_format_deserialization(self):
        rust_data = {
            "prediction_id": 901,
            "model_name": "diabetes_onnx",
            "base_value": 0.05,
            "predicted_value": 0.72,
            "feature_contributions": [
                {"feature_name": "bmi", "feature_value": 32.0, "shap_value": 0.40, "impact": "POSITIVE"},
                {"feature_name": "age", "feature_value": 60.0, "shap_value": 0.25, "impact": "POSITIVE"},
            ],
            "conformal_prediction": {
                "alpha": 0.05,
                "lower_bound": 0.65,
                "upper_bound": 0.79,
                "prediction_set": ["High Risk"],
            },
        }
        resp = ExplainabilityResponse(**rust_data)
        assert resp.prediction_id == 901
        assert resp.base_value == 0.05
        assert resp.predicted_value == 0.72
        assert len(resp.feature_contributions) == 2
        assert resp.conformal_prediction["prediction_set"] == ["High Risk"]

    def test_legacy_python_format_deserialization(self):
        py_data = {
            "prediction_id": 902,
            "model_name": "heart_disease_legacy",
            "feature_importances": {"chol": 0.35, "trestbps": 0.25},
            "explanation_text": "Elevated cholesterol increases CVD risk.",
        }
        resp = ExplainabilityResponse(**py_data)
        assert resp.prediction_id == 902
        assert resp.feature_importances["chol"] == 0.35
        assert resp.explanation_text == "Elevated cholesterol increases CVD risk."
        assert resp.base_value is None

    def test_hybrid_format_with_extra_fields(self):
        hybrid_data = {
            "prediction_id": 903,
            "model_name": "kidney_hybrid",
            "base_value": 0.1,
            "predicted_value": 0.9,
            "extra_metric": 42.0,
        }
        resp = ExplainabilityResponse(**hybrid_data)
        assert resp.prediction_id == 903
        assert resp.extra_metric == 42.0  # extra="allow" preserves arbitrary fields


# ─────────────────────────────────────────────────────────────────────────────
# 7. Data Governance Float Precision Stress Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDataGovernanceFloatTypes:
    """Verifies that quality_threshold and quality_score are defined as SQLAlchemy Float."""

    def test_columns_are_float_instances(self):
        assert isinstance(DbSchemaContract.quality_threshold.type, Float)
        assert isinstance(DbDatasetEntry.quality_score.type, Float)

    def test_fractional_float_precision_preserved(self):
        contract = DbSchemaContract(
            contract_id="test_cntr_01",
            name="Test Contract",
            producer="source",
            consumer="sink",
            schema_definition={},
            required_fields=[],
            quality_threshold=0.987654321,
        )
        assert abs(contract.quality_threshold - 0.987654321) < 1e-6

        entry = DbDatasetEntry(
            dataset_id="test_ds_01",
            name="Test Dataset",
            owner="data_team",
            schema_definition={},
            tags=[],
            quality_score=0.99999,
        )
        assert abs(entry.quality_score - 0.99999) < 1e-5
