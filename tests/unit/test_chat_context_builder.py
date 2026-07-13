"""
Tests for chat_context.py — RAG context builder.

Covers: scope normalisation, patient profile building, prediction context,
health record context, general stats, chat history, global RAG mode,
full build_chat_context assembly, truncation, and suggested questions.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import chat_context, models
from backend.database import Base

# ── Fixtures ──────────────────────────────────────────────────────────────────

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


def _make_user(
    db,
    username="testpatient",
    role="patient",
    full_name="Test Patient",
    gender="female",
    dob="1990-05-15",
    blood_type="O+",
    height=165.0,
    weight=60.0,
    diet="vegetarian",
    activity_level="moderate",
    sleep_hours=7.5,
    stress_level="low",
    about_me="Enjoys hiking.",
    facility_id=None,
    allow_data_collection=1,
) -> models.User:
    user = models.User(
        username=username,
        hashed_password="hashed",
        role=role,
        full_name=full_name,
        gender=gender,
        dob=dob,
        blood_type=blood_type,
        height=height,
        weight=weight,
        diet=diet,
        activity_level=activity_level,
        sleep_hours=sleep_hours,
        stress_level=stress_level,
        about_me=about_me,
        facility_id=facility_id,
        allow_data_collection=allow_data_collection,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_record(db, user_id, record_type, prediction, timestamp=None):
    r = models.HealthRecord(
        user_id=user_id,
        record_type=record_type,
        data="{}",
        prediction=prediction,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _add_chat_log(db, user_id, role, content):
    log = models.ChatLog(
        user_id=user_id,
        role=role,
        content=content,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    return log


# ── _normalize_rag_scope ──────────────────────────────────────────────────────

def test_normalize_rag_scope_defaults_to_patient(db):
    user = _make_user(db, role="patient")
    assert chat_context._normalize_rag_scope(None, user) == "patient"


def test_normalize_rag_scope_maps_all_to_global_for_doctor(db):
    user = _make_user(db, role="doctor", username="doc1")
    assert chat_context._normalize_rag_scope("all", user) == "global"


def test_normalize_rag_scope_blocks_global_for_patient(db):
    user = _make_user(db, role="patient", username="p1")
    assert chat_context._normalize_rag_scope("global", user) == "patient"


def test_normalize_rag_scope_allows_global_for_admin(db):
    user = _make_user(db, role="admin", username="adm1")
    assert chat_context._normalize_rag_scope("global", user) == "global"


def test_normalize_rag_scope_ignores_invalid_scope(db):
    user = _make_user(db, role="doctor", username="doc2")
    assert chat_context._normalize_rag_scope("nonsense", user) == "patient"


def test_normalize_rag_scope_allows_guidelines(db):
    user = _make_user(db, role="patient", username="p2")
    assert chat_context._normalize_rag_scope("guidelines", user) == "guidelines"


# ── _build_patient_profile ────────────────────────────────────────────────────

def test_build_patient_profile_includes_name(db):
    user = _make_user(db, full_name="Jane Doe")
    profile = chat_context._build_patient_profile(user)
    assert "Jane Doe" in profile


def test_build_patient_profile_includes_demographics(db):
    user = _make_user(db)
    profile = chat_context._build_patient_profile(user)
    assert "female" in profile.lower()
    assert "O+" in profile


def test_build_patient_profile_includes_lifestyle(db):
    user = _make_user(db)
    profile = chat_context._build_patient_profile(user)
    assert "vegetarian" in profile.lower()
    assert "moderate" in profile.lower()
    assert "7.5" in profile


def test_build_patient_profile_includes_about_me(db):
    user = _make_user(db)
    profile = chat_context._build_patient_profile(user)
    assert "hiking" in profile.lower()


def test_build_patient_profile_handles_minimal_user(db):
    user = models.User(username="minimal", hashed_password="x", role="patient")
    db.add(user)
    db.commit()
    db.refresh(user)
    profile = chat_context._build_patient_profile(user)
    assert "minimal" in profile  # Falls back to username


# ── _build_health_records_context ────────────────────────────────────────────

def test_build_health_records_context_returns_records(db):
    user = _make_user(db, username="u1")
    _add_record(db, user.id, "diabetes", "High Risk")
    _add_record(db, user.id, "heart", "Healthy Heart")

    ctx, sources = chat_context._build_health_records_context(db, user.id)

    assert "diabetes" in ctx.lower()
    assert "heart" in ctx.lower()
    assert len(sources) == 2


def test_build_health_records_context_empty_when_no_records(db):
    user = _make_user(db, username="u2")
    ctx, sources = chat_context._build_health_records_context(db, user.id)
    assert ctx == ""
    assert sources == []


def test_build_health_records_context_filters_by_type(db):
    user = _make_user(db, username="u3")
    _add_record(db, user.id, "diabetes", "Low Risk")
    _add_record(db, user.id, "heart", "Healthy Heart")

    ctx, sources = chat_context._build_health_records_context(db, user.id, record_type="diabetes")

    assert "diabetes" in ctx.lower()
    assert "heart" not in ctx.lower()
    assert len(sources) == 1


def test_build_health_records_context_respects_limit(db):
    user = _make_user(db, username="u4")
    for i in range(15):
        _add_record(db, user.id, "diabetes", f"result_{i}")

    ctx, sources = chat_context._build_health_records_context(db, user.id, limit=5)
    assert len(sources) == 5


# ── _build_prediction_context ─────────────────────────────────────────────────

def test_build_prediction_context_matches_heart_keyword(db):
    user = _make_user(db, username="u5")
    _add_record(db, user.id, "heart", "Heart Disease Detected")

    ctx, sources = chat_context._build_prediction_context("What does my heart result mean?", db, user.id)

    assert "heart" in ctx.lower()
    assert len(sources) > 0


def test_build_prediction_context_matches_glucose_keyword(db):
    user = _make_user(db, username="u6")
    _add_record(db, user.id, "diabetes", "High Risk")

    ctx, sources = chat_context._build_prediction_context("My glucose is high", db, user.id)

    assert "diabetes" in ctx.lower()


def test_build_prediction_context_returns_empty_on_no_match(db):
    user = _make_user(db, username="u7")
    _add_record(db, user.id, "heart", "Healthy Heart")

    ctx, sources = chat_context._build_prediction_context("Tell me about vitamins", db, user.id)

    assert ctx == ""
    assert sources == []


def test_build_prediction_context_matches_renal_to_kidney(db):
    user = _make_user(db, username="u8")
    _add_record(db, user.id, "kidney", "Healthy Kidneys")

    ctx, sources = chat_context._build_prediction_context("What does renal function mean?", db, user.id)

    assert "kidney" in ctx.lower()


# ── _build_chat_history_context ───────────────────────────────────────────────

def test_build_chat_history_context_includes_recent_messages(db):
    user = _make_user(db, username="u9")
    _add_chat_log(db, user.id, "user", "What is my risk?")
    _add_chat_log(db, user.id, "assistant", "Your risk is low.")

    ctx = chat_context._build_chat_history_context(db, user.id)

    assert "Patient" in ctx or "AI" in ctx
    assert len(ctx) > 0


def test_build_chat_history_context_empty_when_no_logs(db):
    user = _make_user(db, username="u10")
    ctx = chat_context._build_chat_history_context(db, user.id)
    assert ctx == ""


def test_build_chat_history_context_truncates_long_content(db):
    user = _make_user(db, username="u11")
    long_content = "x" * 500
    _add_chat_log(db, user.id, "user", long_content)

    ctx = chat_context._build_chat_history_context(db, user.id)
    # Content should be capped at 150 chars per message
    assert len(ctx) < 500


# ── _build_general_stats_context ─────────────────────────────────────────────

def test_build_general_stats_context_triggers_on_trend_keyword(db):
    user = _make_user(db, username="u12")
    _add_record(db, user.id, "diabetes", "Low Risk")
    _add_record(db, user.id, "heart", "Healthy Heart")

    ctx = chat_context._build_general_stats_context("Show me my trend over time", db, user.id)

    assert "Total checkups" in ctx
    assert "2" in ctx  # 2 records


def test_build_general_stats_context_empty_on_non_trend_question(db):
    user = _make_user(db, username="u13")
    _add_record(db, user.id, "diabetes", "Low Risk")

    ctx = chat_context._build_general_stats_context("What is diabetes?", db, user.id)
    assert ctx == ""


def test_build_general_stats_context_triggers_on_summary_keyword(db):
    user = _make_user(db, username="u14")
    _add_record(db, user.id, "kidney", "Healthy Kidneys")

    ctx = chat_context._build_general_stats_context("Give me an overview of my health", db, user.id)
    assert "Total checkups" in ctx


# ── _build_global_rag_context ─────────────────────────────────────────────────

def test_build_global_rag_context_returns_anonymized_cases(db):
    doctor = _make_user(db, username="doc3", role="doctor")
    patient = _make_user(db, username="gpatient1", role="patient")
    _add_record(db, patient.id, "heart", "Heart Disease Detected")

    ctx, sources = chat_context._build_global_rag_context(db, "heart disease treatment", doctor)

    assert "heart" in ctx.lower()
    # Must not include PII
    assert "gpatient1" not in ctx
    assert patient.full_name not in ctx


def test_build_global_rag_context_fallback_message_on_no_keyword(db):
    doctor = _make_user(db, username="doc4", role="doctor")

    ctx, sources = chat_context._build_global_rag_context(db, "tell me about vitamins", doctor)

    assert "historical health records" in ctx.lower()
    assert sources == []


def test_build_global_rag_context_source_type_is_global_record(db):
    doctor = _make_user(db, username="doc5", role="doctor")
    patient = _make_user(db, username="gpatient2", role="patient")
    _add_record(db, patient.id, "diabetes", "High Risk")

    ctx, sources = chat_context._build_global_rag_context(db, "diabetes management", doctor)

    assert any(s["type"] == "global_record" for s in sources)


# ── build_chat_context (full integration) ────────────────────────────────────

def test_build_chat_context_patient_scope_returns_profile_and_records(db):
    user = _make_user(db, username="full1")
    _add_record(db, user.id, "heart", "Healthy Heart")

    ctx, sources = chat_context.build_chat_context(db, "heart health", user, rag_scope="patient")

    assert "full1" in ctx or "Test Patient" in ctx
    assert "heart" in ctx.lower()
    assert len(sources) > 0


def test_build_chat_context_global_scope_for_doctor(db):
    doctor = _make_user(db, username="doc6", role="doctor")
    patient = _make_user(db, username="gp3", role="patient")
    _add_record(db, patient.id, "liver", "Liver Disease")

    ctx, sources = chat_context.build_chat_context(db, "liver cases", doctor, rag_scope="global")

    assert "liver" in ctx.lower()


def test_build_chat_context_global_scope_blocked_for_patient(db):
    patient = _make_user(db, username="p3", role="patient")

    # Even if patient requests global, should get patient-scoped context
    ctx, sources = chat_context.build_chat_context(db, "question", patient, rag_scope="global")

    # Should still return something (patient profile at minimum)
    assert len(ctx) > 0


def test_build_chat_context_truncates_at_max_chars(db):
    user = _make_user(db, username="trunc1")
    # Add enough records to potentially exceed MAX_CONTEXT_CHARS
    for i in range(50):
        _add_record(db, user.id, "heart", "Healthy Heart " + "x" * 100)

    ctx, _ = chat_context.build_chat_context(db, "heart health trend", user)

    assert len(ctx) <= chat_context.MAX_CONTEXT_CHARS + len("\n...(truncated)")


def test_build_chat_context_no_records_returns_profile_only(db):
    user = _make_user(db, username="norec1")
    ctx, sources = chat_context.build_chat_context(db, "general health advice", user)

    assert "norec1" in ctx or "Test Patient" in ctx
    # Profile source always present
    assert any(s["type"] == "patient_profile" for s in sources)


def test_build_chat_context_global_includes_chat_history(db):
    doctor = _make_user(db, username="doc7", role="doctor")
    _add_chat_log(db, doctor.id, "user", "Any updates on cardiac cases?")

    ctx, _ = chat_context.build_chat_context(db, "cardiac cases", doctor, rag_scope="global")

    assert "cardiac" in ctx.lower() or "Any updates" in ctx


# ── get_suggested_questions ───────────────────────────────────────────────────

def test_get_suggested_questions_includes_diabetes_when_record_exists(db):
    user = _make_user(db, username="sq1")
    _add_record(db, user.id, "diabetes", "High Risk")

    suggestions = chat_context.get_suggested_questions(db, user)

    assert any("diabetes" in s.lower() or "blood sugar" in s.lower() for s in suggestions)


def test_get_suggested_questions_includes_heart_when_record_exists(db):
    user = _make_user(db, username="sq2")
    _add_record(db, user.id, "heart", "Healthy Heart")

    suggestions = chat_context.get_suggested_questions(db, user)

    assert any("heart" in s.lower() for s in suggestions)


def test_get_suggested_questions_returns_generic_when_no_records(db):
    user = _make_user(db, username="sq3")

    suggestions = chat_context.get_suggested_questions(db, user)

    assert len(suggestions) > 0
    assert any("health" in s.lower() for s in suggestions)


def test_get_suggested_questions_max_8_items(db):
    user = _make_user(db, username="sq4")
    for rtype in ["diabetes", "heart", "liver", "kidney", "lungs"]:
        _add_record(db, user.id, rtype, "result")

    suggestions = chat_context.get_suggested_questions(db, user)
    assert len(suggestions) <= 8


def test_get_suggested_questions_includes_liver_when_record_exists(db):
    user = _make_user(db, username="sq5")
    _add_record(db, user.id, "liver", "Liver Disease Detected")

    suggestions = chat_context.get_suggested_questions(db, user)
    assert any("liver" in s.lower() for s in suggestions)
