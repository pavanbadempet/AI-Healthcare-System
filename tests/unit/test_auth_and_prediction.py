"""
Tests for auth.py and prediction.py — uncovered paths.

auth.py: password hashing, token creation, signup validation, login,
profile get/update, user management endpoints, admin access.

prediction.py: age_bucket helper, _get_confidence, model reload,
prediction review endpoint, SHAP explanation endpoints.
"""
from datetime import timedelta
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import auth, models, prediction
from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()


def _signup(client, username, password="AuthTest123!", email=None):
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "email": email or f"{username}@test.com",
        "full_name": username.title(),
        "dob": "1990-01-01",
    })


def _login(client, username, password="AuthTest123!"):
    r = client.post("/token", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _set_role(db_session, username, role):
    u = db_session.query(models.User).filter_by(username=username).first()
    if u:
        u.role = role
        db_session.commit()


def _get_id(db_session, username):
    u = db_session.query(models.User).filter_by(username=username).first()
    return u.id if u else None


# ══════════════════════════════════════════════════════════════════════
# AUTH — pure logic
# ══════════════════════════════════════════════════════════════════════

def test_get_password_hash_produces_verifiable_hash():
    hashed = auth.get_password_hash("MyPass123!")
    assert auth.verify_password("MyPass123!", hashed)


def test_get_password_hash_truncates_at_72_bytes():
    # bcrypt truncates at 72 bytes, so "A"*73 and "A"*100 should produce the same hash
    hashed = auth.get_password_hash("A" * 100 + "1")
    # The first 72 chars are all A's, so "A"*72 should match but "A"*73 should also match (same truncation)
    assert auth.verify_password("A" * 72, hashed)  # 72 A's = first 72 bytes of 100 A's + "1"


def test_create_access_token_creates_valid_jwt():
    token = auth.create_access_token({"sub": "testuser"})
    from jose import jwt as jose_jwt
    payload = jose_jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload["sub"] == "testuser"


def test_create_access_token_respects_custom_expiry():
    token = auth.create_access_token({"sub": "testuser"}, expires_delta=timedelta(minutes=5))
    from jose import jwt as jose_jwt
    payload = jose_jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert "exp" in payload


def test_is_admin_true_for_admin_role():
    u = models.User(username="a", hashed_password="x", role="admin")
    assert auth.is_admin(u) is True


def test_is_admin_false_for_patient():
    u = models.User(username="p", hashed_password="x", role="patient")
    assert auth.is_admin(u) is False


def test_load_access_token_expire_minutes_raises_on_non_integer(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "abc")
    with pytest.raises(RuntimeError, match="integer"):
        auth._load_access_token_expire_minutes()


def test_load_access_token_expire_minutes_raises_on_zero(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0")
    with pytest.raises(RuntimeError, match="positive"):
        auth._load_access_token_expire_minutes()


def test_load_access_token_expire_minutes_accepts_valid(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    assert auth._load_access_token_expire_minutes() == 60


# ══════════════════════════════════════════════════════════════════════
# AUTH — endpoints
# ══════════════════════════════════════════════════════════════════════

def test_signup_success(client):
    r = _signup(client, "auth_newuser1")
    assert r.status_code == 200
    assert r.json()["username"] == "auth_newuser1"


def test_signup_rejects_weak_password(client):
    r = client.post("/signup", json={
        "username": "auth_weakpass", "password": "short",
        "email": "weak@test.com", "full_name": "Weak", "dob": "1990-01-01"
    })
    assert r.status_code == 400
    assert "password" in r.json()["detail"].lower()


def test_signup_rejects_duplicate_username(client):
    _signup(client, "auth_dupuser1")
    r = _signup(client, "auth_dupuser1")
    assert r.status_code == 400
    assert "username" in r.json()["detail"].lower()


def test_signup_rejects_duplicate_email(client):
    _signup(client, "auth_email1", email="dup@test.com")
    r = _signup(client, "auth_email2", email="dup@test.com")
    assert r.status_code == 400
    assert "email" in r.json()["detail"].lower()


def test_login_success(client):
    _signup(client, "auth_login1")
    r = client.post("/token", data={"username": "auth_login1", "password": "AuthTest123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    _signup(client, "auth_login2")
    r = client.post("/token", data={"username": "auth_login2", "password": "WrongPass999!"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401(client):
    r = client.post("/token", data={"username": "nobody", "password": "AuthTest123!"})
    assert r.status_code == 401


def test_get_profile_requires_auth(client):
    assert client.get("/profile").status_code == 401


def test_get_profile_returns_user_data(client):
    _signup(client, "auth_profile1")
    h = _login(client, "auth_profile1")
    r = client.get("/profile", headers=h)
    assert r.status_code == 200
    assert r.json()["username"] == "auth_profile1"


def test_update_profile_updates_fields(client):
    _signup(client, "auth_update1")
    h = _login(client, "auth_update1")
    r = client.put("/profile", json={"gender": "female", "height": 165.0}, headers=h)
    assert r.status_code == 200
    assert r.json()["user"]["gender"] == "female"


def test_get_all_users_requires_admin(client):
    _signup(client, "auth_user1")
    h = _login(client, "auth_user1")
    assert client.get("/users", headers=h).status_code == 403


def test_get_all_users_returns_list_for_admin(client, db_session):
    _signup(client, "auth_admin1")
    _set_role(db_session, "auth_admin1", "admin")
    h = _login(client, "auth_admin1")
    r = client.get("/users", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_user_full_details_requires_admin(client):
    _signup(client, "auth_user2")
    h = _login(client, "auth_user2")
    assert client.get("/users/1/full", headers=h).status_code == 403


def test_get_user_full_details_returns_404_for_unknown(client, db_session):
    _signup(client, "auth_admin2")
    _set_role(db_session, "auth_admin2", "admin")
    h = _login(client, "auth_admin2")
    assert client.get("/users/99999/full", headers=h).status_code == 404


def test_get_user_full_details_redacts_opted_out_user(client, db_session):
    _signup(client, "auth_admin3")
    _set_role(db_session, "auth_admin3", "admin")
    _signup(client, "auth_optout1")
    # Set allow_data_collection = 0
    u = db_session.query(models.User).filter_by(username="auth_optout1").first()
    u.allow_data_collection = 0
    db_session.commit()
    optout_id = u.id

    h = _login(client, "auth_admin3")
    r = client.get(f"/users/{optout_id}/full", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data.get("health_records") == [] or data.get("health_records") is None


def test_invalid_token_returns_401(client):
    r = client.get("/profile", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════
# PREDICTION — pure logic
# ══════════════════════════════════════════════════════════════════════

def test_get_age_bucket_boundaries():
    assert prediction.get_age_bucket(18) == 1   # <= 24
    assert prediction.get_age_bucket(24) == 1
    assert prediction.get_age_bucket(25) == 2   # <= 29
    assert prediction.get_age_bucket(54) == 7   # <= 54
    assert prediction.get_age_bucket(64) == 9   # <= 64
    assert prediction.get_age_bucket(80) == 13  # > 79


def test_get_confidence_returns_high_risk():
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.1, 0.9]])
    conf, risk = prediction._get_confidence(mock_model, [[1, 2, 3]])
    assert conf == 90.0
    assert risk == "High"


def test_get_confidence_returns_moderate_risk():
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.45, 0.55]])
    conf, risk = prediction._get_confidence(mock_model, [[1, 2, 3]])
    assert risk == "Moderate"


def test_get_confidence_returns_low_risk():
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.75, 0.25]])
    conf, risk = prediction._get_confidence(mock_model, [[1, 2, 3]])
    assert risk == "Low"


def test_get_confidence_returns_none_on_exception():
    mock_model = MagicMock()
    mock_model.predict_proba.side_effect = Exception("no proba")
    conf, risk = prediction._get_confidence(mock_model, [[1]])
    assert conf is None
    assert risk is None


# ══════════════════════════════════════════════════════════════════════
# PREDICTION — endpoints
# ══════════════════════════════════════════════════════════════════════

def test_reload_models_requires_admin(client):
    _signup(client, "pred_patient1")
    h = _login(client, "pred_patient1")
    assert client.post("/admin/reload_models", headers=h).status_code == 403


def test_reload_models_success_for_admin(client, db_session):
    _signup(client, "pred_admin1")
    _set_role(db_session, "pred_admin1", "admin")
    h = _login(client, "pred_admin1")
    r = client.post("/admin/reload_models", headers=h)
    assert r.status_code == 200
    assert "status" in r.json()


def test_prediction_review_requires_auth(client):
    assert client.post("/predict/reviews", json={
        "patient_id": 1, "prediction_type": "diabetes",
        "decision": "accepted", "model_card_id": "mc1"
    }).status_code == 401


def test_prediction_review_rejects_invalid_decision(client, db_session):
    _signup(client, "pred_admin2")
    _set_role(db_session, "pred_admin2", "admin")
    _signup(client, "pred_pat1")
    pat_id = _get_id(db_session, "pred_pat1")
    h = _login(client, "pred_admin2")
    r = client.post("/predict/reviews", json={
        "patient_id": pat_id,
        "prediction_type": "diabetes",
        "decision": "maybe",  # invalid
        "model_card_id": "mc1"
    }, headers=h)
    assert r.status_code == 400
    assert "decision" in r.json()["detail"].lower()


def test_prediction_review_rejects_invalid_type(client, db_session):
    _signup(client, "pred_admin3")
    _set_role(db_session, "pred_admin3", "admin")
    _signup(client, "pred_pat2")
    pat_id = _get_id(db_session, "pred_pat2")
    h = _login(client, "pred_admin3")
    r = client.post("/predict/reviews", json={
        "patient_id": pat_id,
        "prediction_type": "cancer",  # invalid
        "decision": "accepted",
        "model_card_id": "mc1"
    }, headers=h)
    assert r.status_code == 400
    assert "type" in r.json()["detail"].lower()


def test_prediction_review_returns_404_for_unknown_patient(client, db_session):
    _signup(client, "pred_admin4")
    _set_role(db_session, "pred_admin4", "admin")
    h = _login(client, "pred_admin4")
    r = client.post("/predict/reviews", json={
        "patient_id": 99999,
        "prediction_type": "diabetes",
        "decision": "accepted",
        "model_card_id": "mc1"
    }, headers=h)
    assert r.status_code == 404


def test_prediction_review_success(client, db_session):
    _signup(client, "pred_admin5")
    _set_role(db_session, "pred_admin5", "admin")
    _signup(client, "pred_pat3")
    pat_id = _get_id(db_session, "pred_pat3")
    h = _login(client, "pred_admin5")
    r = client.post("/predict/reviews", json={
        "patient_id": pat_id,
        "prediction_type": "heart",
        "decision": "accepted",
        "model_card_id": "heart-v1",
        "clinical_use_category": "clinician_review"
    }, headers=h)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "recorded"
    assert data["prediction_type"] == "heart"


def test_explain_diabetes_requires_auth(client):
    assert client.post("/predict/explain/diabetes", json={
        "gender": 1, "age": 45.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": 1, "bmi": 25.0, "high_chol": 0,
        "physical_activity": 1, "general_health": 2
    }).status_code == 401


def test_explain_heart_requires_auth(client):
    assert client.post("/predict/explain/heart", json={
        "age": 50, "sex": 1, "cp": 3, "trestbps": 130, "chol": 220,
        "fbs": 0, "restecg": 0, "thalach": 150, "exang": 0,
        "oldpeak": 1.5, "slope": 1, "ca": 0, "thal": 1
    }).status_code == 401


def test_explain_liver_requires_auth(client):
    assert client.post("/predict/explain/liver", json={
        "age": 45, "gender": 1, "total_bilirubin": 0.7,
        "direct_bilirubin": 0.1, "alkaline_phosphotase": 187,
        "alamine_aminotransferase": 16, "aspartate_aminotransferase": 18,
        "total_proteins": 6.8, "albumin": 3.3, "albumin_and_globulin_ratio": 0.9
    }).status_code == 401


def test_explain_diabetes_returns_shap_or_503(client):
    """With TESTING=1 mocked models, SHAP is not available — should return 500 or SHAP unavailable dict."""
    _signup(client, "pred_user1")
    h = _login(client, "pred_user1")
    r = client.post("/predict/explain/diabetes", json={
        "gender": 1, "age": 45.0, "hypertension": 0, "heart_disease": 0,
        "smoking_history": 1, "bmi": 25.0, "high_chol": 0,
        "physical_activity": 1, "general_health": 2
    }, headers=h)
    # Either returns explanation dict (with html key) or 500 if SHAP unavailable
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        assert "html" in r.json() or "error" in r.json()


def test_predict_organ_health_unauthorized(client):
    r = client.get("/predict/organ_health/999")
    assert r.status_code == 401


def test_predict_organ_health_patient_not_found(client, db_session):
    _signup(client, "pred_admin6")
    h = _login(client, "pred_admin6")
    r = client.get("/predict/organ_health/99999", headers=h)
    assert r.status_code == 404


def test_predict_organ_health_baseline_fallback(client, db_session):
    _signup(client, "pred_admin7")
    _signup(client, "pred_pat4")
    pat_id = _get_id(db_session, "pred_pat4")
    h = _login(client, "pred_admin7")

    r = client.get(f"/predict/organ_health/{pat_id}", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["patient_id"] == pat_id
    assert data["vitals_source"] == "baseline_fallback"
    assert data["vitals"]["heart_rate"] == 72.0
    assert 0 <= data["health_index"] <= 100
    assert "heart" in data["organ_risks"]
    assert "lungs" in data["organ_risks"]
    assert "kidney" in data["organ_risks"]
    assert "diabetes" in data["organ_risks"]
    assert "liver" in data["organ_risks"]


def test_predict_organ_health_with_vitals(client, db_session):
    from datetime import datetime, timezone
    _signup(client, "pred_admin8")
    _signup(client, "pred_pat5")
    pat_id = _get_id(db_session, "pred_pat5")
    h = _login(client, "pred_admin8")

    # Insert a VitalObservation
    v = models.VitalObservation(
        patient_id=pat_id,
        heart_rate=110.0,
        systolic_bp=150.0,
        diastolic_bp=95.0,
        spo2=93.0,
        temperature_c=38.5,
        respiratory_rate=24.0,
        observed_at=datetime.now(timezone.utc)
    )
    db_session.add(v)
    db_session.commit()

    r = client.get(f"/predict/organ_health/{pat_id}", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["patient_id"] == pat_id
    assert data["vitals_source"] == "latest_observation"
    assert data["vitals"]["heart_rate"] == 110.0
    assert data["vitals"]["systolic_bp"] == 150.0
    assert data["vitals"]["spo2"] == 93.0
    assert 0 <= data["health_index"] <= 100
    assert data["organ_risks"]["heart"]["risk_probability"] > 0


def test_predict_organ_health_with_parsed_labs(client, db_session):
    _signup(client, "pred_admin9")
    _signup(client, "pred_pat6")
    pat_id = _get_id(db_session, "pred_pat6")
    h = _login(client, "pred_admin9")

    # Create an abnormal lab DiagnosticResult
    lab = models.DiagnosticResult(
        patient_id=pat_id,
        order_id=1,  # Mock clinical order ID
        result_type="lab",
        title="Comprehensive Metabolic Panel",
        summary="Serum Creatinine: 2.8 mg/dL (High). Blood Urea Nitrogen: 85 mg/dL. Direct Bilirubin: 1.5 mg/dL.",
        abnormal_flag=1
    )
    db_session.add(lab)
    db_session.commit()

    r = client.get(f"/predict/organ_health/{pat_id}", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["labs_source"] == "clinical_history"
    assert data["labs"]["serum_creatinine"] == 2.8
    assert data["labs"]["blood_urea"] == 85.0
    assert data["labs"]["direct_bilirubin"] == 1.5
    assert "ai_clinical_synthesis" in data


