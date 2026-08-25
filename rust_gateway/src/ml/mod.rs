pub mod scalers;
pub mod engine;
pub mod predictors;
pub mod longitudinal;
pub mod calculators;
pub mod explain;

use std::collections::HashMap;
use std::sync::Arc;
use serde::{Deserialize, Serialize};

pub use engine::{MlEngineError, ModelSessions};
pub use predictors::{
    DiabetesInput, HeartInput, KidneyInput, LiverInput, LungInput, StrokeInput,
    PredictionResult, predict_diabetes, predict_heart_disease, predict_kidney_disease,
    predict_liver_disease, predict_lung_disease, predict_stroke_risk,
    classify_confidence, get_age_bucket, MEDICAL_DISCLAIMER,
};
pub use longitudinal::{
    LongitudinalPredictionResponse, VisitAttention, predict_longitudinal,
    get_features_for_condition,
};
pub use calculators::{
    EgfrResult, Fib4Result, FraminghamResult, QsofaResult, Cha2ds2VascResult, MeldResult,
    calculate_egfr_ckd_epi, calculate_fib4_index, calculate_framingham_risk,
    calculate_qsofa, calculate_cha2ds2_vasc, calculate_meld_score,
};
pub use explain::{
    ConformalPredictionInfo, ClinicalRecourseResponse, calculate_conformal_metadata,
    compute_feature_attributions, generate_counterfactual_recourse,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelHealthStatus {
    pub diabetes: bool,
    pub heart: bool,
    pub kidney: bool,
    pub liver: bool,
    pub lungs: bool,
    pub stroke: bool,
    pub all_healthy: bool,
}

/// Unified High-Level Native Rust Inference Manager.
/// Manages thread-safe model sessions and exposes unified interfaces for
/// predictions, clinical calculators, longitudinal trend scoring, and explainability.
#[derive(Clone)]
pub struct InferenceManager {
    sessions: Arc<ModelSessions>,
}

impl InferenceManager {
    /// Creates a new InferenceManager by loading models from environment or standard paths.
    pub fn new() -> Result<Self, MlEngineError> {
        let sessions = ModelSessions::load_from_env()?;
        Ok(Self {
            sessions: Arc::new(sessions),
        })
    }

    /// Creates a new InferenceManager from a custom models directory.
    pub fn from_dir<P: AsRef<std::path::Path>>(dir: P) -> Result<Self, MlEngineError> {
        let sessions = ModelSessions::load_from_dir(dir)?;
        Ok(Self {
            sessions: Arc::new(sessions),
        })
    }

    /// Access underlying ModelSessions.
    pub fn sessions(&self) -> &ModelSessions {
        &self.sessions
    }

    // ── Disease Predictions ─────────────────────────────────────────

    pub fn predict_diabetes(&self, input: &DiabetesInput) -> Result<PredictionResult, MlEngineError> {
        predict_diabetes(&self.sessions, input)
    }

    pub fn predict_heart(&self, input: &HeartInput) -> Result<PredictionResult, MlEngineError> {
        predict_heart_disease(&self.sessions, input)
    }

    pub fn predict_kidney(&self, input: &KidneyInput) -> Result<PredictionResult, MlEngineError> {
        predict_kidney_disease(&self.sessions, input)
    }

    pub fn predict_liver(&self, input: &LiverInput) -> Result<PredictionResult, MlEngineError> {
        predict_liver_disease(&self.sessions, input)
    }

    pub fn predict_lungs(&self, input: &LungInput) -> Result<PredictionResult, MlEngineError> {
        predict_lung_disease(&self.sessions, input)
    }

    pub fn predict_stroke(&self, input: &StrokeInput) -> Result<PredictionResult, MlEngineError> {
        predict_stroke_risk(&self.sessions, input)
    }

    // ── Longitudinal Progression ───────────────────────────────────

    pub fn predict_longitudinal(
        &self,
        condition: &str,
        visits: &[HashMap<String, Option<f64>>],
    ) -> Result<LongitudinalPredictionResponse, String> {
        predict_longitudinal(condition, visits)
    }

    // ── Health Check ───────────────────────────────────────────────

    pub fn health_check(&self) -> ModelHealthStatus {
        ModelHealthStatus {
            diabetes: true,
            heart: true,
            kidney: true,
            liver: true,
            lungs: true,
            stroke: true,
            all_healthy: true,
        }
    }
}
