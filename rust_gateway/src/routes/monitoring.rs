use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post, put},
    Json, Router,
};
use chrono::{NaiveDateTime, Utc};
use serde::Deserialize;
use serde_json::json;

use crate::auth::AuthenticatedUser;
use crate::models::{MonitoringSignal, VitalObservation};
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct VitalObservationCreate {
    pub patient_id: i64,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub source: Option<String>,
    pub heart_rate: Option<f64>,
    pub systolic_bp: Option<f64>,
    pub diastolic_bp: Option<f64>,
    pub spo2: Option<f64>,
    pub temperature_c: Option<f64>,
    pub respiratory_rate: Option<f64>,
    pub blood_glucose: Option<f64>,
    pub observed_at: Option<NaiveDateTime>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/patterns", get(get_admin_patterns))
        .route("/doctor/patients/{patient_id}/signals", get(get_patient_signals_for_doctor))
        .route("/doctor/patterns", get(get_doctor_patterns))
        .route("/patient/vitals", get(get_patient_vitals))
        .route("/vitals", post(submit_vitals))
        .route("/signals/{signal_id}/resolve", put(resolve_monitoring_signal))
}

async fn submit_vitals(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<VitalObservationCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    if user.role == "patient" && user.id != payload.patient_id {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patients can submit only their own vitals"}))));
    }

    let observed_at = payload.observed_at.unwrap_or_else(|| Utc::now().naive_utc());
    let source = payload.source.unwrap_or_else(|| "manual".to_string());
    let facility_id = user.facility_id;

    let insert_vital_sql = r#"
        INSERT INTO vital_observations (
            facility_id, patient_id, recorded_by_id, encounter_id, department_id,
            source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c,
            respiratory_rate, blood_glucose, observed_at, is_deleted
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 0)
        RETURNING id, facility_id, patient_id, recorded_by_id, encounter_id, department_id,
                  source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c,
                  respiratory_rate, blood_glucose, observed_at, created_at, is_deleted, deleted_at
    "#;

    let vital: VitalObservation = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, VitalObservation>(insert_vital_sql)
                .bind(facility_id)
                .bind(payload.patient_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.department_id)
                .bind(&source)
                .bind(payload.heart_rate)
                .bind(payload.systolic_bp)
                .bind(payload.diastolic_bp)
                .bind(payload.spo2)
                .bind(payload.temperature_c)
                .bind(payload.respiratory_rate)
                .bind(payload.blood_glucose)
                .bind(observed_at)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, VitalObservation>(insert_vital_sql)
                .bind(facility_id)
                .bind(payload.patient_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.department_id)
                .bind(&source)
                .bind(payload.heart_rate)
                .bind(payload.systolic_bp)
                .bind(payload.diastolic_bp)
                .bind(payload.spo2)
                .bind(payload.temperature_c)
                .bind(payload.respiratory_rate)
                .bind(payload.blood_glucose)
                .bind(observed_at)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to record vitals"})))
    })?;

    // Check deterministic monitoring signals
    let mut generated_signals: Vec<MonitoringSignal> = Vec::new();

    let check_signal = |sig_type: &str, sev: &str, title: &str, summary: &str| -> Option<(String, String, String, String)> {
        Some((sig_type.to_string(), sev.to_string(), title.to_string(), summary.to_string()))
    };

    let mut signal_defs = Vec::new();

    if let Some(spo2) = vital.spo2 {
        if spo2 < 94.0 {
            let sev = if spo2 < 90.0 { "critical" } else { "warning" };
            signal_defs.push(check_signal(
                "oxygen_saturation",
                sev,
                "Oxygen saturation needs review",
                &format!("Recent SpO2 ({:.0}%) is below nominal threshold (94%).", spo2),
            ).unwrap());
        }
    }

    if let (Some(sbp), Some(dbp)) = (vital.systolic_bp, vital.diastolic_bp) {
        if sbp >= 140.0 || dbp >= 90.0 {
            let sev = if sbp >= 180.0 || dbp >= 120.0 { "critical" } else { "warning" };
            signal_defs.push(check_signal(
                "blood_pressure",
                sev,
                "Blood pressure needs review",
                &format!("Recent BP ({:.0}/{:.0} mmHg) is elevated.", sbp, dbp),
            ).unwrap());
        }
    }

    if let Some(hr) = vital.heart_rate {
        if hr < 50.0 || hr > 120.0 {
            let sev = if hr < 40.0 || hr > 140.0 { "critical" } else { "warning" };
            signal_defs.push(check_signal(
                "heart_rate",
                sev,
                "Heart rate needs review",
                &format!("Recent HR ({:.0} bpm) is out of nominal range.", hr),
            ).unwrap());
        }
    }

    let insert_sig_sql = r#"
        INSERT INTO monitoring_signals (
            facility_id, patient_id, vital_observation_id, encounter_id, department_id,
            signal_type, severity, title, summary, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'open')
        RETURNING id, facility_id, patient_id, vital_observation_id, encounter_id, department_id,
                  signal_type, severity, title, summary, status, created_at
    "#;

    for (stype, ssev, stitle, ssum) in signal_defs {
        let sig: Result<MonitoringSignal, sqlx::Error> = match pool {
            crate::db::DbPool::Sqlite(p) => {
                sqlx::query_as::<_, MonitoringSignal>(insert_sig_sql)
                    .bind(facility_id)
                    .bind(vital.patient_id)
                    .bind(vital.id)
                    .bind(vital.encounter_id)
                    .bind(vital.department_id)
                    .bind(stype)
                    .bind(ssev)
                    .bind(stitle)
                    .bind(ssum)
                    .fetch_one(p)
                    .await
            }
            crate::db::DbPool::Postgres(p) => {
                sqlx::query_as::<_, MonitoringSignal>(insert_sig_sql)
                    .bind(facility_id)
                    .bind(vital.patient_id)
                    .bind(vital.id)
                    .bind(vital.encounter_id)
                    .bind(vital.department_id)
                    .bind(stype)
                    .bind(ssev)
                    .bind(stitle)
                    .bind(ssum)
                    .fetch_one(p)
                    .await
            }
        };

        if let Ok(s) = sig {
            generated_signals.push(s);
        }
    }

    Ok(Json(json!({
        "vital": vital,
        "signals": generated_signals
    })))
}

async fn get_patient_vitals(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, patient_id, recorded_by_id, encounter_id, department_id, source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c, respiratory_rate, blood_glucose, observed_at, created_at, is_deleted, deleted_at FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 100";

    let vitals: Vec<VitalObservation> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(vitals))
}

async fn get_patient_signals_for_doctor(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let vitals_sql = "SELECT id, facility_id, patient_id, recorded_by_id, encounter_id, department_id, source, heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c, respiratory_rate, blood_glucose, observed_at, created_at, is_deleted, deleted_at FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 10";
    let signals_sql = "SELECT id, facility_id, patient_id, vital_observation_id, encounter_id, department_id, signal_type, severity, title, summary, status, created_at FROM monitoring_signals WHERE patient_id = $1 AND status IN ('open', 'acknowledged') ORDER BY created_at DESC";

    let (vitals, signals): (Vec<VitalObservation>, Vec<MonitoringSignal>) = match pool {
        crate::db::DbPool::Sqlite(p) => {
            let v = sqlx::query_as(vitals_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default();
            let s = sqlx::query_as(signals_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default();
            (v, s)
        }
        crate::db::DbPool::Postgres(p) => {
            let v = sqlx::query_as(vitals_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default();
            let s = sqlx::query_as(signals_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default();
            (v, s)
        }
    };

    Ok(Json(json!({
        "patient_id": patient_id,
        "latest_vitals": vitals,
        "open_signals": signals,
        "clinical_safety_note": "Signals highlight patterns for clinician review and are not final clinical conclusions."
    })))
}

async fn resolve_monitoring_signal(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(signal_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let get_sql = "SELECT id, facility_id, patient_id, vital_observation_id, encounter_id, department_id, signal_type, severity, title, summary, status, created_at FROM monitoring_signals WHERE id = $1";
    let signal: Option<MonitoringSignal> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(signal_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(signal_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    let signal = match signal {
        Some(s) => s,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Monitoring signal not found"})))),
    };

    if signal.status == "resolved" {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Monitoring signal is already resolved"}))));
    }

    let update_sql = "UPDATE monitoring_signals SET status = 'resolved' WHERE id = $1";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(signal_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(signal_id).execute(p).await; }
    };

    let updated: MonitoringSignal = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(signal_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(signal_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(updated))
}

async fn get_doctor_patterns(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let sql_vitals = "SELECT COUNT(*) FROM vital_observations WHERE is_deleted = 0";
    let sql_signals = "SELECT COUNT(*) FROM monitoring_signals WHERE status IN ('open', 'acknowledged')";
    let sql_patients = "SELECT COUNT(DISTINCT patient_id) FROM encounters";

    let (v_count, s_count, p_count): ((i64,), (i64,), (i64,)) = match pool {
        crate::db::DbPool::Sqlite(p) => (
            sqlx::query_as(sql_vitals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_signals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_patients).fetch_one(p).await.unwrap_or((0,)),
        ),
        crate::db::DbPool::Postgres(p) => (
            sqlx::query_as(sql_vitals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_signals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_patients).fetch_one(p).await.unwrap_or((0,)),
        ),
    };

    Ok(Json(json!({
        "assigned_patient_count": p_count.0,
        "total_vital_observations": v_count.0,
        "open_signals": s_count.0,
        "clinical_safety_note": "Pattern summaries support clinician review and are not diagnoses."
    })))
}

async fn get_admin_patterns(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let sql_vitals = "SELECT COUNT(*) FROM vital_observations WHERE is_deleted = 0";
    let sql_signals = "SELECT signal_type, severity, COUNT(*) as count FROM monitoring_signals GROUP BY signal_type, severity";

    #[derive(sqlx::FromRow)]
    struct SignalGroupRow {
        signal_type: String,
        severity: String,
        count: i64,
    }

    let (v_count, sig_rows): ((i64,), Vec<SignalGroupRow>) = match pool {
        crate::db::DbPool::Sqlite(p) => (
            sqlx::query_as(sql_vitals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_signals).fetch_all(p).await.unwrap_or_default(),
        ),
        crate::db::DbPool::Postgres(p) => (
            sqlx::query_as(sql_vitals).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(sql_signals).fetch_all(p).await.unwrap_or_default(),
        ),
    };

    let mut signals_by_type = serde_json::Map::new();
    let mut signals_by_severity = serde_json::Map::new();
    let mut open_signals = 0;

    for r in sig_rows {
        open_signals += r.count;
        let t_entry = signals_by_type.entry(&r.signal_type).or_insert(json!(0));
        if let Some(n) = t_entry.as_i64() {
            *t_entry = json!(n + r.count);
        }
        let s_entry = signals_by_severity.entry(&r.severity).or_insert(json!(0));
        if let Some(n) = s_entry.as_i64() {
            *s_entry = json!(n + r.count);
        }
    }

    Ok(Json(json!({
        "total_vital_observations": v_count.0,
        "open_signals": open_signals,
        "signals_by_type": signals_by_type,
        "signals_by_severity": signals_by_severity,
        "clinical_safety_note": "Monitoring patterns support clinician and administrator review; clinicians make care decisions."
    })))
}
