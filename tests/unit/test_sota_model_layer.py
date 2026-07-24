"""
Unit tests for SOTA Domain Model Layer Engine (backend/sota_model_layer.py).
"""

import time

from backend.sota_model_layer import ClinicalPatientModel, PatientMRN


def test_domain_model_value_object_and_audit_trail():
    mrn = PatientMRN(value="MRN-88776655")
    patient = ClinicalPatientModel(
        mrn=mrn,
        full_name="Jane Smith",
        age=38,
        primary_condition="DIABETES_TYPE_2",
    )

    assert patient.mrn.value == "MRN-88776655"
    assert len(patient.audit_trail) == 0

    now = time.time()
    patient.update_condition("DIABETES_IN_REMISSION", now)

    assert patient.primary_condition == "DIABETES_IN_REMISSION"
    assert len(patient.audit_trail) == 1
    assert patient.audit_trail[0].old_val == "DIABETES_TYPE_2"
    assert patient.audit_trail[0].new_val == "DIABETES_IN_REMISSION"
