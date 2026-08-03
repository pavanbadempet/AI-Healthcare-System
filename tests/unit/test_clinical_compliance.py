"""
Unit tests for FDA SaMD & HIPAA Regulatory Compliance Engine.
"""

from backend.clinical_compliance.fda_samd_compliance import (
    samd_evaluator,
    fda_audit_chain,
    hipaa_data_minimizer,
    HealthcareState,
    SaMDSignificance,
    SaMDRiskCategory,
)


def test_samd_risk_categorization_evaluator():
    cat_iv = samd_evaluator.evaluate_risk(
        HealthcareState.CRITICAL, SaMDSignificance.TREAT_OR_DIAGNOSE,
    )
    assert cat_iv == SaMDRiskCategory.CATEGORY_IV

    cat_i = samd_evaluator.evaluate_risk(
        HealthcareState.NON_SERIOUS, SaMDSignificance.INFORM_MANAGEMENT,
    )
    assert cat_i == SaMDRiskCategory.CATEGORY_I


def test_fda_21_cfr_part_11_audit_chain_integrity():
    # Record initial events
    block1 = fda_audit_chain.record_event(
        event_type="CLINICIAN_LOGIN",
        actor_id="DR_SMITH_99",
        action_details="Clinician logged into ICU dashboard",
    )
    assert block1.index == 1

    block2 = fda_audit_chain.record_event(
        event_type="PRESCRIPTION_APPROVAL",
        actor_id="DR_SMITH_99",
        action_details="Approved Warfarin dosage adjustment",
        digital_signature="SIG-RSA4096-HEX-998877665544332211",
    )
    assert block2.index == 2
    assert block2.previous_hash == block1.current_hash

    # Verify chain cryptographic integrity
    assert fda_audit_chain.verify_integrity() is True


def test_hipaa_minimum_necessary_data_minimization():
    full_patient = {
        "patient_id": "P-9000",
        "name": "Jane Doe",
        "ssn": "000-11-2222",
        "billing_codes": ["ICD10-I10", "CPT-99214"],
        "total_amount": 350.00,
        "medications": ["Lisinopril"],
        "allergies": ["Penicillin"],
        "renal_function": "eGFR=88",
    }

    billing_record = hipaa_data_minimizer.filter_minimum_necessary(full_patient, "BILLING")
    assert "ssn" not in billing_record
    assert "name" not in billing_record
    assert billing_record["billing_codes"] == ["ICD10-I10", "CPT-99214"]

    pharmacy_record = hipaa_data_minimizer.filter_minimum_necessary(full_patient, "PHARMACY")
    assert "total_amount" not in pharmacy_record
    assert pharmacy_record["medications"] == ["Lisinopril"]
