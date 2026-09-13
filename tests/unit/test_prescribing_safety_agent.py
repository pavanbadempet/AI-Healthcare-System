"""
Comprehensive Unit Tests for Precision Pharmacotherapy & Toxicology Agent
=========================================================================
Tests multi-drug DDI, CPIC pharmacogenomics, Beers Criteria (2023), Cockcroft-Gault
CrCl renal adjustment matrix, synergistic QT prolongation, and FHIR action proposals.
"""

import pytest
from backend.agents.prescribing_safety_agent import prescribing_safety_agent


# ── 1. Baseline Safety & DDI Tests ─────────────────────────────────────────────

def test_evaluate_prescription_safe():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Amoxicillin",
        dosage_mg=500,
        egfr=90.0,
        active_medications=["Vitamin D"],
    )
    assert res["safety_status"] == "SAFE"
    assert len(res["warnings"]) == 0


def test_evaluate_prescription_renal_warning():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Metformin",
        dosage_mg=1000,
        egfr=25.0,
        active_medications=[],
    )
    assert res["safety_status"] == "REJECTED"
    assert res["warnings"][0]["type"] == "RENAL_CONTRAINDICATION"


def test_evaluate_prescription_drug_interaction():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Lisinopril",
        dosage_mg=10,
        egfr=80.0,
        active_medications=["Spironolactone"],
    )
    assert res["safety_status"] == "REJECTED"
    assert res["warnings"][0]["type"] == "DRUG_INTERACTION"


def test_ddi_methotrexate_nsaid_critical():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Methotrexate",
        dosage_mg=15,
        egfr=85.0,
        active_medications=["Ibuprofen"],
    )
    assert res["safety_status"] == "REJECTED"
    assert any("pancytopenia" in w["message"].lower() for w in res["warnings"])


def test_ddi_sildenafil_nitrate_absolute_contraindication():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Sildenafil",
        dosage_mg=50,
        active_medications=["Nitroglycerin"],
    )
    assert res["safety_status"] == "REJECTED"
    assert any("refractory hypotension" in w["message"].lower() for w in res["warnings"])


def test_ddi_simvastatin_amiodarone_rhabdomyolysis():
    res = prescribing_safety_agent.evaluate_prescription_safety(
        medication_name="Simvastatin",
        dosage_mg=40,
        active_medications=["Amiodarone"],
    )
    assert res["safety_status"] == "REJECTED"
    assert any("rhabdomyolysis" in w["message"].lower() for w in res["warnings"])


# ── 2. Cockcroft-Gault CrCl & Renal Adjustment Matrix ──────────────────────────

def test_cockcroft_gault_formula():
    # 70yo male, 72kg, SCr 1.0 mg/dL -> (140 - 70) * 72 / (72 * 1.0) = 70.0 mL/min
    crcl_male = prescribing_safety_agent.calculate_cockcroft_gault_crcl(
        age_years=70.0, weight_kg=72.0, serum_creatinine_mg_dl=1.0, is_female=False
    )
    assert crcl_male == 70.0

    # Same parameters for female -> 70.0 * 0.85 = 59.5 mL/min
    crcl_female = prescribing_safety_agent.calculate_cockcroft_gault_crcl(
        age_years=70.0, weight_kg=72.0, serum_creatinine_mg_dl=1.0, is_female=True
    )
    assert crcl_female == 59.5


def test_renal_dosage_matrix_cefepime_neurotoxicity():
    # Severe renal impairment CrCl < 11 mL/min
    res = prescribing_safety_agent.evaluate_renal_dosage_matrix(
        medication_name="Cefepime", dosage_mg=2000, crcl_ml_min=8.0
    )
    assert res["dosage_adjusted"] is True
    assert "1g" in res["recommended_regimen"]
    assert any("status epilepticus" in w.lower() or "neurotoxicity" in w.lower() for w in res["renal_warnings"])


def test_renal_dosage_matrix_enoxaparin_severe_renal():
    res = prescribing_safety_agent.evaluate_renal_dosage_matrix(
        medication_name="Enoxaparin", dosage_mg=80, crcl_ml_min=22.0
    )
    assert res["dosage_adjusted"] is True
    assert "24 hours" in res["recommended_regimen"]


def test_renal_dosage_matrix_rivaroxaban_contraindication():
    res = prescribing_safety_agent.evaluate_renal_dosage_matrix(
        medication_name="Rivaroxaban", dosage_mg=20, crcl_ml_min=12.0
    )
    assert res["is_contraindicated"] is True


# ── 3. Pharmacogenomics (CPIC Level A) ──────────────────────────────────────────

def test_cpic_cyp2c19_clopidogrel_poor_metabolizer():
    findings = prescribing_safety_agent.evaluate_pharmacogenomics(
        medication_name="Clopidogrel",
        patient_genotypes={"cyp2c19": "*2/*2"},
    )
    assert len(findings) == 1
    assert findings[0]["phenotype"] == "Poor Metabolizer"
    assert findings[0]["severity"] == "CRITICAL"
    assert "Ticagrelor" in findings[0]["recommendation"] or "Prasugrel" in findings[0]["recommendation"]


def test_cpic_cyp2d6_codeine_ultrarapid():
    findings = prescribing_safety_agent.evaluate_pharmacogenomics(
        medication_name="Codeine",
        patient_genotypes={"cyp2d6": "*1/*1xN"},
    )
    assert len(findings) == 1
    assert findings[0]["phenotype"] == "Ultrarapid Metabolizer"
    assert "respiratory depression" in findings[0]["recommendation"].lower()


def test_cpic_slco1b1_simvastatin_myopathy():
    findings = prescribing_safety_agent.evaluate_pharmacogenomics(
        medication_name="Simvastatin",
        patient_genotypes={"slco1b1": "521CC"},
    )
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"
    assert "rhabdomyolysis" in findings[0]["recommendation"].lower()


def test_cpic_hla_b_5701_abacavir_hypersensitivity():
    findings = prescribing_safety_agent.evaluate_pharmacogenomics(
        medication_name="Abacavir",
        patient_genotypes={"hla_b_5701": "Positive"},
    )
    assert len(findings) == 1
    assert findings[0]["actionability"] == "CPIC_LEVEL_A_CONTRAINDICATION"
    assert findings[0]["severity"] == "CRITICAL"


# ── 4. Beers Criteria (2023 AGS) ───────────────────────────────────────────────

def test_beers_criteria_geriatric_antihistamine():
    # 75-year-old prescribed diphenhydramine
    finding = prescribing_safety_agent.evaluate_beers_criteria(
        medication_name="Diphenhydramine",
        patient_age_years=75.0,
    )
    assert finding is not None
    assert finding["is_beers_pim"] is True
    assert "Anticholinergic" in finding["category"]


def test_beers_criteria_non_geriatric():
    # 45-year-old prescribed diphenhydramine -> not flagged by Beers
    finding = prescribing_safety_agent.evaluate_beers_criteria(
        medication_name="Diphenhydramine",
        patient_age_years=45.0,
    )
    assert finding is None


# ── 5. Synergistic QT Prolongation & Drug-Disease ──────────────────────────────

def test_synergistic_qt_prolongation():
    res = prescribing_safety_agent.evaluate_qt_and_drug_disease_risk(
        candidate_medication="Haloperidol",
        active_medications=["Azithromycin"],
        baseline_qtc_ms=480.0,
        serum_potassium_meq_l=3.2,  # Hypokalemia
    )
    assert res["qt_risk_level"] == "HIGH"
    assert len(res["qt_prolonging_drugs_active"]) == 2
    assert any("Torsades de Pointes" in w for w in res["qt_warnings"])
    assert any("Hypokalemia" in w for w in res["qt_warnings"])


def test_drug_disease_contraindication_asthma():
    res = prescribing_safety_agent.evaluate_qt_and_drug_disease_risk(
        candidate_medication="Propranolol",
        active_medications=[],
        patient_conditions=["Severe Asthma"],
    )
    assert len(res["drug_disease_contraindications"]) == 1
    assert res["drug_disease_contraindications"][0]["condition"] == "Severe Asthma / Reactive Airway"


# ── 6. ClinicalAgentResponse & FHIR Proposals ─────────────────────────────────

def test_evaluate_clinical_pharmacotherapy_response():
    response = prescribing_safety_agent.evaluate_clinical_pharmacotherapy(
        patient_id="PAT-5532",
        medication_name="Clopidogrel",
        dosage_mg=75,
        patient_age_years=68.0,
        patient_weight_kg=75.0,
        serum_creatinine_mg_dl=1.1,
        active_medications=["Omeprazole", "Aspirin"],
        patient_genotypes={"cyp2c19": "*2/*2"},
    )

    assert response.agent_name == "PrescribingSafetyAgent"
    assert response.epistemic_confidence >= 0.9
    assert len(response.proposed_fhir_actions) >= 2

    # Proposes alternative Ticagrelor
    med_proposals = [a for a in response.proposed_fhir_actions if getattr(a, "medication_name", "") == "Ticagrelor"]
    assert len(med_proposals) == 1
    assert med_proposals[0].dosage == "90 mg"

    # Flag proposal for CYP2C19 Poor Metabolizer and DDI
    flags = [a for a in response.proposed_fhir_actions if getattr(a, "category", "") == "clinical_alert"]
    assert len(flags) > 0

    # Verify serialization
    dict_repr = response.to_dict()
    assert dict_repr["agent_name"] == "PrescribingSafetyAgent"
    assert len(dict_repr["proposed_fhir_actions"]) >= 2
