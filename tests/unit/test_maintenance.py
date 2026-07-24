from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.maintenance import run_system_maintenance
from backend.models.records import ChatLog


def test_run_system_maintenance(db_session: Session):
    # 1. Seed some expired chat logs (retention is 365 days)
    expired_date = datetime.now(timezone.utc) - timedelta(days=400)
    recent_date = datetime.now(timezone.utc) - timedelta(days=10)

    chat_expired = ChatLog(
        user_id=1,
        role="user",
        content="This is an expired chat message",
        timestamp=expired_date
    )
    chat_recent = ChatLog(
        user_id=1,
        role="user",
        content="This is a recent chat message",
        timestamp=recent_date
    )

    db_session.add(chat_expired)
    db_session.add(chat_recent)
    db_session.commit()

    # Verify records were inserted
    assert db_session.query(ChatLog).count() >= 2

    # 2. Run system maintenance coordinator
    report = run_system_maintenance(db_session, executor_id=1)

    assert report["status"] == "success"
    assert report["database_optimized"] is True
    assert "chat_logs" in report["purged_records"]
    assert report["purged_records"]["chat_logs"] >= 1

    # Verify the expired log is deleted and recent log remains
    chats = db_session.query(ChatLog).all()
    messages = [c.content for c in chats]
    assert "This is an expired chat message" not in messages
    assert "This is a recent chat message" in messages

def test_admin_maintenance_endpoint_unauthorized(client):
    # Hitting without authentication
    response = client.post("/v1/admin/maintenance")
    assert response.status_code == 401

def test_admin_maintenance_endpoint_authorized(client, db_session: Session):
    # Create an admin user to authorize the call
    from backend.auth import get_password_hash
    from backend.models.auth import User

    # Clean up existing test admin if present
    db_session.query(User).filter(User.username == "maint_admin").delete()
    db_session.commit()

    admin_user = User(
        username="maint_admin",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        email="maint_admin@example.com",
        allow_data_collection=0
    )
    db_session.add(admin_user)
    db_session.commit()

    # Generate token (note: use /v1/token or /token depending on the router, but client uses relative URL)
    auth_response = client.post(
        "/v1/token",
        data={"username": "maint_admin", "password": "adminpass"}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]

    # Hit maintenance endpoint with authentication
    response = client.post(
        "/v1/admin/maintenance",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    report = response.json()
    assert report["status"] == "success"
    assert report["database_optimized"] is True
