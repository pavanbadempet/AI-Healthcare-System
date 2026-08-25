use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::Deserialize;
use serde_json::json;
use sqlx::FromRow;

use crate::auth::AuthenticatedUser;
use crate::models::CareEvent;
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct CareEventCreate {
    pub patient_id: i64,
    pub event_type: String,
    pub title: String,
    pub summary: Option<String>,
    pub severity: Option<String>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct FeedQuery {
    pub after_id: Option<i64>,
    pub limit: Option<i64>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/dispatch", post(dispatch_care_event))
        .route("/patient/feed", get(get_patient_event_feed))
        .route("/doctor/patients/{patient_id}/feed", get(get_doctor_patient_event_feed))
        .route("/admin/recent", get(get_admin_recent_events))
        .route("/admin/patients/{patient_id}/feed", get(get_admin_patient_event_feed))
        .route("/admin/metrics", get(get_admin_event_metrics))
}

const ALLOWED_EVENT_TYPES: &[&str] = &[
    "code-blue",
    "nurse-call",
    "rapid-response",
    "fall-alert",
    "medication-alert",
    "discharge-initiated",
];

async fn dispatch_care_event(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<CareEventCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if !ALLOWED_EVENT_TYPES.contains(&payload.event_type.as_str()) {
        return Err((
            StatusCode::UNPROCESSABLE_ENTITY,
            Json(json!({
                "detail": format!("Invalid event_type '{}'. Allowed: {:?}", payload.event_type, ALLOWED_EVENT_TYPES)
            })),
        ));
    }

    let severity = payload.severity.unwrap_or_else(|| "info".to_string());
    let sql = r#"
        INSERT INTO care_events (facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at
    "#;

    let event: CareEvent = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.department_id)
                .bind(&payload.event_type)
                .bind(&payload.title)
                .bind(&payload.summary)
                .bind(&severity)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.department_id)
                .bind(&payload.event_type)
                .bind(&payload.title)
                .bind(&payload.summary)
                .bind(&severity)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    Ok(Json(json!({
        "event": event,
        "clinical_safety_note": "Care events are operational records and do not replace clinician review."
    })))
}

async fn get_patient_event_feed(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Query(query): Query<FeedQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let limit = query.limit.unwrap_or(100).clamp(1, 500);
    let after_id = query.after_id.unwrap_or(0);

    let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE patient_id = $1 AND id > $2 ORDER BY id ASC LIMIT $3";

    let events: Vec<CareEvent> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(user.id)
                .bind(after_id)
                .bind(limit)
                .fetch_all(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(user.id)
                .bind(after_id)
                .bind(limit)
                .fetch_all(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    let next_after_id = events.iter().map(|e| e.id).max();

    Ok(Json(json!({
        "events": events,
        "next_after_id": next_after_id,
        "clinical_safety_note": "Care events are operational records and do not replace clinician review."
    })))
}

async fn get_doctor_patient_event_feed(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
    Query(query): Query<FeedQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let limit = query.limit.unwrap_or(100).clamp(1, 500);
    let after_id = query.after_id.unwrap_or(0);

    let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE patient_id = $1 AND id > $2 ORDER BY id ASC LIMIT $3";

    let events: Vec<CareEvent> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(patient_id)
                .bind(after_id)
                .bind(limit)
                .fetch_all(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, CareEvent>(sql)
                .bind(patient_id)
                .bind(after_id)
                .bind(limit)
                .fetch_all(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    let next_after_id = events.iter().map(|e| e.id).max();

    Ok(Json(json!({
        "patient_id": patient_id,
        "events": events,
        "next_after_id": next_after_id,
        "clinical_safety_note": "Care events are operational records and do not replace clinician review."
    })))
}

async fn get_admin_recent_events(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Query(query): Query<FeedQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let limit = query.limit.unwrap_or(100).clamp(1, 500);
    let after_id = query.after_id.unwrap_or(0);

    let events: Vec<CareEvent> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE facility_id = $1 AND id > $2 ORDER BY id ASC LIMIT $3";
            match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, CareEvent>(sql).bind(fid).bind(after_id).bind(limit).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, CareEvent>(sql).bind(fid).bind(after_id).bind(limit).fetch_all(p).await,
            }
        }
        None => {
            let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE id > $1 ORDER BY id ASC LIMIT $2";
            match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, CareEvent>(sql).bind(after_id).bind(limit).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, CareEvent>(sql).bind(after_id).bind(limit).fetch_all(p).await,
            }
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    let next_after_id = events.iter().map(|e| e.id).max();

    Ok(Json(json!({
        "events": events,
        "next_after_id": next_after_id,
        "clinical_safety_note": "Care events are operational records and do not replace clinician review."
    })))
}

async fn get_admin_patient_event_feed(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
    Query(query): Query<FeedQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let limit = query.limit.unwrap_or(100).clamp(1, 500);
    let after_id = query.after_id.unwrap_or(0);

    let events: Vec<CareEvent> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE patient_id = $1 AND facility_id = $2 AND id > $3 ORDER BY id ASC LIMIT $4";
            match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, CareEvent>(sql).bind(patient_id).bind(fid).bind(after_id).bind(limit).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, CareEvent>(sql).bind(patient_id).bind(fid).bind(after_id).bind(limit).fetch_all(p).await,
            }
        }
        None => {
            let sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE patient_id = $1 AND id > $2 ORDER BY id ASC LIMIT $3";
            match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, CareEvent>(sql).bind(patient_id).bind(after_id).bind(limit).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, CareEvent>(sql).bind(patient_id).bind(after_id).bind(limit).fetch_all(p).await,
            }
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    let next_after_id = events.iter().map(|e| e.id).max();

    Ok(Json(json!({
        "patient_id": patient_id,
        "events": events,
        "next_after_id": next_after_id,
        "clinical_safety_note": "Care events are operational records and do not replace clinician review."
    })))
}

#[derive(FromRow)]
struct EventTypeCount {
    event_type: String,
    count: i64,
}

#[derive(FromRow)]
struct SeverityCount {
    severity: String,
    count: i64,
}

async fn get_admin_event_metrics(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let (events_by_type, events_by_severity, total_events) = match user.facility_id {
        Some(fid) => {
            let sql_type = "SELECT event_type, COUNT(*) as count FROM care_events WHERE facility_id = $1 GROUP BY event_type";
            let sql_sev = "SELECT severity, COUNT(*) as count FROM care_events WHERE facility_id = $1 GROUP BY severity";
            let sql_total = "SELECT COUNT(*) FROM care_events WHERE facility_id = $1";

            let (types, sevs, total): (Vec<EventTypeCount>, Vec<SeverityCount>, (i64,)) = match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => {
                    let t = sqlx::query_as(sql_type).bind(fid).fetch_all(p).await.unwrap_or_default();
                    let s = sqlx::query_as(sql_sev).bind(fid).fetch_all(p).await.unwrap_or_default();
                    let tot = sqlx::query_as(sql_total).bind(fid).fetch_one(p).await.unwrap_or((0,));
                    (t, s, tot)
                }
                crate::db::DbPool::Postgres(p) => {
                    let t = sqlx::query_as(sql_type).bind(fid).fetch_all(p).await.unwrap_or_default();
                    let s = sqlx::query_as(sql_sev).bind(fid).fetch_all(p).await.unwrap_or_default();
                    let tot = sqlx::query_as(sql_total).bind(fid).fetch_one(p).await.unwrap_or((0,));
                    (t, s, tot)
                }
            };
            (types, sevs, total.0)
        }
        None => {
            let sql_type = "SELECT event_type, COUNT(*) as count FROM care_events GROUP BY event_type";
            let sql_sev = "SELECT severity, COUNT(*) as count FROM care_events GROUP BY severity";
            let sql_total = "SELECT COUNT(*) FROM care_events";

            let (types, sevs, total): (Vec<EventTypeCount>, Vec<SeverityCount>, (i64,)) = match &state.db_pool {
                crate::db::DbPool::Sqlite(p) => {
                    let t = sqlx::query_as(sql_type).fetch_all(p).await.unwrap_or_default();
                    let s = sqlx::query_as(sql_sev).fetch_all(p).await.unwrap_or_default();
                    let tot = sqlx::query_as(sql_total).fetch_one(p).await.unwrap_or((0,));
                    (t, s, tot)
                }
                crate::db::DbPool::Postgres(p) => {
                    let t = sqlx::query_as(sql_type).fetch_all(p).await.unwrap_or_default();
                    let s = sqlx::query_as(sql_sev).fetch_all(p).await.unwrap_or_default();
                    let tot = sqlx::query_as(sql_total).fetch_one(p).await.unwrap_or((0,));
                    (t, s, tot)
                }
            };
            (types, sevs, total.0)
        }
    };

    let mut type_map = serde_json::Map::new();
    for row in events_by_type {
        type_map.insert(row.event_type, json!(row.count));
    }

    let mut sev_map = serde_json::Map::new();
    for row in events_by_severity {
        sev_map.insert(row.severity, json!(row.count));
    }

    Ok(Json(json!({
        "total_events": total_events,
        "events_by_type": type_map,
        "events_by_severity": sev_map,
        "operations_note": "Care event metrics support operational dashboards and do not represent clinical diagnoses."
    })))
}
