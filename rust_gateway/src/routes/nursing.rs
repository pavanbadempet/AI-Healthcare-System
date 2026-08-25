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
use crate::models::NursingTask;
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct NursingTaskCreate {
    pub patient_id: i64,
    pub assigned_nurse_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub admission_id: Option<i64>,
    pub department_id: Option<i64>,
    pub task_type: String,
    pub title: String,
    pub instructions: Option<String>,
    pub priority: Option<String>,
    pub due_at: Option<NaiveDateTime>,
}

#[derive(Debug, Deserialize)]
pub struct NursingTaskComplete {
    pub completion_note: Option<String>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/admin/metrics", get(get_nursing_metrics))
        .route("/doctor/patients/{patient_id}/tasks", get(get_doctor_patient_nursing_tasks))
        .route("/nurse/tasks", get(get_nurse_tasks))
        .route("/patient/tasks", get(get_patient_nursing_tasks))
        .route("/patients/{patient_id}/handoff", post(generate_nursing_handoff_card))
        .route("/tasks", post(create_nursing_task))
        .route("/tasks/{task_id}/complete", put(complete_nursing_task))
}

async fn create_nursing_task(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Json(payload): Json<NursingTaskCreate>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let priority = payload.priority.unwrap_or_else(|| "routine".to_string());
    let facility_id = user.facility_id;

    let insert_sql = r#"
        INSERT INTO nursing_tasks (
            facility_id, patient_id, assigned_nurse_id, created_by_id,
            encounter_id, admission_id, department_id,
            task_type, title, instructions, priority, due_at, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'assigned')
        RETURNING id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id,
                  encounter_id, admission_id, department_id, task_type, title, instructions,
                  priority, status, due_at, completed_at, completion_note, created_at
    "#;

    let task: NursingTask = match pool {
        crate::db::DbPool::Sqlite(p) => {
            sqlx::query_as::<_, NursingTask>(insert_sql)
                .bind(facility_id)
                .bind(payload.patient_id)
                .bind(payload.assigned_nurse_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.admission_id)
                .bind(payload.department_id)
                .bind(&payload.task_type)
                .bind(&payload.title)
                .bind(&payload.instructions)
                .bind(&priority)
                .bind(payload.due_at)
                .fetch_one(p)
                .await
        }
        crate::db::DbPool::Postgres(p) => {
            sqlx::query_as::<_, NursingTask>(insert_sql)
                .bind(facility_id)
                .bind(payload.patient_id)
                .bind(payload.assigned_nurse_id)
                .bind(user.id)
                .bind(payload.encounter_id)
                .bind(payload.admission_id)
                .bind(payload.department_id)
                .bind(&payload.task_type)
                .bind(&payload.title)
                .bind(&payload.instructions)
                .bind(&priority)
                .bind(payload.due_at)
                .fetch_one(p)
                .await
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "Failed to create nursing task"})))
    })?;

    Ok(Json(task))
}

async fn complete_nursing_task(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(task_id): Path<i64>,
    Json(payload): Json<NursingTaskComplete>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let pool = &state.db_pool;

    let get_sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks WHERE id = $1";
    let task: Option<NursingTask> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(task_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(task_id).fetch_optional(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    let task = match task {
        Some(t) => t,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Nursing task not found"})))),
    };

    if user.role != "admin" && user.role != "nurse" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Nurse or admin privileges required"}))));
    }

    if user.role == "nurse" && task.assigned_nurse_id.is_some() && task.assigned_nurse_id != Some(user.id) {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Nurse is not assigned to this task"}))));
    }

    if task.status == "completed" {
        return Err((StatusCode::CONFLICT, Json(json!({"detail": "Nursing task is already completed"}))));
    }

    let now = Utc::now().naive_utc();
    let update_sql = "UPDATE nursing_tasks SET status = 'completed', completed_by_id = $1, completed_at = $2, completion_note = $3 WHERE id = $4";
    match pool {
        crate::db::DbPool::Sqlite(p) => { let _ = sqlx::query(update_sql).bind(user.id).bind(now).bind(&payload.completion_note).bind(task_id).execute(p).await; }
        crate::db::DbPool::Postgres(p) => { let _ = sqlx::query(update_sql).bind(user.id).bind(now).bind(&payload.completion_note).bind(task_id).execute(p).await; }
    };

    let updated: NursingTask = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(get_sql).bind(task_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(get_sql).bind(task_id).fetch_one(p).await.map_err(|_| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"}))))?,
    };

    Ok(Json(updated))
}

async fn get_nurse_tasks(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "nurse" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Nurse or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    let tasks: Vec<NursingTask> = if user.role == "nurse" {
        let sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks WHERE assigned_nurse_id = $1 ORDER BY created_at DESC";
        match pool {
            crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
            crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
        }
    } else {
        match user.facility_id {
            Some(fid) => {
                let sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks WHERE facility_id = $1 ORDER BY created_at DESC";
                match pool {
                    crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
                    crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(fid).fetch_all(p).await,
                }
            }
            None => {
                let sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks ORDER BY created_at DESC";
                match pool {
                    crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).fetch_all(p).await,
                    crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).fetch_all(p).await,
                }
            }
        }
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(tasks))
}

async fn get_patient_nursing_tasks(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "patient" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Patient access required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks WHERE patient_id = $1 ORDER BY created_at DESC";

    let tasks: Vec<NursingTask> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(user.id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(tasks))
}

async fn get_doctor_patient_nursing_tasks(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Doctor or admin privileges required"}))));
    }

    let pool = &state.db_pool;
    let sql = "SELECT id, facility_id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, instructions, priority, status, due_at, completed_at, completion_note, created_at FROM nursing_tasks WHERE patient_id = $1 ORDER BY created_at DESC";

    let tasks: Vec<NursingTask> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(sql).bind(patient_id).fetch_all(p).await,
    }
    .map_err(|e| {
        eprintln!("DB Error: {:?}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": "DB error"})))
    })?;

    Ok(Json(json!({
        "patient_id": patient_id,
        "tasks": tasks,
        "clinical_safety_note": "Nursing tasks support care coordination and require staff completion."
    })))
}

async fn get_nursing_metrics(
    State(state): State<AppState>,
    user: AuthenticatedUser,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Admin privileges required"}))));
    }

    #[derive(sqlx::FromRow)]
    struct TaskMetricRow {
        status: String,
        task_type: String,
        due_at: Option<NaiveDateTime>,
    }

    const SQL_BY_FACILITY: &str = "SELECT status, task_type, due_at FROM nursing_tasks WHERE facility_id = $1";
    const SQL_ALL: &str = "SELECT status, task_type, due_at FROM nursing_tasks";

    let rows: Vec<TaskMetricRow> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            if let Some(fid) = user.facility_id {
                sqlx::query_as::<_, TaskMetricRow>(SQL_BY_FACILITY).bind(fid).fetch_all(p).await.unwrap_or_default()
            } else {
                sqlx::query_as::<_, TaskMetricRow>(SQL_ALL).fetch_all(p).await.unwrap_or_default()
            }
        }
        crate::db::DbPool::Postgres(p) => {
            if let Some(fid) = user.facility_id {
                sqlx::query_as::<_, TaskMetricRow>(SQL_BY_FACILITY).bind(fid).fetch_all(p).await.unwrap_or_default()
            } else {
                sqlx::query_as::<_, TaskMetricRow>(SQL_ALL).fetch_all(p).await.unwrap_or_default()
            }
        }
    };

    let total = rows.len();
    let assigned = rows.iter().filter(|r| r.status == "assigned").count();
    let completed = rows.iter().filter(|r| r.status == "completed").count();
    let now = Utc::now().naive_utc();
    let overdue = rows.iter().filter(|r| r.status != "completed" && r.due_at.is_some() && r.due_at.unwrap() < now).count();

    let mut tasks_by_type = serde_json::Map::new();
    for r in &rows {
        let entry = tasks_by_type.entry(&r.task_type).or_insert(json!(0));
        if let Some(n) = entry.as_i64() {
            *entry = json!(n + 1);
        }
    }

    Ok(Json(json!({
        "total_tasks": total,
        "assigned_tasks": assigned,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "tasks_by_type": tasks_by_type,
        "operations_note": "Nursing metrics support care coordination; clinical accountability remains with licensed staff."
    })))
}

async fn generate_nursing_handoff_card(
    State(state): State<AppState>,
    user: AuthenticatedUser,
    Path(patient_id): Path<i64>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    if user.role != "nurse" && user.role != "doctor" && user.role != "admin" {
        return Err((StatusCode::FORBIDDEN, Json(json!({"detail": "Nurse, doctor, or admin privileges required"}))));
    }

    let pool = &state.db_pool;

    let patient_sql = "SELECT id, full_name, username, gender, dob, existing_ailments FROM users WHERE id = $1 AND role = 'patient'";
    #[derive(sqlx::FromRow)]
    struct PatientHandoffInfo {
        id: i64,
        full_name: Option<String>,
        username: String,
        gender: Option<String>,
        dob: Option<String>,
        existing_ailments: Option<String>,
    }

    let patient: Option<PatientHandoffInfo> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(patient_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(patient_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
    };

    let p_info = match patient {
        Some(p) => p,
        None => return Err((StatusCode::NOT_FOUND, Json(json!({"detail": "Patient not found"})))),
    };

    let vitals_sql = "SELECT heart_rate, systolic_bp, diastolic_bp, spo2, temperature_c, respiratory_rate FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 1";
    #[derive(sqlx::FromRow)]
    struct LatestVitals {
        heart_rate: Option<f64>,
        systolic_bp: Option<f64>,
        diastolic_bp: Option<f64>,
        spo2: Option<f64>,
        temperature_c: Option<f64>,
        respiratory_rate: Option<f64>,
    }

    let vitals: Option<LatestVitals> = match pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(vitals_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
        crate::db::DbPool::Postgres(p) => sqlx::query_as(vitals_sql).bind(patient_id).fetch_optional(p).await.unwrap_or(None),
    };

    let vitals_str = match vitals {
        Some(v) => format!("HR: {:.0} bpm, BP: {:.0}/{:.0} mmHg, SpO2: {:.0}%, Temp: {:.1}°C, RR: {:.0}/min",
            v.heart_rate.unwrap_or(72.0),
            v.systolic_bp.unwrap_or(120.0),
            v.diastolic_bp.unwrap_or(80.0),
            v.spo2.unwrap_or(98.0),
            v.temperature_c.unwrap_or(37.0),
            v.respiratory_rate.unwrap_or(16.0),
        ),
        None => "No recorded vital signs".to_string(),
    };

    let handoff_card = json!({
        "patient_id": patient_id,
        "patient_name": p_info.full_name.unwrap_or(p_info.username),
        "gender": p_info.gender.unwrap_or_else(|| "Unknown".to_string()),
        "isbar_situation": format!("Patient #{}, history: {}", patient_id, p_info.existing_ailments.unwrap_or_else(|| "General monitoring".to_string())),
        "isbar_background": "Inpatient care episode in active management.",
        "isbar_assessment": format!("Current status stable. Vitals: {}", vitals_str),
        "isbar_recommendation": "Continue planned medication and round schedule. Re-evaluate vitals in 4 hours.",
        "generated_at": Utc::now().to_rfc3339(),
        "clinical_safety_note": "ISBAR shift handoff cards provide structured communication aids; nurses must verbally verify patient condition during handover."
    });

    Ok(Json(handoff_card))
}
