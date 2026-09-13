/// High-Performance Rust Clinical Score Calculator Module.
/// Provides sub-microsecond calculation of CKD-EPI eGFR, FIB-4 liver fibrosis, and Framingham risk.

#[allow(dead_code)]
pub fn calculate_egfr_ckd_epi(serum_creatinine: f64, age: f64, is_female: bool) -> f64 {
    if serum_creatinine <= 0.0 || age <= 0.0 {
        return 0.0;
    }
    let (kappa, alpha) = if is_female { (0.7, -0.241) } else { (0.9, -0.302) };
    let scr_over_kappa = serum_creatinine / kappa;
    let min_part = scr_over_kappa.min(1.0).powf(alpha);
    let max_part = scr_over_kappa.max(1.0).powf(-1.200);
    let gender_factor = if is_female { 1.012 } else { 1.0 };
    let age_part = 0.9938_f64.powf(age);

    142.0 * min_part * max_part * age_part * gender_factor
}

#[allow(dead_code)]
pub fn calculate_fib4_index(age: f64, ast: f64, alt: f64, platelets: f64) -> f64 {
    if alt <= 0.0 || platelets <= 0.0 {
        return 0.0;
    }
    (age * ast) / (platelets * alt.sqrt())
}

#[allow(dead_code)]
pub fn calculate_framingham_risk_score(age: f64, total_chol: f64, hdl_chol: f64, sbp: f64, smoker: bool) -> f64 {
    let mut score = (age - 30.0) * 0.2;
    if total_chol > 200.0 { score += 2.0; }
    if hdl_chol < 40.0 { score += 2.0; }
    if sbp > 140.0 { score += 3.0; }
    if smoker { score += 4.0; }
    score.clamp(0.0, 100.0)
}

/// Model for End-Stage Liver Disease (MELD) Score
/// Evaluates mortality in end-stage chronic liver disease.
#[allow(dead_code)]
pub fn calculate_meld_score(bilirubin_mg_dl: f64, inr: f64, creatinine_mg_dl: f64, on_dialysis: bool) -> f64 {
    let bili = bilirubin_mg_dl.max(1.0);
    let inr_val = inr.max(1.0);
    let creat = if on_dialysis { 4.0 } else { creatinine_mg_dl.clamp(1.0, 4.0) };

    let meld_raw = (9.57 * creat.ln()) + (3.78 * bili.ln()) + (11.20 * inr_val.ln()) + 6.43;
    meld_raw.round().clamp(6.0, 40.0)
}

/// 10-Year Atherosclerotic Cardiovascular Disease (ASCVD) Risk Estimator
/// Pooled Cohort Equations approximation for primary prevention.
#[allow(dead_code)]
pub fn calculate_ascvd_risk(
    age: f64,
    total_chol: f64,
    hdl_chol: f64,
    sbp: f64,
    treated_bp: bool,
    smoker: bool,
    diabetic: bool,
    is_female: bool,
) -> f64 {
    if age < 20.0 || age > 79.0 {
        return 0.0;
    }

    let mut points = 0.0;
    // Age points
    points += (age - 40.0) * 0.4;

    // Lipid ratios
    let ratio = total_chol / hdl_chol.max(1.0);
    if ratio > 5.0 { points += 3.0; }
    else if ratio > 4.0 { points += 1.5; }

    // Blood pressure
    if sbp >= 160.0 { points += if treated_bp { 4.0 } else { 3.0 }; }
    else if sbp >= 140.0 { points += if treated_bp { 2.5 } else { 1.5 }; }
    else if sbp >= 130.0 { points += 1.0; }

    // Risk factors
    if smoker { points += 3.0; }
    if diabetic { points += 2.5; }
    if !is_female { points += 1.0; } // Male gender demographic factor

    // Sigmoid calibration to percentage
    let risk_pct = (1.0 / (1.0 + (-0.25 * (points - 10.0)).exp())) * 100.0;
    risk_pct.clamp(0.1, 99.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_meld_bounds_and_dialysis() {
        // Normal baseline
        let meld_normal = calculate_meld_score(0.8, 1.0, 0.9, false);
        assert_eq!(meld_normal, 6.0); // Clamped floor

        // Severe liver failure on dialysis
        let meld_severe = calculate_meld_score(4.5, 2.8, 3.2, true);
        assert!(meld_severe >= 30.0 && meld_severe <= 40.0);
    }

    #[test]
    fn test_ascvd_risk_demographics() {
        // Low-risk young non-smoker
        let low_risk = calculate_ascvd_risk(35.0, 170.0, 55.0, 115.0, false, false, false, true);
        assert!(low_risk < 15.0);

        // High-risk older diabetic smoker with hypertension
        let high_risk = calculate_ascvd_risk(65.0, 260.0, 32.0, 165.0, true, true, true, false);
        assert!(high_risk > 50.0);
    }
}
