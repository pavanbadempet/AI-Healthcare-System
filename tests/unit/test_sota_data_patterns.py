"""
Unit tests for SOTA Enterprise Data Patterns (CQRS, SCD Type 2, Differential Privacy).
"""

from backend.sota_data_patterns import cqrs_event_store, scd2_tracker, dp_engine

def test_cqrs_event_sourcing_and_read_projection():
    evt = cqrs_event_store.append_command("P9901", "ENCOUNTER_ADMISSION", {"department": "ICU"})
    assert evt.event_id.startswith("EVT-")
    assert evt.patient_id == "P9901"

    proj = cqrs_event_store.get_read_projection("P9901")
    assert proj is not None
    assert proj["encounter_count"] >= 1
    assert proj["latest_event"] == "ENCOUNTER_ADMISSION"

def test_scd_type_2_patient_versioning():
    v1 = scd2_tracker.upsert_patient_attribute("P100", "Aarav Sharma", "123 Old St")
    assert v1.version == 1
    assert v1.is_current is True

    v2 = scd2_tracker.upsert_patient_attribute("P100", "Aarav Sharma", "456 New Ave")
    assert v2.version == 2
    assert v2.is_current is True
    assert v1.is_current is False
    assert v1.valid_to is not None

def test_differential_privacy_noise():
    val = 100.0
    noised = dp_engine.apply_laplace_noise(val, epsilon=1.0)
    assert isinstance(noised, float)
