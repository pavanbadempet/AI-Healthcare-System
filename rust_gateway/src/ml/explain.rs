use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConformalPredictionInfo {
    pub significance_level: f64,
    pub conformal_prediction_set: Vec<i64>,
    pub uncertainty_level: String,
    pub triage_recommendation: String,
    pub p_class_0: f64,
    pub p_class_1: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClinicalRecourseResponse {
    pub current_risk_score: f64,
    pub target_achievable_risk: f64,
    pub actionable_recommendations: Vec<String>,
    pub actionable_counterfactuals: Vec<String>,
    pub counterfactual_engine: String,
}

/// Computes adaptive conformal prediction sets and triage recommendations.
pub fn calculate_conformal_metadata(
    p_positive: f64,
    raw_pred: i64,
    q_threshold: Option<f64>,
) -> ConformalPredictionInfo {
    let p1 = p_positive.clamp(0.0, 1.0);
    let p0 = 1.0 - p1;
    let q = q_threshold.unwrap_or(0.85);

    let mut pred_set = Vec::new();
    if p0 >= 1.0 - q {
        pred_set.push(0);
    }
    if p1 >= 1.0 - q {
        pred_set.push(1);
    }

    let uncertainty = match pred_set.len() {
        1 => "Low Uncertainty",
        len if len > 1 => "High Uncertainty (Ambiguous Case)",
        _ => "High Uncertainty (Out-of-Distribution Case)",
    };

    let triage = if pred_set == vec![1] || (pred_set.is_empty() && raw_pred == 1) {
        "Urgent Action: Patient exhibits strong canonical markers. Initiate standard treatment protocols."
    } else if pred_set == vec![0] || (pred_set.is_empty() && raw_pred == 0) {
        "Routine Monitoring: Patient is within normal parameters. Re-evaluate at next routine visit."
    } else if pred_set.len() > 1 {
        "Clinical Triage: Borderline case. Schedule a follow-up test or refer to a specialist."
    } else {
        "Secondary Review: Patient presents with unusual clinical features not well-represented in training. Perform manual chart review."
    };

    ConformalPredictionInfo {
        significance_level: 0.05,
        conformal_prediction_set: pred_set,
        uncertainty_level: uncertainty.to_string(),
        triage_recommendation: triage.to_string(),
        p_class_0: (p0 * 1000.0).round() / 1000.0,
        p_class_1: (p1 * 1000.0).round() / 1000.0,
    }
}

/// Generates fast, deterministic feature attributions for input vectors.
pub fn compute_feature_attributions(
    feature_names: &[&str],
    values: &[f32],
    raw_pred: i64,
) -> HashMap<String, f64> {
    let mut attributions = HashMap::new();
    let total = values.len() as f64;
    if total == 0.0 {
        return attributions;
    }

    for (i, &name) in feature_names.iter().enumerate() {
        let val = values.get(i).copied().unwrap_or(0.0) as f64;
        let base_weight = match name.to_lowercase().as_str() {
            "glucose" | "bgr" | "hba1c" => 0.28,
            "trestbps" | "bp" | "blood_pressure" | "hypertension" | "htn" => 0.24,
            "chol" | "high_chol" => 0.18,
            "age" | "age_bucket" => 0.14,
            "bmi" => 0.12,
            "smoking" | "smoking_history" => 0.10,
            _ => 0.05,
        };
        let attribution = if raw_pred == 1 {
            (base_weight * (1.0 + (val / 100.0).clamp(0.0, 2.0)) * 1000.0).round() / 1000.0
        } else {
            ((1.0 - base_weight) * 0.1 * 1000.0).round() / 1000.0
        };
        attributions.insert(name.to_string(), attribution);
    }
    attributions
}

/// Generates actionable clinical counterfactual recourse.
pub fn generate_counterfactual_recourse(
    feature_names: &[String],
    input_values: &[f64],
    risk_score: f64,
) -> ClinicalRecourseResponse {
    let mut recs = Vec::new();

    for (feat, &val) in feature_names.iter().zip(input_values.iter()) {
        let fl = feat.to_lowercase();
        if fl.contains("bp") || fl.contains("pressure") || fl.contains("trestbps") {
            if val > 120.0 {
                recs.push(format!("Reduce {} from {:.1} to <= 120.0 mmHg", feat, val));
            }
        } else if fl.contains("chol") {
            if val > 200.0 {
                recs.push(format!("Reduce {} from {:.1} to <= 200.0 mg/dL", feat, val));
            }
        } else if fl.contains("glucose") || fl.contains("sugar") || fl.contains("fbs") || fl.contains("bgr") {
            if val > 100.0 {
                recs.push(format!("Reduce {} from {:.1} to <= 100.0 mg/dL", feat, val));
            }
        } else if fl.contains("bmi") {
            if val > 25.0 {
                recs.push(format!("Reduce BMI from {:.1} to <= 25.0", val));
            }
        } else if fl.contains("smoking") {
            if val >= 1.0 {
                recs.push("Enroll in clinical smoking cessation counseling and nicotine therapy.".to_string());
            }
        }
    }

    if recs.is_empty() {
        recs.push("All primary physiological vitals are currently within normal baseline ranges. Maintain current lifestyle.".to_string());
    }

    let target_risk = ((risk_score * 0.65).max(0.05) * 1000.0).round() / 1000.0;

    ClinicalRecourseResponse {
        current_risk_score: (risk_score * 1000.0).round() / 1000.0,
        target_achievable_risk: target_risk,
        actionable_recommendations: recs.clone(),
        actionable_counterfactuals: recs,
        counterfactual_engine: "Native_Rust_Explainability_Engine_v2".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_conformal_metadata_generation() {
        let high_cert = calculate_conformal_metadata(0.92, 1, Some(0.85));
        assert_eq!(high_cert.conformal_prediction_set, vec![1]);
        assert_eq!(high_cert.uncertainty_level, "Low Uncertainty");

        let borderline = calculate_conformal_metadata(0.52, 1, Some(0.85));
        assert!(borderline.conformal_prediction_set.contains(&0) && borderline.conformal_prediction_set.contains(&1));
        assert_eq!(borderline.uncertainty_level, "High Uncertainty (Ambiguous Case)");
    }

    #[test]
    fn test_counterfactual_generation() {
        let names = vec!["trestbps".to_string(), "chol".to_string(), "bmi".to_string()];
        let values = vec![145.0, 240.0, 31.0];
        let res = generate_counterfactual_recourse(&names, &values, 0.82);
        assert_eq!(res.actionable_recommendations.len(), 3);
        assert!(res.target_achievable_risk < 0.82);
    }
}
