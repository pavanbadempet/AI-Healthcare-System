use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Patient health prediction history record.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct HealthRecord {
    pub id: i64,
    pub user_id: Option<i64>,
    pub record_type: String,
    pub data: Option<String>, // Encrypted JSON
    pub prediction: Option<String>,
    pub timestamp: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// AI medical chatbot conversation log.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ChatLog {
    pub id: i64,
    pub user_id: Option<i64>,
    pub role: String,
    pub content: String,
    pub timestamp: Option<NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

/// Administrative and security audit log.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct AuditLog {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub admin_id: i64,
    pub target_user_id: Option<i64>,
    pub action: String,
    pub timestamp: Option<NaiveDateTime>,
    pub details: Option<String>,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}
