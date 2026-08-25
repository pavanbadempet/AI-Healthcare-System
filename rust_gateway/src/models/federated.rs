use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Clinician correction feedback for federated model fine-tuning.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ModelFeedback {
    pub id: i64,
    pub patient_id: i64,
    pub model_name: String,
    pub input_features: String,   // JSON
    pub prediction_result: String, // JSON
    pub corrected_label: String,
    pub clinician_id: i64,
    pub status: String, // pending_sync | synced
    pub created_at: Option<NaiveDateTime>,
}

/// Differential-privacy federated learning aggregation audit log.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct FederatedSyncAudit {
    pub id: i64,
    pub sync_run_id: String,
    pub node_id: String,
    pub model_name: String,
    pub records_synced: i64,
    pub epsilon_consumed: f64,
    pub delta_consumed: f64,
    pub status: String, // completed | failed | rejected
    pub error_message: Option<String>,
    pub created_at: Option<NaiveDateTime>,
}
