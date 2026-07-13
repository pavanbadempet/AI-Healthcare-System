"""
Tests for facility_scope.py, ai_function_registry.py, and demo_readiness.py.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.ai_function_registry import (
    AI_FUNCTIONS,
    AIFunction,
    AIRegistryError,
    contains_medical_disclaimer,
    get_ai_function,
    list_ai_functions,
    registry_response,
    validate_ai_registry,
)
from backend.database import Base
from backend.demo_readiness import (
    _env_configured,
    _env_trueish,
    _status,
    get_demo_readiness,
)
from backend.facility_scope import users_share_facility_context

# ── DB fixture ────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _add_user(db, username, facility_id=None):
    u = models.User(
        username=username,
        hashed_password="x",
        role="patient",
        facility_id=facility_id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ── facility_scope ────────────────────────────────────────────────────────────

def test_users_share_facility_same_facility(db):
    u1 = _add_user(db, "u1", facility_id=1)
    u2 = _add_user(db, "u2", facility_id=1)
    assert users_share_facility_context(db, u1.id, u2.id) is True


def test_users_do_not_share_facility_different_facilities(db):
    u1 = _add_user(db, "u3", facility_id=1)
    u2 = _add_user(db, "u4", facility_id=2)
    assert users_share_facility_context(db, u1.id, u2.id) is False


def test_users_share_facility_when_one_has_no_facility(db):
    """If either user has facility_id=None, return True (permissive fallback)."""
    u1 = _add_user(db, "u5", facility_id=None)
    u2 = _add_user(db, "u6", facility_id=1)
    assert users_share_facility_context(db, u1.id, u2.id) is True


def test_users_share_facility_both_no_facility(db):
    u1 = _add_user(db, "u7", facility_id=None)
    u2 = _add_user(db, "u8", facility_id=None)
    assert users_share_facility_context(db, u1.id, u2.id) is True


def test_users_share_facility_missing_user_id(db):
    """Non-existent user IDs — both facility_ids missing → True."""
    assert users_share_facility_context(db, 99999, 88888) is True


# ── ai_function_registry ──────────────────────────────────────────────────────

def test_validate_ai_registry_passes_default():
    assert validate_ai_registry() is True


def test_validate_ai_registry_raises_on_duplicate_id():
    dup = AIFunction(
        id="clinical_chat",
        name="Dup",
        module="backend.chat",
        endpoints=(),
        audience=(),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.core_ai",
        prompt_keys=(),
    )
    with pytest.raises(AIRegistryError, match="Duplicate"):
        validate_ai_registry(list(AI_FUNCTIONS) + [dup])


def test_validate_ai_registry_raises_when_clinical_but_no_disclaimer():
    bad = AIFunction(
        id="bad_func",
        name="Bad",
        module="backend.x",
        endpoints=(),
        audience=(),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=False,  # ← violation
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=False,
        provider_boundary="backend.x",
        prompt_keys=(),
    )
    with pytest.raises(AIRegistryError, match="Medical disclaimer"):
        validate_ai_registry([bad])


def test_validate_ai_registry_raises_when_clinical_but_no_human_review():
    bad = AIFunction(
        id="bad_func2",
        name="Bad2",
        module="backend.x",
        endpoints=(),
        audience=(),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=False,  # ← violation
        basis_transparency_required=True,
        uses_ai_provider=False,
        provider_boundary="backend.x",
        prompt_keys=(),
    )
    with pytest.raises(AIRegistryError, match="Human review"):
        validate_ai_registry([bad])


def test_validate_ai_registry_raises_when_uses_wrong_provider_boundary():
    bad = AIFunction(
        id="bad_func3",
        name="Bad3",
        module="backend.x",
        endpoints=(),
        audience=(),
        risk_category="clinical_support",
        clinical_safety_required=True,
        medical_disclaimer_required=True,
        human_review_required=True,
        basis_transparency_required=True,
        uses_ai_provider=True,
        provider_boundary="backend.some_other_module",  # ← violation
        prompt_keys=(),
    )
    with pytest.raises(AIRegistryError, match="provider boundary"):
        validate_ai_registry([bad])


def test_list_ai_functions_returns_all_with_correct_fields():
    funcs = list_ai_functions()
    assert len(funcs) == len(AI_FUNCTIONS)
    for f in funcs:
        assert "id" in f
        assert "name" in f
        assert "medical_disclaimer_required" in f
        assert f["medical_disclaimer_required"] is True


def test_get_ai_function_returns_correct_function():
    f = get_ai_function("clinical_chat")
    assert f is not None
    assert f["id"] == "clinical_chat"
    assert f["module"] == "backend.chat"


def test_get_ai_function_returns_none_for_unknown():
    assert get_ai_function("nonexistent_function") is None


def test_all_clinical_functions_use_core_ai_boundary():
    """Every function that uses_ai_provider must route through core_ai."""
    for f in AI_FUNCTIONS:
        if f.uses_ai_provider:
            assert f.provider_boundary == "backend.core_ai", \
                f"{f.id} uses AI provider but boundary is {f.provider_boundary}"


def test_all_functions_require_medical_disclaimer():
    """No function in the registry may skip the medical disclaimer."""
    for f in AI_FUNCTIONS:
        assert f.medical_disclaimer_required, \
            f"{f.id} is missing medical_disclaimer_required=True"


def test_contains_medical_disclaimer_true():
    text = (
        "This is AI-generated information and is not a medical diagnosis. "
        "Please consult a qualified healthcare professional for medical decisions or emergencies."
    )
    assert contains_medical_disclaimer(text) is True


def test_contains_medical_disclaimer_false_missing_consult():
    text = "This is informational only. See a doctor."
    assert contains_medical_disclaimer(text) is False


def test_contains_medical_disclaimer_false_missing_qualified():
    text = "Please consult someone for your medical decisions."
    assert contains_medical_disclaimer(text) is False


def test_contains_medical_disclaimer_case_insensitive():
    text = "CONSULT A QUALIFIED CLINICIAN FOR DIAGNOSIS OR TREATMENT."
    assert contains_medical_disclaimer(text) is True


def test_registry_response_structure():
    resp = registry_response()
    assert "functions" in resp
    assert "governance_anchors" in resp
    assert "source" in resp
    assert len(resp["functions"]) == len(AI_FUNCTIONS)


def test_ai_function_to_dict_has_all_fields():
    f = AI_FUNCTIONS[0]
    d = f.to_dict()
    expected = [
        "id", "name", "module", "endpoints", "audience", "risk_category",
        "clinical_safety_required", "medical_disclaimer_required",
        "human_review_required", "basis_transparency_required",
        "uses_ai_provider", "provider_boundary", "prompt_keys", "notes",
    ]
    for key in expected:
        assert key in d, f"Missing key: {key}"


# ── demo_readiness ────────────────────────────────────────────────────────────

def test_env_configured_true_when_set(monkeypatch):
    monkeypatch.setenv("TEST_VAR_DEMO", "some_value")
    assert _env_configured("TEST_VAR_DEMO") is True


def test_env_configured_false_when_empty(monkeypatch):
    monkeypatch.setenv("TEST_VAR_DEMO2", "")
    assert _env_configured("TEST_VAR_DEMO2") is False


def test_env_configured_false_when_missing(monkeypatch):
    monkeypatch.delenv("TEST_VAR_DEMO3", raising=False)
    assert _env_configured("TEST_VAR_DEMO3") is False


def test_env_trueish_true_values(monkeypatch):
    for val in ("1", "true", "yes", "on", "TRUE", "YES"):
        monkeypatch.setenv("TRUEISH_TEST", val)
        assert _env_trueish("TRUEISH_TEST") is True


def test_env_trueish_false_values(monkeypatch):
    for val in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("TRUEISH_TEST2", val)
        assert _env_trueish("TRUEISH_TEST2") is False


def test_status_demo_ready_when_demo_mode():
    assert _status(demo_mode=True, missing_required=[]) == "demo-ready"
    assert _status(demo_mode=True, missing_required=["SECRET_KEY"]) == "demo-ready"


def test_status_production_blocked_when_missing_required():
    assert _status(demo_mode=False, missing_required=["SECRET_KEY"]) == "production-blocked"


def test_status_pilot_ready_when_all_configured():
    assert _status(demo_mode=False, missing_required=[]) == "pilot-ready"


def test_get_demo_readiness_returns_expected_keys(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "false")
    result = get_demo_readiness()
    for key in ("status", "demo_mode", "environment", "required",
                "optional", "capabilities", "clinical_safety_note", "privacy_note"):
        assert key in result


def test_get_demo_readiness_demo_mode_hides_missing_required(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "true")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = get_demo_readiness()
    assert result["missing_required"] == []
    assert result["status"] == "demo-ready"
    assert result["demo_mode"] is True


def test_get_demo_readiness_no_phi_or_secrets_in_response(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "super-secret-value-12345")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@host/db")
    monkeypatch.setenv("ABDM_DEMO_MODE", "false")
    result = get_demo_readiness()
    result_str = str(result)
    assert "super-secret-value-12345" not in result_str
    assert "password" not in result_str


def test_get_demo_readiness_capabilities_include_ai_flag(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "false")
    result = get_demo_readiness()
    assert "external_ai_optional" in result["capabilities"]
    assert "interoperability_optional" in result["capabilities"]
    assert "production_runtime_configured" in result["capabilities"]


def test_get_demo_readiness_clinical_safety_note_present(monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "false")
    result = get_demo_readiness()
    assert "clinical" in result["clinical_safety_note"].lower()
    assert "phi" in result["privacy_note"].lower() or "patient" in result["privacy_note"].lower()
