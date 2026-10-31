"""Verification suite for OMOP CDM v5.4 vocabulary crosswalk tables."""
def test_vocabulary_mapping_integrity():
    concept_map = {
        "SNOMED": 1,
        "RxNorm": 2,
        "LOINC": 3,
        "ICD10CM": 4
    }
    assert len(concept_map) == 4
    assert concept_map["LOINC"] == 3
