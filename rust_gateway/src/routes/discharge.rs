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
use crate::models::DischargeSummary;
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct DischargeSummaryCreate {
    pub admission_id: i64,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub diagnosis_summary: String,
    pub hospital_course: String,
    pub medications: Option<String>,
    pub follow_up_plan: Option<String>,
    pub discharge_instructions: Option<String>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/metrics", get(get_discharge_metrics))
        .route("/doctor/patients/{patient_id}/summaries", get(get_doctor_patient_discharge_summaries))
        .route("/patient/summaries", get(get_patient_discharge_summaries))
        .route("/summaries", post(create_discharge_summary))
        .route("/summaries/generate/{patient_id}", post(auto_generate_discharge_summary))
        .route("/summaries/{summary_id}/finalize", put(finalize_discharge_summary))
}

async fn create_discharge_summary(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<DischargeSummaryCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    // Check admission exists
    let adm_sql = "SELECT id, facility_id, patient_id, doctor_id, status FROM admissions WHERE id = $1 AND is_deleted = 0";
    #[derive(sqlx::FromRow)]
    struct AdmissionCheck {
        id: i64,
        facility_id: Option<i64>,
        patient_id: i64,
        doctor_id: Option<i64>,
        status: String,
    }

    let adm: Option<AdmissionCheck> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(adm_sql).bind(payload.admission_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(adm_sql).bind(payload.admission_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    let adm = match adm {
        Some(a) => a,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Admission not found"})))),
    };

    if adm.patient_id != payload.patient_id {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Admission patient must match discharge summary patient"}))));
    }

    if adm.status == "discharged" {
        return Err((StatusCode::BAD_REQUEST, Json(json!({"detail": "Cannot create discharge summary for an already discharged admission"}))));
    }

    if let Some(user_fid) = user.facility_id {
        if adm.facility_id.is_some() && adm.facility_id != Some(user_fid) {
            return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Discharge resource is outside the user's facility"}))));
        }
    }

    // Check if duplicate summary exists for this admission
    let dup_sql = "SELECT id FROM discharge_summaries WHERE admission_id = $1";
    let dup: Option<(i64,)> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(dup_sql).bind(payload.admission_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(dup_sql).bind(payload.admission_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };
    if dup.is_some() {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Discharge summary already exists for admission"}))));
    }

    let doctor_id = payload.doctor_id.or(if user.role == "doctor" { Some(user.id) } else { adm.doctor_id });
    let facility_id = user.facility_id.or(adm.facility_id);

    let insert_sql = r#"
        INSERT INTO discharge_summaries (
            facility_id, admission_id, encounter_id, patient_id, doctor_id,
            diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions,
            status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'draft')
        RETURNING id, facility_id, admission_id, encounter_id, patient_id, doctor_id,
                  diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions,
                  status, created_at, finalized_at
    "#;

    let summary: DischargeSummary = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, DischargeSummary>(insert_sql)
                .bind(facility_id)
                .bind(payload.admission_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&payload.diagnosis_summary)
                .bind(&payload.hospital_course)
                .bind(&payload.medications)
                .bind(&payload.follow_up_plan)
                .bind(&payload.discharge_instructions)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, DischargeSummary>(insert_sql)
                .bind(facility_id)
                .bind(payload.admission_id)
                .bind(payload.encounter_id)
                .bind(payload.patient_id)
                .bind(doctor_id)
                .bind(&payload.diagnosis_summary)
                .bind(&payload.hospital_course)
                .bind(&payload.medications)
                .bind(&payload.follow_up_plan)
                .bind(&payload.discharge_instructions)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create discharge summary"})))
    })?;

    Ok(Json(summary))
}

async fn finalize_discharge_summary(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(summary_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    let get_sql = "SELECT id, facility_id, admission_id, encounter_id, patient_id, doctor_id, diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions, status, created_at, finalized_at FROM discharge_summaries WHERE id = $1";
    let summary: Option<DischargeSummary> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(summary_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(summary_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    let summary = match summary {
        Some(s) => s,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Discharge summary not found"})))),
    };

    if summary.status == "finalized" {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Discharge summary is already finalized"}))));
    }

    let now = Utc::now().naive_utc();

    // 1. Update summary status
    let update_sum_sql = "UPDATE discharge_summaries SET status = 'finalized', finalized_at = $1 WHERE id = $2";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sum_sql).bind(now).bind(summary_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sum_sql).bind(now).bind(summary_id).execute(p).await; }
    };

    // 2. Discharge admission and free bed
    #[derive(sqlx::FromRow)]
    struct AdmissionBedInfo {
        bed_id: Option<i64>,
    }
    let get_adm_sql = "SELECT bed_id FROM admissions WHERE id = $1";
    let adm_bed: Option<AdmissionBedInfo> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_adm_sql).bind(summary.admission_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_adm_sql).bind(summary.admission_id).fetch_optional(p).await.unwrap_or(None),
    };

    let update_adm_sql = "UPDATE admissions SET status = 'discharged', discharged_at = $1 WHERE id = $2";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_adm_sql).bind(now).bind(summary.admission_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_adm_sql).bind(now).bind(summary.admission_id).execute(p).await; }
    };

    if let Some(abi) = adm_bed {
        if let Some(bid) = abi.bed_id {
            let update_bed_sql = "UPDATE beds SET status = 'available', current_patient_id = NULL WHERE id = $1";
            match pool {
                crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_bed_sql).bind(bid).execute(p).await; }
                crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_bed_sql).bind(bid).execute(p).await; }
            };
        }
    }

    // 3. Close encounter if attached
    if let Some(enc_id) = summary.encounter_id {
        let update_enc_sql = "UPDATE encounters SET status = 'closed', ended_at = $1 WHERE id = $2";
        match pool {
            crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_enc_sql).bind(now).bind(enc_id).execute(p).await; }
            crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_enc_sql).bind(now).bind(enc_id).execute(p).await; }
        };
    }

    // Fetch updated summary
    let updated_summary: DischargeSummary = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(summary_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(summary_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(updated_summary))
}

async fn get_patient_discharge_summaries(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, admission_id, encounter_id, patient_id, doctor_id, diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions, status, created_at, finalized_at FROM discharge_summaries WHERE patient_id = $1 AND status = 'finalized' ORDER BY finalized_at DESC";

    let summaries: Vec<DischargeSummary> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(summaries))
}

async fn get_doctor_patient_discharge_summaries(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, admission_id, encounter_id, patient_id, doctor_id, diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions, status, created_at, finalized_at FROM discharge_summaries WHERE patient_id = $1 ORDER BY created_at DESC";

    let summaries: Vec<DischargeSummary> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(json!({
        "patient_id": patient_id,
        "summaries": summaries,
        "clinical_safety_note": "Discharge summaries are clinician-authored records and require clinician finalization."
    })))
}

async fn get_discharge_metrics(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let (total_summaries, draft_summaries, finalized_summaries, active_admissions, discharged_admissions) = match user.facility_id {
        Some(fid) => {
            let sql_sums = "SELECT status, COUNT(*) as count FROM discharge_summaries WHERE facility_id = $1 GROUP BY status";
            let sql_adms = "SELECT status, COUNT(*) as count FROM admissions WHERE facility_id = $1 GROUP BY status";

            #[derive(sqlx::FromRow)]
            struct StatusCount { status: String, count: i64 }

            let (sums, adms): (Vec<StatusCount>, Vec<StatusCount>) = match pool {
                crate::db::DbPool::Sqlite(p) => (
                    sqlx::query_as(sql_sums).bind(fid).fetch_all(p).await.unwrap_or_default(),
                    sqlx::query_as(sql_adms).bind(fid).fetch_all(p).await.unwrap_or_default(),
                ),
                crate::db::DbPool::Postgres(p) => (
                    sqlx::query_as(sql_sums).bind(fid).fetch_all(p).await.unwrap_or_default(),
                    sqlx::query_as(sql_adms).bind(fid).fetch_all(p).await.unwrap_or_default(),
                ),
            };

            let total_s: i64 = sums.iter().map(|s| s.count).sum();
            let draft_s: i64 = sums.iter().filter(|s| s.status == "draft").map(|s| s.count).sum();
            let fin_s: i64 = sums.iter().filter(|s| s.status == "finalized").map(|s| s.count).sum();
            let act_a: i64 = adms.iter().filter(|a| a.status == "active").map(|a| a.count).sum();
            let dis_a: i64 = adms.iter().filter(|a| a.status == "discharged").map(|a| a.count).sum();
            (total_s, draft_s, fin_s, act_a, dis_a)
        }
        None => {
            let sql_sums = "SELECT status, COUNT(*) as count FROM discharge_summaries GROUP BY status";
            let sql_adms = "SELECT status, COUNT(*) as count FROM admissions GROUP BY status";

            #[derive(sqlx::FromRow)]
            struct StatusCount { status: String, count: i64 }

            let (sums, adms): (Vec<StatusCount>, Vec<StatusCount>) = match pool {
                crate::db::DbPool::Sqlite(p) => (
                    sqlx::query_as(sql_sums).fetch_all(p).await.unwrap_or_default(),
                    sqlx::query_as(sql_adms).fetch_all(p).await.unwrap_or_default(),
                ),
                crate::db::DbPool::Postgres(p) => (
                    sqlx::query_as(sql_sums).fetch_all(p).await.unwrap_or_default(),
                    sqlx::query_as(sql_adms).fetch_all(p).await.unwrap_or_default(),
                ),
            };

            let total_s: i64 = sums.iter().map(|s| s.count).sum();
            let draft_s: i64 = sums.iter().filter(|s| s.status == "draft").map(|s| s.count).sum();
            let fin_s: i64 = sums.iter().filter(|s| s.status == "finalized").map(|s| s.count).sum();
            let act_a: i64 = adms.iter().filter(|a| a.status == "active").map(|a| a.count).sum();
            let dis_a: i64 = adms.iter().filter(|a| a.status == "discharged").map(|a| a.count).sum();
            (total_s, draft_s, fin_s, act_a, dis_a)
        }
    };

    Ok(Json(json!({
        "total_summaries": total_summaries,
        "draft_summaries": draft_summaries,
        "finalized_summaries": finalized_summaries,
        "active_admissions": active_admissions,
        "discharged_admissions": discharged_admissions,
        "clinical_safety_note": "Discharge metrics support operations; clinicians remain responsible for discharge decisions."
    })))
}

async fn auto_generate_discharge_summary(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    // Fetch patient info
    let patient_sql = "SELECT id, full_name, username, gender, dob, existing_ailments FROM users WHERE id = $1 AND role = 'patient'";
    #[derive(sqlx::FromRow)]
    struct PatientInfo {
        id: i64,
        full_name: Option<String>,
        username: String,
        gender: Option<String>,
        dob: Option<String>,
        existing_ailments: Option<String>,
    }

    let patient: Option<PatientInfo> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(patient_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(patient_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
    };

    let p_info = match patient {
        Some(p) => p,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Patient not found"})))),
    };

    let p_name = p_info.full_name.unwrap_or(p_info.username);
    let ailments = p_info.existing_ailments.unwrap_or_else(|| "None reported".to_string());

    Ok(Json(json!({
        "patient_id": patient_id,
        "patient_name": p_name,
        "diagnosis_summary": format!("Resolved inpatient episode. Primary history: {}", ailments),
        "hospital_course": "Patient underwent comprehensive inpatient evaluation and monitoring with stable clinical indicators.",
        "medications": "Continue prescribed home maintenance regimen. Follow medication schedule strictly.",
        "follow_up_plan": "Follow up in OPD clinic within 7-10 days for vital signs check and symptom review.",
        "discharge_instructions": "Rest, maintain adequate hydration, monitor vitals daily, report to ED immediately if symptoms worsen.",
        "status": "draft",
        "clinical_safety_note": "AI-generated discharge summaries are clinical decision-support drafts; attending clinicians verify and finalize all documentation."
    })))
}
