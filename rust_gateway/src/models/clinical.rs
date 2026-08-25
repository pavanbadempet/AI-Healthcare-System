use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Clinical order model (lab, radiology, pharmacy, procedure, nursing).
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ClinicalOrder {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub order_type: String,
    pub title: String,
    pub priority: String,
    pub status: String,
    pub notes: Option<String>,
    pub created_at: Option<NaiveDateTime>,
    pub completed_at: Option<NaiveDateTime>,
}

/// Care event model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct CareEvent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub actor_user_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub event_type: String,
    pub title: String,
    pub summary: Option<String>,
    pub severity: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Vital observation model with physiological indicators.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct VitalObservation {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub recorded_by_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub source: String,
    pub heart_rate: Option<f64>,
    pub systolic_bp: Option<f64>,
    pub diastolic_bp: Option<f64>,
    pub spo2: Option<f64>,
    pub temperature_c: Option<f64>,
    pub respiratory_rate: Option<f64>,
    pub blood_glucose: Option<f64>,
    pub observed_at: Option<NaiveDateTime>,
    pub created_at: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// Real-time clinical monitoring signal.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct MonitoringSignal {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub vital_observation_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub signal_type: String,
    pub severity: String,
    pub title: String,
    pub summary: String,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

/// Diagnostic lab/radiology result.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DiagnosticResult {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub order_id: i64,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub result_type: String,
    pub title: String,
    pub summary: String,
    pub abnormal_flag: i64,
    pub status: String,
    pub review_status: String,
    pub review_note: Option<String>,
    pub reviewed_by_id: Option<i64>,
    pub reviewed_at: Option<NaiveDateTime>,
    pub created_at: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// Spark streaming pipeline metrics.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SparkStreamingMetrics {
    pub id: i64,
    pub batch_id: i64,
    pub records_processed: i64,
    pub processing_time_ms: f64,
    pub ml_latency_ms: f64,
    pub timestamp: Option<NaiveDateTime>,
}
