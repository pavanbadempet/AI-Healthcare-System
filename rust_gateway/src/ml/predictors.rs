use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::ml::calculators::{self, EgfrResult, Fib4Result, FraminghamResult};
use crate::ml::engine::{MlEngineError, ModelSessions};
use crate::ml::explain::{self, ConformalPredictionInfo};
use crate::ml::scalers;

pub const MEDICAL_DISCLAIMER: &str = "This is an AI-assisted screening tool, not a medical diagnosis. Please consult a qualified healthcare professional for clinical decisions.";

pub const HIGH_RISK_THRESHOLD: f64 = 75.0;
pub const MODERATE_RISK_THRESHOLD: f64 = 40.0;

/// Map age in years to BRFSS 13-tier age bucket (1-13).
pub fn get_age_bucket(age: f32) -> f32 {
    if age <= 24.0 { 1.0 }
    else if age <= 29.0 { 2.0 }
    else if age <= 34.0 { 3.0 }
    else if age <= 39.0 { 4.0 }
    else if age <= 44.0 { 5.0 }
    else if age <= 49.0 { 6.0 }
    else if age <= 54.0 { 7.0 }
    else if age <= 59.0 { 8.0 }
    else if age <= 64.0 { 9.0 }
    else if age <= 69.0 { 10.0 }
    else if age <= 74.0 { 11.0 }
    else if age <= 79.0 { 12.0 }
    else { 13.0 }
}

/// Classify probability into confidence percentage and clinical risk category.
pub fn classify_confidence(probability: f64) -> (f64, String) {
    let confidence = (probability * 100.0 * 10.0).round() / 10.0;
    let risk_level = if confidence >= HIGH_RISK_THRESHOLD {
        "High".to_string()
    } else if confidence >= MODERATE_RISK_THRESHOLD {
        "Moderate".to_string()
    } else {
        "Low".to_string()
    };
    (confidence, risk_level)
}

// ── Input Schemas ───────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiabetesInput {
    pub hypertension: f32,
    pub high_chol: f32,
    pub bmi: f32,
    pub smoking_history: f32,
    pub heart_disease: f32,
    pub physical_activity: f32,
    pub general_health: f32,
    pub gender: f32,
    pub age: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeartInput {
    pub age: f32,
    pub sex: f32,
    pub cp: f32,
    pub trestbps: f32,
    pub chol: f32,
    pub fbs: f32,
    pub restecg: f32,
    pub thalach: f32,
    pub exang: f32,
    pub oldpeak: f32,
    pub slope: f32,
    pub ca: f32,
    pub thal: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KidneyInput {
    pub age: f32,
    pub bp: f32,
    pub sg: f32,
    pub al: f32,
    pub su: f32,
    pub rbc: f32,
    pub pc: f32,
    pub pcc: f32,
    pub ba: f32,
    pub bgr: f32,
    pub bu: f32,
    pub sc: f32,
    pub sod: f32,
    pub pot: f32,
    pub hemo: f32,
    pub pcv: f32,
    pub wc: f32,
    pub rc: f32,
    pub htn: f32,
    pub dm: f32,
    pub cad: f32,
    pub appet: f32,
    pub pe: f32,
    pub ane: f32,
    #[serde(default)]
    pub is_female: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiverInput {
    pub age: f32,
    pub gender: f32,
    pub total_bilirubin: f32,
    pub direct_bilirubin: f32,
    pub alkaline_phosphotase: f32,
    pub alamine_aminotransferase: f32,
    pub aspartate_aminotransferase: f32,
    pub total_proteins: f32,
    pub albumin: f32,
    pub albumin_and_globulin_ratio: f32,
    #[serde(default)]
    pub platelets: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LungInput {
    pub gender: f32,
    pub age: f32,
    pub smoking: f32,
    pub yellow_fingers: f32,
    pub anxiety: f32,
    pub peer_pressure: f32,
    pub chronic_disease: f32,
    pub fatigue: f32,
    pub allergy: f32,
    pub wheezing: f32,
    pub alcohol: f32,
    pub coughing: f32,
    pub shortness_of_breath: f32,
    pub swallowing_difficulty: f32,
    pub chest_pain: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrokeInput {
    #[serde(default)]
    pub gender: Option<f32>,
    #[serde(default)]
    pub age: Option<f32>,
    #[serde(default)]
    pub hypertension: Option<f32>,
    #[serde(default)]
    pub heart_disease: Option<f32>,
    #[serde(default)]
    pub smoking: Option<f32>,
    #[serde(default)]
    pub bmi: Option<f32>,
    #[serde(default)]
    pub glucose: Option<f32>,
}

// ── Structured Output Result ────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionResult {
    pub prediction: String,
    pub raw: i64,
    pub confidence: Option<f64>,
    pub risk_level: Option<String>,
    pub disclaimer: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub probability: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub probabilities: Option<Vec<f64>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub egfr: Option<EgfrResult>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fib4: Option<Fib4Result>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub framingham: Option<FraminghamResult>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub conformal_interval: Option<ConformalPredictionInfo>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub feature_attributions: Option<HashMap<String, f64>>,
}

// ── Prediction Handlers ─────────────────────────────────────────────

/// Predicts diabetes risk from 9 lifestyle & clinical features.
pub fn predict_diabetes(
    sessions: &ModelSessions,
    data: &DiabetesInput,
) -> Result<PredictionResult, MlEngineError> {
    let age_bucket = get_age_bucket(data.age);
    let input = [
        data.hypertension,
        data.high_chol,
        data.bmi,
        data.smoking_history,
        data.heart_disease,
        data.physical_activity,
        data.general_health,
        data.gender,
        age_bucket,
    ];

    let (raw, prob) = sessions.run_standard_inference(&sessions.diabetes, &input)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "High Risk" } else { "Low Risk" };
    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);
    let feat_names = &[
        "hypertension", "high_chol", "bmi", "smoking_history",
        "heart_disease", "physical_activity", "general_health", "gender", "age_bucket",
    ];
    let attributions = explain::compute_feature_attributions(feat_names, &input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr: None,
        fib4: None,
        framingham: None,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}

/// Predicts heart disease risk and calculates Framingham 10-year CVD risk score.
pub fn predict_heart_disease(
    sessions: &ModelSessions,
    data: &HeartInput,
) -> Result<PredictionResult, MlEngineError> {
    let input = [
        data.age,
        data.sex,
        data.cp,
        data.trestbps,
        data.chol,
        data.fbs,
        data.restecg,
        data.thalach,
        data.exang,
        data.oldpeak,
        data.slope,
        data.ca,
        data.thal,
    ];

    let (raw, prob) = sessions.run_heart_inference(&input)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "Heart Disease Detected" } else { "Healthy Heart" };
    let is_female = data.sex == 0.0;
    let framingham = calculators::calculate_framingham_risk(
        data.age as f64,
        is_female,
        data.chol as f64,
        50.0, // default HDL baseline
        data.trestbps as f64,
        false,
        data.fbs == 1.0,
        false,
    );

    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);
    let feat_names = &[
        "age", "sex", "cp", "trestbps", "chol", "fbs",
        "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
    ];
    let attributions = explain::compute_feature_attributions(feat_names, &input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr: None,
        fib4: None,
        framingham,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}

/// Predicts chronic kidney disease using native static affine scalers and computes eGFR.
pub fn predict_kidney_disease(
    sessions: &ModelSessions,
    data: &KidneyInput,
) -> Result<PredictionResult, MlEngineError> {
    let raw_input = [
        data.age, data.bp, data.sg, data.al, data.su,
        data.rbc, data.pc, data.pcc, data.ba,
        data.bgr, data.bu, data.sc, data.sod, data.pot, data.hemo, data.pcv, data.wc, data.rc,
        data.htn, data.dm, data.cad, data.appet, data.pe, data.ane,
    ];

    let scaled = scalers::preprocess_kidney(&raw_input);
    let (raw, prob) = sessions.run_standard_inference(&sessions.kidney, &scaled)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "Chronic Kidney Disease Detected" } else { "Healthy Kidney" };
    let is_female = data.is_female.unwrap_or(false);
    let egfr = calculators::calculate_egfr_ckd_epi(data.sc as f64, data.age as f64, is_female);
    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);

    let feat_names = &[
        "age", "bp", "sg", "al", "su", "rbc", "pc", "pcc", "ba",
        "bgr", "bu", "sc", "sod", "pot", "hemo", "pcv", "wc", "rc",
        "htn", "dm", "cad", "appet", "pe", "ane",
    ];
    let attributions = explain::compute_feature_attributions(feat_names, &raw_input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr,
        fib4: None,
        framingham: None,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}

/// Predicts liver disease using log1p + affine scaling and computes FIB-4 index.
pub fn predict_liver_disease(
    sessions: &ModelSessions,
    data: &LiverInput,
) -> Result<PredictionResult, MlEngineError> {
    let raw_input = [
        data.age,
        data.gender,
        data.total_bilirubin,
        data.direct_bilirubin,
        data.alkaline_phosphotase,
        data.alamine_aminotransferase,
        data.aspartate_aminotransferase,
        data.total_proteins,
        data.albumin,
        data.albumin_and_globulin_ratio,
    ];

    let scaled = scalers::preprocess_liver(&raw_input);
    let (raw, prob) = sessions.run_standard_inference(&sessions.liver, &scaled)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "Liver Disease Detected" } else { "Healthy Liver" };
    let platelets = data.platelets.unwrap_or(200.0) as f64;
    let fib4 = calculators::calculate_fib4_index(
        data.age as f64,
        data.aspartate_aminotransferase as f64,
        data.alamine_aminotransferase as f64,
        platelets,
    );
    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);

    let feat_names = &[
        "age", "gender", "total_bilirubin", "direct_bilirubin",
        "alkaline_phosphotase", "alamine_aminotransferase",
        "aspartate_aminotransferase", "total_proteins", "albumin",
        "albumin_and_globulin_ratio",
    ];
    let attributions = explain::compute_feature_attributions(feat_names, &raw_input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr: None,
        fib4,
        framingham: None,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}

/// Predicts respiratory / lung disease using native static affine scalers.
pub fn predict_lung_disease(
    sessions: &ModelSessions,
    data: &LungInput,
) -> Result<PredictionResult, MlEngineError> {
    let raw_input = [
        data.gender,
        data.age,
        data.smoking,
        data.yellow_fingers,
        data.anxiety,
        data.peer_pressure,
        data.chronic_disease,
        data.fatigue,
        data.allergy,
        data.wheezing,
        data.alcohol,
        data.coughing,
        data.shortness_of_breath,
        data.swallowing_difficulty,
        data.chest_pain,
    ];

    let scaled = scalers::preprocess_lungs(&raw_input);
    let (raw, prob) = sessions.run_standard_inference(&sessions.lungs, &scaled)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "Respiratory Issue Detected" } else { "Healthy Lungs" };
    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);

    let feat_names = &[
        "gender", "age", "smoking", "yellow_fingers", "anxiety",
        "peer_pressure", "chronic_disease", "fatigue", "allergy",
        "wheezing", "alcohol", "coughing", "shortness_of_breath",
        "swallowing_difficulty", "chest_pain",
    ];
    let attributions = explain::compute_feature_attributions(feat_names, &raw_input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr: None,
        fib4: None,
        framingham: None,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}

/// Predicts stroke risk with cerebrovascular scoring profile.
pub fn predict_stroke_risk(
    sessions: &ModelSessions,
    data: &StrokeInput,
) -> Result<PredictionResult, MlEngineError> {
    let gender = data.gender.unwrap_or(0.0);
    let age = data.age.unwrap_or(45.0);
    let htn = data.hypertension.unwrap_or(0.0);
    let hd = data.heart_disease.unwrap_or(0.0);
    let smoking = data.smoking.unwrap_or(0.0);
    let bmi = data.bmi.unwrap_or(25.0);
    let glucose = data.glucose.unwrap_or(90.0);

    let input = [gender, age, htn, hd, smoking, bmi, glucose];
    let (raw, prob) = sessions.run_stroke_inference(&input)?;
    let p_pos = prob as f64;
    let (mut confidence, risk_level) = classify_confidence(p_pos);

    if raw == 0 {
        confidence = ((100.0 - confidence) * 10.0).round() / 10.0;
    }

    let prediction_str = if raw == 1 { "High Stroke Risk" } else { "Low Stroke Risk" };
    let conformal = explain::calculate_conformal_metadata(p_pos, raw, None);

    let feat_names = &["gender", "age", "hypertension", "heart_disease", "smoking", "bmi", "glucose"];
    let attributions = explain::compute_feature_attributions(feat_names, &input, raw);

    Ok(PredictionResult {
        prediction: prediction_str.to_string(),
        raw,
        confidence: Some(confidence),
        risk_level: Some(risk_level),
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
        probability: Some((p_pos * 10000.0).round() / 10000.0),
        probabilities: Some(vec![1.0 - p_pos, p_pos]),
        egfr: None,
        fib4: None,
        framingham: None,
        conformal_interval: Some(conformal),
        feature_attributions: Some(attributions),
    })
}
