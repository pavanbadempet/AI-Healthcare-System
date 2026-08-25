use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// User ORM model representing users, patients, clinicians, nurses, pharmacists, and admins.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub hashed_password: String,
    pub created_at: Option<NaiveDateTime>,
    pub role: String,
    pub email: Option<String>,
    pub full_name: Option<String>,
    pub gender: Option<String>,
    pub blood_type: Option<String>,
    pub dob: Option<String>,
    pub height: Option<f64>,
    pub weight: Option<f64>,
    pub existing_ailments: Option<String>,
    pub profile_picture: Option<String>,
    pub about_me: Option<String>,
    pub diet: Option<String>,
    pub activity_level: Option<String>,
    pub sleep_hours: Option<f64>,
    pub stress_level: Option<String>,
    pub allow_data_collection: i64,
    pub facility_id: Option<i64>,
    pub plan_tier: String,
    pub subscription_expiry: Option<NaiveDateTime>,
    pub razorpay_customer_id: Option<String>,
    pub consultation_fee: f64,
    pub specialization: Option<String>,
    pub psych_profile: Option<String>,
    pub totp_secret: Option<String>,
    pub is_totp_enabled: i64,
    pub is_deleted: i64,
    pub deleted_at: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserCreate {
    pub username: String,
    pub password: String,
    pub role: Option<String>,
    pub email: Option<String>,
    pub full_name: Option<String>,
    pub facility_id: Option<i64>,
    pub specialization: Option<String>,
    pub consultation_fee: Option<f64>,
}
