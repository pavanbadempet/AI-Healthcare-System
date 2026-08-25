use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EgfrResult {
    pub egfr: f64,
    pub stage: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Fib4Result {
    pub score: f64,
    pub risk_level: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FraminghamResult {
    pub risk_percent: f64,
    pub risk_level: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QsofaResult {
    pub score: i32,
    pub risk_level: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cha2ds2VascResult {
    pub score: i32,
    pub annual_stroke_risk_percent: f64,
    pub recommendation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeldResult {
    pub score: f64,
    pub mortality_3_month_percent: f64,
    pub risk_category: String,
}

/// Calculates Estimated Glomerular Filtration Rate (eGFR) using the race-free 2021 CKD-EPI equation.
pub fn calculate_egfr_ckd_epi(serum_creatinine: f64, age: f64, is_female: bool) -> Option<EgfrResult> {
    if serum_creatinine <= 0.0 || age < 18.0 {
        return None;
    }

    let (kappa, alpha) = if is_female { (0.7, -0.241) } else { (0.9, -0.302) };
    let scr_over_kappa = serum_creatinine / kappa;
    let min_part = scr_over_kappa.min(1.0).powf(alpha);
    let max_part = scr_over_kappa.max(1.0).powf(-1.200);
    let gender_factor = if is_female { 1.012 } else { 1.0 };
    let age_part = 0.9938_f64.powf(age);

    let egfr_val = 142.0 * min_part * max_part * age_part * gender_factor;
    let egfr_rounded = (egfr_val * 10.0).round() / 10.0;

    let (stage, desc) = if egfr_rounded >= 90.0 {
        ("Stage G1", "Normal or high")
    } else if egfr_rounded >= 60.0 {
        ("Stage G2", "Mildly decreased")
    } else if egfr_rounded >= 45.0 {
        ("Stage G3a", "Mildly to moderately decreased")
    } else if egfr_rounded >= 30.0 {
        ("Stage G3b", "Moderately to severely decreased")
    } else if egfr_rounded >= 15.0 {
        ("Stage G4", "Severely decreased")
    } else {
        ("Stage G5", "Kidney failure")
    };

    Some(EgfrResult {
        egfr: egfr_rounded,
        stage: stage.to_string(),
        description: desc.to_string(),
    })
}

/// Calculates Fibrosis-4 (FIB-4) Index for assessing liver fibrosis.
pub fn calculate_fib4_index(age: f64, ast: f64, alt: f64, platelets: f64) -> Option<Fib4Result> {
    if platelets <= 0.0 || alt <= 0.0 || ast <= 0.0 || age <= 0.0 {
        return None;
    }

    let score_raw = (age * ast) / (platelets * alt.sqrt());
    let score = (score_raw * 100.0).round() / 100.0;

    let (risk_level, desc) = if age < 65.0 {
        if score < 1.30 {
            ("Low Risk", "Advanced fibrosis excluded (Negative Predictive Value > 90%)")
        } else if score <= 2.67 {
            ("Indeterminate Risk", "Biopsy or transient elastography recommended for confirmation")
        } else {
            ("High Risk", "Advanced fibrosis likely (Positive Predictive Value ~ 65-80%)")
        }
    } else {
        if score < 2.00 {
            ("Low Risk", "Advanced fibrosis excluded (adjusted threshold for age >= 65)")
        } else if score <= 2.67 {
            ("Indeterminate Risk", "Biopsy or transient elastography recommended for confirmation")
        } else {
            ("High Risk", "Advanced fibrosis likely (Positive Predictive Value ~ 65-80%)")
        }
    };

    Some(Fib4Result {
        score,
        risk_level: risk_level.to_string(),
        description: desc.to_string(),
    })
}

/// Calculates 10-year risk of general cardiovascular disease using the 2008 Framingham Study model.
pub fn calculate_framingham_risk(
    age: f64,
    is_female: bool,
    total_chol: f64,
    hdl_chol: f64,
    sbp: f64,
    smoker: bool,
    diabetes: bool,
    hyp_treatment: bool,
) -> Option<FraminghamResult> {
    if age <= 0.0 || total_chol <= 0.0 || hdl_chol <= 0.0 || sbp <= 0.0 {
        return None;
    }

    let clamped_age = age.max(30.0).min(74.0);
    let ln_age = clamped_age.ln();
    let ln_tc = total_chol.ln();
    let ln_hdl = hdl_chol.ln();
    let ln_sbp = sbp.ln();

    let (mean_sum, baseline, coeff_sum): (f64, f64, f64) = if is_female {
        let ms: f64 = 26.0145;
        let bl: f64 = 0.94833;
        let sbp_coeff = if hyp_treatment { 2.88267 } else { 2.81291 };
        let cs = (2.72107 * ln_age)
            + (0.81734 * ln_tc)
            + (-0.27634 * ln_hdl)
            + (sbp_coeff * ln_sbp)
            + (0.61868 * (if smoker { 1.0 } else { 0.0 }))
            + (0.77763 * (if diabetes { 1.0 } else { 0.0 }));
        (ms, bl, cs)
    } else {
        let ms = 23.9388;
        let bl = 0.88431;
        let sbp_coeff = if hyp_treatment { 1.99881 } else { 1.93303 };
        let cs = (3.06117 * ln_age)
            + (1.12370 * ln_tc)
            + (-0.93267 * ln_hdl)
            + (sbp_coeff * ln_sbp)
            + (0.70953 * (if smoker { 1.0 } else { 0.0 }))
            + (0.53160 * (if diabetes { 1.0 } else { 0.0 }));
        (ms, bl, cs)
    };

    let exponent = (coeff_sum - mean_sum).exp();
    let risk = 1.0 - baseline.powf(exponent);
    let risk_percent = ((risk * 100.0).clamp(0.1, 99.9) * 10.0).round() / 10.0;

    let (risk_level, desc) = if risk_percent < 10.0 {
        ("Low Risk", "10-year risk of cardiovascular event is under 10%")
    } else if risk_percent < 20.0 {
        ("Intermediate Risk", "10-year risk of cardiovascular event is between 10% and 20%")
    } else {
        ("High Risk", "10-year risk of cardiovascular event is 20% or higher")
    };

    Some(FraminghamResult {
        risk_percent,
        risk_level: risk_level.to_string(),
        description: desc.to_string(),
    })
}

/// Evaluates Quick Sepsis-related Organ Failure Assessment (qSOFA).
pub fn calculate_qsofa(respiratory_rate: f64, systolic_bp: f64, gcs_score: f64) -> QsofaResult {
    let mut score = 0;
    if respiratory_rate >= 22.0 {
        score += 1;
    }
    if systolic_bp <= 100.0 {
        score += 1;
    }
    if gcs_score < 15.0 {
        score += 1;
    }

    let (risk, desc) = if score >= 2 {
        ("HIGH_SEPSIS_RISK", "High risk of poor outcome or septic shock; consider ICU transfer.")
    } else if score == 1 {
        ("ELEVATED_RISK", "Elevated risk; frequent monitoring recommended.")
    } else {
        ("LOW_RISK", "Low acute organ dysfunction risk.")
    };

    QsofaResult {
        score,
        risk_level: risk.to_string(),
        description: desc.to_string(),
    }
}

/// Computes CHA2DS2-VASc score for atrial fibrillation stroke risk stratification.
pub fn calculate_cha2ds2_vasc(
    age: f64,
    is_female: bool,
    chf: bool,
    hypertension: bool,
    stroke_history: bool,
    vascular_disease: bool,
    diabetes: bool,
) -> Cha2ds2VascResult {
    let mut score = 0;
    if chf { score += 1; }
    if hypertension { score += 1; }
    if age >= 75.0 {
        score += 2;
    } else if age >= 65.0 {
        score += 1;
    }
    if diabetes { score += 1; }
    if stroke_history { score += 2; }
    if vascular_disease { score += 1; }
    if is_female { score += 1; }

    let (risk_pct, rec) = match score {
        0 => (0.2, "Low stroke risk. No anticoagulation recommended."),
        1 => (0.6, "Low-moderate risk. Anticoagulation may be considered."),
        2 => (2.2, "Moderate-high risk. Oral anticoagulation recommended."),
        3 => (3.2, "High risk. Oral anticoagulation indicated."),
        4 => (4.8, "High risk. Oral anticoagulation indicated."),
        5 => (7.2, "Very high risk. Oral anticoagulation indicated."),
        6 => (9.7, "Very high risk. Oral anticoagulation indicated."),
        7 => (11.2, "Extreme risk. Strict oral anticoagulation indicated."),
        8 => (12.5, "Extreme risk. Strict oral anticoagulation indicated."),
        _ => (15.0, "Maximum risk. Strict oral anticoagulation indicated."),
    };

    Cha2ds2VascResult {
        score,
        annual_stroke_risk_percent: risk_pct,
        recommendation: rec.to_string(),
    }
}

/// Computes MELD score (Model for End-Stage Liver Disease, 2016 race-free/UNOS formula).
pub fn calculate_meld_score(
    creatinine: f64,
    bilirubin: f64,
    inr: f64,
    on_dialysis: bool,
) -> MeldResult {
    let cr = if on_dialysis { 4.0 } else { creatinine.clamp(1.0, 4.0) };
    let bili = bilirubin.max(1.0);
    let inr_val = inr.max(1.0);

    let meld_raw = (9.57 * cr.ln()) + (3.78 * bili.ln()) + (11.20 * inr_val.ln()) + 6.43;
    let score = (meld_raw * 10.0).round() / 10.0;

    let (mortality, cat) = if score < 10.0 {
        (1.9, "Low (3-month mortality < 2%)")
    } else if score < 20.0 {
        (6.0, "Moderate (3-month mortality ~ 6%)")
    } else if score < 30.0 {
        (19.6, "High (3-month mortality ~ 20%)")
    } else if score < 40.0 {
        (52.6, "Very High (3-month mortality ~ 50%)")
    } else {
        (71.3, "Critical (3-month mortality > 70%)")
    };

    MeldResult {
        score,
        mortality_3_month_percent: mortality,
        risk_category: cat.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_egfr_male_female_bounds() {
        let female_res = calculate_egfr_ckd_epi(0.6, 50.0, true).unwrap();
        assert!(female_res.egfr > 90.0);
        assert_eq!(female_res.stage, "Stage G1");

        let male_res = calculate_egfr_ckd_epi(1.4, 65.0, false).unwrap();
        assert!(male_res.egfr < 60.0);
        assert!(male_res.stage.starts_with("Stage G3"));
    }

    #[test]
    fn test_fib4_index_calculation() {
        let res = calculate_fib4_index(55.0, 45.0, 35.0, 220.0).unwrap();
        // (55 * 45) / (220 * sqrt(35)) = 2475 / (220 * 5.916) = 2475 / 1301.53 = 1.90
        assert!((res.score - 1.90).abs() < 0.05);
        assert_eq!(res.risk_level, "Indeterminate Risk");
    }

    #[test]
    fn test_framingham_risk_calculation() {
        let res = calculate_framingham_risk(55.0, false, 240.0, 45.0, 140.0, true, false, false).unwrap();
        assert!(res.risk_percent > 10.0);
        assert!(res.risk_level == "Intermediate Risk" || res.risk_level == "High Risk");
    }
}
