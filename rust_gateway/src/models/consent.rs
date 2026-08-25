use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// EULA Terms of Service consent audit record.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct ConsentRecord {
    pub id: i64,
    pub user_id: i64,
    pub eula_version: String,
    pub accepted_at: NaiveDateTime,
    pub ip_address: Option<String>,
    pub user_agent: Option<String>,
}
