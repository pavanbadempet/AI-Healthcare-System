from backend import terminology


def test_lookup_loinc_code_returns_fhir_coding():
    concept = terminology.lookup_code("loinc", "8867-4")

    assert concept is not None
    assert concept["system"] == "http://loinc.org"
    assert concept["code"] == "8867-4"
    assert concept["display"] == "Heart rate"
    assert concept["category"] == "vital-sign"
    assert concept["coding"] == {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate",
    }


def test_lookup_accepts_canonical_system_uri_and_normalizes_icd10_code():
    concept = terminology.lookup_code("http://hl7.org/fhir/sid/icd-10-cm", "e11.9")

    assert concept is not None
    assert concept["system"] == "http://hl7.org/fhir/sid/icd-10-cm"
    assert concept["code"] == "E11.9"
    assert concept["display"] == "Type 2 diabetes mellitus without complications"


def test_lookup_unknown_code_returns_none():
    assert terminology.lookup_code("loinc", "not-a-code") is None
    assert terminology.lookup_code("not-a-system", "8867-4") is None


def test_supported_systems_are_phi_safe():
    systems = terminology.list_supported_systems()

    assert {system["system"] for system in systems} >= {
        "http://loinc.org",
        "http://snomed.info/sct",
        "http://hl7.org/fhir/sid/icd-10-cm",
    }
    assert all("patient" not in str(system).lower() for system in systems)


def test_rxnorm_lookup_and_caching(monkeypatch):
    # Mock requests to return simulated RxNorm properties
    class MockResponse:
        status_code = 200
        def json(self):
            return {"idAndName": {"rxcui": "198440", "name": "Acetaminophen 325 MG Oral Tablet"}}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: MockResponse())

    # Clean terminology cache
    if os.path.exists(terminology.CACHE_DB):
        try:
            os.remove(terminology.CACHE_DB)
        except Exception:
            pass

    concept = terminology.lookup_code("rxnorm", "198440")
    assert concept is not None
    assert concept["code"] == "198440"
    assert concept["display"] == "Acetaminophen 325 MG Oral Tablet"
    assert concept["category"] == "medication"

    # Subsequent lookup should fetch from cache, not API (monkeypatch to error)
    def fail_get(*args, **kwargs):
        raise RuntimeError("API should not be called")
    monkeypatch.setattr("requests.get", fail_get)

    cached_concept = terminology.lookup_code("rxnorm", "198440")
    assert cached_concept is not None
    assert cached_concept["display"] == "Acetaminophen 325 MG Oral Tablet"
import os

