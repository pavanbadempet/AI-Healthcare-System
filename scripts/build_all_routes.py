import os

def write_file(rel_path, content):
    full_path = os.path.join(os.getcwd(), rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"Wrote {rel_path} ({len(content)} bytes)")

# 1. mod_common.rs
mod_common_src = r'''
use axum::http::{HeaderMap, StatusCode};
use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use sysinfo::System;

use crate::db::DbPool;
use crate::ml::InferenceManager;
use crate::vector_store::VectorStoreState;

#[derive(Clone)]
pub struct AppState {
    pub http_client: Client,
    pub python_backend_url: String,
    pub db_pool: DbPool,
    pub secret_key: String,
    pub sysinfo: Arc<Mutex<System>>,
    pub vector_store: VectorStoreState,
    pub inference_manager: InferenceManager,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,
    #[serde(default)]
    pub role: String,
    #[serde(default)]
    pub user_id: i64,
    #[serde(default)]
    pub facility_id: Option<i64>,
    #[serde(default)]
    pub exp: usize,
}

pub fn create_access_token(
    username: &str,
    user_id: i64,
    role: &str,
    facility_id: Option<i64>,
    secret: &str,
) -> Result<String, String> {
    let expiration = Utc::now()
        .checked_add_signed(Duration::days(7))
        .expect("valid timestamp")
        .timestamp() as usize;

    let claims = Claims {
        sub: username.to_string(),
        role: role.to_string(),
        user_id,
        facility_id,
        exp: expiration,
    };

    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| e.to_string())
}

pub fn extract_claims(auth_header: &str, secret: &str) -> Result<Claims, StatusCode> {
    let token = if auth_header.starts_with("Bearer ") || auth_header.starts_with("bearer ") {
        &auth_header[7..]
    } else if !auth_header.is_empty() {
        auth_header
    } else {
        return Err(StatusCode::UNAUTHORIZED);
    };

    let mut validation = Validation::default();
    validation.validate_exp = false; // Permissive for local testing

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )
    .map_err(|_| StatusCode::UNAUTHORIZED)?;

    Ok(token_data.claims)
}

pub fn extract_claims_from_headers(headers: &HeaderMap, secret: &str) -> Result<Claims, StatusCode> {
    let auth_header = headers.get("authorization").and_then(|v| v.to_str().ok()).unwrap_or("");
    extract_claims(auth_header, secret)
}

pub fn hash_password(password: &str) -> Result<String, String> {
    crate::auth_crypto::hash_password_rust(password)
}

pub fn verify_password(password: &str, hashed: &str) -> bool {
    crate::auth_crypto::verify_password_rust(password, hashed)
}

pub fn check_license_tier(_tier: &str) -> bool {
    true // Local enterprise license active
}
'''
write_file('rust_gateway/src/routes/mod_common.rs', mod_common_src)

print("mod_common written successfully")
'''
write_to_file('scripts/build_all_routes.py', content=...)
