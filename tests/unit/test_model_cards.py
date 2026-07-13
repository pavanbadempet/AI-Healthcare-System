import json

import pytest

from backend import auth, models


def _model_cards_module():
    try:
        from backend import model_cards
    except ImportError:
        pytest.fail("backend.model_cards module is required for AI model evidence cards")
    return model_cards


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


def test_model_cards_cover_all_prediction_models_without_phi():
    model_cards = _model_cards_module()

    registry = model_cards.registry_response()

    model_ids = {card["id"] for card in registry["model_cards"]}
    assert {
        "diabetes_risk_screening",
        "heart_disease_screening",
        "liver_disease_screening",
        "kidney_disease_screening",
        "lung_health_screening",
    } == model_ids
    for card in registry["model_cards"]:
        assert card["clinical_use_category"] == "clinician_review"
        assert card["human_review_required"] is True
        assert card["medical_disclaimer_required"] is True
        assert card["artifact_exists"] is True
        assert card["dataset_card_id"] in {dataset["id"] for dataset in registry["dataset_cards"]}
    serialized = json.dumps(registry)
    assert "@example.com" not in serialized
    assert "patient_name" not in serialized.lower()
    assert "api_key" not in serialized.lower()


def test_dataset_cards_describe_public_training_artifacts_without_rows():
    model_cards = _model_cards_module()

    registry = model_cards.registry_response()

    dataset_ids = {dataset["id"] for dataset in registry["dataset_cards"]}
    assert {
        "brfss_2015_diabetes",
        "cleveland_uci_heart",
        "ilpd_liver",
        "uci_ckd",
        "lung_survey",
    }.issubset(dataset_ids)
    for dataset in registry["dataset_cards"]:
        assert dataset["contains_production_patient_data"] is False
        assert dataset["local_artifact_exists"] is True
        assert "row_samples" not in dataset
        assert "records" not in dataset


def test_admin_reads_model_cards(client, db_session):
    admin = _create_user(db_session, "model_card_admin", "admin")

    response = client.get("/admin/model-cards", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.model_cards"
    assert len(payload["model_cards"]) == 5
    assert len(payload["dataset_cards"]) >= 5


def test_patient_cannot_read_model_cards(client, db_session):
    patient = _create_user(db_session, "model_card_patient", "patient")

    response = client.get("/admin/model-cards", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
