"""
Comprehensive Unit Tests for Emergency Department (ED) Triage & Critical Care Agent
===================================================================================
Tests ESI 1-5 triage, adult & pediatric danger zones, qSOFA, full SOFA, NEWS2,
physiological trajectory dynamics, Surviving Sepsis Campaign bundle, and FHIR proposals.
"""

import pytest
from backend.agents.ed_triage_agent import ed_triage_agent


# ── 1. ESI Level 1 to 5 Tests ──────────────────────────────────────────────────

def test_evaluate_esi_level_1():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Unresponsive",
        heart_rate=160,
        systolic_bp=75,
        oxygen_sat=82,
        respiratory_rate=30,
        is_unresponsive_or_dying=True,
    )
    assert res["esi_level"] == 1
    assert res["acuity_category"] == "IMMEDIATE_RESUSCITATION"
    assert res["target_time_to_physician_min"] == 0
    assert "Resuscitation" in res["recommended_area"]


def test_evaluate_esi_level_1_extreme_vitals():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Severe distress",
        heart_rate=155,
        systolic_bp=70,
        oxygen_sat=80,
        respiratory_rate=36,
    )
    assert res["esi_level"] == 1
    assert res["acuity_category"] == "IMMEDIATE_RESUSCITATION"


def test_evaluate_esi_level_2_high_risk():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Crushing substernal chest pain with diaphoresis",
        heart_rate=95,
        systolic_bp=140,
        oxygen_sat=97,
        respiratory_rate=18,
        is_high_risk_situation=True,
    )
    assert res["esi_level"] == 2
    assert res["acuity_category"] == "EMERGENT"
    assert res["target_time_to_physician_min"] == 10


def test_evaluate_esi_level_2_altered_mental_status():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Found confused on floor",
        heart_rate=88,
        systolic_bp=130,
        oxygen_sat=96,
        respiratory_rate=16,
        confused_lethargic_disoriented=True,
    )
    assert res["esi_level"] == 2
    assert res["acuity_category"] == "EMERGENT"


def test_evaluate_esi_level_3():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Moderate abdominal pain",
        heart_rate=88,
        systolic_bp=128,
        oxygen_sat=98,
        respiratory_rate=16,
        projected_resources_needed=2,
    )
    assert res["esi_level"] == 3
    assert res["acuity_category"] == "URGENT"
    assert res["target_time_to_physician_min"] == 30


def test_evaluate_esi_level_4():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Possible ankle sprain",
        heart_rate=72,
        systolic_bp=120,
        oxygen_sat=99,
        respiratory_rate=14,
        projected_resources_needed=1,
    )
    assert res["esi_level"] == 4
    assert res["acuity_category"] == "LESS_URGENT"
    assert res["target_time_to_physician_min"] == 60


def test_evaluate_esi_level_5():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Medication refill requested",
        heart_rate=70,
        systolic_bp=118,
        oxygen_sat=99,
        respiratory_rate=14,
        projected_resources_needed=0,
    )
    assert res["esi_level"] == 5
    assert res["acuity_category"] == "NON_URGENT"
    assert res["target_time_to_physician_min"] == 120


# ── 2. Pediatric & Adult Vital Danger Zones ─────────────────────────────────────

def test_pediatric_vital_danger_zones():
    # Infant with tachypnea and tachycardia
    in_danger, flags = ed_triage_agent.evaluate_pediatric_vital_danger_zone(
        age_years=0.5, heart_rate=175, respiratory_rate=55, oxygen_sat=95
    )
    assert in_danger is True
    assert any("Infant abnormal HR" in f for f in flags)
    assert any("Infant abnormal RR" in f for f in flags)

    # Normal toddler
    in_danger_norm, _ = ed_triage_agent.evaluate_pediatric_vital_danger_zone(
        age_years=2.0, heart_rate=100, respiratory_rate=24, oxygen_sat=98
    )
    assert in_danger_norm is False

    # Hypoxic school-age child
    in_danger_hypox, flags_hypox = ed_triage_agent.evaluate_pediatric_vital_danger_zone(
        age_years=8.0, heart_rate=90, respiratory_rate=20, oxygen_sat=90
    )
    assert in_danger_hypox is True
    assert any("Hypoxia" in f for f in flags_hypox)


def test_esi_pediatric_uptriage():
    # Child with asthma exacerbation in vital danger zone -> uptriaged to ESI 2
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Wheezing and coughing",
        heart_rate=165,
        systolic_bp=100,
        oxygen_sat=90,
        respiratory_rate=45,
        age_years=3.0,
        projected_resources_needed=2,
    )
    assert res["esi_level"] == 2
    assert res["is_pediatric"] is True


# ── 3. qSOFA Scoring Engine ────────────────────────────────────────────────────

def test_qsofa_scoring_full_positive():
    # Tachypnea + Hypotension + Altered mentation -> 3 points
    res = ed_triage_agent.calculate_qsofa(
        respiratory_rate=24.0,
        systolic_bp=92.0,
        gcs=13,
    )
    assert res["qsofa_score"] == 3
    assert res["high_risk"] is True
    assert res["estimated_mortality_risk_pct"] > 20.0
    assert len(res["criteria_met"]) == 3


def test_qsofa_scoring_negative():
    res = ed_triage_agent.calculate_qsofa(
        respiratory_rate=16.0,
        systolic_bp=124.0,
        gcs=15,
        avpu="A",
    )
    assert res["qsofa_score"] == 0
    assert res["high_risk"] is False
    assert len(res["criteria_met"]) == 0


# ── 4. Full SOFA Scoring Engine ───────────────────────────────────────────────

def test_full_sofa_multiorgan_failure():
    # PaO2/FiO2 = 180 on vent (score 3), Platelets 45 (score 3), Bilirubin 3.5 (score 2),
    # Norepinephrine 0.2 (score 4), GCS 8 (score 3), Creatinine 2.5 (score 2)
    res = ed_triage_agent.calculate_full_sofa(
        pao2=90,
        fio2=0.5,
        is_mechanically_ventilated=True,
        platelets=45.0,
        bilirubin=3.5,
        norepinephrine_dose=0.2,
        gcs=8,
        creatinine=2.5,
    )
    assert res["total_sofa_score"] == 17
    assert res["organ_failures_count"] == 6
    assert res["estimated_icu_mortality_pct"] > 80.0
    assert res["sepsis_organ_dysfunction_confirmed"] is True


def test_full_sofa_normal():
    res = ed_triage_agent.calculate_full_sofa(
        pao2=100,
        fio2=0.21,
        platelets=250.0,
        bilirubin=0.8,
        mean_arterial_pressure=85.0,
        gcs=15,
        creatinine=0.9,
    )
    assert res["total_sofa_score"] == 0
    assert res["organ_failures_count"] == 0
    assert res["sepsis_organ_dysfunction_confirmed"] is False


# ── 5. NEWS2 Scoring Engine ───────────────────────────────────────────────────

def test_news2_scale_1_high_risk():
    # RR 26 (3), SpO2 90% (3), O2 Yes (2), SBP 85 (3), HR 135 (3), ACVPU 'V' (3), Temp 39.2 (2)
    res = ed_triage_agent.calculate_news2(
        respiratory_rate=26,
        oxygen_sat=90,
        hypercapnic_respiratory_failure=False,
        supplemental_oxygen=True,
        systolic_bp=85,
        heart_rate=135,
        consciousness="V",
        temperature_c=39.2,
    )
    assert res["total_news2_score"] >= 15
    assert res["clinical_risk_level"] == "HIGH"
    assert res["has_extreme_single_parameter"] is True


def test_news2_scale_2_copd_target():
    # Patient with hypercapnic respiratory failure target 88-92%
    # SpO2 is 90% on room air -> 0 points on Scale 2
    res = ed_triage_agent.calculate_news2(
        respiratory_rate=18,
        oxygen_sat=90,
        hypercapnic_respiratory_failure=True,
        supplemental_oxygen=False,
        systolic_bp=125,
        heart_rate=78,
        consciousness="A",
        temperature_c=36.8,
    )
    assert res["parameter_scores"]["oxygen_saturation"] == 0
    assert res["total_news2_score"] == 0
    assert res["clinical_risk_level"] == "LOW"


# ── 6. Shock Index & Trajectory Dynamics ──────────────────────────────────────

def test_shock_indices():
    # Tachycardic and hypotensive: HR 115, SBP 85, DBP 50 -> MAP = 61.7
    res = ed_triage_agent.evaluate_shock_indices(heart_rate=115, systolic_bp=85, diastolic_bp=50)
    assert res["shock_index"] > 1.0
    assert res["shock_index_status"] == "CRITICAL_SHOCK"
    assert res["modified_shock_index"] > 1.3
    assert res["hypoperfusion_detected"] is True


def test_trajectory_trend_deteriorating():
    history = [
        {"heart_rate": 85, "systolic_bp": 125, "diastolic_bp": 80},
        {"heart_rate": 105, "systolic_bp": 100, "diastolic_bp": 65},
    ]
    res = ed_triage_agent.evaluate_trajectory_trend(history)
    assert res["trajectory_state"] in ["DETERIORATING", "CRITICAL_COLLAPSE"]
    assert res["delta_map"] < 0
    assert res["delta_hr"] > 0


# ── 7. Surviving Sepsis Campaign (SSC) 1-Hour Bundle ──────────────────────────

def test_ssc_bundle_activated_for_septic_shock():
    res = ed_triage_agent.evaluate_ssc_bundle(
        suspected_infection=True,
        qsofa_score=2,
        mean_arterial_pressure=60.0,
        serum_lactate=4.5,
        patient_weight_kg=70.0,
    )
    assert res["ssc_bundle_activated"] is True
    assert res["crystalloid_volume_ml"] == 2100  # 30 mL/kg * 70 kg
    assert len(res["bundle_actions"]) == 5
    action_types = [a["action"] for a in res["bundle_actions"]]
    assert "MEASURE_LACTATE" in action_types
    assert "OBTAIN_BLOOD_CULTURES" in action_types
    assert "ADMINISTER_ANTIBIOTICS" in action_types
    assert "FLUID_RESUSCITATION" in action_types
    assert "VASOPRESSORS" in action_types


# ── 8. ClinicalAgentResponse & FHIR Proposals ─────────────────────────────────

def test_evaluate_emergency_patient_clinical_response():
    response = ed_triage_agent.evaluate_emergency_patient(
        patient_id="PAT-9912",
        chief_complaint="Fever, altered mental status, and shortness of breath",
        heart_rate=132,
        systolic_bp=82,
        oxygen_sat=88,
        respiratory_rate=28,
        diastolic_bp=48,
        temperature_c=39.5,
        age_years=68,
        avpu="C",
        gcs=12,
        suspected_infection=True,
        serum_lactate=4.2,
        platelets=85.0,
        creatinine=2.1,
    )

    assert response.agent_name == "EmergencyTriageAgent"
    assert response.epistemic_confidence >= 0.8
    assert len(response.proposed_fhir_actions) >= 4

    # Check FHIR action proposals
    flag_proposals = [a for a in response.proposed_fhir_actions if getattr(a, "category", "") == "clinical_alert"]
    assert len(flag_proposals) > 0
    assert any("SEPSIS" in f.details for f in flag_proposals)

    service_proposals = [a for a in response.proposed_fhir_actions if hasattr(a, "code") and hasattr(a, "urgency")]
    assert any("Blood Culture" in s.description for s in service_proposals)

    med_proposals = [a for a in response.proposed_fhir_actions if hasattr(a, "medication_name")]
    assert any("Cefepime" in m.medication_name for m in med_proposals)

    # Test serialization to dict and FHIR
    dict_out = response.to_dict()
    assert "agent_name" in dict_out
    assert "proposed_fhir_actions" in dict_out

    for proposal in response.proposed_fhir_actions:
        if hasattr(proposal, "to_fhir"):
            fhir_json = proposal.to_fhir()
            assert "resourceType" in fhir_json
            assert fhir_json["subject"]["reference"] == "Patient/PAT-9912"
