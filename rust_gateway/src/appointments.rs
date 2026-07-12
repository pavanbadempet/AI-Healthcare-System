use axum::{
    extract::{Path, Query, State},
    routing::{delete, get, post, put},
    Json, Router,
};
use chrono::NaiveDateTime;
use reqwest::StatusCode;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

use crate::AppState;

#[derive(Serialize, Deserialize, FromRow)]
pub struct Appointment {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub user_id: Option<i64>,
    pub doctor_id: Option<i64>,
    pub specialist: Option<String>,
    pub date_time: Option<NaiveDateTime>,
    pub reason: Option<String>,
    pub status: String,
    pub created_at: Option<NaiveDateTime>,
}

#[derive(Serialize, Deserialize)]
pub struct AppointmentCreate {
    pub date: String,
    pub time: String,
    pub doctor_id: i64,
    pub specialist: String,
    pub reason: String,
}

#[derive(Serialize, Deserialize, FromRow)]
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

#[derive(Serialize)]
pub struct MessageResponse {
    pub message: String,
}

pub fn router() -> Router<AppState> {
    Router::new()
        // Native routes
        .route("/", get(get_appointments).post(create_appointment))
        .route("/{id}", delete(delete_appointment))
        .route("/{id}/cancel", put(cancel_appointment))
        .route("/{id}/reschedule", put(reschedule_appointment))
        .route("/doctors", get(get_doctors))
        // Unimplemented routes (agent) are not registered here,
        // so they will automatically hit the global fallback proxy in main.rs and be handled by Python.
}

async fn get_appointments(
    State(state): State<AppState>,
    user: crate::auth::AuthenticatedUser,
) -> Result<Json<Vec<Appointment>>, StatusCode> {
    let pool = &state.db_pool;

    let query = if user.role == "admin" {
        if let Some(fid) = user.facility_id {
            sqlx::query_as::<_, Appointment>("SELECT * FROM appointments WHERE facility_id = ? AND is_deleted = 0 ORDER BY date_time ASC")
                .bind(fid)
        } else {
            sqlx::query_as::<_, Appointment>("SELECT * FROM appointments WHERE is_deleted = 0 ORDER BY date_time ASC")
        }
    } else if user.role == "doctor" {
        sqlx::query_as::<_, Appointment>("SELECT * FROM appointments WHERE doctor_id = ? AND is_deleted = 0 ORDER BY date_time ASC")
            .bind(user.id)
    } else {
        sqlx::query_as::<_, Appointment>("SELECT * FROM appointments WHERE user_id = ? AND is_deleted = 0 ORDER BY date_time ASC")
            .bind(user.id)
    };

    let appointments = query.fetch_all(pool).await.map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    Ok(Json(appointments))
}

async fn create_appointment(
    State(state): State<AppState>,
    user: crate::auth::AuthenticatedUser,
    Json(payload): Json<AppointmentCreate>,
) -> Result<Json<Appointment>, StatusCode> {
    let pool = &state.db_pool;

    let dt_str = format!("{} {}", payload.date, payload.time);
    let appointment_dt = chrono::NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M:%S")
        .or_else(|_| chrono::NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M"))
        .map_err(|_| {
            eprintln!("Invalid datetime format: {}", dt_str);
            StatusCode::BAD_REQUEST
        })?;

    if appointment_dt <= chrono::Utc::now().naive_utc() {
        eprintln!("Appointment time must be in the future");
        return Err(StatusCode::BAD_REQUEST);
    }

    #[derive(sqlx::FromRow)]
    struct DoctorInfo {
        id: i64,
        role: String,
        facility_id: Option<i64>,
        specialization: Option<String>,
    }

    let doctor_id = payload.doctor_id;
    let doctor: Option<DoctorInfo> = sqlx::query_as(
        "SELECT id, role, facility_id, specialization FROM users WHERE id = ? AND role = 'doctor'"
    )
    .bind(doctor_id)
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let doctor = doctor.ok_or(StatusCode::BAD_REQUEST)?;

    let first_fid = user.facility_id;
    let second_fid = doctor.facility_id;
    let shares_facility = first_fid.is_none() || second_fid.is_none() || first_fid == second_fid;

    if !shares_facility {
        eprintln!("Facility mismatch");
        return Err(StatusCode::BAD_REQUEST);
    }

    let existing: Option<(i64,)> = sqlx::query_as(
        "SELECT id FROM appointments WHERE doctor_id = ? AND date_time = ? AND status IN (?, ?)"
    )
    .bind(doctor_id)
    .bind(appointment_dt)
    .bind("Scheduled")
    .bind("Rescheduled")
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if existing.is_some() {
        eprintln!("Doctor already has an active appointment at that time");
        return Err(StatusCode::CONFLICT);
    }

    let facility_id = user.facility_id.or(doctor.facility_id);
    let specialist = doctor.specialization.unwrap_or_else(|| "General Physician".to_string());
    
    let result = sqlx::query_as::<_, Appointment>(
        r#"
        INSERT INTO appointments (facility_id, user_id, doctor_id, specialist, date_time, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING id, facility_id, user_id, doctor_id, specialist, date_time, reason, status, created_at
        "#
    )
    .bind(facility_id)
    .bind(user.id)
    .bind(doctor_id)
    .bind(specialist)
    .bind(appointment_dt)
    .bind(payload.reason)
    .bind("Scheduled")
    .fetch_one(pool)
    .await
    .map_err(|e| {
        eprintln!("DB Insert Error: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    println!("Booking confirmation email simulated for appointment {}", result.id);

    Ok(Json(result))
}

async fn get_doctors(
    State(state): State<AppState>,
    user: crate::auth::AuthenticatedUser,
) -> Result<Json<Vec<DoctorResponse>>, StatusCode> {
    let pool = &state.db_pool;

    let query = if user.role == "admin" && user.facility_id.is_some() {
        sqlx::query_as::<_, DoctorResponse>(
            r#"SELECT id, full_name, specialization, consultation_fee, profile_picture 
               FROM users WHERE role = 'doctor' AND facility_id = ?"#
        ).bind(user.facility_id)
    } else if user.facility_id.is_some() {
        sqlx::query_as::<_, DoctorResponse>(
            r#"SELECT id, full_name, specialization, consultation_fee, profile_picture 
               FROM users WHERE role = 'doctor' AND (facility_id = ? OR facility_id IS NULL)"#
        ).bind(user.facility_id)
    } else {
        sqlx::query_as::<_, DoctorResponse>(
            r#"SELECT id, full_name, specialization, consultation_fee, profile_picture 
               FROM users WHERE role = 'doctor'"#
        )
    };

    let doctors = query.fetch_all(pool).await.map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        StatusCode::INTERNAL_SERVER_ERROR
    })?;

    let mapped = doctors.into_iter().map(|mut d| {
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
    user: crate::auth::AuthenticatedUser,
    Path(appointment_id): Path<i64>,
) -> Result<Json<MessageResponse>, StatusCode> {
    let pool = &state.db_pool;

    let appt: Option<Appointment> = sqlx::query_as(
        "SELECT * FROM appointments WHERE id = ?"
    )
    .bind(appointment_id)
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let appt = appt.ok_or(StatusCode::NOT_FOUND)?;

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id != Some(user_fid) {
                return Err(StatusCode::FORBIDDEN);
            }
        }
    } else {
        if appt.user_id != Some(user.id) {
            return Err(StatusCode::FORBIDDEN);
        }
    }

    sqlx::query("UPDATE appointments SET status = 'Cancelled' WHERE id = ?")
        .bind(appointment_id)
        .execute(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(MessageResponse {
        message: "Appointment cancelled".to_string(),
    }))
}

async fn reschedule_appointment(
    State(state): State<AppState>,
    user: crate::auth::AuthenticatedUser,
    Path(appointment_id): Path<i64>,
    Query(query): Query<RescheduleQuery>,
) -> Result<Json<MessageResponse>, StatusCode> {
    let pool = &state.db_pool;

    let appt: Option<Appointment> = sqlx::query_as(
        "SELECT * FROM appointments WHERE id = ?"
    )
    .bind(appointment_id)
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let appt = appt.ok_or(StatusCode::NOT_FOUND)?;

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id != Some(user_fid) {
                return Err(StatusCode::FORBIDDEN);
            }
        }
    } else {
        if appt.user_id != Some(user.id) {
            return Err(StatusCode::FORBIDDEN);
        }
    }

    let dt_str = format!("{} {}", query.date, query.time);
    let new_dt = chrono::NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M:%S")
        .or_else(|_| chrono::NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M"))
        .map_err(|_| {
            eprintln!("Invalid datetime format: {}", dt_str);
            StatusCode::BAD_REQUEST
        })?;

    if new_dt <= chrono::Utc::now().naive_utc() {
        eprintln!("Appointment time must be in the future");
        return Err(StatusCode::BAD_REQUEST);
    }

    if let Some(doc_id) = appt.doctor_id {
        let existing: Option<(i64,)> = sqlx::query_as(
            "SELECT id FROM appointments WHERE doctor_id = ? AND date_time = ? AND status IN (?, ?) AND id != ?"
        )
        .bind(doc_id)
        .bind(new_dt)
        .bind("Scheduled")
        .bind("Rescheduled")
        .bind(appointment_id)
        .fetch_optional(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

        if existing.is_some() {
            eprintln!("Doctor already has an active appointment at that time");
            return Err(StatusCode::CONFLICT);
        }
    }

    sqlx::query("UPDATE appointments SET date_time = ?, status = 'Rescheduled' WHERE id = ?")
        .bind(new_dt)
        .bind(appointment_id)
        .execute(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(MessageResponse {
        message: "Appointment rescheduled".to_string(),
    }))
}

async fn delete_appointment(
    State(state): State<AppState>,
    user: crate::auth::AuthenticatedUser,
    Path(appointment_id): Path<i64>,
) -> Result<Json<MessageResponse>, StatusCode> {
    let pool = &state.db_pool;

    let appt: Option<Appointment> = sqlx::query_as(
        "SELECT * FROM appointments WHERE id = ?"
    )
    .bind(appointment_id)
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let appt = appt.ok_or(StatusCode::NOT_FOUND)?;

    if user.role == "admin" {
        if let Some(user_fid) = user.facility_id {
            if appt.facility_id != Some(user_fid) {
                return Err(StatusCode::FORBIDDEN);
            }
        }
    } else {
        if appt.user_id != Some(user.id) {
            return Err(StatusCode::FORBIDDEN);
        }
    }

    sqlx::query("DELETE FROM appointments WHERE id = ?")
        .bind(appointment_id)
        .execute(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(MessageResponse {
        message: "Appointment deleted".to_string(),
    }))
}
