import pytest
from starlette.websockets import WebSocketDisconnect

from backend import auth, models, telemetry


class FailingWebSocket:
    query_params = {"token": "synthetic-test-token"}

    async def accept(self):
        return None

    async def send_text(self, message: str):
        raise Exception("telemetry send failed token=telemetry-secret patient_name=Sensitive User")


class MissingTokenWebSocket:
    query_params = {}

    def __init__(self):
        self.accepted = False
        self.closed_code = None

    async def accept(self):
        self.accepted = True

    async def close(self, code: int):
        self.closed_code = code

    async def send_text(self, message: str):
        raise AssertionError("Anonymous telemetry stream should not send data")


@pytest.mark.asyncio
async def test_telemetry_stream_hides_error_details(caplog):
    caplog.set_level("ERROR", logger="backend.telemetry")

    await telemetry.telemetry_stream(FailingWebSocket())

    assert "telemetry-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
    assert "telemetry send failed" not in caplog.text


@pytest.mark.asyncio
async def test_telemetry_stream_rejects_missing_token():
    websocket = MissingTokenWebSocket()

    await telemetry.telemetry_stream(websocket)

    assert websocket.closed_code == 1008
    assert websocket.accepted is False


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
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        facility_id=facility_id,
        allow_data_collection=1,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_telemetry_snapshot_requires_admin(client, db_session):
    patient = _create_user(db_session, "telemetry_patient", "patient")

    unauthenticated = client.get("/telemetry/snapshot")
    patient_response = client.get("/telemetry/snapshot", headers=_auth_headers(patient.username))

    assert unauthenticated.status_code == 401
    assert patient_response.status_code == 403
    assert patient_response.json()["detail"] == "Admin privileges required"


def test_telemetry_stream_rejects_invalid_token(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("ws://127.0.0.1/telemetry/stream?token=not-a-real-token") as websocket:
            websocket.receive_json()

    assert exc.value.code == 1008


def test_telemetry_stream_rejects_non_admin_token(client, db_session):
    patient = _create_user(db_session, "telemetry_stream_patient", "patient")
    token = auth.create_access_token({"sub": patient.username})

    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"ws://127.0.0.1/telemetry/stream?token={token}"):
            pass

    assert exc.value.code == 1008


def test_facility_admin_telemetry_snapshot_is_facility_scoped(client, db_session):
    primary_facility = _create_facility(db_session, "Telemetry Primary")
    other_facility = _create_facility(db_session, "Telemetry Other")
    admin = _create_user(db_session, "telemetry_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "telemetry_patient_primary", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "telemetry_patient_other", "patient", facility_id=other_facility.id)
    primary_facility_id = primary_facility.id
    other_facility_id = other_facility.id
    department = models.Department(
        facility_id=primary_facility_id,
        name="Telemetry Primary Ward",
        department_type="IPD",
        status="active",
    )
    other_department = models.Department(
        facility_id=other_facility_id,
        name="Telemetry Other Ward",
        department_type="IPD",
        status="active",
    )
    db_session.add_all([department, other_department])
    db_session.flush()
    db_session.add_all([
        models.Bed(
            facility_id=primary_facility_id,
            department_id=department.id,
            bed_number="TEL-01",
            ward="Ward",
            status="occupied",
            current_patient_id=patient.id,
        ),
        models.Bed(
            facility_id=primary_facility_id,
            department_id=department.id,
            bed_number="TEL-02",
            ward="Ward",
            status="cleaning",
        ),
        models.Bed(
            facility_id=other_facility_id,
            department_id=other_department.id,
            bed_number="TEL-OTHER",
            ward="Ward",
            status="occupied",
            current_patient_id=other_patient.id,
        ),
        models.Admission(
            facility_id=primary_facility_id,
            patient_id=patient.id,
            department_id=department.id,
            status="active",
            reason="Telemetry census",
        ),
        models.Admission(
            facility_id=other_facility_id,
            patient_id=other_patient.id,
            department_id=other_department.id,
            status="active",
            reason="Other census",
        ),
        models.MonitoringSignal(
            facility_id=primary_facility_id,
            patient_id=patient.id,
            department_id=department.id,
            signal_type="heart_rate",
            severity="warning",
            title="Heart rate needs review",
            summary="Synthetic signal summary.",
            status="open",
        ),
        models.MonitoringSignal(
            facility_id=other_facility_id,
            patient_id=other_patient.id,
            department_id=other_department.id,
            signal_type="oxygen",
            severity="critical",
            title="Oxygen needs review",
            summary="Other signal summary.",
            status="open",
        ),
    ])
    db_session.commit()

    response = client.get("/telemetry/snapshot", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["facility_id"] == primary_facility_id
    assert payload["active_census"] == 1
    assert payload["total_capacity"] == 2
    assert payload["open_monitoring_signals"] == 1
    assert payload["bed_units"] == [
        {
            "unit": "Telemetry Primary Ward",
            "total": 2,
            "occupied": 1,
            "cleaning": 1,
            "available": 0,
        }
    ]
