use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Nursing care workflow task.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct NursingTask {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub assigned_nurse_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub completed_by_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub admission_id: Option<i64>,
    pub department_id: Option<i64>,
    pub task_type: String,
    pub title: String,
    pub instructions: Option<String>,
    pub priority: String, // routine, urgent, stat
    pub status: String,   // assigned, in_progress, completed, cancelled
    pub due_at: Option<NaiveDateTime>,
    pub completed_at: Option<NaiveDateTime>,
    pub completion_note: Option<String>,
    pub created_at: Option<NaiveDateTime>,
}
