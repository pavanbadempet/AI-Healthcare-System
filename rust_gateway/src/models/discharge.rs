use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Inpatient discharge summary.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DischargeSummary {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub admission_id: i64,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub diagnosis_summary: String,
    pub hospital_course: String,
    pub medications: Option<String>,
    pub follow_up_plan: Option<String>,
    pub discharge_instructions: Option<String>,
    pub status: String, // draft, finalized, amended
    pub created_at: Option<NaiveDateTime>,
    pub finalized_at: Option<NaiveDateTime>,
}
