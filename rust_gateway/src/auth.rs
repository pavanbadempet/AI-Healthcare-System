use axum::{
    body::{Body, Bytes},
    extract::{Request, State},
    http::{HeaderMap, Method, StatusCode, Uri},
    response::{IntoResponse, Response},
    Json,
};
use bcrypt::verify;
use jsonwebtoken::{encode, EncodingKey, Header};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};
use sqlx::FromRow;

use crate::{execute_proxy, AppState};

#[derive(Deserialize)]
struct LoginForm {
    username: String,
    password: String,
}

#[derive(Serialize)]
struct TokenResponse {
    access_token: String,
    token_type: String,
}

#[derive(Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
}

pub async fn login_handler(
    State(state): State<AppState>,
    req: Request,
) -> Result<Response, StatusCode> {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let headers = req.headers().clone();

    // 1. Buffer the body so we can retry on fallback
    let body_result = http_body_util::BodyExt::collect(req.into_body()).await;
    if body_result.is_err() {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    let body_bytes = body_result.unwrap().to_bytes();

    // 2. Try the native Rust implementation
    match try_native_login(&state, &body_bytes).await {
        Ok(response) => {
            println!("Rust natively handled /v1/auth/token");
            return Ok(response);
        }
        Err(e) => {
            eprintln!("Rust native login failed: {:?}. Falling back to Python.", e);
            // Fallthrough to proxy
        }
    }

    // 3. Fallback: Proxy to Python if anything goes wrong natively
    execute_proxy(&state, method, uri, headers, body_bytes).await
}

async fn try_native_login(
    state: &AppState,
    body_bytes: &Bytes,
) -> Result<Response, Box<dyn std::error::Error>> {
    // Parse form data
    let form: LoginForm = serde_urlencoded::from_bytes(body_bytes)?;

#[derive(FromRow)]
struct UserRow {
    id: i64,
    username: String,
    hashed_password: String,
}

    let user_row = sqlx::query_as::<_, UserRow>(
        r#"
        SELECT id, username, hashed_password 
        FROM users 
        WHERE username = $1 AND is_deleted = 0
        "#
    )
    .bind(&form.username)
    .fetch_optional(&state.db_pool)
    .await?;

    let user_row = match user_row {
        Some(u) => u,
        None => {
            return Ok((
                StatusCode::UNAUTHORIZED,
                Json(serde_json::json!({"detail": "Incorrect username or password"})),
            )
                .into_response());
        }
    };

    // Verify password
    let password_valid = match verify(&form.password, &user_row.hashed_password) {
        Ok(valid) => valid,
        Err(_) => false,
    };

    if !password_valid {
        return Ok((
            StatusCode::UNAUTHORIZED,
            Json(serde_json::json!({"detail": "Incorrect username or password"})),
        )
            .into_response());
    }

    // Generate JWT
    let exp = SystemTime::now()
        .duration_since(UNIX_EPOCH)?
        .as_secs() as usize
        + (525600 * 60); // Match Python's default ACCESS_TOKEN_EXPIRE_MINUTES (1 year)

    let claims = Claims {
        sub: user_row.username.clone(),
        exp,
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.secret_key.as_bytes()),
    )?;

    // Audit Log logic in Rust is skipped for now, but in Python it inserts to audit_logs. 
    // To ensure exact behavior we could just insert it, or fallback.
    // If we must insert it to match Python exactly:
    let now = chrono::Utc::now().to_rfc3339();
    let details = serde_json::json!({
        "resource_type": "auth_session",
        "outcome": "success",
        "occurred_at": now
    }).to_string();

    sqlx::query(
        r#"
        INSERT INTO audit_logs (admin_id, target_user_id, action, details)
        VALUES ($1, $2, $3, $4)
        "#
    )
    .bind(user_row.id)
    .bind(user_row.id)
    .bind("LOGIN_SUCCESS")
    .bind(details)
    .execute(&state.db_pool)
    .await?;

    Ok(Json(TokenResponse {
        access_token: token,
        token_type: "bearer".to_string(),
    })
    .into_response())
}

#[derive(Serialize)]
pub struct UserProfile {
    username: String,
    email: Option<String>,
    full_name: Option<String>,
    gender: Option<String>,
    dob: Option<String>,
    height: Option<f64>,
    weight: Option<f64>,
    blood_type: Option<String>,
    existing_ailments: Option<String>,
    profile_picture: Option<String>,
    about_me: Option<String>,
    diet: Option<String>,
    activity_level: Option<String>,
    sleep_hours: Option<f64>,
    stress_level: Option<String>,
    specialization: Option<String>,
    allow_data_collection: bool,
    role: String,
}

pub async fn profile_handler(
    State(state): State<AppState>,
    req: Request,
) -> Result<Response, StatusCode> {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let headers = req.headers().clone();

    // Buffer the body
    let body_result = http_body_util::BodyExt::collect(req.into_body()).await;
    if body_result.is_err() {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    let body_bytes = body_result.unwrap().to_bytes();

    match try_native_profile(&state, &headers).await {
        Ok(response) => {
            println!("Rust natively handled /v1/auth/profile");
            return Ok(response);
        }
        Err(e) => {
            eprintln!("Rust native profile failed: {:?}. Falling back to Python.", e);
        }
    }

    // Fallback proxy
    execute_proxy(&state, method, uri, headers, body_bytes).await
}

async fn try_native_profile(
    state: &AppState,
    headers: &axum::http::HeaderMap,
) -> Result<Response, Box<dyn std::error::Error>> {
    // 1. Extract Bearer token
    let auth_header = headers
        .get("Authorization")
        .ok_or("Missing Authorization header")?
        .to_str()?;

    if !auth_header.starts_with("Bearer ") {
        return Err("Invalid Authorization header format".into());
    }
    let token = &auth_header[7..];

    // 2. Decode JWT
    let token_data = jsonwebtoken::decode::<Claims>(
        token,
        &jsonwebtoken::DecodingKey::from_secret(state.secret_key.as_bytes()),
        &jsonwebtoken::Validation::new(jsonwebtoken::Algorithm::HS256),
    )?;

#[derive(FromRow)]
struct UserProfileRow {
    username: String,
    email: Option<String>,
    full_name: Option<String>,
    gender: Option<String>,
    dob: Option<String>,
    height: Option<f64>,
    weight: Option<f64>,
    blood_type: Option<String>,
    existing_ailments: Option<String>,
    profile_picture: Option<String>,
    about_me: Option<String>,
    diet: Option<String>,
    activity_level: Option<String>,
    sleep_hours: Option<f64>,
    stress_level: Option<String>,
    specialization: Option<String>,
    allow_data_collection: i64,
    role: String,
}

    let user_row = sqlx::query_as::<_, UserProfileRow>(
        r#"
        SELECT 
            username, email, full_name, gender, dob, height, weight, 
            blood_type, existing_ailments, profile_picture, about_me, 
            diet, activity_level, sleep_hours, stress_level, specialization, 
            allow_data_collection, role
        FROM users 
        WHERE username = $1 AND is_deleted = 0
        "#
    )
    .bind(&token_data.claims.sub)
    .fetch_optional(&state.db_pool)
    .await?;

    let u = user_row.ok_or("User not found")?;

    let profile = UserProfile {
        username: u.username.clone(),
        email: u.email,
        full_name: u.full_name,
        gender: u.gender,
        dob: u.dob,
        height: u.height,
        weight: u.weight,
        blood_type: u.blood_type,
        existing_ailments: u.existing_ailments,
        profile_picture: u.profile_picture,
        about_me: u.about_me,
        diet: u.diet,
        activity_level: u.activity_level,
        sleep_hours: u.sleep_hours,
        stress_level: u.stress_level,
        specialization: u.specialization,
        allow_data_collection: u.allow_data_collection != 0,
        role: u.role.clone(),
    };

    Ok(Json(profile).into_response())
}

#[derive(Clone, Serialize, Deserialize)]
pub struct AuthenticatedUser {
    pub id: i64,
    pub username: String,
    pub role: String,
    pub facility_id: Option<i64>,
}

impl axum::extract::FromRequestParts<AppState> for AuthenticatedUser
{
    type Rejection = (StatusCode, Json<serde_json::Value>);

    async fn from_request_parts(
        parts: &mut axum::http::request::Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        match extract_user(state, &parts.headers).await {
            Ok(user) => Ok(user),
            Err(_e) => {
                Err((
                    StatusCode::UNAUTHORIZED,
                    Json(serde_json::json!({"detail": "Not authenticated"})),
                ))
            }
        }
    }
}

pub async fn extract_user(
    state: &AppState,
    headers: &axum::http::HeaderMap,
) -> Result<AuthenticatedUser, Box<dyn std::error::Error>> {
    let auth_header = headers
        .get("Authorization")
        .ok_or("Missing Authorization header")?
        .to_str()?;

    if !auth_header.starts_with("Bearer ") {
        return Err("Invalid Authorization header format".into());
    }
    let token = &auth_header[7..];

    let token_data = jsonwebtoken::decode::<Claims>(
        token,
        &jsonwebtoken::DecodingKey::from_secret(state.secret_key.as_bytes()),
        &jsonwebtoken::Validation::new(jsonwebtoken::Algorithm::HS256),
    )?;

#[derive(FromRow)]
struct AuthUserRow {
    id: i64,
    username: String,
    role: String,
    facility_id: Option<i64>,
}

    let user_row = sqlx::query_as::<_, AuthUserRow>(
        r#"SELECT id, username, role, facility_id FROM users WHERE username = $1 AND is_deleted = 0"#
    )
    .bind(&token_data.claims.sub)
    .fetch_optional(&state.db_pool)
    .await?;

    let u = user_row.ok_or("User not found")?;
    Ok(AuthenticatedUser {
        id: u.id,
        username: u.username.clone(),
        role: u.role.clone(),
        facility_id: u.facility_id,
    })
}
