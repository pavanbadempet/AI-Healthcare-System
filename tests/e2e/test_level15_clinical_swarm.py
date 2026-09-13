"""Level 15 Autonomous Multi-Specialty Clinical Intelligence Swarm E2E Test Suite.

Comprehensive 4-Tier Verification:
- Tier 1: Smoke & Specialty Baseline (Emergency, Pharmacotherapy, Radiology, Oncology, Nursing, Prior-Auth, Coding)
- Tier 2: Edge Cases & Clinical Boundary Stress (Borderline vitals, extreme eGFR, polymedication, Beers criteria)
- Tier 3: Multi-Agent Swarm Deliberation & Dung Argumentation (Cross-specialty attacks, grounded extension consensus)
- Tier 4: Closed-Loop Invariant Execution Gate & Epistemic Calibration (Pre-action safety gate, epistemic uncertainty yield)
"""

from __future__ import annotations

from clinical_fhir_abdm.schemas import (
    ClinicalAgentResponse,
    FHIRMedicationRequestProposal,
)

from backend.agentic.dialectical_consensus import (
    DialecticalConsensusEngine,
)
from backend.agentic.invariant_execution_gate import (
    PreActionInvariantGate,
    ValidationStatus,
)
from backend.agentic.metacognitive_calibrator import (
    MetacognitiveCalibrator,
)
from backend.agents.ed_triage_agent import ed_triage_agent
from backend.agents.medical_coding_auditor import coding_auditor_agent
from backend.agents.nursing_handoff_agent import nursing_handoff_agent
from backend.agents.prescribing_safety_agent import (
    prescribing_safety_agent,
)
from backend.agents.prior_authorization_agent import (
    prior_auth_agent,
)
from backend.agents.radiology_prereader_agent import (
    radiology_prereader_agent,
)
from backend.agents.tumor_board_agent import tumor_board_agent

# =============================================================================
# TIER 1: SMOKE & SPECIALTY BASELINE TESTS
# =============================================================================

class TestTier1SpecialtyBaselines:
    """Smoke and baseline verification across all 5 clinical specialties and 2 operational modules."""

    def test_emergency_medicine_esi1_resuscitation(self):
        """Emergency Agent flags ESI Level 1 immediate life-saving intervention."""
        res = ed_triage_agent.evaluate_esi_triage(
            chief_complaint="Unresponsive, severe trauma",
            heart_rate=160.0,
            systolic_bp=70.0,
            oxygen_sat=82.0,
            respiratory_rate=32.0,
            is_unresponsive_or_dying=True,
            gcs=6,
        )
        assert res["esi_level"] == 1
        assert res["acuity_category"] == "IMMEDIATE_RESUSCITATION"
        assert res["target_time_to_physician_min"] == 0

        # Verify Shock Index and qSOFA calculations
        si = ed_triage_agent.evaluate_shock_indices(heart_rate=160.0, systolic_bp=70.0, diastolic_bp=45.0)
        assert si["shock_index"] > 1.0
        assert si["hypoperfusion_detected"] is True

        qsofa = ed_triage_agent.calculate_qsofa(respiratory_rate=32.0, systolic_bp=70.0, gcs=6)
        assert qsofa["qsofa_score"] >= 2
        assert qsofa["high_risk"] is True

        # Surviving Sepsis Campaign bundle
        bundle = ed_triage_agent.evaluate_ssc_bundle(
            suspected_infection=True,
            qsofa_score=2,
            mean_arterial_pressure=53.0,
            serum_lactate=4.5,
            patient_weight_kg=70.0,
        )
        assert bundle["ssc_bundle_activated"] is True
        assert len(bundle["bundle_actions"]) >= 4

    def test_emergency_medicine_news2_hypercapnic_scale2(self):
        """Emergency Agent computes NEWS2 using Scale 2 for hypercapnic respiratory failure."""
        res = ed_triage_agent.calculate_news2(
            respiratory_rate=22,
            oxygen_sat=89,
            hypercapnic_respiratory_failure=True,
            supplemental_oxygen=True,
            systolic_bp=128,
            heart_rate=98,
            consciousness="A",
            temperature_c=37.8,
        )
        assert res["total_news2_score"] > 0
        assert res["clinical_risk_level"] in ["LOW_MEDIUM", "MEDIUM", "HIGH"]

    def test_pharmacotherapy_cpic_pharmacogenomics(self):
        """Pharmacotherapy Agent checks CPIC Level A pharmacogenomics (HLA-B*5701 & CYP2C19)."""
        # Abacavir with positive HLA-B*5701 -> absolute contraindication
        findings_abacavir = prescribing_safety_agent.evaluate_pharmacogenomics(
            medication_name="Abacavir",
            patient_genotypes={"hla_b_5701": "Positive"},
        )
        assert len(findings_abacavir) == 1
        assert findings_abacavir[0]["actionability"] == "CPIC_LEVEL_A_CONTRAINDICATION"
        assert findings_abacavir[0]["severity"] == "CRITICAL"

        # Clopidogrel with CYP2C19 *2/*2 poor metabolizer
        findings_clopidogrel = prescribing_safety_agent.evaluate_pharmacogenomics(
            medication_name="Clopidogrel",
            patient_genotypes={"cyp2c19": "*2/*2"},
        )
        assert len(findings_clopidogrel) == 1
        assert findings_clopidogrel[0]["phenotype"] == "Poor Metabolizer"
        assert "Ticagrelor" in findings_clopidogrel[0]["recommendation"] or "Prasugrel" in findings_clopidogrel[0]["recommendation"]

    def test_pharmacotherapy_beers_2023_geriatric_criteria(self):
        """Pharmacotherapy Agent flags Beers 2023 high-risk drugs in patients aged >= 65."""
        finding = prescribing_safety_agent.evaluate_beers_criteria(
            medication_name="Diphenhydramine",
            patient_age_years=75.0,
        )
        assert finding is not None
        assert finding["is_beers_pim"] is True
        assert "Anticholinergic" in finding["category"]

    def test_radiology_prereader_acr_and_stat_alert(self):
        """Radiology Pre-Reader computes ACR appropriateness and STAT critical alert."""
        res = radiology_prereader_agent.generate_pre_read_impression(
            modality="CXRAY",
            clinical_indication="Sudden pleuritic chest pain, dyspnea after trauma",
            detected_findings=["Right-sided tension pneumothorax", "Rib fracture"],
        )
        assert res["urgency_level"] == "CRITICAL_STAT"
        assert res["requires_stat_radiologist_alert"] is True
        assert "pneumothorax" in res["impression_text"].lower()

    def test_molecular_tumor_board_somatic_matching(self):
        """Tumor Board Agent matches somatic mutations to NCCN Category 1 therapies."""
        res = tumor_board_agent.evaluate_case(
            patient_id="PT-ONC-001",
            patient_name="Alex Mercer",
            cancer_type="Non-Small Cell Lung Cancer (NSCLC)",
            tnm_stage="T3N2M1a (Stage IVA)",
            pathology_summary="Lung adenocarcinoma with metastatic pleural effusion",
            genomic_biomarkers={"EGFR": "L858R Mutated", "KRAS": "Wild Type", "ALK": "Negative"},
            prior_therapies=[],
        )
        assert len(res.proposed_fhir_actions) >= 1
        assert any("Osimertinib" in rec.get("therapy", "") for rec in res.recommendations)
        assert res.epistemic_confidence >= 0.90

    def test_inpatient_nursing_sbar_and_telemetry(self):
        """Nursing Agent synthesizes SBAR handoff with telemetry and ISMP high-alert check."""
        res = nursing_handoff_agent.generate_sbar_handoff(
            patient_id=201,
            patient_name="Evelyn Cross",
            room_number="ICU-04",
            chief_complaint="STEMI s/p PCI with Atrial Fibrillation",
            recent_vitals_summary="BP 118/76, HR 115, AFIB rhythm, SpO2 96%",
            active_iv_lines=["Heparin Infusion @ 1000u/hr"],
            pending_labs=["CBC", "Troponin I q4h"],
        )
        assert res["status"] == "HANDOFF_READY"
        assert "Evelyn Cross" in res["sbar"]["situation"]
        assert "Troponin" in res["sbar"]["recommendation"]

    def test_operational_prior_authorization(self):
        """Prior Authorization Agent audits coverage against LCD criteria and generates packet."""
        res = prior_auth_agent.generate_prior_auth_package(
            patient_id=401,
            patient_name="Robert Taylor",
            requested_procedure_cpt="72148",  # Lumbar Spine MRI
            primary_icd10="M54.5",            # Low back pain
            clinical_justification="Patient has severe radicular low back pain with numbness for 8 weeks.",
            failed_conservative_therapies=["Physical Therapy 6 weeks", "NSAIDs"],
        )
        assert res["submission_status"] == "READY_FOR_SUBMISSION"
        assert res["has_sufficient_evidence"] is True
        assert "72148" in res["prior_auth_package_text"]

    def test_operational_medical_coding_auditor(self):
        """Medical Coding Auditor detects NCCI unbundling and scores compliance status."""
        res = coding_auditor_agent.audit_coding_accuracy(
            clinical_note_text="Routine follow-up for mild headache. Patient has diabetes.",
            assigned_icd10_codes=["R51.9"],
            assigned_cpt_codes=["99215"],  # Upcoded 99215 without documentation
        )
        assert res["is_compliant"] is False
        assert res["audit_status"] == "AUDIT_FLAGGED"
        assert len(res["findings"]) >= 1


# =============================================================================
# TIER 2: EDGE CASES & CLINICAL BOUNDARY STRESS
# =============================================================================

class TestTier2BoundaryStress:
    """Stress tests on physiological edge cases, renal inflection boundaries, and polymedication."""

    def test_renal_clearance_boundary_egfr_thresholds(self):
        """Verify strict behavior at renal cutoff boundaries (eGFR 25 vs 40 mL/min)."""
        # Boundary 1: eGFR = 25 (Metformin contraindicated)
        res_below = prescribing_safety_agent.evaluate_prescription_safety(
            medication_name="Metformin",
            dosage_mg=1000.0,
            egfr=25.0,
        )
        assert res_below["safety_status"] == "REJECTED"
        assert any(w["type"] == "RENAL_CONTRAINDICATION" for w in res_below["warnings"])

        # Boundary 2: eGFR = 40 (Metformin allowed with dose adjustment)
        res_above = prescribing_safety_agent.evaluate_prescription_safety(
            medication_name="Metformin",
            dosage_mg=1000.0,
            egfr=40.0,
        )
        assert res_above["dosage_adjusted"] is True
        assert res_above["recommended_dosage_mg"] <= 500.0

    def test_polymedication_synergistic_qt_prolongation(self):
        """Polymedication regimen triggering synergistic QT-prolongation risk alert."""
        res = prescribing_safety_agent.evaluate_qt_and_drug_disease_risk(
            candidate_medication="Haloperidol",
            active_medications=["Azithromycin"],
            baseline_qtc_ms=480.0,
            serum_potassium_meq_l=3.2,
        )
        assert res["qt_risk_level"] == "HIGH"
        assert any("Torsades de Pointes" in w for w in res["qt_warnings"])
        assert any("Hypokalemia" in w for w in res["qt_warnings"])

    def test_ed_vital_trajectory_inflection(self):
        """ED Triage evaluates sudden Shock Index deterioration."""
        si = ed_triage_agent.evaluate_shock_indices(heart_rate=125.0, systolic_bp=88.0, diastolic_bp=55.0)
        assert si["shock_index"] > 1.0
        assert si["shock_index_status"] in ["ELEVATED_RISK", "CRITICAL_SHOCK"]

        esi = ed_triage_agent.evaluate_esi_triage(
            chief_complaint="Post-op acute abdominal pain",
            heart_rate=125.0,
            systolic_bp=88.0,
            oxygen_sat=94.0,
            respiratory_rate=26.0,
            is_high_risk_situation=True,
        )
        assert esi["esi_level"] <= 2
        assert esi["acuity_category"] in ["IMMEDIATE_RESUSCITATION", "EMERGENT"]


# =============================================================================
# TIER 3: MULTI-AGENT SWARM DELIBERATION & DUNG CONSENSUS
# =============================================================================

class TestTier3SwarmDeliberation:
    """Deliberation across multiple specialist agent responses using Dung's argumentation."""

    def test_virtual_tumor_board_oncology_pharmacology_genetics_consensus(self):
        """MDT Tumor Board deliberates when Pharmacist and Geneticist attack an Attending's proposal."""
        engine = DialecticalConsensusEngine()

        # Attending proposes Gefitinib
        resp_oncologist = ClinicalAgentResponse(
            agent_name="AttendingOncologist",
            recommendations=["Initiate standard first-generation EGFR TKI Gefitinib 250mg daily"],
            epistemic_confidence=0.85,
            proposed_fhir_actions=[
                FHIRMedicationRequestProposal(patient_id="PT-SWARM-MDT", medication_name="Gefitinib", dosage="250mg oral daily")
            ],
        )

        # Geneticist refutes with KRAS G12C mutation causing primary EGFR resistance
        resp_geneticist = ClinicalAgentResponse(
            agent_name="MedicalGeneticist",
            recommendations=["Hold Gefitinib; tumor harbors KRAS G12C mutation conferring absolute EGFR resistance. Proceed with Sotorasib."],
            epistemic_confidence=0.98,
        )

        # Pharmacist flags drug interaction
        resp_pharmacist = ClinicalAgentResponse(
            agent_name="ClinicalPharmacist",
            recommendations=["Hold Gefitinib; concomitant PPI Omeprazole reduces Gefitinib bioavailability by >60%."],
            epistemic_confidence=0.95,
        )

        delib = engine.deliberate_proposals(
            patient_id="PT-SWARM-MDT",
            specialist_responses=[resp_oncologist, resp_geneticist, resp_pharmacist],
        )

        assert delib["consensus_action"] == "SAFETY_HOLD_APPLIED"
        assert len(delib["attacks_evaluated"]) >= 2
        assert len(delib["grounded_consensus_arguments"]) >= 1

        # Defeated arguments must contain the initial inappropriate proposal
        defeated_claims = [a["claim"] for a in delib["defeated_arguments"]]
        assert any("Gefitinib 250mg" in c for c in defeated_claims)

    def test_acute_icu_sepsis_resuscitation_dispute(self):
        """ICU Care team consensus between Critical Care Specialist, Nurse, and Pharmacist."""
        engine = DialecticalConsensusEngine()

        resp_icu = ClinicalAgentResponse(
            agent_name="CriticalCareSpecialist",
            recommendations=["Administer rapid fluid bolus 30 mL/kg and give IV Ceftriaxone 2g"],
            epistemic_confidence=0.90,
        )

        resp_nurse = ClinicalAgentResponse(
            agent_name="InpatientNurse",
            recommendations=["Hold fluid bolus; patient exhibiting acute pulmonary edema with bilateral crackles and BNP > 2000."],
            epistemic_confidence=0.94,
        )

        delib = engine.deliberate_proposals(
            patient_id="PT-SWARM-ICU",
            specialist_responses=[resp_icu, resp_nurse],
        )

        assert delib["consensus_action"] == "SAFETY_HOLD_APPLIED"
        assert any("Inpatient Nurse" in att["justification"] for att in delib["attacks_evaluated"])


# =============================================================================
# TIER 4: CLOSED-LOOP INVARIANT EXECUTION GATE & EPISTEMIC CALIBRATION
# =============================================================================

class TestTier4ClosedLoopInvariantAndCalibration:
    """Closed-loop validation through the deterministic Pre-Action Invariant Gate and Epistemic Calibrator."""

    def test_invariant_gate_blocks_absolute_contraindication(self):
        """Invariant Gate blocks proposed thrombolytic tool call when active hemorrhage is present."""
        gate = PreActionInvariantGate()
        patient = {
            "conditions": ["Acute Ischemic Stroke", "Subdural Hemorrhage"],
            "allergies": [],
            "egfr": 90,
        }
        proposal = FHIRMedicationRequestProposal(
            patient_id="PT-INV-001",
            medication_name="Alteplase",
            dosage="0.9 mg/kg IV",
            indication="Acute stroke",
        )

        verdict = gate.validate_proposal(proposal, patient)
        assert verdict.passed is False
        assert verdict.status == ValidationStatus.REJECT
        assert verdict.barrier_triggered == "ABSOLUTE_CONTRAINDICATION"
        assert len(verdict.violations) >= 1

    def test_invariant_gate_approves_safe_action_with_audit_token(self):
        """Invariant Gate permits safe antibiotic order and issues cryptographic audit token."""
        gate = PreActionInvariantGate()
        patient = {
            "conditions": ["Community Acquired Pneumonia"],
            "current_meds": ["Lisinopril"],
            "egfr": 75.0,
            "platelets": 220000.0,
            "inr": 1.0,
            "is_pregnant": False,
            "allergies": ["Sulfa"],
        }
        proposal = FHIRMedicationRequestProposal(
            patient_id="PT-INV-002",
            medication_name="Azithromycin",
            dosage="500 mg IV daily",
        )

        verdict = gate.validate_proposal(proposal, patient)
        assert verdict.passed is True
        assert verdict.status == ValidationStatus.PASS
        assert verdict.audit_token is not None
        assert len(verdict.audit_token) == 64  # SHA-256 hash

    def test_metacognitive_calibrator_yields_on_high_uncertainty(self):
        """Metacognitive Calibrator halts execution when epistemic uncertainty exceeds safety threshold."""
        calibrator = MetacognitiveCalibrator(default_safe_threshold=0.35)

        # Presentation of chest pain with missing troponin curve and pending ECG
        assessment = calibrator.evaluate_epistemic_confidence(
            clinical_claim="Patient experiencing atypical non-cardiac chest discomfort; safe for immediate outpatient discharge.",
            available_evidence=["Normal BP 120/80", "HR 72 bpm"],
            missing_observations=["High-Sensitivity Troponin I", "12-Lead ECG", "D-Dimer"],
            acuity_level="HIGH",
        )

        assert assessment.autonomous_execution_permitted is False
        assert assessment.yield_decision == "YIELD_TO_HUMAN_CLINICIAN"
        assert assessment.epistemic_uncertainty > 0.35
        assert len(assessment.identified_knowledge_gaps) >= 2
        assert "High-Sensitivity Troponin I" in assessment.identified_knowledge_gaps
        assert assessment.clinician_escalation_brief is not None
        assert "AUTONOMOUS YIELD" in assessment.clinician_escalation_brief["headline"]
