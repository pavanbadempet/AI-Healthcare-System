use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{delete, get, post},
    Json, Router,
};
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, EncodingKey, Header};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use uuid::Uuid;

use crate::models::smart_app::{SmartApp, SmartLaunchContext};
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct SmartAppCreate {
    pub app_name: String,
    pub redirect_uri: String,
    pub launch_url: String,
    pub scopes: String,
}

#[derive(Debug, Deserialize)]
pub struct SmartLaunchRequest {
    pub app_id: i64,
    pub patient_id: i64,
}

#[derive(Debug, Deserialize)]
pub struct TokenExchangeRequest {
    pub grant_type: String,
    pub code: String,
    pub redirect_uri: String,
    pub client_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SmartClaims {
    sub: String,
    patient: String,
    client_id: String,
    scope: String,
    smart_launch_id: String,
    exp: usize,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/apps", get(list_smart_apps).post(register_smart_app))
        .route("/apps/{app_id}", delete(delete_smart_app))
        .route("/launch", post(launch_smart_app))
        .route("/token", post(exchange_token_handler))
}

/// Standalone handler for /.well-known/smart-configuration
pub async fn well_known_smart_configuration() -> Json<Value> {
    Json(json!({
        "authorization_endpoint": "/v1/interop/smart/authorize-url",
        "token_endpoint": "/v1/smart/token",
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
            "none"
        ],
        "grant_types_supported": [
            "authorization_code"
        ],
        "response_types_supported": [
            "code"
        ],
        "scopes_supported": [
            "openid",
            "profile",
            "fhirUser",
            "launch",
            "launch/patient",
            "patient/*.read",
            "patient/Patient.read",
            "patient/Observation.read",
            "patient/Condition.read",
            "offline_access"
        ],
        "capabilities": [
            "launch-standalone",
            "launch-ehr",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "permission-patient",
            "permission-user"
        ],
        "code_challenge_methods_supported": [
            "S256"
        ]
    }))
}

/// GET /v1/smart/apps
pub async fn list_smart_apps(
    State(state): State<AppState>,
) -> Result<Json<Vec<SmartApp>>, (StatusCode, Json<Value>)> {
    let sql = "SELECT * FROM smart_apps WHERE is_active = 1 ORDER BY id DESC";
    let apps: Vec<SmartApp> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).fetch_all(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    Ok(Json(apps))
}

/// POST /v1/smart/apps
pub async fn register_smart_app(
    State(state): State<AppState>,
    Json(payload): Json<SmartAppCreate>,
) -> Result<(StatusCode, Json<SmartApp>), (StatusCode, Json<Value>)> {
    let find_sql = "SELECT * FROM smart_apps WHERE app_name = $1";
    let existing: Option<SmartApp> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(find_sql).bind(&payload.app_name).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(find_sql).bind(&payload.app_name).fetch_optional(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    if let Some(mut app) = existing {
        if app.is_active == 1 {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": "An application with this name is already registered"})),
            ));
        }
        // Reactivate soft-deleted app
        let update_sql = "UPDATE smart_apps SET is_active = 1, redirect_uri = $1, launch_url = $2, scopes = $3 WHERE id = $4";
        match &state.db_pool {
            crate::db::DbPool::Sqlite(p) => {
                sqlx::query(update_sql)
                    .bind(&payload.redirect_uri)
                    .bind(&payload.launch_url)
                    .bind(&payload.scopes)
                    .bind(app.id)
                    .execute(p)
                    .await
                    .map(|_| ())
            }
            crate::db::DbPool::Postgres(p) => {
                sqlx::query(update_sql)
                    .bind(&payload.redirect_uri)
                    .bind(&payload.launch_url)
                    .bind(&payload.scopes)
                    .bind(app.id)
                    .execute(p)
                    .await
                    .map(|_| ())
            }
        }
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

        app.is_active = 1;
        app.redirect_uri = payload.redirect_uri;
        app.launch_url = payload.launch_url;
        app.scopes = payload.scopes;
        return Ok((StatusCode::OK, Json(app)));
    }

    let client_id = Uuid::new_v4().to_string();
    let now = Utc::now().naive_utc();
    let insert_sql = r#"
        INSERT INTO smart_apps (app_name, client_id, redirect_uri, launch_url, scopes, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, 1, $6)
    "#;

    let app_id: i64 = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            let res = sqlx::query(insert_sql)
                .bind(&payload.app_name)
                .bind(&client_id)
                .bind(&payload.redirect_uri)
                .bind(&payload.launch_url)
                .bind(&payload.scopes)
                .bind(now)
                .execute(p)
                .await
                .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;
            res.last_insert_rowid()
        }
        crate::db::DbPool::Postgres(p) => {
            let row: (i64,) = sqlx::query_as(
                r#"
                INSERT INTO smart_apps (app_name, client_id, redirect_uri, launch_url, scopes, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, 1, $6)
                RETURNING id
                "#,
            )
            .bind(&payload.app_name)
            .bind(&client_id)
            .bind(&payload.redirect_uri)
            .bind(&payload.launch_url)
            .bind(&payload.scopes)
            .bind(now)
            .fetch_one(p)
            .await
            .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;
            row.0
        }
    };

    let new_app = SmartApp {
        id: app_id,
        app_name: payload.app_name,
        client_id,
        redirect_uri: payload.redirect_uri,
        launch_url: payload.launch_url,
        scopes: payload.scopes,
        is_active: 1,
        created_at: Some(now),
    };

    Ok((StatusCode::CREATED, Json(new_app)))
}

/// DELETE /v1/smart/apps/{app_id}
pub async fn delete_smart_app(
    State(state): State<AppState>,
    Path(app_id): Path<i64>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let sql = "UPDATE smart_apps SET is_active = 0 WHERE id = $1 AND is_active = 1";
    let rows_affected: u64 = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query(sql).bind(app_id).execute(p).await.map(|r| r.rows_affected()),
        crate::db::DbPool::Postgres(p) => sqlx::query(sql).bind(app_id).execute(p).await.map(|r| r.rows_affected()),
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    if rows_affected == 0 {
        return Err((
            StatusCode::NOT_FOUND,
            Json(json!({"detail": "Application not found"})),
        ));
    }

    Ok(Json(json!({"status": "deleted"})))
}

/// POST /v1/smart/launch
pub async fn launch_smart_app(
    State(state): State<AppState>,
    Json(payload): Json<SmartLaunchRequest>,
) -> Result<Json<SmartLaunchContext>, (StatusCode, Json<Value>)> {
    let app_sql = "SELECT * FROM smart_apps WHERE id = $1 AND is_active = 1";
    let app: Option<SmartApp> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(app_sql).bind(payload.app_id).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(app_sql).bind(payload.app_id).fetch_optional(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let app = match app {
        Some(a) => a,
        None => {
            return Err((
                StatusCode::NOT_FOUND,
                Json(json!({"detail": "Application not found"})),
            ));
        }
    };

    let user_sql = "SELECT * FROM users WHERE id = $1 AND is_deleted = 0";
    let user_exists: Option<crate::models::User> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(user_sql).bind(payload.patient_id).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(user_sql).bind(payload.patient_id).fetch_optional(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    if user_exists.is_none() {
        return Err((
            StatusCode::NOT_FOUND,
            Json(json!({"detail": "Patient not found"})),
        ));
    }

    let launch_token = Uuid::new_v4().to_string();
    let auth_code = Uuid::new_v4().to_string();
    let now = Utc::now().naive_utc();
    let expires_at = (Utc::now() + Duration::minutes(10)).naive_utc();

    let insert_sql = r#"
        INSERT INTO smart_launch_contexts (app_id, patient_id, user_id, launch_token, auth_code, scope, expires_at, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    "#;

    let launch_id: i64 = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            let res = sqlx::query(insert_sql)
                .bind(payload.app_id)
                .bind(payload.patient_id)
                .bind(1i64) // default clinician user context
                .bind(&launch_token)
                .bind(&auth_code)
                .bind(&app.scopes)
                .bind(expires_at)
                .bind(now)
                .execute(p)
                .await
                .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;
            res.last_insert_rowid()
        }
        crate::db::DbPool::Postgres(p) => {
            let row: (i64,) = sqlx::query_as(
                r#"
                INSERT INTO smart_launch_contexts (app_id, patient_id, user_id, launch_token, auth_code, scope, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                "#,
            )
            .bind(payload.app_id)
            .bind(payload.patient_id)
            .bind(1i64)
            .bind(&launch_token)
            .bind(&auth_code)
            .bind(&app.scopes)
            .bind(expires_at)
            .bind(now)
            .fetch_one(p)
            .await
            .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;
            row.0
        }
    };

    let context = SmartLaunchContext {
        id: launch_id,
        app_id: payload.app_id,
        patient_id: payload.patient_id,
        user_id: 1,
        launch_token,
        auth_code: Some(auth_code),
        scope: app.scopes,
        expires_at,
        created_at: Some(now),
    };

    Ok(Json(context))
}

/// POST /v1/smart/token
pub async fn exchange_token_handler(
    State(state): State<AppState>,
    // Can receive either form-urlencoded or JSON payload
    req: axum::extract::Request,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let (_parts, body) = req.into_parts();
    let body_bytes = match http_body_util::BodyExt::collect(body).await {
        Ok(c) => c.to_bytes(),
        Err(e) => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Failed to read body: {}", e)})),
            ));
        }
    };

    let params: TokenExchangeRequest = if let Ok(form) = serde_urlencoded::from_bytes::<TokenExchangeRequest>(&body_bytes) {
        form
    } else if let Ok(json_body) = serde_json::from_slice::<TokenExchangeRequest>(&body_bytes) {
        json_body
    } else {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Invalid token exchange payload. Required: grant_type, code, redirect_uri, client_id"})),
        ));
    };

    if params.grant_type != "authorization_code" {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Unsupported grant_type. Only authorization_code is supported."})),
        ));
    }

    let ctx_sql = "SELECT * FROM smart_launch_contexts WHERE auth_code = $1";
    let launch_ctx: Option<SmartLaunchContext> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(ctx_sql).bind(&params.code).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(ctx_sql).bind(&params.code).fetch_optional(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let launch_ctx = match launch_ctx {
        Some(c) => c,
        None => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": "Invalid authorization code."})),
            ));
        }
    };

    let now = Utc::now().naive_utc();
    if now > launch_ctx.expires_at {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Authorization code has expired."})),
        ));
    }

    let app_sql = "SELECT * FROM smart_apps WHERE id = $1";
    let app: Option<SmartApp> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(app_sql).bind(launch_ctx.app_id).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(app_sql).bind(launch_ctx.app_id).fetch_optional(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let app = match app {
        Some(a) => a,
        None => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": "Client ID mismatch or application not found."})),
            ));
        }
    };

    if app.client_id != params.client_id {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Client ID mismatch."})),
        ));
    }

    if app.redirect_uri != params.redirect_uri {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Redirect URI mismatch."})),
        ));
    }

    let exp = (Utc::now() + Duration::hours(1)).timestamp() as usize;
    let claims = SmartClaims {
        sub: launch_ctx.user_id.to_string(),
        patient: launch_ctx.patient_id.to_string(),
        client_id: params.client_id,
        scope: launch_ctx.scope.clone(),
        smart_launch_id: launch_ctx.id.to_string(),
        exp,
    };

    let access_token = match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.secret_key.as_bytes()),
    ) {
        Ok(t) => t,
        Err(e) => {
            return Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Token signing failed: {}", e)})),
            ));
        }
    };

    Ok(Json(json!({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": launch_ctx.scope,
        "patient": launch_ctx.patient_id.to_string(),
        "need_patient_banner": true
    })))
}
