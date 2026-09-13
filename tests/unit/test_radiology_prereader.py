"""
Comprehensive Unit Tests for Multimodal Radiology Pre-Reader Agent
==================================================================
Tests ACR Appropriateness Criteria CDS, Hounsfield Unit density profiling,
structured RADS preliminary impressions, STAT emergency alerts, and FHIR proposals.
"""

import pytest
from backend.agents.radiology_prereader_agent import radiology_prereader_agent


# ── 1. Baseline Pre-Read & Urgency Detection ───────────────────────────────────

def test_generate_pre_read_impression_stat():
    res = radiology_prereader_agent.generate_pre_read_impression(
        modality="CXRAY",
        clinical_indication="Shortness of breath after trauma",
        detected_findings=["Right-sided tension pneumothorax", "Rib fracture"],
    )
    assert res["urgency_level"] == "CRITICAL_STAT"
    assert res["requires_stat_radiologist_alert"] is True
    assert "pneumothorax" in res["impression_text"].lower()


def test_generate_pre_read_impression_routine():
    res = radiology_prereader_agent.generate_pre_read_impression(
        modality="CXRAY",
        clinical_indication="Routine pre-op clearance",
        detected_findings=["Lungs clear without consolidation"],
    )
    assert res["urgency_level"] == "ROUTINE"
    assert res["requires_stat_radiologist_alert"] is False


# ── 2. STAT Critical Alert Triggers ───────────────────────────────────────────

def test_stat_intracranial_hemorrhage():
    is_stat, triggers, urgency = radiology_prereader_agent.detect_stat_critical_findings(
        detected_findings=["Acute left subdural hematoma with 8mm midline shift", "Subfalcine herniation"],
        clinical_indication="Head trauma with sudden lethargy",
    )
    assert is_stat is True
    assert urgency == "CRITICAL_STAT"
    assert any("Intracranial Hemorrhage" in t for t in triggers)


def test_stat_aortic_dissection():
    is_stat, triggers, urgency = radiology_prereader_agent.detect_stat_critical_findings(
        detected_findings=["Stanford Type A aortic dissection with intimal flap extending to root"],
        clinical_indication="Sudden tearing chest pain radiating to back",
    )
    assert is_stat is True
    assert urgency == "CRITICAL_STAT"
    assert any("Aortic Dissection" in t for t in triggers)


def test_stat_saddle_pulmonary_embolism():
    is_stat, triggers, urgency = radiology_prereader_agent.detect_stat_critical_findings(
        detected_findings=["Large saddle pulmonary embolism occluding main pulmonary artery bifurcation", "RV strain pattern"],
        clinical_indication="Syncope and severe dyspnea",
    )
    assert is_stat is True
    assert urgency == "CRITICAL_STAT"
    assert any("Pulmonary Embolism" in t for t in triggers)


def test_stat_pneumoperitoneum():
    is_stat, triggers, urgency = radiology_prereader_agent.detect_stat_critical_findings(
        detected_findings=["Free intraperitoneal air under right hemidiaphragm", "Pneumoperitoneum"],
        clinical_indication="Acute rigid surgical abdomen",
    )
    assert is_stat is True
    assert any("Pneumoperitoneum" in t for t in triggers)


# ── 3. ACR Appropriateness Criteria CDS ───────────────────────────────────────

def test_acr_thunderclap_headache():
    acr_res = radiology_prereader_agent.evaluate_acr_appropriateness(
        clinical_indication="Sudden severe thunderclap headache rule out subarachnoid hemorrhage"
    )
    assert acr_res["rule_matched"] is True
    assert "CT Head without IV contrast" in acr_res["evaluated_procedures"]
    assert acr_res["evaluated_procedures"]["CT Head without IV contrast"]["score"] == 9
    assert acr_res["evaluated_procedures"]["CT Head with IV contrast"]["score"] <= 3


def test_acr_suspected_pulmonary_embolism():
    acr_res = radiology_prereader_agent.evaluate_acr_appropriateness(
        clinical_indication="High pre-test probability suspected pulmonary embolism positive d-dimer"
    )
    assert acr_res["rule_matched"] is True
    assert acr_res["evaluated_procedures"]["CT Pulmonary Angiography (CTPA) Chest with IV contrast"]["score"] == 9
    assert acr_res["evaluated_procedures"]["V/Q Scan (Ventilation-Perfusion)"]["score"] == 8


def test_acr_uncomplicated_low_back_pain():
    acr_res = radiology_prereader_agent.evaluate_acr_appropriateness(
        clinical_indication="Uncomplicated low back pain for 2 weeks without red flags"
    )
    assert acr_res["rule_matched"] is True
    # MRI should not be appropriate initially
    assert acr_res["evaluated_procedures"]["MRI Lumbar Spine without IV contrast"]["score"] == 1
    assert acr_res["evaluated_procedures"]["MRI Lumbar Spine without IV contrast"]["category"] == "Usually Not Appropriate"


# ── 4. Hounsfield Unit (HU) Tissue Attenuation Profiling ──────────────────────

def test_hu_profiling_acute_hemorrhage():
    # Mean HU 68 is acute clotted blood
    profile = radiology_prereader_agent.profile_tissue_density(
        mean_hu=68.0, std_hu=6.0, anatomical_region="BRAIN"
    )
    assert profile["is_acute_blood"] is True
    assert profile["attenuation_category"] == "HYPERDENSE_HEMORRHAGE"
    assert profile["recommended_window_preset"] == "SUBDURAL_BLOOD"
    assert "Acute clotted hemorrhage" in profile["pathology_interpretation"]


def test_hu_profiling_fat_and_fluid():
    # Fat tissue (-75 HU)
    fat_prof = radiology_prereader_agent.profile_tissue_density(mean_hu=-75.0, anatomical_region="ABDOMEN")
    assert fat_prof["attenuation_category"] == "HYPODENSE_FAT"
    assert "FAT" in fat_prof["classified_tissue_type"]

    # Simple fluid (+8 HU)
    fluid_prof = radiology_prereader_agent.profile_tissue_density(mean_hu=8.0, anatomical_region="KIDNEY")
    assert fluid_prof["attenuation_category"] == "FLUID_DENSITY"
    assert "SIMPLE FLUID" in fluid_prof["classified_tissue_type"]


def test_hu_profiling_bone():
    bone_prof = radiology_prereader_agent.profile_tissue_density(mean_hu=850.0, anatomical_region="SPINE")
    assert bone_prof["attenuation_category"] == "DENSE_CALCIFICATION"
    assert bone_prof["recommended_window_preset"] == "BONE"


# ── 5. Structured RADS Report & ClinicalAgentResponse ─────────────────────────

def test_pre_read_and_triage_study_stat_response():
    response = radiology_prereader_agent.pre_read_and_triage_study(
        patient_id="PAT-7781",
        modality="CT_HEAD_NON_CONTRAST",
        clinical_indication="Sudden severe headache with right hemiparesis and lethargy",
        detected_findings=[
            "Hyperdense 45cc right basal ganglia intraparenchymal hemorrhage",
            "6mm midline shift with compression of lateral ventricle",
        ],
        hu_measurements=[{"mean_hu": 65.0, "std_hu": 8.0, "region": "HEAD"}],
    )

    assert response.agent_name == "RadiologyPreReaderAgent"
    assert response.epistemic_confidence >= 0.9
    assert len(response.proposed_fhir_actions) >= 3

    # Check STAT Flag Proposal
    stat_flags = [a for a in response.proposed_fhir_actions if getattr(a, "severity", "") == "critical"]
    assert len(stat_flags) == 1
    assert "STAT RADIOLOGY ALERT" in stat_flags[0].details

    # Check Neurosurgery Consult ServiceRequest
    consult_proposals = [a for a in response.proposed_fhir_actions if getattr(a, "category", "") == "consult"]
    assert len(consult_proposals) == 1
    assert "Neurosurgery" in consult_proposals[0].description
    assert consult_proposals[0].urgency == "stat"

    # Check Hemorrhage Reversal Medication Proposal (Kcentra)
    med_proposals = [a for a in response.proposed_fhir_actions if hasattr(a, "medication_name")]
    assert len(med_proposals) == 1
    assert "Kcentra" in med_proposals[0].medication_name

    # Check dictionary serialization
    res_dict = response.to_dict()
    assert res_dict["agent_name"] == "RadiologyPreReaderAgent"
    assert len(res_dict["proposed_fhir_actions"]) >= 3
