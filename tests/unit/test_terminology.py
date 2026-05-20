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
