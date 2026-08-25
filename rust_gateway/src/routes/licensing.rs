use axum::{
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use jsonwebtoken::{decode, DecodingKey, Validation};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::env;

use crate::AppState;

const DEFAULT_LICENSE_SECRET: &str = "ai-healthcare-system-license-signature-validation-key-2026";
const TRIAL_KEY: &str = "CLINIC-TRIAL-2026";

#[derive(Debug, Deserialize)]
pub struct LicenseActivationPayload {
    pub license_key: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseClaims {
    pub holder: Option<String>,
    pub tier: Option<String>,
    pub exp: Option<usize>,
    pub perpetual: Option<bool>,
    pub modules: Option<Vec<String>>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/status", get(get_licensing_status))
        .route("/activate", post(activate_license))
}

pub fn verify_license(key: &str) -> (bool, String, String, Vec<String>, bool) {
    let clean_key = key.trim();
    if clean_key.is_empty() {
        return (false, "License key is missing".to_string(), "none".to_string(), vec![], false);
    }

    if clean_key == TRIAL_KEY {
        return (
            true,
            "Valid Trial License (Holder: Trial Clinic)".to_string(),
            "enterprise".to_string(),
            vec!["*".to_string()],
            false,
        );
    }

    let secret = env::var("LICENSE_SIGNING_SECRET").unwrap_or_else(|_| DEFAULT_LICENSE_SECRET.to_string());
    let mut validation = Validation::default();
    validation.validate_exp = false;

    match decode::<LicenseClaims>(
        clean_key,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    ) {
        Ok(token_data) => {
            let claims = token_data.claims;
            let holder = claims.holder.unwrap_or_else(|| "Unknown Clinic".to_string());
            let tier = claims.tier.unwrap_or_else(|| "community".to_string());
            let modules = claims.modules.unwrap_or_else(|| vec!["*".to_string()]);
            let perpetual = claims.perpetual.unwrap_or(false);

            (
                true,
                format!("Valid {} License (Holder: {})", tier, holder),
                tier,
                modules,
                perpetual,
            )
        }
        Err(_) => (
            false,
            "Cryptographic signature validation failed".to_string(),
            "none".to_string(),
            vec![],
            false,
        ),
    }
}

/// GET /v1/licensing/status
pub async fn get_licensing_status() -> Json<Value> {
    let raw_key = env::var("LICENSE_KEY").unwrap_or_else(|_| TRIAL_KEY.to_string());
    let key = if raw_key.trim().is_empty() { TRIAL_KEY } else { raw_key.trim() };

    let (is_valid, details, tier, modules, perpetual) = verify_license(key);
    let masked_key = if key.len() > 12 {
        format!("{}...", &key[..12])
    } else {
        key.to_string()
    };

    Json(json!({
        "active_key": masked_key,
        "is_valid": is_valid,
        "tier": tier,
        "details": details,
        "modules": modules,
        "perpetual": perpetual
    }))
}

/// POST /v1/licensing/activate
pub async fn activate_license(
    Json(payload): Json<LicenseActivationPayload>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let clean_key = payload.license_key.trim();
    let (is_valid, details, tier, modules, _) = verify_license(clean_key);

    if !is_valid {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": format!("License activation failed: {}", details)})),
        ));
    }

    unsafe {
        env::set_var("LICENSE_KEY", clean_key);
    }

    Ok(Json(json!({
        "status": "activated",
        "tier": tier,
        "details": details,
        "modules": modules
    })))
}
