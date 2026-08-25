use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// SMART on FHIR registered application.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SmartApp {
    pub id: i64,
    pub app_name: String,
    pub client_id: String,
    pub redirect_uri: String,
    pub launch_url: String,
    pub scopes: String,
    pub is_active: i64,
    pub created_at: Option<NaiveDateTime>,
}

/// SMART on FHIR EHR launch context with ephemeral tokens.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SmartLaunchContext {
    pub id: i64,
    pub app_id: i64,
    pub patient_id: i64,
    pub user_id: i64,
    pub launch_token: String,
    pub auth_code: Option<String>,
    pub scope: String,
    pub expires_at: NaiveDateTime,
    pub created_at: Option<NaiveDateTime>,
}
