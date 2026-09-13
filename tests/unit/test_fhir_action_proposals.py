"""Unit tests for strongly-typed FHIR action proposals and serialization.

Tests:
1. FHIRMedicationRequestProposal creation, numeric dose parsing, to_dict, from_dict, and to_fhir.
2. FHIRServiceRequestProposal creation, coding systems, urgency mapping, and to_fhir.
3. FHIRFlagProposal creation, category normalization, severity extension, and to_fhir.
4. ClinicalAgentResponse aggregation, filtering, serialization roundtrip, and confidence clamping.
5. fhir.py helpers: service_request_resource, flag_resource, and build_bundle validation.
"""

from __future__ import annotations

import datetime
import pytest

from clinical_fhir_abdm.fhir import (
    FHIRValidationError,
    build_bundle,
    flag_resource,
    medication_request_resource,
    patient_resource,
    service_request_resource,
)
from clinical_fhir_abdm.schemas import (
    ClinicalAgentResponse,
    FHIRFlagProposal,
    FHIRMedicationRequestProposal,
    FHIRServiceRequestProposal,
)


def test_medication_request_proposal_creation_and_numeric_dose():
    """Verify strongly-typed MedicationRequest proposal and automatic numeric dose extraction."""
    # Test with string dosage
    prop1 = FHIRMedicationRequestProposal(
        patient_id="PT-100",
        medication_name="Vancomycin",
        dosage="1500 mg IV q12h",
        route="intravenous",
        frequency="every 12 hours",
        indication="MRSA bacteremia",
        clinical_evidence=["Blood culture positive for MRSA"],
    )
    assert prop1.patient_id == "PT-100"
    assert prop1.medication_name == "Vancomycin"
    assert prop1.numeric_dose == 1500.0
    assert prop1.id.startswith("medreq-")

    # Test with explicit numeric dose and unit
    prop2 = FHIRMedicationRequestProposal(
        patient_id="PT-101",
        medication_name="Metformin",
        dose=1000.0,
        unit="mg",
        route="oral",
        frequency="twice daily",
    )
    assert prop2.numeric_dose == 1000.0
    assert "1000" in prop2.dosage
    assert "mg" in prop2.dosage


def test_medication_request_proposal_to_fhir_and_dict_roundtrip():
    """Verify MedicationRequest FHIR R4 schema conformity and dict serialization."""
    prop = FHIRMedicationRequestProposal(
        patient_id="PT-102",
        medication_name="Osimertinib",
        dosage="80 mg oral daily",
        route="oral",
        frequency="daily",
        indication="EGFR T790M NSCLC",
        clinical_evidence=["EGFR exon 19 deletion confirmed"],
        priority="stat",
        countersigned_by="Dr. Sarah Chen, MD",
    )

    # 1. Test dict serialization & roundtrip
    d = prop.to_dict()
    assert d["patient_id"] == "PT-102"
    assert d["medication_name"] == "Osimertinib"
    assert d["countersigned_by"] == "Dr. Sarah Chen, MD"

    reconstructed = FHIRMedicationRequestProposal.from_dict(d)
    assert reconstructed.patient_id == prop.patient_id
    assert reconstructed.medication_name == prop.medication_name
    assert reconstructed.numeric_dose == 80.0
    assert reconstructed.countersigned_by == "Dr. Sarah Chen, MD"

    # 2. Test FHIR R4 resource generation
    fhir_res = prop.to_fhir()
    assert fhir_res["resourceType"] == "MedicationRequest"
    assert fhir_res["id"] == prop.id
    assert fhir_res["status"] == "active"
    assert fhir_res["priority"] == "stat"
    assert fhir_res["subject"]["reference"] == "Patient/PT-102"
    assert fhir_res["medicationCodeableConcept"]["text"] == "Osimertinib"
    assert len(fhir_res["dosageInstruction"]) == 1
    assert "80 mg oral daily" in fhir_res["dosageInstruction"][0]["text"]
    assert fhir_res["reasonCode"][0]["text"] == "EGFR T790M NSCLC"


def test_service_request_proposal_creation_and_fhir_serialization():
    """Verify ServiceRequest proposal creation, priority mapping, and SNOMED/LOINC codes."""
    # Test LOINC diagnostic lab request
    sr_lab = FHIRServiceRequestProposal(
        patient_id="PT-200",
        category="laboratory",
        code="24357-6",  # LOINC for Urinalysis
        description="Urinalysis with microscopic examination",
        urgency="urgent",
        indication="Suspected pyelonephritis",
        supporting_info=["Fever 38.8C", "Costovertebral angle tenderness"],
    )
    assert sr_lab.patient_id == "PT-200"
    assert sr_lab.category == "laboratory"

    # Test dict roundtrip
    sr_dict = sr_lab.to_dict()
    sr_reconstructed = FHIRServiceRequestProposal.from_dict(sr_dict)
    assert sr_reconstructed.description == sr_lab.description
    assert sr_reconstructed.code == "24357-6"

    # Test FHIR R4 generation
    fhir_lab = sr_lab.to_fhir()
    assert fhir_lab["resourceType"] == "ServiceRequest"
    assert fhir_lab["priority"] == "urgent"
    assert fhir_lab["code"]["coding"][0]["system"] == "http://loinc.org"
    assert fhir_lab["code"]["coding"][0]["code"] == "24357-6"
    assert fhir_lab["subject"]["reference"] == "Patient/PT-200"
    assert fhir_lab["reasonCode"][0]["text"] == "Suspected pyelonephritis"
    assert len(fhir_lab["supportingInfo"]) == 2

    # Test SNOMED CT imaging request with STAT priority
    sr_img = FHIRServiceRequestProposal(
        patient_id="PT-201",
        category="imaging",
        code="241042004",  # SNOMED CT for CT chest
        description="STAT CT Angiography Chest Pulmonary Embolism",
        urgency="stat",
    )
    fhir_img = sr_img.to_fhir()
    assert fhir_img["priority"] == "stat"
    assert fhir_img["code"]["coding"][0]["system"] == "http://snomed.info/sct"


def test_flag_proposal_creation_and_fhir_serialization():
    """Verify Flag proposal creation, severity extension, and SNOMED coding."""
    flag_prop = FHIRFlagProposal(
        patient_id="PT-300",
        category="safety_risk",
        severity="critical",
        code="404684003",
        details="Severe Penicillin Anaphylaxis Alert",
        author="Dr. Alan Turing, MD",
    )

    assert flag_prop.status == "active"
    assert flag_prop.severity == "critical"

    # Dict roundtrip
    flag_dict = flag_prop.to_dict()
    flag_reconstructed = FHIRFlagProposal.from_dict(flag_dict)
    assert flag_reconstructed.details == "Severe Penicillin Anaphylaxis Alert"
    assert flag_reconstructed.author == "Dr. Alan Turing, MD"

    # FHIR serialization
    fhir_flag = flag_prop.to_fhir()
    assert fhir_flag["resourceType"] == "Flag"
    assert fhir_flag["status"] == "active"
    assert fhir_flag["subject"]["reference"] == "Patient/PT-300"
    assert fhir_flag["author"]["display"] == "Dr. Alan Turing, MD"
    assert fhir_flag["extension"][0]["valueString"] == "critical"
    assert fhir_flag["category"][0]["coding"][0]["code"] == "safety"


def test_clinical_agent_response_aggregation_and_filtering():
    """Verify ClinicalAgentResponse collects multi-modal proposals and clamps confidence."""
    med_prop = FHIRMedicationRequestProposal(
        patient_id="PT-400",
        medication_name="Cefepime",
        dosage="2 g IV q8h",
    )
    sr_prop = FHIRServiceRequestProposal(
        patient_id="PT-400",
        category="laboratory",
        code="2160-0",
        description="Serum Creatinine and eGFR",
    )
    flag_prop = FHIRFlagProposal(
        patient_id="PT-400",
        category="clinical_alert",
        severity="warning",
        details="Monitor renal function closely",
    )

    response = ClinicalAgentResponse(
        agent_name="PrecisionPharmacotherapyAgent",
        recommendations=["Initiate empiric Cefepime", "Order baseline renal panel"],
        proposed_fhir_actions=[med_prop, sr_prop],
        epistemic_confidence=1.45,  # Needs clamping to 1.0
        reasoning="Patient presents with severe neutropenic fever",
    )

    # Check confidence clamped to 1.0
    assert response.epistemic_confidence == 1.0

    # Add third action
    response.add_action(flag_prop)
    assert len(response.proposed_fhir_actions) == 3

    # Check filtering methods
    assert len(response.get_medication_requests()) == 1
    assert response.get_medication_requests()[0].medication_name == "Cefepime"
    assert len(response.get_service_requests()) == 1
    assert response.get_service_requests()[0].category == "laboratory"
    assert len(response.get_flags()) == 1
    assert "Monitor renal function" in response.get_flags()[0].details

    # Check serialization roundtrip
    resp_dict = response.to_dict()
    assert resp_dict["agent_name"] == "PrecisionPharmacotherapyAgent"
    assert len(resp_dict["proposed_fhir_actions"]) == 3

    reconstructed = ClinicalAgentResponse.from_dict(resp_dict)
    assert len(reconstructed.get_medication_requests()) == 1
    assert len(reconstructed.get_service_requests()) == 1
    assert len(reconstructed.get_flags()) == 1


def test_fhir_helpers_and_bundle_integration():
    """Verify fhir.py helpers service_request_resource and flag_resource assemble into a valid bundle."""
    patient = {"id": "PT-500", "full_name": "Eleanor Vance", "gender": "female", "dob": "1982-04-12"}
    patient_res = patient_resource(patient)

    # ServiceRequest from dict
    sr_data = {
        "id": "SR-501",
        "category": "diagnostic",
        "code": "71388002",
        "description": "Procedure: 12-lead Electrocardiogram",
        "urgency": "stat",
        "indication": "Acute chest pain",
    }
    sr_res = service_request_resource(sr_data, patient_id="PT-500")
    assert sr_res["resourceType"] == "ServiceRequest"
    assert sr_res["subject"]["reference"] == "Patient/PT-500"
    assert sr_res["priority"] == "stat"

    # Flag from proposal object
    flag_prop = FHIRFlagProposal(
        patient_id="PT-500",
        id="FLAG-502",
        category="allergy",
        severity="high",
        details="Severe anaphylaxis to Sulfa drugs",
    )
    flag_res = flag_resource(flag_prop, patient_id="PT-500")
    assert flag_res["resourceType"] == "Flag"
    assert flag_res["subject"]["reference"] == "Patient/PT-500"

    # Build bundle containing Patient, ServiceRequest, and Flag
    bundle = build_bundle([patient_res, sr_res, flag_res])
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 3
    assert bundle["entry"][0]["resource"]["resourceType"] == "Patient"
    assert bundle["entry"][1]["resource"]["resourceType"] == "ServiceRequest"
    assert bundle["entry"][2]["resource"]["resourceType"] == "Flag"

    # Bundle validation error when unresolved patient reference exists
    unresolved_sr = service_request_resource(sr_data, patient_id="PT-MISSING-999")
    with pytest.raises(FHIRValidationError, match="Unresolved FHIR reference"):
        build_bundle([patient_res, unresolved_sr])
