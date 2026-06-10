import math
from typing import Any, Dict, Optional


def calculate_egfr_ckd_epi(age: float, gender: int, creatinine: float) -> Optional[Dict[str, Any]]:
    """
    Calculates Estimated Glomerular Filtration Rate (eGFR) using the race-free 2021 CKD-EPI equation.

    Parameters:
    -----------
    age : float
        Age of the patient in years (must be >= 18).
    gender : int
        0: Female, 1: Male
    creatinine : float
        Serum Creatinine level in mg/dL (must be > 0).

    Returns:
    --------
    dict: A dictionary containing:
        - "egfr": float (rounded to 1 decimal place)
        - "stage": str (CKD classification stage)
        - "description": str (meaning of the stage)
    Or None if input validation fails.
    """
    if creatinine <= 0 or age < 18:
        return None

    # Constants based on gender
    if gender == 0:  # Female
        kappa = 0.7
        alpha = -0.241
        gender_factor = 1.012
    else:  # Male (and fallback default)
        kappa = 0.9
        alpha = -0.302
        gender_factor = 1.0

    # Calculate min/max components
    cr_kappa_ratio = creatinine / kappa
    min_term = min(cr_kappa_ratio, 1.0)
    max_term = max(cr_kappa_ratio, 1.0)

    # eGFR = 142 * min(Cr/K, 1)^alpha * max(Cr/K, 1)^-1.200 * 0.9938^Age * gender_factor
    egfr = 142 * (min_term ** alpha) * (max_term ** -1.200) * (0.9938 ** age) * gender_factor
    egfr_rounded = round(egfr, 1)

    # CKD Staging classification
    if egfr_rounded >= 90:
        stage = "Stage G1"
        desc = "Normal or high"
    elif egfr_rounded >= 60:
        stage = "Stage G2"
        desc = "Mildly decreased"
    elif egfr_rounded >= 45:
        stage = "Stage G3a"
        desc = "Mildly to moderately decreased"
    elif egfr_rounded >= 30:
        stage = "Stage G3b"
        desc = "Moderately to severely decreased"
    elif egfr_rounded >= 15:
        stage = "Stage G4"
        desc = "Severely decreased"
    else:
        stage = "Stage G5"
        desc = "Kidney failure"

    return {
        "egfr": egfr_rounded,
        "stage": stage,
        "description": desc
    }


def calculate_fib4_index(age: float, ast: float, alt: float, platelets: float) -> Optional[Dict[str, Any]]:
    """
    Calculates Fibrosis-4 (FIB-4) Index for assessing liver fibrosis.

    Parameters:
    -----------
    age : float
        Age in years.
    ast : float
        Aspartate Aminotransferase in U/L.
    alt : float
        Alanine Aminotransferase in U/L.
    platelets : float
        Platelet count in 10^9/L.

    Returns:
    --------
    dict: A dictionary containing:
        - "score": float (rounded to 2 decimal places)
        - "risk_level": str (Low, Indeterminate, High)
        - "description": str (detailed clinical interpretation)
    Or None if input validation fails.
    """
    if platelets <= 0 or alt <= 0 or ast <= 0 or age <= 0:
        return None

    # FIB-4 = (Age * AST) / (Platelets * sqrt(ALT))
    fib4 = (age * ast) / (platelets * math.sqrt(alt))
    score = round(fib4, 2)

    # Risk threshold classifications (age-dependent cutoffs)
    if age < 65:
        if score < 1.30:
            risk_level = "Low Risk"
            desc = "Advanced fibrosis excluded (Negative Predictive Value > 90%)"
        elif score <= 2.67:
            risk_level = "Indeterminate Risk"
            desc = "Biopsy or transient elastography recommended for confirmation"
        else:
            risk_level = "High Risk"
            desc = "Advanced fibrosis likely (Positive Predictive Value ~ 65-80%)"
    else:
        # Age >= 65 cutoff shifts the lower boundary to 2.0 to avoid false positives
        if score < 2.00:
            risk_level = "Low Risk"
            desc = "Advanced fibrosis excluded (adjusted threshold for age >= 65)"
        elif score <= 2.67:
            risk_level = "Indeterminate Risk"
            desc = "Biopsy or transient elastography recommended for confirmation"
        else:
            risk_level = "High Risk"
            desc = "Advanced fibrosis likely (Positive Predictive Value ~ 65-80%)"

    return {
        "score": score,
        "risk_level": risk_level,
        "description": desc
    }


def calculate_framingham_risk(
    age: float,
    gender: int,
    total_chol: float,
    hdl_chol: float,
    sbp: float,
    smoker: int,
    diabetes: int,
    hyp_treatment: int
) -> Optional[Dict[str, Any]]:
    """
    Calculates 10-year risk of general cardiovascular disease using the 2008 Framingham Study model.

    Parameters:
    -----------
    age : float
        Age in years (model validated for age 30-74).
    gender : int
        0: Female, 1: Male
    total_chol : float
        Total cholesterol in mg/dL.
    hdl_chol : float
        HDL cholesterol in mg/dL.
    sbp : float
        Systolic Blood Pressure in mmHg.
    smoker : int
        0: Non-smoker, 1: Smoker
    diabetes : int
        0: No, 1: Yes
    hyp_treatment : int
        0: Untreated, 1: Treated (taking hypertension medication)

    Returns:
    --------
    dict: A dictionary containing:
        - "risk_percent": float (10-year risk percentage, rounded to 1 decimal place)
        - "risk_level": str (Low, Intermediate, High)
        - "description": str (clinical interpretation)
    Or None if input validation fails.
    """
    # Safe validation bounds (Framingham equations require positive inputs)
    if age <= 0 or total_chol <= 0 or hdl_chol <= 0 or sbp <= 0:
        return None

    # Clamp age to valid FRS bounds to prevent extreme extrapolation
    clamped_age = max(30.0, min(74.0, age))

    ln_age = math.log(clamped_age)
    ln_total_chol = math.log(total_chol)
    ln_hdl_chol = math.log(hdl_chol)
    ln_sbp = math.log(sbp)

    if gender == 0:  # Female
        mean_sum = 26.0145
        baseline_survival = 0.94833

        # Beta coefficients
        b_age = 2.72107
        b_total_chol = 0.81734
        b_hdl_chol = -0.27634
        b_sbp = 2.88267 if hyp_treatment == 1 else 2.81291
        b_smoker = 0.61868
        b_diabetes = 0.77763

    else:  # Male
        mean_sum = 23.9388
        baseline_survival = 0.88431

        # Beta coefficients
        b_age = 3.06117
        b_total_chol = 1.12370
        b_hdl_chol = -0.93267
        b_sbp = 1.99881 if hyp_treatment == 1 else 1.93303
        b_smoker = 0.70953
        b_diabetes = 0.53160

    # Sum of beta * value
    coeff_sum = (
        (b_age * ln_age) +
        (b_total_chol * ln_total_chol) +
        (b_hdl_chol * ln_hdl_chol) +
        (b_sbp * ln_sbp) +
        (b_smoker * float(smoker)) +
        (b_diabetes * float(diabetes))
    )

    # Risk calculation: 1 - baseline_survival ^ exp(coeff_sum - mean_sum)
    try:
        power = math.exp(coeff_sum - mean_sum)
        risk = 1.0 - (baseline_survival ** power)
        risk_percent = round(risk * 100.0, 1)
    except OverflowError:
        # Prevent math overflow for extreme values
        risk_percent = 99.9

    # Risk level classification
    if risk_percent < 10.0:
        risk_level = "Low Risk"
        desc = "10-year risk of cardiovascular event is under 10%"
    elif risk_percent < 20.0:
        risk_level = "Intermediate Risk"
        desc = "10-year risk of cardiovascular event is between 10% and 20%"
    else:
        risk_level = "High Risk"
        desc = "10-year risk of cardiovascular event is 20% or higher"

    return {
        "risk_percent": risk_percent,
        "risk_level": risk_level,
        "description": desc
    }
