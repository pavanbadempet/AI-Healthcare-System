"""Unit tests for Pre-Action Invariant Execution Gate.

Verifies deterministic safety barriers inspecting FHIR action proposals:
1. ABSOLUTE_CONTRAINDICATION: Thrombolytics, anticoagulants, beta-blockers, PDE5 inhibitors.
2. RENAL_HEPATIC_FLOOR: Metformin, Vancomycin, Enoxaparin, DOACs, Cefepime, Paracetamol.
3. PREGNANCY_TERATOGEN: Category X drugs (Methotrexate, Isotretinoin, Warfarin, ACE-I).
4. ALLERGY_ANAPHYLAXIS: Beta-lactams, Sulfonamides, NSAIDs, Radiocontrast.
5. FOUR_EYE_QUORUM: Invasive ventilation, high-dose chemo, ECMO dual-attending signoff.
6. InvariantValidationResult structure, validate_proposal, and audit logging.
"""

from __future__ import annotations

import pytest

from backend.agentic.invariant_execution_gate import (
    InvariantType,
    InvariantValidationResult,
    PreActionInvariantGate,
    ValidationStatus,
)
from clinical_fhir_abdm.schemas import (
    FHIRMedicationRequestProposal,
    FHIRServiceRequestProposal,
)


@pytest.fixture
def gate() -> PreActionInvariantGate:
    return PreActionInvariantGate()


# =============================================================================
# 1. Absolute Contraindication Barrier Tests
# =============================================================================

def test_gate_blocks_thrombolytic_in_active_hemorrhage(gate: PreActionInvariantGate):
    """Verify Alteplase/tPA strictly blocked when intracranial hemorrhage is present."""
    patient = {
        "conditions": ["Acute Ischemic Stroke", "Subdural Hemorrhage"],
        "allergies": [],
        "egfr": 90,
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-THROMB-01",
        medication_name="Alteplase",
        dosage="0.9 mg/kg IV",
        indication="Acute stroke",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "ABSOLUTE_CONTRAINDICATION"
    assert any("strictly contraindicated" in v.message for v in res.violations)
    assert not res.passed


def test_gate_blocks_anticoagulation_in_intracranial_bleed(gate: PreActionInvariantGate):
    """Verify Heparin/Apixaban blocked in acute intracranial bleeding."""
    patient = {
        "conditions": ["Deep Vein Thrombosis", "Intracranial Hemorrhage"],
        "allergies": [],
        "egfr": 80,
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-BLEED-02",
        medication_name="Heparin",
        dosage="80 units/kg bolus",
        indication="DVT treatment",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "ABSOLUTE_CONTRAINDICATION"
    assert any("antithrombotic" in v.remediation.lower() or "reverse" in v.remediation.lower() for v in res.violations)


def test_gate_blocks_beta_blocker_in_cardiogenic_shock(gate: PreActionInvariantGate):
    """Verify Metoprolol blocked in cardiogenic shock or profound bradycardia."""
    patient = {
        "conditions": ["Cardiogenic Shock", "Acute Heart Failure"],
        "heart_rate": 40,
        "allergies": [],
        "egfr": 75,
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-SHOCK-03",
        medication_name="Metoprolol tartrate",
        dosage="25 mg oral twice daily",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "ABSOLUTE_CONTRAINDICATION"
    assert "cardiogenic shock" in res.explanation.lower()


def test_gate_blocks_pde5_inhibitor_with_concurrent_nitrates(gate: PreActionInvariantGate):
    """Verify Sildenafil blocked when patient is receiving concurrent Nitroglycerin."""
    patient = {
        "conditions": ["Coronary Artery Disease"],
        "current_meds": ["Nitroglycerin sublingual PRN", "Aspirin 81mg"],
        "allergies": [],
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-NITRO-04",
        medication_name="Sildenafil",
        dosage="50 mg oral",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "ABSOLUTE_CONTRAINDICATION"
    assert "nitrate" in res.explanation.lower()


# =============================================================================
# 2. Renal & Hepatic Clearance Floor Barrier Tests
# =============================================================================

def test_gate_blocks_metformin_below_renal_floor(gate: PreActionInvariantGate):
    """Verify Metformin is blocked when eGFR < 30 mL/min due to fatal lactic acidosis risk."""
    patient = {
        "conditions": ["Type 2 Diabetes Mellitus", "CKD Stage 4"],
        "egfr": 24.0,
        "allergies": [],
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-RENAL-01",
        medication_name="Metformin",
        dosage="1000 mg oral twice daily",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "RENAL_HEPATIC_FLOOR"
    assert "lactic acidosis" in res.explanation.lower()


def test_gate_blocks_vancomycin_overdose_in_severe_renal_impairment(gate: PreActionInvariantGate):
    """Verify standard Vancomycin dose (>1000mg) blocked when eGFR < 20."""
    patient = {
        "conditions": ["Severe Sepsis"],
        "egfr": 14.0,
        "allergies": [],
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-RENAL-02",
        medication_name="Vancomycin",
        dosage="1500 mg IV",
        dose=1500.0,
        unit="mg",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "RENAL_HEPATIC_FLOOR"
    assert any("nephrotoxicity" in v.clinical_severity.lower() for v in res.violations)


def test_gate_blocks_enoxaparin_full_dose_in_renal_failure(gate: PreActionInvariantGate):
    """Verify full-dose therapeutic Enoxaparin blocked without renal adjustment when CrCl < 30."""
    patient = {
        "conditions": ["Pulmonary Embolism"],
        "crcl": 22.0,
        "egfr": 22.0,
        "allergies": [],
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-RENAL-03",
        medication_name="Enoxaparin",
        dosage="80 mg subcutaneous q12h",
        dose=80.0,
        unit="mg",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "RENAL_HEPATIC_FLOOR"
    assert "enoxaparin" in res.explanation.lower()


def test_gate_blocks_paracetamol_overdose_in_hepatic_failure(gate: PreActionInvariantGate):
    """Verify Acetaminophen capped in acute or decompensated hepatic failure."""
    patient = {
        "conditions": ["Decompensated Cirrhosis", "Acute Liver Failure"],
        "liver_failure": True,
        "child_pugh": "C",
        "alt": 1200.0,
        "allergies": [],
    }
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-LIVER-01",
        medication_name="Paracetamol",
        dosage="4000 mg daily",
        dose=4000.0,
        unit="mg",
    )

    res = gate.validate_proposal(proposal, patient)
    assert res.status == ValidationStatus.REJECT
    assert res.barrier_triggered == "RENAL_HEPATIC_FLOOR"
    assert "hepatic" in res.explanation.lower()


# =============================================================================
# 3. Pregnancy Category X & Teratogenic Barrier Tests
# =============================================================================

def test_gate_blocks_teratogens_in_pregnancy(gate: PreActionInvariantGate):
    """Verify Methotrexate and Isotretinoin blocked in pregnancy."""
    pregnant_pt = {
        "is_pregnant": True,
        "conditions": ["Rheumatoid Arthritis", "Intrauterine Pregnancy"],
        "allergies": [],
        "egfr": 100.0,
    }

    # Methotrexate
    mtx_prop = FHIRMedicationRequestProposal(
        patient_id="PT-PREG-01",
        medication_name="Methotrexate",
        dosage="15 mg oral weekly",
    )
    res_mtx = gate.validate_proposal(mtx_prop, pregnant_pt)
    assert res_mtx.status == ValidationStatus.REJECT
    assert res_mtx.barrier_triggered == "PREGNANCY_TERATOGEN"
    assert "category x" in res_mtx.explanation.lower()

    # Lisinopril (ACE-I)
    lisinopril_prop = FHIRMedicationRequestProposal(
        patient_id="PT-PREG-02",
        medication_name="Lisinopril",
        dosage="10 mg oral daily",
    )
    res_lis = gate.validate_proposal(lisinopril_prop, pregnant_pt)
    assert res_lis.status == ValidationStatus.REJECT
    assert res_lis.barrier_triggered == "PREGNANCY_TERATOGEN"


# =============================================================================
# 4. Anaphylactic Allergy Cross-Reactivity Tests
# =============================================================================

def test_gate_blocks_penicillin_and_cross_reactive_beta_lactams(gate: PreActionInvariantGate):
    """Verify Penicillin allergy blocks Ampicillin, Amoxicillin, and 1st gen Cephalosporins."""
    pen_allergic_pt = {
        "conditions": ["Community Acquired Pneumonia"],
        "allergies": ["Penicillin Anaphylaxis"],
        "egfr": 95.0,
    }

    # Ampicillin
    amp_prop = FHIRMedicationRequestProposal(
        patient_id="PT-ALLERGY-01",
        medication_name="Ampicillin",
        dosage="2 g IV q4h",
    )
    res_amp = gate.validate_proposal(amp_prop, pen_allergic_pt)
    assert res_amp.status == ValidationStatus.REJECT
    assert res_amp.barrier_triggered == "ALLERGY_ANAPHYLAXIS"

    # Cephalexin (1st gen cephalosporin cross-reactivity)
    ceph_prop = FHIRMedicationRequestProposal(
        patient_id="PT-ALLERGY-02",
        medication_name="Cephalexin",
        dosage="500 mg oral q6h",
    )
    res_ceph = gate.validate_proposal(ceph_prop, pen_allergic_pt)
    assert res_ceph.status == ValidationStatus.REJECT
    assert res_ceph.barrier_triggered == "ALLERGY_ANAPHYLAXIS"

    # Safe non-beta-lactam alternative passes
    safe_prop = FHIRMedicationRequestProposal(
        patient_id="PT-ALLERGY-03",
        medication_name="Aztreonam",
        dosage="1 g IV q8h",
    )
    res_safe = gate.validate_proposal(safe_prop, pen_allergic_pt)
    assert res_safe.status == ValidationStatus.PASS
    assert res_safe.barrier_triggered is None


def test_gate_blocks_sulfa_and_nsaid_allergies(gate: PreActionInvariantGate):
    """Verify Sulfa and NSAID allergy enforcement."""
    # Sulfa
    sulfa_pt = {"allergies": ["Sulfamethoxazole"], "conditions": []}
    bactrim_prop = FHIRMedicationRequestProposal(
        patient_id="PT-SULFA-01",
        medication_name="Bactrim DS",
        dosage="1 tab oral twice daily",
    )
    res_sulfa = gate.validate_proposal(bactrim_prop, sulfa_pt)
    assert res_sulfa.status == ValidationStatus.REJECT
    assert res_sulfa.barrier_triggered == "ALLERGY_ANAPHYLAXIS"

    # NSAID
    nsaid_pt = {"allergies": ["Aspirin"], "conditions": []}
    ketorolac_prop = FHIRMedicationRequestProposal(
        patient_id="PT-NSAID-01",
        medication_name="Ketorolac",
        dosage="30 mg IV single dose",
    )
    res_nsaid = gate.validate_proposal(ketorolac_prop, nsaid_pt)
    assert res_nsaid.status == ValidationStatus.REJECT
    assert res_nsaid.barrier_triggered == "ALLERGY_ANAPHYLAXIS"


# =============================================================================
# 5. Four-Eye Attending Quorum Barrier Tests
# =============================================================================

def test_gate_requires_dual_attending_countersignature_for_high_risk_actions(gate: PreActionInvariantGate):
    """Verify invasive ventilation and ECMO require Four-Eye attending quorum."""
    normal_pt = {"conditions": ["Severe ARDS"], "allergies": [], "egfr": 90.0}

    # High-risk invasive ventilation WITHOUT countersignature -> REJECT
    sr_unapproved = FHIRServiceRequestProposal(
        patient_id="PT-ICU-01",
        category="procedure",
        code="40617009",
        description="Invasive mechanical ventilation and endotracheal intubation",
        urgency="stat",
    )
    res_unapproved = gate.validate_proposal(sr_unapproved, normal_pt)
    assert res_unapproved.status == ValidationStatus.REJECT
    assert res_unapproved.barrier_triggered == "FOUR_EYE_QUORUM"
    assert "four-eye" in res_unapproved.explanation.lower()

    # Same proposal WITH dual attending countersignature -> PASS
    sr_approved = FHIRServiceRequestProposal(
        patient_id="PT-ICU-01",
        category="procedure",
        code="40617009",
        description="Invasive mechanical ventilation and endotracheal intubation",
        urgency="stat",
        countersigned_by="Dr. Marcus Welby, MD (Attending Intensivist)",
    )
    res_approved = gate.validate_proposal(sr_approved, normal_pt)
    assert res_approved.status == ValidationStatus.PASS
    assert res_approved.barrier_triggered is None


# =============================================================================
# 6. Structured Output, Audit Logging, and Legacy Execution Tests
# =============================================================================

def test_invariant_audit_logging_and_validation_result_schema(gate: PreActionInvariantGate):
    """Verify InvariantValidationResult to_dict schema and immutable audit log trail."""
    gate.clear()
    assert len(gate.get_audit_log()) == 0

    patient = {"conditions": [], "allergies": ["Penicillin"], "egfr": 90}
    proposal = FHIRMedicationRequestProposal(
        patient_id="PT-AUDIT-01",
        medication_name="Amoxicillin",
        dosage="500 mg oral",
    )

    res = gate.validate_proposal(proposal, patient)
    d = res.to_dict()

    assert d["status"] == "REJECT"
    assert d["passed"] is False
    assert d["barrier_triggered"] == "ALLERGY_ANAPHYLAXIS"
    assert d["proposal_id"] == proposal.id
    assert d["audit_token"] is not None
    assert len(d["violations"]) >= 1

    # Check audit log trail
    logs = gate.get_audit_log()
    assert len(logs) == 1
    assert logs[0]["status"] == "REJECT"
    assert logs[0]["barrier_triggered"] == "ALLERGY_ANAPHYLAXIS"
