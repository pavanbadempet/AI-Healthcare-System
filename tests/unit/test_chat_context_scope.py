from datetime import datetime, timezone

from backend import models
from backend.chat_context import build_chat_context


def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="IN",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    facility_id: int | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hashed-test-password",
        role=role,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_health_record(
    db_session,
    user: models.User,
    prediction: str,
    record_type: str = "diabetes",
) -> models.HealthRecord:
    record = models.HealthRecord(
        user_id=user.id,
        record_type=record_type,
        data="{}",
        prediction=prediction,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


def test_all_scope_alias_allows_doctor_global_context(db_session):
    doctor = _create_user(db_session, "scope_doctor", "doctor")
    patient = _create_user(db_session, "scope_patient", "patient")
    _create_health_record(db_session, patient, "Synthetic cross-patient diabetes trend")

    context, sources = build_chat_context(db_session, "diabetes cases", doctor, "all")

    assert "Global Hospital Database" in context
    assert "Synthetic cross-patient diabetes trend" in context
    assert any(source["type"] == "global_record" for source in sources)


def test_global_context_for_facility_doctor_is_scoped_to_own_facility(db_session):
    primary_facility = _create_facility(db_session, "RAG Scope Primary")
    other_facility = _create_facility(db_session, "RAG Scope Other")
    doctor = _create_user(db_session, "scope_facility_doctor", "doctor", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "scope_facility_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "scope_other_facility_patient", "patient", facility_id=other_facility.id)
    _create_health_record(db_session, local_patient, "Local facility diabetes trend")
    _create_health_record(db_session, other_patient, "Other facility diabetes trend")

    context, sources = build_chat_context(db_session, "diabetes cases", doctor, "global")

    assert "Global Hospital Database" in context
    assert "Local facility diabetes trend" in context
    assert "Other facility diabetes trend" not in context
    assert len(sources) == 1


def test_all_scope_alias_is_patient_scoped_for_patient(db_session):
    patient = _create_user(db_session, "patient_scope_owner", "patient")
    other_patient = _create_user(db_session, "patient_scope_other", "patient")
    _create_health_record(db_session, patient, "Own synthetic diabetes record")
    _create_health_record(db_session, other_patient, "Other synthetic diabetes record")

    context, sources = build_chat_context(db_session, "diabetes cases", patient, "all")

    assert "Global Hospital Database" not in context
    assert "Own synthetic diabetes record" in context
    assert "Other synthetic diabetes record" not in context
    assert all(source["type"] != "global_record" for source in sources)


def test_unknown_scope_is_patient_scoped(db_session):
    patient = _create_user(db_session, "unknown_scope_owner", "patient")
    other_patient = _create_user(db_session, "unknown_scope_other", "patient")
    _create_health_record(db_session, patient, "Owned unknown-scope record")
    _create_health_record(db_session, other_patient, "Other unknown-scope record")

    context, sources = build_chat_context(db_session, "diabetes cases", patient, "unexpected")

    assert "Global Hospital Database" not in context
    assert "Owned unknown-scope record" in context
    assert "Other unknown-scope record" not in context
    assert all(source["type"] != "global_record" for source in sources)
