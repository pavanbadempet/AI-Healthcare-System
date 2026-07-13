from backend import auth, models


def _create_user(db_session, username: str, role: str) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_sales_readiness_requires_admin(client, db_session):
    patient = _create_user(db_session, "readiness_patient", "patient")

    response = client.get("/admin/sales-readiness", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_sales_readiness_returns_india_first_market_plan(client, db_session):
    admin = _create_user(db_session, "readiness_admin", "admin")

    response = client.get("/admin/sales-readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_positioning"]["primary_market"] == "India"
    assert payload["product_positioning"]["safe_category"] == "AI-assisted clinic workflow software"
    assert payload["markets"][0]["code"] == "IN"
    assert payload["markets"][0]["priority"] == 1
    assert "DPDP Act privacy notice" in payload["markets"][0]["paid_pilot_requirements"]
    assert "ABDM compatibility roadmap" in payload["markets"][0]["paid_pilot_requirements"]
    assert "autonomous diagnosis" in payload["blocked_claims"]


def test_sales_readiness_does_not_claim_certifications(client, db_session):
    admin = _create_user(db_session, "readiness_claim_admin", "admin")

    response = client.get("/admin/sales-readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    response_text = response.text.lower()
    assert "hipaa certified" not in response_text
    assert "soc 2 certified" not in response_text
    assert "fda approved" not in response_text
    assert "cdsco approved" not in response_text
    assert "ce marked" not in response_text
    assert "clinician-in-the-loop" in response_text
