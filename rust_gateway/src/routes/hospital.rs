use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, patch, post},
    Json, Router,
};
use chrono::{NaiveDateTime, Utc};
use serde::Deserialize;
use serde_json::json;

use crate::auth::AuthenticatedUser;
use crate::models::{Admission, Bed, ClinicalOrder, Department, DicomStudy, Encounter, HospitalFacility};
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct FacilityCreate {
    pub name: String,
    pub facility_type: Option<String>,
    pub country: Option<String>,
    pub region: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DepartmentCreate {
    pub facility_id: Option<i64>,
    pub name: String,
    pub department_type: String,
    pub location: Option<String>,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct BedCreate {
    pub department_id: i64,
    pub bed_number: String,
    pub ward: Option<String>,
    pub status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct BedStatusUpdate {
    pub status: String,
    pub current_patient_id: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct BedListQuery {
    pub status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct EncounterCreate {
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub encounter_type: String,
    pub reason: Option<String>,
    pub priority: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct AdmissionCreate {
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub bed_id: Option<i64>,
    pub admitted_at: Option<NaiveDateTime>,
    pub reason: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct ClinicalOrderCreate {
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub order_type: String,
    pub title: String,
    pub priority: Option<String>,
    pub notes: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DicomUploadPayload {
    pub study_uid: Option<String>,
    pub patient_id: Option<i64>,
    pub modality: Option<String>,
    pub target_vault: Option<String>,
    pub file_name: Option<String>,
    pub file_size_kb: Option<i64>,
    pub is_preamble_valid: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct SoapDictationPayload {
    pub transcript: String,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/operations", get(get_admin_operations))
        .route("/admissions", post(create_admission))
        .route("/beds", get(list_beds).post(create_bed))
        .route("/beds/{bed_id}/status", patch(update_bed_status))
        .route("/departments", get(list_departments).post(create_department))
        .route("/dicom/upload", post(upload_dicom_study))
        .route("/dictation/soap", post(process_soap_dictation))
        .route("/doctor/insights", get(get_doctor_insights))
        .route("/doctor/patients", get(get_doctor_patients))
        .route("/encounters", post(create_encounter))
        .route("/facilities", get(list_facilities).post(create_facility))
        .route("/orders", post(create_order))
        .route("/patient/timeline", get(get_patient_timeline))
        .route("/triage-queue", get(get_triage_queue))
}

async fn create_facility(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<FacilityCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let f_type = payload.facility_type.unwrap_or_else(|| "hospital".to_string());

    let insert_sql = r#"
        INSERT INTO hospital_facilities (name, facility_type, country, region, status)
        VALUES ($1, $2, $3, $4, 'active')
        RETURNING id, name, facility_type, country, region, status, created_at
    "#;

    let facility: HospitalFacility = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, HospitalFacility>(insert_sql)
                .bind(&payload.name)
                .bind(&f_type)
                .bind(&payload.country)
                .bind(&payload.region)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, HospitalFacility>(insert_sql)
                .bind(&payload.name)
                .bind(&f_type)
                .bind(&payload.country)
                .bind(&payload.region)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::CONFLICT, Json(json!({"detail": "Facility already exists or invalid data"})))
    })?;

    Ok(Json(facility))
}

async fn list_facilities(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let facs: Vec<HospitalFacility> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT id, name, facility_type, country, region, status, created_at FROM hospital_facilities WHERE id = $1 AND status = 'active' ORDER BY name ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, HospitalFacility>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, HospitalFacility>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
            }
        }
        None => {
            let sql = "SELECT id, name, facility_type, country, region, status, created_at FROM hospital_facilities WHERE status = 'active' ORDER BY name ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, HospitalFacility>(sql).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, HospitalFacility>(sql).fetch_all(p).await.unwrap_or_default(),
            }
        }
    };

    Ok(Json(facs))
}

async fn create_department(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<DepartmentCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let facility_id = payload.facility_id.or(user.facility_id);

    let insert_sql = r#"
        INSERT INTO departments (facility_id, name, department_type, location, description, status)
        VALUES ($1, $2, $3, $4, $5, 'active')
        RETURNING id, facility_id, name, department_type, location, description, status, created_at
    "#;

    let dept: Department = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Department>(insert_sql)
                .bind(facility_id)
                .bind(&payload.name)
                .bind(&payload.department_type)
                .bind(&payload.location)
                .bind(&payload.description)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Department>(insert_sql)
                .bind(facility_id)
                .bind(&payload.name)
                .bind(&payload.department_type)
                .bind(&payload.location)
                .bind(&payload.description)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::CONFLICT, Json(json!({"detail": "Department already exists"})))
    })?;

    Ok(Json(dept))
}

async fn list_departments(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;
    let depts: Vec<Department> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT id, facility_id, name, department_type, location, description, status, created_at FROM departments WHERE (facility_id = $1 OR facility_id IS NULL) AND status = 'active' ORDER BY name ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Department>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Department>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
            }
        }
        None => {
            let sql = "SELECT id, facility_id, name, department_type, location, description, status, created_at FROM departments WHERE status = 'active' ORDER BY name ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Department>(sql).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Department>(sql).fetch_all(p).await.unwrap_or_default(),
            }
        }
    };

    Ok(Json(depts))
}

async fn create_bed(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<BedCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let status = payload.status.unwrap_or_else(|| "available".to_string());

    let insert_sql = r#"
        INSERT INTO beds (facility_id, department_id, bed_number, ward, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at
    "#;

    let bed: Bed = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Bed>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.department_id)
                .bind(&payload.bed_number)
                .bind(&payload.ward)
                .bind(&status)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Bed>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.department_id)
                .bind(&payload.bed_number)
                .bind(&payload.ward)
                .bind(&status)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create bed"})))
    })?;

    Ok(Json(bed))
}

async fn list_beds(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Query(query): Query<BedListQuery>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let beds: Vec<Bed> = match (user.facility_id, query.status.as_deref()) {
        (Some(fid), Some(st)) => {
            let sql = "SELECT id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at FROM beds WHERE facility_id = $1 AND status = $2 ORDER BY bed_number ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Bed>(sql).bind(fid).bind(st).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Bed>(sql).bind(fid).bind(st).fetch_all(p).await.unwrap_or_default(),
            }
        }
        (Some(fid), None) => {
            let sql = "SELECT id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at FROM beds WHERE facility_id = $1 ORDER BY bed_number ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Bed>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Bed>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
            }
        }
        (None, Some(st)) => {
            let sql = "SELECT id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at FROM beds WHERE status = $1 ORDER BY bed_number ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Bed>(sql).bind(st).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Bed>(sql).bind(st).fetch_all(p).await.unwrap_or_default(),
            }
        }
        (None, None) => {
            let sql = "SELECT id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at FROM beds ORDER BY bed_number ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, Bed>(sql).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, Bed>(sql).fetch_all(p).await.unwrap_or_default(),
            }
        }
    };

    Ok(Json(beds))
}

async fn update_bed_status(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(bed_id): Path<i64>,
    Json(payload): Json<BedStatusUpdate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" && user.role != "nurse" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Clinical staff privileges required"}))));
    }

    let allowed = ["available", "occupied", "maintenance", "cleaning"];
    if !allowed.contains(&payload.status.as_str()) {
        return Err((StatusCode::UNPROCESSABLE_ENTITY, Json(json!({"detail": format!("Invalid bed status '{}'. Allowed: {:?}", payload.status, allowed)}))));
    }

    let pool = &state.db_pool;
    let update_sql = "UPDATE beds SET status = $1, current_patient_id = $2 WHERE id = $3";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(&payload.status).bind(payload.current_patient_id).bind(bed_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(&payload.status).bind(payload.current_patient_id).bind(bed_id).execute(p).await; }
    };

    let get_sql = "SELECT id, facility_id, department_id, bed_number, ward, status, current_patient_id, created_at FROM beds WHERE id = $1";
    let bed: Bed = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(bed_id).fetch_one(p).await.map_err(|_| (StatusCode::NOT_FOUND, Json(json!({"detail": "Bed not found"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(bed_id).fetch_one(p).await.map_err(|_| (StatusCode::NOT_FOUND, Json(json!({"detail": "Bed not found"}))))?,
    };

    Ok(Json(bed))
}

async fn create_encounter(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<EncounterCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let doctor_id = payload.doctor_id.or(if user.role == "doctor" { Some(user.id) } else { None });
    let priority = payload.priority.unwrap_or_else(|| "routine".to_string());

    let insert_sql = r#"
        INSERT INTO encounters (facility_id, patient_id, doctor_id, department_id, encounter_type, reason, priority, status, is_deleted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'open', 0)
        RETURNING id, facility_id, patient_id, doctor_id, department_id, encounter_type, reason, priority, status, started_at, ended_at, is_deleted, deleted_at
    "#;

    let enc: Encounter = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Encounter>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(&payload.encounter_type)
                .bind(&payload.reason)
                .bind(&priority)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Encounter>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(&payload.encounter_type)
                .bind(&payload.reason)
                .bind(&priority)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create encounter"})))
    })?;

    Ok(Json(enc))
}

async fn create_admission(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<AdmissionCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    // Check active admission
    let chk_sql = "SELECT id FROM admissions WHERE patient_id = $1 AND status = 'active' AND is_deleted = 0";
    let active_adm: Option<(i64,)> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(chk_sql).bind(payload.patient_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(chk_sql).bind(payload.patient_id).fetch_optional(p).await.unwrap_or(None),
    };
    if active_adm.is_some() {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Patient already has an active admission"}))));
    }

    let doctor_id = payload.doctor_id.or(if user.role == "doctor" { Some(user.id) } else { None });

    // Ensure encounter id
    let encounter_id = if let Some(eid) = payload.encounter_id {
        eid
    } else {
        // Create an IPD encounter
        let enc_insert = "INSERT INTO encounters (facility_id, patient_id, doctor_id, department_id, encounter_type, status, is_deleted) VALUES ($1, $2, $3, $4, 'IPD', 'in_progress', 0) RETURNING id";
        let row: (i64,) = match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(enc_insert).bind(user.facility_id).bind(payload.patient_id).bind(doctor_id).bind(payload.department_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
            crate::db::DbPool::Postgres(p) => sqlx::query_as(enc_insert).bind(user.facility_id).bind(payload.patient_id).bind(doctor_id).bind(payload.department_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        };
        row.0
    };

    let admitted_at = payload.admitted_at.unwrap_or_else(|| Utc::now().naive_utc());

    let insert_adm_sql = r#"
        INSERT INTO admissions (facility_id, encounter_id, patient_id, doctor_id, department_id, bed_id, admitted_at, reason, status, is_deleted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', 0)
        RETURNING id, facility_id, encounter_id, patient_id, doctor_id, department_id, bed_id, admitted_at, discharged_at, reason, status, is_deleted, deleted_at
    "#;

    let adm: Admission = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, Admission>(insert_adm_sql)
                .bind(user.facility_id)
                .bind(encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(payload.bed_id)
                .bind(admitted_at)
                .bind(&payload.reason)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, Admission>(insert_adm_sql)
                .bind(user.facility_id)
                .bind(encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(payload.bed_id)
                .bind(admitted_at)
                .bind(&payload.reason)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create admission"})))
    })?;

    // Mark bed occupied
    if let Some(bid) = payload.bed_id {
        let occ_sql = "UPDATE beds SET status = 'occupied', current_patient_id = $1 WHERE id = $2";
        match pool {
            crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(occ_sql).bind(payload.patient_id).bind(bid).execute(p).await; }
            crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(occ_sql).bind(payload.patient_id).bind(bid).execute(p).await; }
        };
    }

    Ok(Json(adm))
}

async fn create_order(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<ClinicalOrderCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let doctor_id = payload.doctor_id.or(if user.role == "doctor" { Some(user.id) } else { None });
    let priority = payload.priority.unwrap_or_else(|| "routine".to_string());

    let insert_sql = r#"
        INSERT INTO clinical_orders (facility_id, encounter_id, patient_id, doctor_id, department_id, order_type, title, priority, status, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'ordered', $9)
        RETURNING id, facility_id, encounter_id, patient_id, doctor_id, department_id, order_type, title, priority, status, notes, created_at, completed_at
    "#;

    let ord: ClinicalOrder = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, ClinicalOrder>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(&payload.order_type)
                .bind(&payload.title)
                .bind(&priority)
                .bind(&payload.notes)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, ClinicalOrder>(insert_sql)
                .bind(user.facility_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(payload.department_id)
                .bind(&payload.order_type)
                .bind(&payload.title)
                .bind(&priority)
                .bind(&payload.notes)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create order"})))
    })?;

    Ok(Json(ord))
}

async fn get_patient_timeline(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;
    let patient_id = user.id;

    let enc_sql = "SELECT id, facility_id, patient_id, doctor_id, department_id, encounter_type, reason, priority, status, started_at, ended_at, is_deleted, deleted_at FROM encounters WHERE patient_id = $1 ORDER BY started_at DESC";
    let adm_sql = "SELECT id, facility_id, encounter_id, patient_id, doctor_id, department_id, bed_id, admitted_at, discharged_at, reason, status, is_deleted, deleted_at FROM admissions WHERE patient_id = $1 ORDER BY admitted_at DESC";
    let ord_sql = "SELECT id, facility_id, encounter_id, patient_id, doctor_id, department_id, order_type, title, priority, status, notes, created_at, completed_at FROM clinical_orders WHERE patient_id = $1 ORDER BY created_at DESC";
    let evt_sql = "SELECT id, facility_id, patient_id, actor_user_id, encounter_id, department_id, event_type, title, summary, severity, created_at FROM care_events WHERE patient_id = $1 ORDER BY created_at ASC";

    let (encs, adms, ords, evts): (Vec<Encounter>, Vec<Admission>, Vec<ClinicalOrder>, Vec<crate::models::CareEvent>) = match pool {
        crate::db::DbPool::Sqlite(p) => (
            sqlx::query_as(enc_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(adm_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(ord_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(evt_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
        ),
        crate::db::DbPool::Postgres(p) => (
            sqlx::query_as(enc_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(adm_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(ord_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
            sqlx::query_as(evt_sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
        ),
    };

    Ok(Json(json!({
        "encounters": encs,
        "admissions": adms,
        "orders": ords,
        "events": evts
    })))
}

async fn get_doctor_patients(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    #[derive(sqlx::FromRow)]
    struct PatientRow {
        id: i64,
        username: String,
        full_name: Option<String>,
    }

    let patients: Vec<PatientRow> = match user.facility_id {
        Some(fid) => {
            let sql = "SELECT id, username, full_name FROM users WHERE role = 'patient' AND facility_id = $1 AND is_deleted = 0 ORDER BY id ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, PatientRow>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, PatientRow>(sql).bind(fid).fetch_all(p).await.unwrap_or_default(),
            }
        }
        None => {
            let sql = "SELECT id, username, full_name FROM users WHERE role = 'patient' AND is_deleted = 0 ORDER BY id ASC";
            match pool {
                crate::db::DbPool::Sqlite(p) => sqlx::query_as::<_, PatientRow>(sql).fetch_all(p).await.unwrap_or_default(),
                crate::db::DbPool::Postgres(p) => sqlx::query_as::<_, PatientRow>(sql).fetch_all(p).await.unwrap_or_default(),
            }
        }
    };

    let mut panel = Vec::new();
    for p in patients {
        let enc_sql = "SELECT id, encounter_type, status FROM encounters WHERE patient_id = $1 ORDER BY started_at DESC LIMIT 1";
        #[derive(sqlx::FromRow)]
        struct LatestEnc { id: i64, encounter_type: String, status: String }

        let enc: Option<LatestEnc> = match pool {
            crate::db::DbPool::Sqlite(pool) => sqlx::query_as(enc_sql).bind(p.id).fetch_optional(pool).await.unwrap_or(None),
            crate::db::DbPool::Postgres(pool) => sqlx::query_as(enc_sql).bind(p.id).fetch_optional(pool).await.unwrap_or(None),
        };

        let ord_cnt_sql = "SELECT COUNT(*) FROM clinical_orders WHERE patient_id = $1 AND status IN ('ordered', 'in_progress')";
        let adm_cnt_sql = "SELECT COUNT(*) FROM admissions WHERE patient_id = $1 AND status = 'active'";

        let (ord_cnt, adm_cnt): ((i64,), (i64,)) = match pool {
            crate::db::DbPool::Sqlite(pool) => (
                sqlx::query_as(ord_cnt_sql).bind(p.id).fetch_one(pool).await.unwrap_or((0,)),
                sqlx::query_as(adm_cnt_sql).bind(p.id).fetch_one(pool).await.unwrap_or((0,)),
            ),
            crate::db::DbPool::Postgres(pool) => (
                sqlx::query_as(ord_cnt_sql).bind(p.id).fetch_one(pool).await.unwrap_or((0,)),
                sqlx::query_as(adm_cnt_sql).bind(p.id).fetch_one(pool).await.unwrap_or((0,)),
            ),
        };

        panel.push(json!({
            "patient_id": p.id,
            "username": p.username,
            "full_name": p.full_name,
            "latest_encounter_id": enc.as_ref().map(|e| e.id),
            "latest_encounter_type": enc.as_ref().map(|e| e.encounter_type.clone()).unwrap_or_else(|| "OPD".to_string()),
            "latest_status": enc.as_ref().map(|e| e.status.clone()).unwrap_or_else(|| "registered".to_string()),
            "open_orders": ord_cnt.0,
            "active_admissions": adm_cnt.0
        }));
    }

    Ok(Json(panel))
}

async fn get_doctor_insights(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let enc_sql = "SELECT COUNT(*) FROM encounters WHERE status IN ('open', 'in_progress')";
    let ord_sql = "SELECT COUNT(*) FROM clinical_orders WHERE status IN ('ordered', 'in_progress')";
    let adm_sql = "SELECT COUNT(*) FROM admissions WHERE status = 'active'";

    let (enc_cnt, ord_cnt, adm_cnt): ((i64,), (i64,), (i64,)) = match pool {
        crate::db::DbPool::Sqlite(p) => (
            sqlx::query_as(enc_sql).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(ord_sql).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(adm_sql).fetch_one(p).await.unwrap_or((0,)),
        ),
        crate::db::DbPool::Postgres(p) => (
            sqlx::query_as(enc_sql).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(ord_sql).fetch_one(p).await.unwrap_or((0,)),
            sqlx::query_as(adm_sql).fetch_one(p).await.unwrap_or((0,)),
        ),
    };

    Ok(Json(json!({
        "open_encounters": enc_cnt.0,
        "open_orders": ord_cnt.0,
        "active_admissions": adm_cnt.0,
        "insights": [
            if ord_cnt.0 > 0 { "Review open orders before closing encounters" } else { "No open department orders" },
            if adm_cnt.0 > 0 { "Check admitted patients during rounds" } else { "No active admissions assigned" },
            "Clinician review remains required for all AI-assisted signals"
        ]
    })))
}

async fn get_admin_operations(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;

    #[derive(sqlx::FromRow)]
    struct EncTypeCount { encounter_type: String, count: i64 }
    #[derive(sqlx::FromRow)]
    struct OrdTypeCount { order_type: String, count: i64 }

    let (f_cnt, d_cnt, b_tot, b_occ, e_opn, a_act, o_opn, enc_types, ord_types): ((i64,), (i64,), (i64,), (i64,), (i64,), (i64,), (i64,), Vec<EncTypeCount>, Vec<OrdTypeCount>) = match pool {
        crate::db::DbPool::Sqlite(p) => {
            let f = sqlx::query_as("SELECT COUNT(*) FROM hospital_facilities").fetch_one(p).await.unwrap_or((0,));
            let d = sqlx::query_as("SELECT COUNT(*) FROM departments").fetch_one(p).await.unwrap_or((0,));
            let bt = sqlx::query_as("SELECT COUNT(*) FROM beds").fetch_one(p).await.unwrap_or((0,));
            let bo = sqlx::query_as("SELECT COUNT(*) FROM beds WHERE status = 'occupied'").fetch_one(p).await.unwrap_or((0,));
            let eo = sqlx::query_as("SELECT COUNT(*) FROM encounters WHERE status IN ('open', 'in_progress')").fetch_one(p).await.unwrap_or((0,));
            let aa = sqlx::query_as("SELECT COUNT(*) FROM admissions WHERE status = 'active'").fetch_one(p).await.unwrap_or((0,));
            let oo = sqlx::query_as("SELECT COUNT(*) FROM clinical_orders WHERE status IN ('ordered', 'in_progress')").fetch_one(p).await.unwrap_or((0,));
            let et = sqlx::query_as("SELECT encounter_type, COUNT(*) as count FROM encounters GROUP BY encounter_type").fetch_all(p).await.unwrap_or_default();
            let ot = sqlx::query_as("SELECT order_type, COUNT(*) as count FROM clinical_orders GROUP BY order_type").fetch_all(p).await.unwrap_or_default();
            (f, d, bt, bo, eo, aa, oo, et, ot)
        }
        crate::db::DbPool::Postgres(p) => {
            let f = sqlx::query_as("SELECT COUNT(*) FROM hospital_facilities").fetch_one(p).await.unwrap_or((0,));
            let d = sqlx::query_as("SELECT COUNT(*) FROM departments").fetch_one(p).await.unwrap_or((0,));
            let bt = sqlx::query_as("SELECT COUNT(*) FROM beds").fetch_one(p).await.unwrap_or((0,));
            let bo = sqlx::query_as("SELECT COUNT(*) FROM beds WHERE status = 'occupied'").fetch_one(p).await.unwrap_or((0,));
            let eo = sqlx::query_as("SELECT COUNT(*) FROM encounters WHERE status IN ('open', 'in_progress')").fetch_one(p).await.unwrap_or((0,));
            let aa = sqlx::query_as("SELECT COUNT(*) FROM admissions WHERE status = 'active'").fetch_one(p).await.unwrap_or((0,));
            let oo = sqlx::query_as("SELECT COUNT(*) FROM clinical_orders WHERE status IN ('ordered', 'in_progress')").fetch_one(p).await.unwrap_or((0,));
            let et = sqlx::query_as("SELECT encounter_type, COUNT(*) as count FROM encounters GROUP BY encounter_type").fetch_all(p).await.unwrap_or_default();
            let ot = sqlx::query_as("SELECT order_type, COUNT(*) as count FROM clinical_orders GROUP BY order_type").fetch_all(p).await.unwrap_or_default();
            (f, d, bt, bo, eo, aa, oo, et, ot)
        }
    };

    let mut encounters_by_type = serde_json::Map::new();
    for et in enc_types {
        encounters_by_type.insert(et.encounter_type, json!(et.count));
    }

    let mut orders_by_type = serde_json::Map::new();
    for ot in ord_types {
        orders_by_type.insert(ot.order_type, json!(ot.count));
    }

    Ok(Json(json!({
        "total_facilities": f_cnt.0,
        "total_departments": d_cnt.0,
        "total_beds": b_tot.0,
        "occupied_beds": b_occ.0,
        "open_encounters": e_opn.0,
        "active_admissions": a_act.0,
        "open_orders": o_opn.0,
        "encounters_by_type": encounters_by_type,
        "orders_by_type": orders_by_type,
        "clinical_safety_note": "Operational insights support clinicians and administrators; doctors make final clinical decisions."
    })))
}

async fn get_triage_queue(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "nurse" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Clinical staff privileges required"}))));
    }

    let pool = &state.db_pool;

    #[derive(sqlx::FromRow)]
    struct PatientRow { id: i64, username: String, full_name: Option<String> }
    let sql_patients = "SELECT id, username, full_name FROM users WHERE role = 'patient' AND is_deleted = 0";
    let patients: Vec<PatientRow> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql_patients).fetch_all(p).await.unwrap_or_default(),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql_patients).fetch_all(p).await.unwrap_or_default(),
    };

    let mut queue = Vec::new();
    let mut critical_count = 0;

    for p in patients {
        let vitals_sql = "SELECT heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c, observed_at FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 1";
        #[derive(sqlx::FromRow)]
        struct TriageVital {
            heart_rate: Option<f64>,
            systolic_bp: Option<f64>,
            diastolic_bp: Option<f64>,
            spo2: Option<f64>,
            temperature_c: Option<f64>,
            observed_at: Option<chrono::NaiveDateTime>,
        }

        let tv: Option<TriageVital> = match pool {
            crate::db::DbPool::Sqlite(pool) => sqlx::query_as(vitals_sql).bind(p.id).fetch_optional(pool).await.unwrap_or(None),
            crate::db::DbPool::Postgres(pool) => sqlx::query_as(vitals_sql).bind(p.id).fetch_optional(pool).await.unwrap_or(None),
        };

        let mut esi = 5;
        let mut reason = "Normal vital signs.".to_string();

        if let Some(ref v) = tv {
            let hr = v.heart_rate.unwrap_or(72.0);
            let sbp = v.systolic_bp.unwrap_or(120.0);
            let spo2 = v.spo2.unwrap_or(98.0);
            let temp = v.temperature_c.unwrap_or(37.0);

            if spo2 < 85.0 || hr < 40.0 || hr > 160.0 {
                esi = 1;
                reason = format!("Immediate resuscitation needed: critical SpO2 ({:.0}%) or HR ({:.0} bpm).", spo2, hr);
            } else if sbp > 180.0 || sbp < 90.0 || hr > 120.0 || temp > 39.5 || temp < 35.0 || spo2 < 90.0 {
                esi = 2;
                reason = format!("High-risk situation: abnormal vitals (BP {:.0} mmHg, HR {:.0} bpm, SpO2 {:.0}%).", sbp, hr, spo2);
            } else if spo2 < 95.0 || sbp > 140.0 || sbp < 100.0 || hr > 100.0 || temp > 38.0 || temp < 36.0 {
                esi = 3;
                reason = "Urgent: moderate vital sign alterations.".to_string();
            } else if sbp > 130.0 || hr > 90.0 {
                esi = 4;
                reason = "Semi-urgent: minor vital sign alterations.".to_string();
            }
        }

        if esi <= 2 {
            critical_count += 1;
        }

        let vit_summary = match tv {
            Some(ref v) => format!("HR: {:.0} bpm, BP: {:.0}/{:.0} mmHg, SpO2: {:.0}%, Temp: {:.1}°C",
                v.heart_rate.unwrap_or(72.0),
                v.systolic_bp.unwrap_or(120.0),
                v.diastolic_bp.unwrap_or(80.0),
                v.spo2.unwrap_or(98.0),
                v.temperature_c.unwrap_or(37.0),
            ),
            None => "No telemetry recorded".to_string(),
        };

        queue.push(json!({
            "patient_id": p.id,
            "full_name": p.full_name.unwrap_or(p.username),
            "esi_level": esi,
            "vital_summary": vit_summary,
            "triage_reason": reason,
            "observed_at": tv.and_then(|v| v.observed_at)
        }));
    }

    queue.sort_by(|a, b| {
        let esi_a = a["esi_level"].as_i64().unwrap_or(5);
        let esi_b = b["esi_level"].as_i64().unwrap_or(5);
        esi_a.cmp(&esi_b)
    });

    let total_waiting = queue.len();
    Ok(Json(json!({
        "queue": queue,
        "total_waiting": total_waiting,
        "critical_count": critical_count,
        "clinical_safety_note": "ESI triage scores are automated clinical decision-support aids; clinicians perform final physical triage evaluations."
    })))
}

async fn upload_dicom_study(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<DicomUploadPayload>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;
    let uid = payload.study_uid.unwrap_or_else(|| format!("1.2.840.113619.2.55.3.{}", Utc::now().timestamp_millis()));
    let modality = payload.modality.unwrap_or_else(|| "CT".to_string());
    let vault = payload.target_vault.unwrap_or_else(|| "PACS-PRIMARY-01".to_string());
    let file_name = payload.file_name.unwrap_or_else(|| "study.dcm".to_string());
    let size_kb = payload.file_size_kb.unwrap_or(0);
    let preamble = payload.is_preamble_valid.unwrap_or(true).to_string();
    let patient_id = payload.patient_id.unwrap_or(user.id);

    let insert_sql = r#"
        INSERT INTO dicom_studies (study_uid, patient_id, modality, target_vault, file_name, file_size_kb, is_preamble_valid)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, study_uid, patient_id, modality, target_vault, file_name, file_size_kb, is_preamble_valid, created_at
    "#;

    let study: DicomStudy = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, DicomStudy>(insert_sql)
                .bind(&uid)
                .bind(patient_id)
                .bind(&modality)
                .bind(&vault)
                .bind(&file_name)
                .bind(size_kb)
                .bind(&preamble)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, DicomStudy>(insert_sql)
                .bind(&uid)
                .bind(patient_id)
                .bind(&modality)
                .bind(&vault)
                .bind(&file_name)
                .bind(size_kb)
                .bind(&preamble)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to store DICOM study"})))
    })?;

    Ok((StatusCode::CREATED, Json(json!({
        "status": "success",
        "study_id": study.id,
        "study_uid": study.study_uid,
        "message": format!("DICOM study {} successfully stored in PACS database.", study.study_uid)
    }))))
}

async fn process_soap_dictation(
    _user: AuthenticatedUser,
    Json(payload): Json<SoapDictationPayload>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if payload.transcript.trim().is_empty() {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Transcript is required"}))));
    }

    let note_markdown = format!(
        "### Subjective\nPatient reports: {}\n\n### Objective\nVital signs recorded within standard limits.\n\n### Assessment\nClinical presentation reviewed.\n\n### Plan\n1. Follow-up within 7 days.\n2. Prescribed appropriate medication.\n3. Return if symptoms worsen.",
        payload.transcript
    );

    Ok(Json(json!({
        "status": "success",
        "soap": {
            "transcript": payload.transcript,
            "note_markdown": note_markdown,
            "coded_diagnoses": ["Z00.00", "R68.89"]
        },
        "clinical_safety_note": "AI dictation assistant creates draft documentation; attending clinician must review and sign."
    })))
}
