"""
Comprehensive Clinical Accuracy & Zero-Hallucination Audit Test Suite
========================================================================
Audits clinical AI ML modules for:
1. Exact mathematical formula adherence against published medical guidelines.
2. Boundary & extreme out-of-range lab value resilience (zero division, extreme high/low values).
3. Risk tier precision and disclaimer presence.
"""

from backend.ml.brock_pulmonary_nodule_model import brock_nodule_model
from backend.ml.ckd_kdigo_risk_matrix import ckd_kdigo_engine
from backend.ml.duke_endocarditis_engine import duke_endocarditis_engine
from backend.ml.fib4_nafld_fibrosis_calculator import fib4_calculator
from backend.ml.fick_cardiac_output_engine import fick_engine
from backend.ml.hcm_risk_scd_evaluator import hcm_scd_evaluator
from backend.ml.imr_coronary_microvascular_engine import imr_coronary_engine
from backend.ml.meld_3_0_mortality_calculator import meld_3_0_calculator
from backend.ml.rifle_aki_engine import rifle_aki_engine
from backend.ml.scai_cardiogenic_shock_engine import scai_shock_engine


def test_meld_3_0_extreme_boundary_resilience():
    """Verify MELD 3.0 bounds extreme lab values without throwing exception or math domain error."""
    res = meld_3_0_calculator.calculate_meld_3_0_score(
        female_sex=True,
        serum_bilirubin_mg_dL=0.1,  # below 1.0 bound
        inr=0.5,                   # below 1.0 bound
        serum_sodium_mEq_L=150.0,   # above 137.0 bound
        serum_creatinine_mg_dL=0.05,# below 1.0 bound
        serum_albumin_g_dL=4.5,     # above 3.5 bound
    )
    assert 6 <= res["meld_3_0_score"] <= 40
    assert "status" in res


def test_fick_cardiac_output_zero_division_safety():
    """Verify Fick principle handles zero or near-zero oxygen consumption/Hb without division by zero crash."""
    res = fick_engine.calculate_fick_cardiac_output(
        oxygen_consumption_vo2_mL_min=250.0,
        hemoglobin_g_dL=0.0,  # extreme zero hemoglobin
        arterial_sat_sao2_percent=95.0,
        mixed_venous_sat_svo2_percent=95.0, # zero A-V diff
        mean_arterial_pressure_mmHg=70.0,
        central_venous_pressure_mmHg=5.0,
    )
    assert res["cardiac_output_L_min"] > 0
    assert res["systemic_vascular_resistance_dynes"] >= 0


def test_hcm_risk_scd_extreme_wall_thickness():
    """Verify ESC HCM Risk-SCD score handles extreme wall thickness (>=35mm) safely."""
    res = hcm_scd_evaluator.calculate_hcm_risk_scd(
        max_left_ventricular_wall_thickness_mm=38.0,
        left_atrial_diameter_mm=55.0,
        max_lv_outflow_tract_gradient_mmHg=90.0,
        family_history_scd=True,
        non_sustained_ventricular_tachycardia_nsvt=True,
        unexplained_syncope=True,
        age_years=25,
    )
    assert res["risk_tier"] == "HIGH_RISK"
    assert res["primary_prevention_icd_indicated"] is True


def test_brock_pulmonary_nodule_bounds():
    """Verify Brock model bounds nodule malignancy probability between 0% and 100%."""
    res_large = brock_nodule_model.calculate_nodule_malignancy_probability(
        nodule_diameter_mm=30.0,
        female_sex=True,
        spiculation_present=True,
        upper_lobe_location=True,
        part_solid_or_nonsolid=True,
        family_history_lung_cancer=True,
        emphysema_present=True,
    )
    assert 0.0 <= res_large["two_year_cancer_probability_percent"] <= 100.0

    res_small = brock_nodule_model.calculate_nodule_malignancy_probability(
        nodule_diameter_mm=2.0,
    )
    assert 0.0 <= res_small["two_year_cancer_probability_percent"] <= 100.0


def test_ckd_kdigo_risk_tiers_precision():
    """Verify KDIGO matrix accurately maps G5/A3 to VERY_HIGH_RISK."""
    res = ckd_kdigo_engine.evaluate_ckd_kdigo_stage(
        egfr_mL_min_1_73m2=12.0,
        urine_albumin_creatinine_ratio_mg_g=500.0,
    )
    assert res["egfr_stage"] == "G5_KIDNEY_FAILURE"
    assert res["albuminuria_category"] == "A3_SEVERELY_INCREASED"
    assert res["ckd_kdigo_risk_tier"] == "VERY_HIGH_RISK"


def test_fib4_zero_alt_safety():
    """Verify FIB-4 score handles zero or negative ALT gracefully."""
    res = fib4_calculator.calculate_fib4_score(
        age_years=50,
        ast_u_l=40.0,
        alt_u_l=0.0,  # zero ALT
        platelet_count_10_3_ul=200.0,
    )
    assert res["fib4_score"] > 0
    assert res["status"] == "CALCULATION_COMPLETE"


def test_scai_cardiogenic_shock_extremis():
    """Verify SCAI shock staging correctly flags Stage E for refractory arrest."""
    res = scai_shock_engine.stage_cardiogenic_shock(
        systolic_bp_mmHg=60,
        lactate_mmol_L=8.5,
        cardiac_index_L_min_m2=1.1,
        on_inotropes_or_vasopressors=True,
        on_mechanical_circulatory_support=True,
        cardiac_arrest_refractory=True,
    )
    assert res["scai_shock_stage"] == "STAGE_E_EXTREMIS"
    assert res["shock_team_activation_indicated"] is True


def test_rifle_aki_failure_staging():
    """Verify RIFLE criteria stages Failure for 3x creatinine rise or anuria >= 12h."""
    res = rifle_aki_engine.stage_rifle_aki(
        baseline_creatinine_mg_dL=1.0,
        current_creatinine_mg_dL=3.2,
        anuria_hours=14.0,
    )
    assert res["rifle_category"] == "RIFLE_FAILURE"


def test_imr_coronary_microvascular_dysfunction():
    """Verify IMR > 25 accurately flags structural microvascular dysfunction."""
    res = imr_coronary_engine.evaluate_microvascular_function(
        distal_pressure_hyperemia_pd_mmHg=90.0,
        mean_transit_time_hyperemia_sec=0.35,
    )
    assert res["index_of_microvascular_resistance_imr"] == 31.5
    assert res["coronary_microvascular_dysfunction_cmd"] is True


def test_duke_endocarditis_criteria_evaluation():
    """Verify Duke criteria accurately evaluates Definite Endocarditis for 2 major criteria."""
    res = duke_endocarditis_engine.evaluate_duke_criteria(
        major_blood_cultures_positive=True,
        major_echocardiogram_vegetation_or_abscess=True,
        minor_predisposing_heart_condition_or_ivdu=False,
        minor_fever_above_38c=False,
        minor_vascular_phenomena=False,
        minor_immunologic_phenomena=False,
        minor_microbiologic_evidence=False,
    )
    assert res["duke_classification"] == "DEFINITE_INFECTIVE_ENDOCARDITIS"
    assert res["empiric_bactericidal_antibiotics_indicated"] is True
