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
    score.min(100.0)
}
