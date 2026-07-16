import asyncio
import json
from tests.unit.test_itches_upgrades import _get_auth_headers
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend import models

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    facility = models.HospitalFacility(id=1, name="Primary Test Facility")
    db.add(facility)
    db.commit()
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app, base_url="http://127.0.0.1") as client:
        headers, pat_id = _get_auth_headers(client, db, "spec_pat", "patient")
        r = client.post(
            "/v1/appointments/special-care",
            json={
                "patient_id": pat_id,
                "specialist": "Gynecology",
                "date_time": "2026-06-25T10:00:00",
                "reason": "Routine Consultation",
                "request_female_clinician": True,
                "home_visit_van": True
            },
            headers=headers
        )
        print("STATUS:", r.status_code)
        print("TEXT:", r.text)
        
run()
