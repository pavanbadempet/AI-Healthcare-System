use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Severity-tagged clinical alert tied to a patient.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ClinicalAlert {
    pub id: i64,
    pub patient_id: i64,
    pub alert_type: String,
    pub severity: String, // CRITICAL | WARNING | INFO
    pub message: String,
    pub source_event_id: Option<String>,
    pub is_acknowledged: i64,
    pub acknowledged_by: Option<i64>,
    pub acknowledged_at: Option<NaiveDateTime>,
    pub created_at: Option<NaiveDateTime>,
}

/// AI-generated longitudinal patient insight (risk summary or trend analysis).
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct PatientInsight {
    pub id: i64,
    pub patient_id: i64,
    pub insight_type: String,
    pub content: String, // JSON
    pub model_version: Option<String>,
    pub created_at: Option<NaiveDateTime>,
}

/// Clinician override audit trail for AI predictions.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ClinicalAICorrection {
    pub id: i64,
    pub patient_id: i64,
    pub clinician_id: i64,
    pub function_name: String,
    pub original_ai_output: String,
    pub corrected_output: Option<String>,
    pub override_action: String, // accepted | overridden | ignored
    pub override_reason: Option<String>,
    pub created_at: Option<NaiveDateTime>,
}
