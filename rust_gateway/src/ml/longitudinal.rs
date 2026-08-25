use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const MEDICAL_DISCLAIMER: &str = "This is an AI-assisted screening tool, not a medical diagnosis. Please consult a qualified healthcare professional for clinical decisions.";

pub const DIABETES_FEATURES: &[&str] = &[
    "hypertension", "high_chol", "bmi", "smoking_history",
    "heart_disease", "physical_activity", "general_health", "gender", "age",
];

pub const HEART_FEATURES: &[&str] = &[
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
];

pub const LIVER_FEATURES: &[&str] = &[
    "age", "gender", "total_bilirubin", "direct_bilirubin",
    "alkaline_phosphotase", "alamine_aminotransferase",
    "aspartate_aminotransferase", "total_proteins", "albumin",
    "albumin_globulin_ratio",
];

pub const KIDNEY_FEATURES: &[&str] = &[
    "age", "blood_pressure", "specific_gravity", "albumin", "sugar",
    "blood_glucose_random", "blood_urea", "serum_creatinine", "sodium",
    "potassium", "hemoglobin", "packed_cell_volume",
    "white_blood_cell_count", "red_blood_cell_count",
    "hypertension", "diabetes_mellitus", "appetite",
    "pedal_edema", "anemia",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisitAttention {
    pub visit_index: usize,
    pub weight: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LongitudinalPredictionResponse {
    pub condition: String,
    pub risk_probability: f64,
    pub risk_label: String,
    pub trend: String,
    pub num_visits: usize,
    pub visit_attention: Vec<VisitAttention>,
    pub medical_disclaimer: String,
}

pub fn get_features_for_condition(condition: &str) -> Option<&'static [&'static str]> {
    match condition.to_lowercase().as_str() {
        "diabetes" => Some(DIABETES_FEATURES),
        "heart" => Some(HEART_FEATURES),
        "liver" => Some(LIVER_FEATURES),
        "kidney" => Some(KIDNEY_FEATURES),
        _ => None,
    }
}

/// Converts a sequence of visit property maps into a 2D matrix (T x F) with
/// forward-fill, backward-fill, and zero-fill imputation.
pub fn visits_to_matrix(
    visits: &[HashMap<String, Option<f64>>],
    feature_names: &[&str],
) -> Vec<Vec<f64>> {
    let n_visits = visits.len();
    let n_features = feature_names.len();
    let mut matrix = vec![vec![f64::NAN; n_features]; n_visits];

    for (t, visit) in visits.iter().enumerate() {
        for (j, &feat) in feature_names.iter().enumerate() {
            if let Some(Some(val)) = visit.get(feat) {
                matrix[t][j] = *val;
            }
        }
    }

    // Forward fill -> backward fill -> zero fill
    for j in 0..n_features {
        // Forward fill
        for t in 1..n_visits {
            if matrix[t][j].is_nan() && !matrix[t - 1][j].is_nan() {
                matrix[t][j] = matrix[t - 1][j];
            }
        }
        // Backward fill
        for t in (0..n_visits.saturating_sub(1)).rev() {
            if matrix[t][j].is_nan() && !matrix[t + 1][j].is_nan() {
                matrix[t][j] = matrix[t + 1][j];
            }
        }
        // Zero fill remaining
        for t in 0..n_visits {
            if matrix[t][j].is_nan() {
                matrix[t][j] = 0.0;
            }
        }
    }

    matrix
}

/// Assesses whether trajectory slope is improving, stable, or worsening.
pub fn assess_trend(matrix: &[Vec<f64>]) -> String {
    let n = matrix.len();
    if n < 2 {
        return "STABLE".to_string();
    }

    let visit_means: Vec<f64> = matrix
        .iter()
        .map(|row| {
            if row.is_empty() {
                0.0
            } else {
                row.iter().sum::<f64>() / (row.len() as f64)
            }
        })
        .collect();

    let n_f = n as f64;
    let sum_x: f64 = (0..n).map(|i| i as f64).sum();
    let sum_y: f64 = visit_means.iter().sum();
    let sum_xy: f64 = visit_means.iter().enumerate().map(|(i, &y)| (i as f64) * y).sum();
    let sum_xx: f64 = (0..n).map(|i| (i as f64) * (i as f64)).sum();

    let denom = n_f * sum_xx - sum_x * sum_x;
    if denom.abs() < 1e-9 {
        return "STABLE".to_string();
    }

    let slope = (n_f * sum_xy - sum_x * sum_y) / denom;
    if slope > 0.05 {
        "WORSENING".to_string()
    } else if slope < -0.05 {
        "IMPROVING".to_string()
    } else {
        "STABLE".to_string()
    }
}

/// Maps risk probability to clinical categorical label.
pub fn classify_risk_label(prob: f64) -> String {
    if prob < 0.20 {
        "LOW".to_string()
    } else if prob < 0.45 {
        "MODERATE".to_string()
    } else if prob < 0.70 {
        "HIGH".to_string()
    } else {
        "VERY HIGH".to_string()
    }
}

/// Runs longitudinal prediction pipeline across sequence of visits.
pub fn predict_longitudinal(
    condition: &str,
    visits: &[HashMap<String, Option<f64>>],
) -> Result<LongitudinalPredictionResponse, String> {
    if visits.len() < 2 {
        return Err("Longitudinal prediction requires at least 2 chronological visits.".to_string());
    }

    let feature_names = get_features_for_condition(condition)
        .ok_or_else(|| format!("Unsupported longitudinal condition '{}'.", condition))?;

    let matrix = visits_to_matrix(visits, feature_names);
    let n_visits = matrix.len();
    let n_features = feature_names.len();

    // Min-Max normalize features across the visit sequence
    let mut mins = vec![f64::INFINITY; n_features];
    let mut maxs = vec![f64::NEG_INFINITY; n_features];

    for row in &matrix {
        for j in 0..n_features {
            mins[j] = mins[j].min(row[j]);
            maxs[j] = maxs[j].max(row[j]);
        }
    }

    let mut normed_latest = Vec::with_capacity(n_features);
    let latest_row = &matrix[n_visits - 1];
    for j in 0..n_features {
        let range = maxs[j] - mins[j];
        let normed = if range.abs() < 1e-9 {
            0.0
        } else {
            (latest_row[j] - mins[j]) / range
        };
        normed_latest.push(normed);
    }

    let latest_mean = normed_latest.iter().sum::<f64>() / (n_features as f64);
    let risk_prob = latest_mean.clamp(0.05, 0.95);

    // Linearly increasing attention weights
    let weight_denom: f64 = (1..=n_visits).map(|k| k as f64).sum();
    let visit_attention: Vec<VisitAttention> = (0..n_visits)
        .map(|i| {
            let w = ((i + 1) as f64) / weight_denom;
            VisitAttention {
                visit_index: i,
                weight: (w * 10000.0).round() / 10000.0,
            }
        })
        .collect();

    let trend = assess_trend(&matrix);
    let risk_label = classify_risk_label(risk_prob);

    Ok(LongitudinalPredictionResponse {
        condition: condition.to_string(),
        risk_probability: (risk_prob * 10000.0).round() / 10000.0,
        risk_label,
        trend,
        num_visits: n_visits,
        visit_attention,
        medical_disclaimer: MEDICAL_DISCLAIMER.to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_longitudinal_trend_worsening() {
        let mut v1 = HashMap::new();
        v1.insert("hypertension".to_string(), Some(0.0));
        v1.insert("high_chol".to_string(), Some(0.0));
        v1.insert("bmi".to_string(), Some(22.0));
        v1.insert("age".to_string(), Some(45.0));

        let mut v2 = HashMap::new();
        v2.insert("hypertension".to_string(), Some(1.0));
        v2.insert("high_chol".to_string(), Some(1.0));
        v2.insert("bmi".to_string(), Some(32.0));
        v2.insert("age".to_string(), Some(46.0));

        let resp = predict_longitudinal("diabetes", &[v1, v2]).unwrap();
        assert_eq!(resp.num_visits, 2);
        assert_eq!(resp.condition, "diabetes");
        assert_eq!(resp.trend, "WORSENING");
        assert_eq!(resp.visit_attention.len(), 2);
        assert!(resp.visit_attention[1].weight > resp.visit_attention[0].weight);
    }

    #[test]
    fn test_longitudinal_invariant_features_low_risk() {
        let mut v1 = HashMap::new();
        v1.insert("hypertension".to_string(), Some(0.0));
        v1.insert("high_chol".to_string(), Some(0.0));
        v1.insert("bmi".to_string(), Some(22.0));
        v1.insert("age".to_string(), Some(45.0));

        let v2 = v1.clone();

        let resp = predict_longitudinal("diabetes", &[v1, v2]).unwrap();
        assert_eq!(resp.num_visits, 2);
        assert_eq!(resp.condition, "diabetes");
        assert_eq!(resp.trend, "STABLE");
        assert_eq!(resp.risk_label, "LOW");
        assert!(resp.risk_probability <= 0.20);
    }
}

