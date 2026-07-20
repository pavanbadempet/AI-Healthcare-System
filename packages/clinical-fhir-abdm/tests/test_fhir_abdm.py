from clinical_fhir_abdm.abdm import get_settings
from clinical_fhir_abdm.fhir import build_bundle, patient_resource


class DummyPatient:
    def __init__(self, id, name, gender, dob):
        self.id = id
        self.name = name
        self.gender = gender
        self.dob = dob


def test_patient_resource_generation():
    patient = DummyPatient(123, "Test Patient", "male", "1990-01-01")
    resource = patient_resource(patient)
    assert resource["resourceType"] == "Patient"
    assert resource["id"] == "123"
    assert resource["gender"] == "male"


def test_build_bundle():
    res = {"resourceType": "Patient", "id": "1"}
    bundle = build_bundle([res])
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) == 1


def test_abdm_settings():
    settings = get_settings()
    assert settings is not None
