use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post, put},
    Json, Router,
};
use chrono::Utc;
use serde::Deserialize;
use serde_json::json;

use crate::auth::AuthenticatedUser;
use crate::models::DiagnosticResult;
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct DiagnosticResultCreate {
    pub order_id: i64,
    pub result_type: String,
    pub title: String,
    pub summary: String,
    pub abnormal_flag: Option<bool>,
    pub status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DiagnosticReviewUpdate {
    pub review_status: Option<String>,
    pub review_note: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DiagnosticUploadCreate {
    pub patient_id: i64,
    pub title: String,
    pub result_type: Option<String>,
    pub summary: Option<String>,
    pub abnormal_flag: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct LabKitOrderRequest {
    pub patient_id: i64,
    pub kit_type: String,
    pub shipping_address: String,
}

#[derive(Debug, Deserialize)]
pub struct ECGAnalyzeRequest {
    pub signal: Vec<f64>,
    pub sampling_rate: Option<f64>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/metrics", get(get_diagnostics_metrics))
        .route("/doctor/patients/{patient_id}/results", get(get_doctor_patient_results))
        .route("/ecg/analyze", post(analyze_ecg_telemetry))
        .route("/lab-kits", post(order_lab_kit))
        .route("/lab-kits/{patient_id}", get(get_lab_kits))
        .route("/patient/results", get(get_patient_results))
        .route("/results", post(post_diagnostic_result))
        .route("/results/{result_id}/review", put(review_diagnostic_result))
        .route("/upload", post(upload_diagnostic_file))
}

async fn post_diagnostic_result(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<DiagnosticResultCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    #[derive(sqlx::FromRow)]
    struct OrderInfo {
        facility_id: Option<i64>,
        encounter_id: Option<i64>,
        patient_id: i64,
        doctor_id: Option<i64>,
        department_id: Option<i64>,
    }

    let order_sql = "SELECT facility_id, encounter_id, patient_id, doctor_id, department_id FROM clinical_orders WHERE id = $1";
    let order: Option<OrderInfo> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(order_sql).bind(payload.order_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(order_sql).bind(payload.order_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    let ord = match order {
        Some(o) => o,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Clinical order not found"})))),
    };

    let status = payload.status.unwrap_or_else(|| "final".to_string());
    let abnormal_flag: i64 = if payload.abnormal_flag.unwrap_or(false) { 1 } else { 0 };

    let insert_sql = r#"
        INSERT INTO diagnostic_results (
            facility_id, order_id, encounter_id, patient_id, doctor_id, department_id,
            result_type, title, summary, abnormal_flag, status, review_status, is_deleted
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'pending_review', 0)
        RETURNING id, facility_id, order_id, encounter_id, patient_id, doctor_id, department_id,
                  result_type, title, summary, abnormal_flag, status, review_status, review_note,
                  reviewed_by_id, reviewed_at, created_at, is_deleted, deleted_at
    "#;

    let result: DiagnosticResult = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, DiagnosticResult>(insert_sql)
                .bind(ord.facility_id)
                .bind(payload.order_id)
                .bind(ord.encounter_id)
                .bind(ord.patient_id)
                .bind(ord.doctor_id)
                .bind(ord.department_id)
                .bind(&payload.result_type)
                .bind(&payload.title)
                .bind(&payload.summary)
                .bind(abnormal_flag)
                .bind(&status)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, DiagnosticResult>(insert_sql)
                .bind(ord.facility_id)
                .bind(payload.order_id)
                .bind(ord.encounter_id)
                .bind(ord.patient_id)
                .bind(ord.doctor_id)
                .bind(ord.department_id)
                .bind(&payload.result_type)
                .bind(&payload.title)
                .bind(&payload.summary)
                .bind(abnormal_flag)
                .bind(&status)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create diagnostic result"})))
    })?;

    // Update clinical order to completed
    let update_ord_sql = "UPDATE clinical_orders SET status = 'completed', completed_at = $1 WHERE id = $2";
    let now = Utc::now().naive_utc();
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_ord_sql).bind(now).bind(payload.order_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_ord_sql).bind(now).bind(payload.order_id).execute(p).await; }
    };

    Ok(Json(result))
}

async fn upload_diagnostic_file(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<DiagnosticUploadCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let result_type = payload.result_type.unwrap_or_else(|| "lab".to_string());
    let summary = payload.summary.unwrap_or_else(|| format!("Uploaded diagnostic attachment for patient #{}", payload.patient_id));
    let abnormal_flag: i64 = if payload.abnormal_flag.unwrap_or(false) { 1 } else { 0 };
    let doctor_id = if user.role == "doctor" { Some(user.id) } else { None };

    let insert_sql = r#"
        INSERT INTO diagnostic_results (
            facility_id, order_id, encounter_id, patient_id, doctor_id, department_id,
            result_type, title, summary, abnormal_flag, status, review_status, is_deleted
        ) VALUES ($1, 0, NULL, $2, $3, NULL, $4, $5, $6, $7, 'final', 'pending_review', 0)
        RETURNING id, facility_id, order_id, encounter_id, patient_id, doctor_id, department_id,
                  result_type, title, summary, abnormal_flag, status, review_status, review_note,
                  reviewed_by_id, reviewed_at, created_at, is_deleted, deleted_at
    "#;

    let res: DiagnosticResult = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, DiagnosticResult>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&result_type)
                .bind(&payload.title)
                .bind(&summary)
                .bind(abnormal_flag)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, DiagnosticResult>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&result_type)
                .bind(&payload.title)
                .bind(&summary)
                .bind(abnormal_flag)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to upload diagnostic file"})))
    })?;

    Ok(Json(json!({
        "result": res,
        "clinical_safety_note": "Uploaded diagnostic documents support decision making and require clinician review."
    })))
}

async fn get_patient_results(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, order_id, encounter_id, patient_id, doctor_id, department_id, result_type, title, summary, abnormal_flag, status, review_status, review_note, reviewed_by_id, reviewed_at, created_at, is_deleted, deleted_at FROM diagnostic_results WHERE patient_id = $1 AND review_status IN ('reviewed', 'needs_follow_up') AND is_deleted = 0 ORDER BY created_at DESC";

    let results: Vec<DiagnosticResult> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(results))
}

async fn get_doctor_patient_results(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, order_id, encounter_id, patient_id, doctor_id, department_id, result_type, title, summary, abnormal_flag, status, review_status, review_note, reviewed_by_id, reviewed_at, created_at, is_deleted, deleted_at FROM diagnostic_results WHERE patient_id = $1 AND is_deleted = 0 ORDER BY created_at DESC";

    let results: Vec<DiagnosticResult> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(json!({
        "patient_id": patient_id,
        "results": results,
        "clinical_safety_note": "Diagnostic results require clinician review and are not AI diagnoses."
    })))
}

async fn review_diagnostic_result(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(result_id): Path<i64>,
    Json(payload): Json<DiagnosticReviewUpdate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let review_status = payload.review_status.unwrap_or_else(|| "reviewed".to_string()).to_lowercase();
    if !["reviewed", "needs_follow_up", "withheld"].contains(&review_status.as_str()) {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Invalid diagnostic review status"}))));
    }

    let now = Utc::now().naive_utc();
    let update_sql = "UPDATE diagnostic_results SET review_status = $1, review_note = $2, reviewed_by_id = $3, reviewed_at = $4 WHERE id = $5";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(&review_status).bind(&payload.review_note).bind(user.id).bind(now).bind(result_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(&review_status).bind(&payload.review_note).bind(user.id).bind(now).bind(result_id).execute(p).await; }
    };

    let get_sql = "SELECT id, facility_id, order_id, encounter_id, patient_id, doctor_id, department_id, result_type, title, summary, abnormal_flag, status, review_status, review_note, reviewed_by_id, reviewed_at, created_at, is_deleted, deleted_at FROM diagnostic_results WHERE id = $1";
    let updated: DiagnosticResult = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(result_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(result_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(updated))
}

async fn get_diagnostics_metrics(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;

    #[derive(sqlx::FromRow)]
    struct DiagMetricRow {
        result_type: String,
        review_status: String,
        abnormal_flag: i64,
    }

    let rows: Vec<DiagMetricRow> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT result_type, review_status, abnormal_flag FROM diagnostic_results WHERE facility_id = $1 AND is_deleted = 0";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
            }
        }
        None => {
            let sql = "SELECT result_type, review_status, abnormal_flag FROM diagnostic_results WHERE is_deleted = 0";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).fetch_all(p).await.unwrap_or_default(),
            }
        }
    };

    let total = rows.len();
    let pending = rows.iter().filter(|r| r.review_status == "pending_review").count();
    let abnormal = rows.iter().filter(|r| r.abnormal_flag != 0).count();

    let mut results_by_type = serde_json::Map::new();
    let mut results_by_status = serde_json::Map::new();

    for r in &rows {
        let t_entry = results_by_type.entry(&r.result_type).or_insert(json!(0));
        if let Some(n) = t_entry.as_i64() {
            *t_entry = json!(n + 1);
        }
        let s_entry = results_by_status.entry(&r.review_status).or_insert(json!(0));
        if let Some(n) = s_entry.as_i64() {
            *s_entry = json!(n + 1);
        }
    }

    Ok(Json(json!({
        "total_results": total,
        "pending_review": pending,
        "abnormal_results": abnormal,
        "results_by_type": results_by_type,
        "results_by_status": results_by_status,
        "clinical_safety_note": "Diagnostics metrics support operations; clinicians interpret results and make care decisions."
    })))
}

async fn order_lab_kit(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(req): Json<LabKitOrderRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role == "patient" && user.id != req.patient_id {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patients can only order kits for themselves"}))));
    }

    let pool = &state.db_pool;
    let title = format!("At-Home Lab Kit - {}", req.kit_type);
    let notes = format!("Shipping Address: {}. Status tracking: ordered -> shipped -> delivered -> results_uploaded.", req.shipping_address);
    let doctor_id = if user.role == "doctor" { Some(user.id) } else { None };

    let insert_sql = r#"
        INSERT INTO clinical_orders (facility_id, patient_id, doctor_id, order_type, title, priority, status, notes)
        VALUES ($1, $2, $3, 'lab', $4, 'routine', 'ordered', $5)
        RETURNING id
    "#;

    let row: (i64,) = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(insert_sql).bind(user.facility_id).bind(req.patient_id).bind(doctor_id).bind(&title).bind(&notes).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(insert_sql).bind(user.facility_id).bind(req.patient_id).bind(doctor_id).bind(&title).bind(&notes).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(json!({
        "order_id": row.0,
        "patient_id": req.patient_id,
        "kit_type": req.kit_type,
        "status": "ordered",
        "shipping_address": req.shipping_address,
        "estimated_delivery": "3-5 business days",
        "message": format!("Successfully ordered at-home {} diagnostic kit.", req.kit_type)
    })))
}

async fn get_lab_kits(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role == "patient" && user.id != patient_id {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patients can only check their own kits"}))));
    }

    let pool = &state.db_pool;
    #[derive(sqlx::FromRow)]
    struct KitOrder {
        id: i64,
        title: String,
        status: String,
        notes: Option<String>,
        created_at: Option<chrono::NaiveDateTime>,
    }

    let sql = "SELECT id, title, status, notes, created_at FROM clinical_orders WHERE patient_id = $1 AND order_type = 'lab' AND title LIKE 'At-Home Lab Kit -%'";
    let orders: Vec<KitOrder> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
    };

    let mut kits = Vec::new();
    for o in orders {
        let kit_type = o.title.replace("At-Home Lab Kit - ", "").replace("At-Home Lab Kit -", "");
        let tracking_status = match o.status.as_str() {
            "completed" => "results_uploaded",
            "in_progress" => "shipped",
            _ => "ordered",
        };
        kits.push(json!({
            "kit_id": o.id,
            "kit_type": kit_type.trim(),
            "ordered_at": o.created_at,
            "tracking_status": tracking_status,
            "tracking_number": format!("1Z999AA1012345{}", o.id),
            "carrier": "UPS Mail Innovations",
            "notes": o.notes
        }));
    }

    let count = kits.len();
    Ok(Json(json!({
        "patient_id": patient_id,
        "kits": kits,
        "total_kits": count,
        "clinical_safety_note": "At-home diagnostic test kits support remote patient monitoring; clinical decisions are made upon physician review of uploaded lab reports."
    })))
}

async fn analyze_ecg_telemetry(
    _user: AuthenticatedUser,
    Json(req): Json<ECGAnalyzeRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if req.signal.is_empty() {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Must provide non-empty signal array"}))));
    }

    let rate = req.sampling_rate.unwrap_or(250.0);
    let res = crate::ecg_dsp::analyze_ecg_waveform(&req.signal, rate);

    Ok(Json(json!({
        "heart_rate_bpm": res.heart_rate_bpm,
        "r_peaks_count": res.r_peaks_count,
        "is_arrhythmia_detected": res.is_arrhythmia_detected,
        "sampling_rate_hz": rate,
        "signal_duration_seconds": req.signal.len() as f64 / rate,
        "clinical_safety_note": "DSP ECG algorithm aids arrhythmia detection; clinical diagnosis requires 12-lead ECG and physician evaluation."
    })))
}
