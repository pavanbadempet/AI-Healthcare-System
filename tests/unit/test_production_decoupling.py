"""
Tests for Requirement R3: Python Specification and Production Decoupling.
Verifies that:
1. Python backend refuses to start in live production mode (ENV=production / ENVIRONMENT=production).
2. Development and test modes operate normally for specification and tooling inspection.
3. Production deployment manifests (Dockerfile.enterprise, docker-compose.enterprise.yml, render.yaml, runners)
   strictly launch the pure Rust Gateway binary and never invoke Uvicorn / Python interpreter in production.
4. Schema & DTO parity between Python Pydantic V2 schemas and Rust Serde structs.
5. Data governance SQL models have correct Float types matching Rust governance models.
"""
import importlib
import os
import re
from pathlib import Path

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


ROOT_DIR = Path(__file__).resolve().parent.parent.parent


# ── 1. Production Runtime Lockout Tests ──────────────────────────────

def test_production_lockout_raises_runtime_error_with_env(monkeypatch):
    """Setting ENV=production must trigger immediate RuntimeError on backend.main startup."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore safe testing state
    monkeypatch.setenv("ENV", "test")
    importlib.reload(backend.main)


def test_production_lockout_raises_runtime_error_with_environment(monkeypatch):
    """Setting ENVIRONMENT=production must trigger immediate RuntimeError on backend.main startup."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENV", raising=False)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore safe testing state
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    importlib.reload(backend.main)


def test_dev_and_test_mode_allowed(monkeypatch):
    """Setting ENV=test or ENV=development allows normal backend loading for contract inspection."""
    for mode in ["test", "development"]:
        monkeypatch.setenv("ENV", mode)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        import backend.main
        reloaded = importlib.reload(backend.main)
        assert reloaded.app is not None
        assert reloaded.app.title == "AI Healthcare API"


# ── 2. Static AST & Deployment Manifest Decoupling Tests ─────────────

def test_dockerfile_enterprise_pure_rust_production():
    """Dockerfile.enterprise must build and run pure Rust rust_gateway without Uvicorn."""
    dockerfile_path = ROOT_DIR / "Dockerfile.enterprise"
    assert dockerfile_path.exists(), "Dockerfile.enterprise must exist"
    content = dockerfile_path.read_text(encoding="utf-8")

    # Assert multi-stage Rust build
    assert "FROM rust:" in content or "FROM rust" in content
    assert "cargo build --release" in content
    assert "--bin rust_gateway" in content

    # Assert builder stage installs protobuf-compiler required by tonic-build for proto compilation
    assert "protobuf-compiler" in content, (
        "Dockerfile.enterprise builder stage must install protobuf-compiler for tonic-build proto compilation"
    )

    # Assert rust_gateway build assets (build.rs and proto/) are copied to the builder stage
    has_full_crate_copy = bool(re.search(r"COPY\s+rust_gateway/\s+\./rust_gateway/?", content))
    has_granular_asset_copies = (
        "build.rs" in content
        and "proto" in content
        and "Cargo.toml" in content
        and "src" in content
    )
    assert has_full_crate_copy or has_granular_asset_copies, (
        "Dockerfile.enterprise must copy rust_gateway build assets including build.rs and proto"
    )

    # Assert final runtime does NOT run uvicorn or python
    assert "uvicorn" not in content.lower()
    assert 'CMD ["/app/rust_gateway"]' in content


def test_docker_compose_enterprise_pure_rust_backend():
    """docker-compose.enterprise.yml must configure the backend service to run rust_gateway."""
    compose_path = ROOT_DIR / "docker-compose.enterprise.yml"
    assert compose_path.exists(), "docker-compose.enterprise.yml must exist"
    content = compose_path.read_text(encoding="utf-8")

    # Assert backend service does not execute uvicorn
    assert "uvicorn backend.main:app" not in content
    assert "command: /app/rust_gateway" in content


def test_render_yaml_pure_rust_service():
    """render.yaml must build and execute the pure Rust Gateway binary."""
    render_path = ROOT_DIR / "render.yaml"
    assert render_path.exists(), "render.yaml must exist"
    content = render_path.read_text(encoding="utf-8")

    assert "env: rust" in content
    assert "cargo run --release" in content or "cargo build --release" in content
    assert "uvicorn backend.main:app" not in content


def test_runner_scripts_pure_rust_production():
    """run_servers.py and run_prod.bat must launch rust_gateway in production mode."""
    run_servers_path = ROOT_DIR / "run_servers.py"
    assert run_servers_path.exists()
    run_servers_content = run_servers_path.read_text(encoding="utf-8")

    # Assert rust_gateway execution path in run_servers.py
    assert "rust_gateway" in run_servers_content
    assert "cargo" in run_servers_content

    run_prod_path = ROOT_DIR / "scripts" / "runners" / "run_prod.bat"
    assert run_prod_path.exists()
    run_prod_content = run_prod_path.read_text(encoding="utf-8")

    # Assert run_prod.bat executes rust_gateway binary and does not launch uvicorn
    assert "uvicorn backend.main:app" not in run_prod_content
    assert "rust_gateway" in run_prod_content


# ── 3. Schema & DTO Parity Tests ────────────────────────────────────

def test_heart_input_schema_parity():
    """HeartInput must enforce the 13 required features and support optional clinical features."""
    # 13 required features matching rust_gateway/src/ml/predictors.rs:HeartInput
    valid_payload = {
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
    model = HeartInput(**valid_payload)
    assert model.age == 63.0
    assert model.sex == 1.0
    assert model.hdl == 50.0  # default
    assert model.smoker == 0   # default
    assert model.hyp_treatment == 0  # default

    # Omitting any of the 13 required fields must raise ValidationError
    for field in ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"]:
        incomplete = valid_payload.copy()
        del incomplete[field]
        with pytest.raises(ValidationError):
            HeartInput(**incomplete)


def test_diabetes_input_schema_parity():
    """DiabetesInput must require all 9 features matching rust_gateway/src/ml/predictors.rs:DiabetesInput."""
    valid_payload = {
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
    model = DiabetesInput(**valid_payload)
    assert model.bmi == 28.5
    assert model.age == 55.0

    # Omitting any of the 9 required fields must raise ValidationError
    for field in valid_payload:
        incomplete = valid_payload.copy()
        del incomplete[field]
        with pytest.raises(ValidationError):
            DiabetesInput(**incomplete)


def test_kidney_input_is_female_bidirectional_parity():
    """KidneyInput must support both is_female and gender with bidirectional parity."""
    # From gender to is_female
    k_female = KidneyInput(gender=0)
    assert k_female.is_female is True

    k_male = KidneyInput(gender=1)
    assert k_male.is_female is False

    # From is_female to gender (Rust DTO compatibility)
    k_from_rust_female = KidneyInput(is_female=True)
    assert k_from_rust_female.gender == 0

    k_from_rust_male = KidneyInput(is_female=False)
    assert k_from_rust_male.gender == 1


def test_prediction_review_create_parity():
    """PredictionReviewCreate must support both Rust Serde fields and Python audit fields."""
    # 1. Rust Serde payload
    rust_payload = {
        "patient_id": 101,
        "prediction_type": "heart",
        "model_prediction": "Positive",
        "clinician_agree": False,
        "revised_diagnosis": "Mild Angina",
        "notes": "Patient requires stress test",
    }
    r_review = PredictionReviewCreate(**rust_payload)
    assert r_review.clinician_agree is False
    assert r_review.decision == "overridden"
    assert r_review.notes == "Patient requires stress test"
    assert r_review.review_note == "Patient requires stress test"
    assert r_review.model_prediction == "Positive"

    # 2. Python legacy payload
    py_payload = {
        "patient_id": 102,
        "prediction_type": "diabetes",
        "decision": "accepted",
        "review_note": "Confirmed with lab HbA1c",
    }
    p_review = PredictionReviewCreate(**py_payload)
    assert p_review.clinician_agree is True
    assert p_review.notes == "Confirmed with lab HbA1c"
    assert p_review.model_prediction == ""


def test_audit_log_response_admin_and_actor_parity():
    """AuditLogResponse must support both admin_id and actor_user_id transparently."""
    # 1. From admin_id (Rust / DB model column name)
    resp1 = AuditLogResponse(
        id=1,
        admin_id=42,
        action="LOGIN",
        timestamp="2026-11-07T00:00:00Z",
        details="User logged in",
    )
    assert resp1.admin_id == 42
    assert resp1.actor_user_id == 42

    # 2. From actor_user_id (Python legacy schema field name)
    resp2 = AuditLogResponse(
        id=2,
        actor_user_id=84,
        action="EXPORT_FHIR",
        timestamp="2026-11-07T00:00:00Z",
        details="Exported bundle",
    )
    assert resp2.admin_id == 84
    assert resp2.actor_user_id == 84


def test_explainability_response_parity():
    """ExplainabilityResponse must support Rust structured explainability format."""
    payload = {
        "prediction_id": 501,
        "model_name": "heart_disease_onnx",
        "base_value": 0.12,
        "predicted_value": 0.88,
        "feature_contributions": [
            {"feature_name": "chol", "feature_value": 260.0, "shap_value": 0.35, "impact": "POSITIVE"},
            {"feature_name": "thalach", "feature_value": 110.0, "shap_value": 0.22, "impact": "POSITIVE"},
        ],
        "conformal_prediction": {
            "alpha": 0.05,
            "lower_bound": 0.82,
            "upper_bound": 0.94,
            "prediction_set": ["High Risk"],
        },
    }
    resp = ExplainabilityResponse(**payload)
    assert resp.prediction_id == 501
    assert resp.base_value == 0.12
    assert resp.predicted_value == 0.88
    assert len(resp.feature_contributions) == 2
    assert resp.conformal_prediction["alpha"] == 0.05


def test_data_governance_quality_columns_are_float():
    """DbSchemaContract.quality_threshold and DbDatasetEntry.quality_score must be Float types."""
    assert isinstance(DbSchemaContract.quality_threshold.type, Float), (
        "DbSchemaContract.quality_threshold must be Float"
    )
    assert isinstance(DbDatasetEntry.quality_score.type, Float), (
        "DbDatasetEntry.quality_score must be Float"
    )
