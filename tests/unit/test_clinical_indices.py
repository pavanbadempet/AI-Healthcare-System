from backend.clinical_indices import (
    calculate_egfr_ckd_epi,
    calculate_fib4_index,
    calculate_framingham_risk,
)


def test_calculate_egfr_ckd_epi():
    # 1. Validation error cases (creatinine <= 0 or age < 18)
    assert calculate_egfr_ckd_epi(age=45, gender=1, creatinine=0) is None
    assert calculate_egfr_ckd_epi(age=45, gender=1, creatinine=-0.5) is None
    assert calculate_egfr_ckd_epi(age=17, gender=1, creatinine=1.0) is None

    # 2. Female, low creatinine (<= 0.7)
    # eGFR = 142 * (0.6 / 0.7)^-0.241 * 0.9938^50 * 1.012
    res_female_low = calculate_egfr_ckd_epi(age=50, gender=0, creatinine=0.6)
    assert res_female_low is not None
    assert res_female_low["egfr"] > 90
    assert "G1" in res_female_low["stage"]

    # 3. Female, high creatinine (> 0.7)
    res_female_high = calculate_egfr_ckd_epi(age=60, gender=0, creatinine=2.0)
    assert res_female_high is not None
    assert res_female_high["egfr"] < 35
    assert "G3b" in res_female_high["stage"] or "G4" in res_female_high["stage"]

    # 4. Male, low creatinine (<= 0.9)
    res_male_low = calculate_egfr_ckd_epi(age=40, gender=1, creatinine=0.8)
    assert res_male_low is not None
    assert res_male_low["egfr"] > 90
    assert "G1" in res_male_low["stage"]

    # 5. Male, high creatinine (> 0.9)
    res_male_high = calculate_egfr_ckd_epi(age=65, gender=1, creatinine=3.5)
    assert res_male_high is not None
    assert res_male_high["egfr"] < 20
    assert "G4" in res_male_high["stage"] or "G5" in res_male_high["stage"]


def test_calculate_fib4_index():
    # 1. Validation error cases
    assert calculate_fib4_index(age=45, ast=40, alt=35, platelets=0) is None
    assert calculate_fib4_index(age=45, ast=40, alt=0, platelets=250) is None
    assert calculate_fib4_index(age=45, ast=0, alt=35, platelets=250) is None
    assert calculate_fib4_index(age=0, ast=40, alt=35, platelets=250) is None

    # 2. Low risk patient under 65
    res_low = calculate_fib4_index(age=40, ast=20, alt=25, platelets=300)
    assert res_low is not None
    assert res_low["score"] < 1.30
    assert res_low["risk_level"] == "Low Risk"

    # 3. High risk patient under 65
    res_high = calculate_fib4_index(age=55, ast=150, alt=80, platelets=100)
    assert res_high is not None
    assert res_high["score"] > 2.67
    assert res_high["risk_level"] == "High Risk"

    # 4. Age-dependent thresholds for age >= 65
    # score = (66 * 60) / (250 * sqrt(50)) = 3960 / 1767.76 = ~2.24
    # For < 65, 2.24 would be Indeterminate Risk
    # For >= 65, 2.24 is Indeterminate Risk (cutoff is < 2.0 for low risk)
    res_65_low = calculate_fib4_index(age=66, ast=20, alt=40, platelets=350)
    assert res_65_low is not None
    # score = (66 * 20) / (350 * sqrt(40)) = 1320 / 2213.59 = ~0.60
    assert res_65_low["score"] < 2.00
    assert res_65_low["risk_level"] == "Low Risk"


def test_calculate_framingham_risk():
    # 1. Validation error cases
    assert calculate_framingham_risk(age=0, gender=1, total_chol=200, hdl_chol=50, sbp=120, smoker=0, diabetes=0, hyp_treatment=0) is None
    assert calculate_framingham_risk(age=50, gender=1, total_chol=0, hdl_chol=50, sbp=120, smoker=0, diabetes=0, hyp_treatment=0) is None
    assert calculate_framingham_risk(age=50, gender=1, total_chol=200, hdl_chol=0, sbp=120, smoker=0, diabetes=0, hyp_treatment=0) is None
    assert calculate_framingham_risk(age=50, gender=1, total_chol=200, hdl_chol=50, sbp=0, smoker=0, diabetes=0, hyp_treatment=0) is None

    # 2. Healthy middle-aged male (Low risk)
    res_low = calculate_framingham_risk(
        age=40, gender=1, total_chol=180, hdl_chol=50, sbp=115, smoker=0, diabetes=0, hyp_treatment=0
    )
    assert res_low is not None
    assert res_low["risk_percent"] < 10.0
    assert res_low["risk_level"] == "Low Risk"

    # 3. High risk male (Older, smoker, diabetic, high BP treated)
    res_high = calculate_framingham_risk(
        age=65, gender=1, total_chol=240, hdl_chol=35, sbp=160, smoker=1, diabetes=1, hyp_treatment=1
    )
    assert res_high is not None
    assert res_high["risk_percent"] >= 20.0
    assert res_high["risk_level"] == "High Risk"

    # 4. Female vs Male comparisons
    res_f = calculate_framingham_risk(
        age=55, gender=0, total_chol=210, hdl_chol=45, sbp=135, smoker=1, diabetes=0, hyp_treatment=0
    )
    res_m = calculate_framingham_risk(
        age=55, gender=1, total_chol=210, hdl_chol=45, sbp=135, smoker=1, diabetes=0, hyp_treatment=0
    )
    assert res_f is not None
    assert res_m is not None
    # Both should have elevated risk (>15%) due to smoking, high cholesterol, and elevated SBP
    assert res_f["risk_percent"] > 15.0
    assert res_m["risk_percent"] > 15.0
