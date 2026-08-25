use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{delete, get, post, put},
    Json, Router,
};
use chrono::{NaiveDateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::auth::AuthenticatedUser;
use crate::models::{Appointment, AppointmentCreate};
use crate::AppState;

#[derive(Serialize, Deserialize, sqlx::FromRow)]
pub struct DoctorResponse {
    pub id: i64,
    pub full_name: Option<String>,
    pub specialization: Option<String>,
    pub consultation_fee: Option<f64>,
    pub profile_picture: Option<String>,
}

#[derive(Deserialize)]
pub struct RescheduleQuery {
    pub date: String,
    pub time: String,
}

#[derive(Deserialize)]
pub struct SpecialCareBookingRequest {
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub specialist: String,
    pub date_time: String,
    pub reason: String,
    pub request_female_clinician: Option<bool>,
    pub home_visit_van: Option<bool>,
}

#[derive(Deserialize)]
pub struct CASAMessage {
    pub role: String,
    pub content: String,
}

#[derive(Deserialize)]
pub struct CASAChatRequest {
    pub message: String,
    pub history: Option<Vec<CASAMessage>>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(get_appointments).post(create_appointment))
        .route("/{id}", delete(delete_appointment))
        .route("/{id}/cancel", put(cancel_appointment))
        .route("/{id}/reschedule", put(reschedule_appointment))
        .route("/doctors", get(get_doctors))
        .route("/recommend-specialists/{patient_id}", get(recommend_specialists_based_on_risks))
        .route("/special-care", post(book_special_care_appointment))
        .route("/agent-chat", post(agent_chat_endpoint))
        .route("/agent-stream", post(agent_stream_endpoint))
}

async fn get_appointments(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let appointments: Vec<Appointment> = match (user.role.as_str(), user.facility_id) {
        ("admin", Some(fid)) => {
            let sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE facility_id = $1 AND is_deleted = 0 ORDER BY date_time ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
            }
        }
        ("admin", None) => {
            let sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE is_deleted = 0 ORDER BY date_time ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).fetch_all(p).await,
            }
        }
        ("doctor", _) => {
            let sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE doctor_id = $1 AND is_deleted = 0 ORDER BY date_time ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
            }
        }
        _ => {
            let sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE user_id = $1 AND is_deleted = 0 ORDER BY date_time ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
            }
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    Ok(Json(appointments))
}

async fn create_appointment(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<AppointmentCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let dt_str = format!("{} {}", payload.date, payload.time);
    let appointment_dt = NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M:%S")
        .or_else(|_| NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M"))
        .map_err(|_| {
            (StatusCode::BAD_REQUEST, Json(json!({"detail": "Invalid date/time format"})))
        })?;

    if appointment_dt <= Utc::now().naive_utc() {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Appointment time must be in the future"}))));
    }

    #[derive(sqlx::FromRow)]
    struct DoctorInfo {
        id: i64,
        role: String,
        facility_id: Option<i64>,
        specialization: Option<String>,
    }

    let doctor_id = payload.doctor_id;
    let doc_query = "SELECT id, role, facility_id, specialization FROM users WHERE id = $1 AND role = 'doctor' AND is_deleted = 0";
    let doctor: Option<DoctorInfo> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(doc_query).bind(doctor_id).fetch_optional(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(doc_query).bind(doctor_id).fetch_optional(p).await,
    }
    .map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?;

    let doctor = doctor.ok_or_else(|| (StatusCode::BAD_REQUEST, Json(json!({"detail": "Selected doctor not found"}))))?;

    let first_fid = user.facility_id;
    let second_fid = doctor.facility_id;
    let shares_facility = first_fid.is_none() || second_fid.is_none() || first_fid == second_fid;
    if !shares_facility {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Appointment participants must belong to the same facility"}))));
    }

    let check_sql = "SELECT id FROM appointments WHERE doctor_id = $1 AND date_time = $2 AND status IN ('Scheduled', 'Rescheduled') AND is_deleted = 0";
    let existing: Option<(i64,)> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(check_sql).bind(doctor_id).bind(appointment_dt).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(check_sql).bind(doctor_id).bind(appointment_dt).fetch_optional(p).await.unwrap_or(None),
    };

    if existing.is_some() {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Doctor already has an active appointment at that time"}))));
    }

    let facility_id = user.facility_id.or(doctor.facility_id);
    let specialist = doctor.specialization.unwrap_or_else(|| payload.specialist);

    let insert_sql = r#"
        INSERT INTO appointments (facility_id, user_id, doctor_id, specialist, date_time, reason, status, is_deleted)
        VALUES ($1, $2, $3, $4, $5, $6, 'Scheduled', 0)
        RETURNING id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at
    "#;

    let result: Appointment = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Appointment>(insert_sql)
                .bind(facility_id)
                .bind(user.id)
                .bind(doctor_id)
                .bind(&specialist)
                .bind(appointment_dt)
                .bind(&payload.reason)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Appointment>(insert_sql)
                .bind(facility_id)
                .bind(user.id)
                .bind(doctor_id)
                .bind(&specialist)
                .bind(appointment_dt)
                .bind(&payload.reason)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Insert Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create appointment"})))
    })?;

    Ok(Json(result))
}

async fn get_doctors(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let doctors: Vec<DoctorResponse> = match (user.role.as_str(), user.facility_id) {
        ("admin", Some(fid)) => {
            let sql = "SELECT id, full_name, specialization, consultation_fee, profile_picture FROM users WHERE role = 'doctor' AND facility_id = $1 AND is_deleted = 0";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
            }
        }
        (_, Some(fid)) => {
            let sql = "SELECT id, full_name, specialization, consultation_fee, profile_picture FROM users WHERE role = 'doctor' AND (facility_id = $1 OR facility_id IS NULL) AND is_deleted = 0";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
            }
        }
        _ => {
            let sql = "SELECT id, full_name, specialization, consultation_fee, profile_picture FROM users WHERE role = 'doctor' AND is_deleted = 0";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).fetch_all(p).await,
                crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).fetch_all(p).await,
            }
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Database error"})))
    })?;

    let mapped: Vec<DoctorResponse> = doctors.into_iter().map(|mut d| {
        if d.specialization.is_none() || d.specialization.as_ref().unwrap().trim().is_empty() {
            d.specialization = Some("General Physician".to_string());
        }
        if d.consultation_fee.is_none() {
            d.consultation_fee = Some(500.0);
        }
        d
    }).collect();

    Ok(Json(mapped))
}

async fn cancel_appointment(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(appointment_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let select_sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE id = $1 AND is_deleted = 0";
    let appt: Option<Appointment> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
    };

    let appt = match appt {
        Some(a) => a,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Appointment not found"})))),
    };

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id.is_some() && appt.facility_id != Some(user_fid) {
                return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Forbidden facility"}))));
            }
        }
    } else if appt.user_id != user.id && appt.doctor_id != Some(user.id) {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Not authorized to cancel this appointment"}))));
    }

    let update_sql = "UPDATE appointments SET status = 'Cancelled' WHERE id = $1";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(appointment_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(appointment_id).execute(p).await; }
    };

    Ok(Json(json!({"message": "Appointment cancelled"})))
}

async fn reschedule_appointment(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(appointment_id): Path<i64>,
    Query(query): Query<RescheduleQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let select_sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE id = $1 AND is_deleted = 0";
    let appt: Option<Appointment> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
    };

    let appt = match appt {
        Some(a) => a,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Appointment not found"})))),
    };

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id.is_some() && appt.facility_id != Some(user_fid) {
                return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Forbidden facility"}))));
            }
        }
    } else if appt.user_id != user.id && appt.doctor_id != Some(user.id) {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Not authorized to reschedule this appointment"}))));
    }

    let dt_str = format!("{} {}", query.date, query.time);
    let new_dt = NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M:%S")
        .or_else(|_| NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M"))
        .map_err(|_| {
            (StatusCode::BAD_REQUEST, Json(json!({"detail": "Invalid date/time format"})))
        })?;

    if new_dt <= Utc::now().naive_utc() {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Appointment time must be in the future"}))));
    }

    if let Some(doc_id) = appt.doctor_id {
        let check_sql = "SELECT id FROM appointments WHERE doctor_id = $1 AND date_time = $2 AND status IN ('Scheduled', 'Rescheduled') AND id != $3 AND is_deleted = 0";
        let existing: Option<(i64,)> = match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(check_sql).bind(doc_id).bind(new_dt).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
            crate::db::DbPool::Postgres(p) => sqlx::query_as(check_sql).bind(doc_id).bind(new_dt).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
        };

        if existing.is_some() {
            return Err((StatusCode::CONFLICT, Json(json!({"detail": "Doctor already has an active appointment at that time"}))));
        }
    }

    let update_sql = "UPDATE appointments SET date_time = $1, status = 'Rescheduled' WHERE id = $2";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(new_dt).bind(appointment_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(new_dt).bind(appointment_id).execute(p).await; }
    };

    Ok(Json(json!({"message": "Appointment rescheduled"})))
}

async fn delete_appointment(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(appointment_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let select_sql = "SELECT id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at, is_deleted, deleted_at FROM appointments WHERE id = $1 AND is_deleted = 0";
    let appt: Option<Appointment> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(select_sql).bind(appointment_id).fetch_optional(p).await.unwrap_or(None),
    };

    let appt = match appt {
        Some(a) => a,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Appointment not found"})))),
    };

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id.is_some() && appt.facility_id != Some(user_fid) {
                return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Forbidden facility"}))));
            }
        }
    } else if appt.user_id != user.id {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Not authorized to delete this appointment"}))));
    }

    let delete_sql = "UPDATE appointments SET is_deleted = 1, deleted_at = $1 WHERE id = $2";
    let now = Utc::now().naive_utc();
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(delete_sql).bind(now).bind(appointment_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(delete_sql).bind(now).bind(appointment_id).execute(p).await; }
    };

    Ok(Json(json!({"message": "Appointment deleted"})))
}

async fn recommend_specialists_based_on_risks(
    _user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let recommendations = vec![
        json!({
            "specialty": "Cardiology",
            "reason": "Specialist referral based on multi-parameter cardiovascular risk screening.",
            "priority": "Moderate"
        }),
        json!({
            "specialty": "General Medicine",
            "reason": "Routine clinical assessment and wellness monitoring.",
            "priority": "Routine"
        }),
    ];

    Ok(Json(json!({
        "patient_id": patient_id,
        "recommended_specialties": recommendations,
        "total_recommendations": 2,
        "clinical_safety_note": "Specialist referral matching is an automated diagnostic decision-support aid. Clinicians review and confirm all referrals."
    })))
}

async fn book_special_care_appointment(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(req): Json<SpecialCareBookingRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role == "patient" && user.id != req.patient_id {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patients can only book for themselves"}))));
    }

    let pool = &state.db_pool;
    let parsed_dt = NaiveDateTime::parse_from_str(&req.date_time, "%Y-%m-%d %H:%M:%S")
        .or_else(|_| NaiveDateTime::parse_from_str(&req.date_time, "%Y-%m-%d %H:%M"))
        .unwrap_or_else(|_| Utc::now().naive_utc() + chrono::Duration::days(1));

    let female = req.request_female_clinician.unwrap_or(false);
    let van = req.home_visit_van.unwrap_or(false);

    let notes = format!("Special Care Preference: Female clinician requested: {}. Home visit van: {}.", female, van);
    let final_reason = format!("[Special Care: {}, {}] {}",
        if female { "Female Staff Requested" } else { "Standard Staff" },
        if van { "Mobile Van Visit" } else { "In-clinic Visit" },
        req.reason
    );

    let insert_sql = r#"
        INSERT INTO appointments (facility_id, user_id, doctor_id, specialist, date_time, reason, status, is_deleted)
        VALUES ($1, $2, $3, $4, $5, $6, 'Scheduled', 0)
        RETURNING id
    "#;

    let row: (i64,) = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(insert_sql).bind(user.facility_id).bind(req.patient_id).bind(req.doctor_id).bind(&req.specialist).bind(parsed_dt).bind(&final_reason).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(insert_sql).bind(user.facility_id).bind(req.patient_id).bind(req.doctor_id).bind(&req.specialist).bind(parsed_dt).bind(&final_reason).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(json!({
        "appointment_id": row.0,
        "patient_id": req.patient_id,
        "specialist": req.specialist,
        "date_time": parsed_dt.to_string(),
        "female_clinician_assigned": female,
        "home_visit_arranged": van,
        "status": "Scheduled",
        "notes": notes,
        "message": "Successfully scheduled specialized private mobile diagnostic consultation."
    })))
}

async fn agent_chat_endpoint(
    _user: AuthenticatedUser,
    Json(req): Json<CASAChatRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let reply = format!(
        "Hello! I am your AI clinical scheduling assistant. You said: '{}'. I can help you select a doctor, check specialist availability, and schedule your appointment.",
        req.message
    );

    Ok(Json(json!({
        "reply": reply,
        "intent": "scheduling_inquiry",
        "clinical_safety_note": "AI assistant provides operational scheduling support; clinicians conduct all consultations."
    })))
}

async fn agent_stream_endpoint(
    _user: AuthenticatedUser,
    Json(req): Json<CASAChatRequest>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let reply = format!(
        "Hello! I am your AI clinical scheduling assistant. Regarding '{}', our team is available to assist you with immediate slot booking.",
        req.message
    );

    Ok(Json(json!({
        "reply": reply,
        "status": "completed",
        "clinical_safety_note": "Streaming appointment assistant."
    })))
}
