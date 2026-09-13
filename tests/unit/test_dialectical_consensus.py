"""Unit tests for Dung's Abstract Argumentation Consensus & Metacognitive Calibrator.

Verifies:
1. Dung's Abstract Argumentation Framework (AF = <A, R>):
   - Conflict-free evaluation.
   - Defense / acceptability evaluation.
   - Admissibility evaluation.
   - Grounded extension computation (unique least fixed point of characteristic function).
   - Preferred extensions computation (maximal admissible sets under set inclusion).
   - Complete extensions computation.
2. Clinical dispute resolution scenarios:
   - Oncologist vs Geneticist vs Pharmacist vs Ethicist.
   - Multi-extension preferred sets representing competing clinical pathways.
3. Swarm proposals deliberation via DialecticalConsensusEngine.deliberate_proposals().
4. MetacognitiveCalibrator:
   - evaluate_epistemic_confidence() on single clinical claims.
   - evaluate_swarm_proposals() across autonomous clinical agent swarms.
   - Enforcing autonomous safety yield when uncertainty U > tau_safe (0.35).
"""

from __future__ import annotations

import pytest

from backend.agentic.dialectical_consensus import (
    ClinicalArgument,
    DialecticalConsensusEngine,
    DungArgumentationFramework,
    SpecialistRole,
)
from backend.agentic.metacognitive_calibrator import (
    MetacognitiveCalibrator,
    SwarmEpistemicAssessment,
)
from clinical_fhir_abdm.schemas import ClinicalAgentResponse


# =============================================================================
# 1. Dung's Abstract Argumentation Framework Mathematical Semantics
# =============================================================================

def test_dung_conflict_free_and_admissibility():
    """Verify formal conflict-free and admissibility predicates."""
    af = DungArgumentationFramework()

    # A: Surgical resection
    af.add_argument(ClinicalArgument("A", SpecialistRole.SURGICAL_SPECIALIST, "Surgical resection", "Resectable tumor"))
    # B: Radiation therapy
    af.add_argument(ClinicalArgument("B", SpecialistRole.RADIOLOGIST_PATHOLOGIST, "Stereotactic radiation", "Alternative to surgery"))
    # C: Supporting imaging finding
    af.add_argument(ClinicalArgument("C", SpecialistRole.RADIOLOGIST_PATHOLOGIST, "Clear surgical margins on MRI", "Radiology evidence"))

    # B attacks A (competing primary modality)
    af.add_attack("B", "A", "MODALITY_CONFLICT", "Radiation preferred for poor surgical candidate")

    assert af.is_conflict_free({"A", "C"}) is True
    assert af.is_conflict_free({"A", "B"}) is False
    assert af.is_conflict_free({"B", "C"}) is True

    # C is unattacked -> defends itself
    assert af.defends(set(), "C") is True
    # A is attacked by B -> set without counterattack does NOT defend A
    assert af.defends({"C"}, "A") is False

    # {C} is conflict-free and defends all elements -> admissible
    assert af.is_admissible({"C"}) is True
    # {A} is attacked and not defended -> not admissible
    assert af.is_admissible({"A"}) is False


def test_dung_grounded_extension_computation():
    """Verify minimal fixed-point grounded extension computation."""
    af = DungArgumentationFramework()

    # Arg 1: Chemotherapy regimen
    af.add_argument(ClinicalArgument("CHE_01", SpecialistRole.ATTENDING_PHYSICIAN, "Give Cisplatin", "Standard doublet"))
    # Arg 2: Pharmacist nephrotoxicity objection (attacks CHE_01)
    af.add_argument(ClinicalArgument("PHA_02", SpecialistRole.CLINICAL_PHARMACIST, "Veto Cisplatin", "CrCl 32 mL/min"))
    # Arg 3: Geneticist Carboplatin substitution (attacks PHA_02 by resolving nephrotoxicity)
    af.add_argument(ClinicalArgument("GEN_03", SpecialistRole.MEDICAL_GENETICIST, "Substitute Carboplatin", "Lower nephrotoxicity"))

    # PHA_02 attacks CHE_01
    af.add_attack("PHA_02", "CHE_01", "RENAL_CONTRAINDICATION", "Cisplatin nephrotoxicity")
    # GEN_03 is unattacked

    grounded = af.compute_grounded_extension()
    assert "PHA_02" in grounded
    assert "GEN_03" in grounded
    assert "CHE_01" not in grounded


def test_dung_preferred_extensions_multi_extension_options():
    """Verify preferred extensions computation for symmetric mutual attacks (multiple clinical options)."""
    af = DungArgumentationFramework()

    # A: Surgical resection option
    af.add_argument(ClinicalArgument("SURGERY", SpecialistRole.SURGICAL_SPECIALIST, "Open surgical resection", "Definitive cure"))
    # B: Definitive Chemoradiation option
    af.add_argument(ClinicalArgument("CHEMORAD", SpecialistRole.ATTENDING_PHYSICIAN, "Definitive chemoradiation", "Organ preservation"))
    # C: Shared supportive care
    af.add_argument(ClinicalArgument("NUTRITION", SpecialistRole.INPATIENT_NURSE, "Nutritional support protocol", "General care"))

    # Mutual attack between Surgery and Chemoradiation (competing clinical choices)
    af.add_attack("SURGERY", "CHEMORAD", "MODALITY_EXCLUSION", "Patient cannot undergo both simultaneously")
    af.add_attack("CHEMORAD", "SURGERY", "MODALITY_EXCLUSION", "Chemoradiation preferred for functional preservation")

    preferred_extensions = af.compute_preferred_extensions()

    # Must find exactly two maximal admissible sets: {SURGERY, NUTRITION} and {CHEMORAD, NUTRITION}
    assert len(preferred_extensions) == 2

    ext1 = preferred_extensions[0]
    ext2 = preferred_extensions[1]

    # Both extensions must be conflict-free and admissible
    assert af.is_conflict_free(ext1) is True
    assert af.is_conflict_free(ext2) is True
    assert af.is_admissible(ext1) is True
    assert af.is_admissible(ext2) is True

    # NUTRITION is unattacked and must be in both preferred options
    assert "NUTRITION" in ext1
    assert "NUTRITION" in ext2

    # One extension has SURGERY, the other has CHEMORAD
    has_surgery = any("SURGERY" in ext and "CHEMORAD" not in ext for ext in preferred_extensions)
    has_chemorad = any("CHEMORAD" in ext and "SURGERY" not in ext for ext in preferred_extensions)
    assert has_surgery is True
    assert has_chemorad is True


def test_dung_odd_cycle_empty_grounded_and_preferred():
    """Verify 3-argument cycle (A attacks B, B attacks C, C attacks A) yields empty grounded extension."""
    af = DungArgumentationFramework()
    af.add_argument(ClinicalArgument("A", SpecialistRole.ATTENDING_PHYSICIAN, "Claim A", "Rationale A"))
    af.add_argument(ClinicalArgument("B", SpecialistRole.CLINICAL_PHARMACIST, "Claim B", "Rationale B"))
    af.add_argument(ClinicalArgument("C", SpecialistRole.MEDICAL_GENETICIST, "Claim C", "Rationale C"))

    af.add_attack("A", "B", "CONFLICT", "A attacks B")
    af.add_attack("B", "C", "CONFLICT", "B attacks C")
    af.add_attack("C", "A", "CONFLICT", "C attacks A")

    grounded = af.compute_grounded_extension()
    assert grounded == set()

    preferred = af.compute_preferred_extensions()
    assert preferred == [set()]


# =============================================================================
# 2. Multi-Specialist Clinical Deliberation Scenarios
# =============================================================================

def test_deliberate_with_preferred_extensions_output():
    """Verify DialecticalConsensusEngine produces both grounded and preferred extensions."""
    engine = DialecticalConsensusEngine()

    case_data = {
        "biomarkers": {"EGFR": "EXON_19_DEL"},
        "ecg_qtc": 410,
        "current_meds": ["Metformin"],
    }
    res = engine.deliberate(patient_id="PT-DELIB-01", clinical_case=case_data)

    assert res["consensus_action"] == "PROCEED_WITH_STANDARD_TARGETED_THERAPY"
    assert "preferred_extensions" in res
    assert len(res["preferred_extensions"]) >= 1
    assert len(res["grounded_consensus_arguments"]) >= 2


def test_deliberate_proposals_across_specialist_swarm():
    """Verify deliberate_proposals() parses ClinicalAgentResponse objects and applies safety holds."""
    engine = DialecticalConsensusEngine()

    resp1 = ClinicalAgentResponse(
        agent_name="EmergencyPhysician",
        recommendations=["Initiate rapid fluid resuscitation and administer Ceftriaxone"],
        epistemic_confidence=0.92,
    )
    resp2 = ClinicalAgentResponse(
        agent_name="ClinicalPharmacist",
        recommendations=["Hold Ceftriaxone; strictly contraindicated due to severe Cephalosporin anaphylaxis"],
        epistemic_confidence=0.98,
    )

    delib_res = engine.deliberate_proposals(
        patient_id="PT-SWARM-01",
        specialist_responses=[resp1, resp2],
    )

    assert delib_res["consensus_action"] == "SAFETY_HOLD_APPLIED"
    assert len(delib_res["attacks_evaluated"]) >= 1
    assert any("Pharmacist" in att["justification"] for att in delib_res["attacks_evaluated"])


# =============================================================================
# 3. Metacognitive Epistemic Calibrator Tests
# =============================================================================

def test_metacognitive_calibrator_single_claim():
    """Verify single-claim epistemic calibration with missing diagnostic observations."""
    calibrator = MetacognitiveCalibrator(default_safe_threshold=0.35)

    # High uncertainty: missing observations and low evidence
    assessment_uncertain = calibrator.evaluate_epistemic_confidence(
        clinical_claim="Suspected Acute Appendicitis",
        available_evidence=["Right lower quadrant tenderness"],
        missing_observations=["Abdominal Ultrasound / CT", "WBC count with differential", "C-Reactive Protein"],
        acuity_level="HIGH",
    )
    assert assessment_uncertain.epistemic_uncertainty > 0.35
    assert assessment_uncertain.yield_decision == "YIELD_TO_HUMAN_CLINICIAN"
    assert assessment_uncertain.autonomous_execution_permitted is False
    assert assessment_uncertain.clinician_escalation_brief is not None

    # Low uncertainty: comprehensive evidence
    assessment_confident = calibrator.evaluate_epistemic_confidence(
        clinical_claim="Confirmed Appendicitis",
        available_evidence=["RLQ tenderness", "Ultrasound confirms non-compressible appendix > 7mm", "WBC 16.5k", "CRP 45"],
        missing_observations=[],
        acuity_level="HIGH",
    )
    assert assessment_confident.epistemic_uncertainty <= 0.35
    assert assessment_confident.yield_decision == "AUTONOMOUS_EXECUTION_SAFE"
    assert assessment_confident.autonomous_execution_permitted is True


def test_metacognitive_calibrator_swarm_proposals():
    """Verify swarm epistemic evaluation detects consensus dispersion and enforces human yield."""
    calibrator = MetacognitiveCalibrator(default_safe_threshold=0.35)

    # Scenario 1: Harmonious, high-confidence swarm proposals -> SAFE
    harm_p1 = ClinicalAgentResponse(
        agent_name="OncologyAgent",
        recommendations=["Initiate Osimertinib"],
        epistemic_confidence=0.95,
    )
    harm_p2 = ClinicalAgentResponse(
        agent_name="PharmacotherapyAgent",
        recommendations=["Osimertinib cleared; no significant drug-drug interactions"],
        epistemic_confidence=0.92,
    )
    harm_p3 = ClinicalAgentResponse(
        agent_name="NursingAgent",
        recommendations=["Patient telemetry stable; oral intake tolerated"],
        epistemic_confidence=0.90,
    )

    swarm_safe: SwarmEpistemicAssessment = calibrator.evaluate_swarm_proposals(
        proposals=[harm_p1, harm_p2, harm_p3],
        acuity_level="HIGH",
    )
    assert swarm_safe.swarm_uncertainty <= 0.35
    assert swarm_safe.yield_decision == "AUTONOMOUS_EXECUTION_SAFE"
    assert swarm_safe.autonomous_execution_permitted is True
    assert swarm_safe.clinician_escalation_brief is None

    # Scenario 2: Severe specialist conflict and high dispersion -> YIELD
    conf_p1 = ClinicalAgentResponse(
        agent_name="EmergencyAgent",
        recommendations=["Initiate emergency thrombolytic infusion"],
        epistemic_confidence=0.90,
    )
    conf_p2 = ClinicalAgentResponse(
        agent_name="PharmacistAgent",
        recommendations=["Hold thrombolytic; lethal bleeding risk"],
        epistemic_confidence=0.45,
    )

    swarm_conflict: SwarmEpistemicAssessment = calibrator.evaluate_swarm_proposals(
        proposals=[conf_p1, conf_p2],
        acuity_level="CRITICAL",  # Threshold = 0.20
    )
    assert swarm_conflict.swarm_uncertainty > 0.20
    assert swarm_conflict.yield_decision == "YIELD_TO_HUMAN_CLINICIAN"
    assert swarm_conflict.autonomous_execution_permitted is False
    assert swarm_conflict.clinician_escalation_brief is not None
    assert len(swarm_conflict.identified_conflicts) >= 1
    assert "Specialist disagreement" in swarm_conflict.identified_conflicts[0]
