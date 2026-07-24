import os
import sqlite3
from datetime import datetime, timedelta, timezone

from backend import models


def get_admin_token(client, db):
    admin = db.query(models.User).filter_by(username="test_admin").first()
    if not admin:
        from backend.auth import get_password_hash
        admin = models.User(
            username="test_admin",
            email="admin@test.com",
            hashed_password=get_password_hash("AdminPassword123"),
            role="admin",
            full_name="Test Admin",
            facility_id=1
        )
        db.add(admin)
        db.commit()

    response = client.post(
        "/token",
        data={"username": "test_admin", "password": "AdminPassword123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_admin_compliance_backup(client, db_session):
    token = get_admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/admin/backups/execute", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "backup_file" in data

    backup_file = data["backup_file"]
    assert os.path.exists(backup_file)
    assert os.path.getsize(backup_file) > 0

    # Verify it is a valid SQLite DB file
    conn = sqlite3.connect(backup_file)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" in tables
    finally:
        conn.close()

    # Clean up backup file
    if os.path.exists(backup_file):
        os.remove(backup_file)


def test_admin_patient_deletion(client, db_session):
    token = get_admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a dummy patient
    patient = models.User(
        username="dummy_patient_1",
        email="dummy@patient.com",
        hashed_password="...",
        role="patient",
        full_name="Dummy Patient",
        facility_id=1
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    # 2. Insert dummy dependent records (using 'diabetes' to satisfy check_health_record_type constraint)
    record = models.HealthRecord(
        user_id=patient.id,
        record_type="diabetes",
        data={"symptoms": "none"},
        timestamp=datetime.now(timezone.utc)
    )
    chat = models.ChatLog(
        user_id=patient.id,
        role="user",
        content="hello copilot",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(record)
    db_session.add(chat)
    db_session.commit()

    # Store patient id and dependent IDs
    patient_id = patient.id
    record_id = record.id
    chat_id = chat.id

    # Verify they exist using a fresh session to avoid cache issues
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        assert db.query(models.HealthRecord).filter_by(id=record_id).count() == 1
        assert db.query(models.ChatLog).filter_by(id=chat_id).count() == 1
    finally:
        db.close()

    # 3. Call execute-deletion
    response = client.post(f"/admin/privacy/execute-deletion/{patient_id}", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["destructive_actions_executed"] is True
    assert res_data["database"]["tables"]["health_records"] == 1
    assert res_data["database"]["tables"]["chat_logs"] == 1

    # 4. Verify patient and all records are deleted using a fresh session
    db = TestingSessionLocal()
    try:
        assert db.query(models.User).filter_by(id=patient_id).first() is None
        assert db.query(models.HealthRecord).filter_by(id=record_id).count() == 0
        assert db.query(models.ChatLog).filter_by(id=chat_id).count() == 0
    finally:
        db.close()


def test_admin_retention_sweep(client, db_session):
    token = get_admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure we have a patient user for foreign keys if needed
    patient = db_session.query(models.User).filter_by(role="patient").first()
    if not patient:
        patient = models.User(
            username="dummy_patient_for_sweep",
            email="dummy_sweep@patient.com",
            hashed_password="...",
            role="patient",
            full_name="Dummy Patient Sweep",
            facility_id=1
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
    patient_id = patient.id

    # Insert old record and fresh record
    old_time = datetime.now(timezone.utc) - timedelta(days=60)
    fresh_time = datetime.now(timezone.utc)

    old_chat = models.ChatLog(
        user_id=patient_id,
        role="user",
        content="old message",
        timestamp=old_time
    )
    fresh_chat = models.ChatLog(
        user_id=patient_id,
        role="user",
        content="fresh message",
        timestamp=fresh_time
    )

    db_session.add(old_chat)
    db_session.add(fresh_chat)
    db_session.commit()

    # Store IDs
    old_chat_id = old_chat.id
    fresh_chat_id = fresh_chat.id

    # Configure env-vars for testing execution retention window
    os.environ["CHAT_LOG_RETENTION_DAYS"] = "30"

    # Run sweep
    response = client.post("/admin/retention/execute-cleanup", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["deleted_records"]["chat_logs"] >= 1

    # Verify old is deleted and fresh remains using a fresh session
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        old_exists = db.query(models.ChatLog).filter_by(id=old_chat_id).first() is not None
        fresh_exists = db.query(models.ChatLog).filter_by(id=fresh_chat_id).first() is not None
        assert not old_exists
        assert fresh_exists

        # Cleanup fresh chat log
        fresh_obj = db.query(models.ChatLog).filter_by(id=fresh_chat_id).first()
        if fresh_obj:
            db.delete(fresh_obj)
            db.commit()
    finally:
        db.close()
