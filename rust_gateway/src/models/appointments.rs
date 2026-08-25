use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Appointment ORM model.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Appointment {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub user_id: i64,
    pub doctor_id: Option<i64>,
    pub specialist: Option<String>,
    pub date_time: Option<NaiveDateTime>,
    pub reason: Option<String>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppointmentCreate {
    pub date: String,
    pub time: String,
    pub doctor_id: i64,
    pub specialist: String,
    pub reason: String,
}
