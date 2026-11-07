//! Axum 0.8 Route Handlers for Enterprise Healthcare Lakehouse Data Engineering:
//! - OMOP CDM v5.4 Relational Transformations
//! - Spark Declarative Pipelines (SDP) & Great Expectations Quality Audits
//! - Delta Lake ACID Commit History, Time-Travel Snapshots, and Table Restores
//! - Delta Change Data Feed (CDF) CDC Stream Queries

use axum::{
    extract::{Query, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::RwLock;

use crate::AppState;

// ── In-Memory Delta Commit Registry (Thread-Safe Stateful Rollback) ───────────

static DELTA_REGISTRY: RwLock<Option<HashMap<String, Vec<DeltaCommitLog>>>> = RwLock::new(None);

fn get_or_init_delta_registry() -> HashMap<String, Vec<DeltaCommitLog>> {
    let mut map = HashMap::new();
    map.insert(
        "workspace.healthcare_silver.patients".to_string(),
        vec![
            DeltaCommitLog {
                version: 2,
                timestamp: "2026-08-12T14:15:00Z".to_string(),
                operation: "MERGE_INTO_SILVER".to_string(),
                operation_parameters: json!({ "matched_updates": 14, "inserted_rows": 6 }),
                user_metadata: Some("Scheduled Databricks Medallion Silver Sync".to_string()),
                read_version: Some(1),
                num_rows: Some(2100),
                author: Some("medallion_pipeline".to_string()),
            },
            DeltaCommitLog {
                version: 1,
                timestamp: "2026-08-11T12:30:00Z".to_string(),
                operation: "GREAT_EXPECTATIONS_CLEANSE".to_string(),
                operation_parameters: json!({ "pass_rate": 0.98 }),
                user_metadata: Some("Spark Declarative Pipeline Quality Filter".to_string()),
                read_version: Some(0),
                num_rows: Some(1820),
                author: Some("streaming_telemetry_job".to_string()),
            },
            DeltaCommitLog {
                version: 0,
                timestamp: "2026-08-10T10:00:00Z".to_string(),
                operation: "BRONZE_INGEST_STREAM".to_string(),
                operation_parameters: json!({ "batch_id": 104 }),
                user_metadata: Some("Initial Table Bootstrap".to_string()),
                read_version: None,
                num_rows: Some(1500),
                author: Some("pipeline_system".to_string()),
            },
        ],
    );
    map
}

// ── OMOP Data Transfer Objects (CDM v5.4) ────────────────────────────────────

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RawPatientPayload {
    pub patient_id: String,
    #[serde(default = "default_year_of_birth")]
    pub year_of_birth: i32,
    #[serde(default = "default_gender")]
    pub gender: String,
    #[serde(default)]
    pub conditions: Vec<String>,
    #[serde(default)]
    pub medications: Vec<String>,
    #[serde(default)]
    pub vitals: HashMap<String, Value>,
}

fn default_year_of_birth() -> i32 {
    1975
}

fn default_gender() -> String {
    "male".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonRow {
    pub person_id: i64,
    pub gender_concept_id: i64,
    pub year_of_birth: i32,
    pub month_of_birth: i32,
    pub day_of_birth: i32,
    pub race_concept_id: i64,
    pub ethnicity_concept_id: i64,
    pub person_source_value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisitOccurrenceRow {
    pub visit_occurrence_id: i64,
    pub person_id: i64,
    pub visit_concept_id: i64,
    pub visit_start_date: String,
    pub visit_end_date: String,
    pub visit_type_concept_id: i64,
    pub visit_source_value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConditionOccurrenceRow {
    pub condition_occurrence_id: i64,
    pub person_id: i64,
    pub condition_concept_id: i64,
    pub condition_start_date: String,
    pub condition_type_concept_id: i64,
    pub condition_source_value: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub condition_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrugExposureRow {
    pub drug_exposure_id: i64,
    pub person_id: i64,
    pub drug_concept_id: i64,
    pub drug_exposure_start_date: String,
    pub drug_type_concept_id: i64,
    pub drug_source_value: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub drug_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeasurementRow {
    pub measurement_id: i64,
    pub person_id: i64,
    pub measurement_concept_id: i64,
    pub measurement_date: String,
    pub measurement_type_concept_id: i64,
    pub value_as_number: f64,
    pub unit_concept_id: i64,
    pub measurement_source_value: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub measurement_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[allow(non_snake_case)]
pub struct OmopTransformResponse {
    pub PERSON: PersonRow,
    pub VISIT_OCCURRENCE: VisitOccurrenceRow,
    pub CONDITION_OCCURRENCE: Vec<ConditionOccurrenceRow>,
    pub DRUG_EXPOSURE: Vec<DrugExposureRow>,
    pub MEASUREMENT: Vec<MeasurementRow>,
}

// ── Quality Audit Data Transfer Objects ──────────────────────────────────────

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct QualityAuditRequest {
    pub records: Vec<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualitySummary {
    pub protocol: String,
    pub total_records: usize,
    pub clean_records: usize,
    pub clean_count: usize,
    pub quarantined_records: usize,
    pub quarantined_count: usize,
    pub pass_rate: f64,
    pub pass_rate_pct: f64,
    pub violation_breakdown: HashMap<String, usize>,
    pub dlt_quarantine_table: String,
    pub silver_clean_table: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityAuditResponse {
    pub summary: QualitySummary,
    pub clean_sample: Vec<Value>,
    pub quarantined_sample: Vec<Value>,
}

// ── Delta Lake Data Transfer Objects ─────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeltaCommitLog {
    pub version: i64,
    pub timestamp: String,
    pub operation: String,
    #[serde(default)]
    pub operation_parameters: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_metadata: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub read_version: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub num_rows: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub author: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DeltaHistoryQuery {
    #[serde(default = "default_table_name")]
    pub table_name: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct TimeTravelRequest {
    #[serde(default = "default_table_name")]
    pub table_name: String,
    #[serde(default)]
    pub target_version: i64,
}

#[derive(Debug, Deserialize)]
pub struct TimeTravelQuery {
    #[serde(default = "default_table_name")]
    pub table_name: String,
    #[serde(default)]
    pub target_version: i64,
}

fn default_table_name() -> String {
    "workspace.healthcare_silver.patients".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeTravelResponse {
    pub table_name: String,
    pub version: i64,
    pub queried_version: i64,
    pub commit_timestamp: String,
    pub operation: String,
    pub rows_at_version: usize,
    pub row_count: usize,
    pub status: String,
    pub data: Vec<Value>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RestoreTableRequest {
    #[serde(default = "default_table_name")]
    pub table_name: String,
    #[serde(default)]
    pub target_version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RestoreTableResponse {
    pub table_name: String,
    pub restored_to_version: i64,
    pub new_commit_version: i64,
    pub status: String,
    pub hipaa_audit_log_id: String,
}

#[derive(Debug, Deserialize)]
pub struct CdfQuery {
    #[serde(default = "default_table_name")]
    pub table_name: String,
    #[serde(default)]
    pub start_version: i64,
    #[serde(default = "default_end_version")]
    pub end_version: i64,
}

fn default_end_version() -> i64 {
    2
}

// ── Concept Resolver & Zero-Allocation Hash Helpers ──────────────────────────

struct OmopConcept {
    concept_id: i64,
    concept_name: &'static str,
    unit_concept_id: i64,
}

fn resolve_concept(raw_term: &str) -> OmopConcept {
    let term = raw_term.trim().to_lowercase();
    // Conditions
    if term.contains("diabetes") || term.contains("type 2") {
        OmopConcept { concept_id: 201826, concept_name: "Type 2 diabetes mellitus", unit_concept_id: 0 }
    } else if term.contains("hypertension") || term.contains("htn") {
        OmopConcept { concept_id: 320128, concept_name: "Essential hypertension", unit_concept_id: 0 }
    } else if term.contains("kidney") || term.contains("ckd") {
        OmopConcept { concept_id: 443614, concept_name: "Chronic kidney disease stage 3", unit_concept_id: 0 }
    } else if term.contains("heart failure") || term.contains("chf") {
        OmopConcept { concept_id: 316139, concept_name: "Heart failure", unit_concept_id: 0 }
    } else if term.contains("hyperlipidemia") || term.contains("cholesterol") {
        OmopConcept { concept_id: 432867, concept_name: "Hyperlipidemia", unit_concept_id: 0 }
    // Drugs
    } else if term.contains("metformin") {
        OmopConcept { concept_id: 1503297, concept_name: "Metformin hydrochloride 500 MG", unit_concept_id: 0 }
    } else if term.contains("lisinopril") {
        OmopConcept { concept_id: 1308216, concept_name: "Lisinopril 10 MG Oral Tablet", unit_concept_id: 0 }
    } else if term.contains("atorvastatin") {
        OmopConcept { concept_id: 1545958, concept_name: "Atorvastatin 40 MG Oral Tablet", unit_concept_id: 0 }
    } else if term.contains("empagliflozin") {
        OmopConcept { concept_id: 44816332, concept_name: "Empagliflozin 10 MG Oral Tablet", unit_concept_id: 0 }
    } else if term.contains("semaglutide") {
        OmopConcept { concept_id: 45774751, concept_name: "Semaglutide 0.5 MG/0.37ML", unit_concept_id: 0 }
    // Measurements
    } else if term.contains("systolic") || term == "sbp" {
        OmopConcept { concept_id: 3004249, concept_name: "Systolic blood pressure", unit_concept_id: 8876 }
    } else if term.contains("diastolic") || term == "dbp" {
        OmopConcept { concept_id: 3012888, concept_name: "Diastolic blood pressure", unit_concept_id: 8876 }
    } else if term.contains("heart_rate") || term.contains("heart rate") || term == "hr" {
        OmopConcept { concept_id: 3027018, concept_name: "Heart rate", unit_concept_id: 8541 }
    } else if term.contains("glucose") || term == "fasting_glucose" {
        OmopConcept { concept_id: 3004501, concept_name: "Glucose [Mass/volume] in Serum or Plasma", unit_concept_id: 8840 }
    } else if term.contains("hba1c") {
        OmopConcept { concept_id: 3004410, concept_name: "Hemoglobin A1c/Hemoglobin.total in Blood", unit_concept_id: 8554 }
    } else if term.contains("egfr") {
        OmopConcept { concept_id: 3049187, concept_name: "Glomerular filtration rate/1.73 sq M.predicted", unit_concept_id: 8645 }
    } else if term.contains("spo2") || term.contains("oxygen") {
        OmopConcept { concept_id: 40762499, concept_name: "Oxygen saturation in Blood", unit_concept_id: 8554 }
    } else {
        OmopConcept { concept_id: 0, concept_name: "Unmapped concept", unit_concept_id: 0 }
    }
}

fn hash_to_id(s: &str) -> i64 {
    let mut hasher = Sha256::new();
    hasher.update(s.as_bytes());
    let result = hasher.finalize();
    let hex_str = format!("{:02x}{:02x}{:02x}{:02x}", result[0], result[1], result[2], result[3]);
    i64::from_str_radix(&hex_str, 16).unwrap_or(1001)
}

// ── Axum Router Builder ──────────────────────────────────────────────────────

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/omop/transform", post(transform_to_omop))
        .route("/quality/audit", post(audit_data_quality))
        .route("/delta/history", get(get_delta_history))
        .route("/delta/time-travel", post(post_delta_time_travel).get(get_delta_time_travel))
        .route("/delta/restore", post(restore_table))
        .route("/delta/cdf", get(read_change_data_feed))
}

// ── Handler Implementations ──────────────────────────────────────────────────

/// POST /v1/lakehouse/omop/transform
pub async fn transform_to_omop(
    State(_state): State<AppState>,
    Json(payload): Json<RawPatientPayload>,
) -> Result<Json<OmopTransformResponse>, (StatusCode, Json<Value>)> {
    let person_id = hash_to_id(&payload.patient_id);
    let today = Utc::now().format("%Y-%m-%d").to_string();

    let g_lower = payload.gender.to_lowercase();
    let gender_concept_id = if g_lower.starts_with('f') {
        8532
    } else if g_lower.starts_with('m') {
        8507
    } else {
        8521
    };

    let person_row = PersonRow {
        person_id,
        gender_concept_id,
        year_of_birth: payload.year_of_birth,
        month_of_birth: 6,
        day_of_birth: 15,
        race_concept_id: 8527,
        ethnicity_concept_id: 38003564,
        person_source_value: payload.patient_id.clone(),
    };

    let visit_occurrence_id = hash_to_id(&format!("VISIT-{}-{}", person_id, today));
    let visit_row = VisitOccurrenceRow {
        visit_occurrence_id,
        person_id,
        visit_concept_id: 9202,
        visit_start_date: today.clone(),
        visit_end_date: today.clone(),
        visit_type_concept_id: 32817,
        visit_source_value: "Telehealth / Outpatient Clinical AI Portal".to_string(),
    };

    let mut conditions = Vec::new();
    for cond_str in &payload.conditions {
        let concept = resolve_concept(cond_str);
        conditions.push(ConditionOccurrenceRow {
            condition_occurrence_id: hash_to_id(&format!("COND-{}-{}", person_id, cond_str)),
            person_id,
            condition_concept_id: concept.concept_id,
            condition_start_date: today.clone(),
            condition_type_concept_id: 32817,
            condition_source_value: cond_str.clone(),
            condition_name: Some(concept.concept_name.to_string()),
        });
    }

    let mut drugs = Vec::new();
    for drug_str in &payload.medications {
        let concept = resolve_concept(drug_str);
        drugs.push(DrugExposureRow {
            drug_exposure_id: hash_to_id(&format!("DRUG-{}-{}", person_id, drug_str)),
            person_id,
            drug_concept_id: concept.concept_id,
            drug_exposure_start_date: today.clone(),
            drug_type_concept_id: 38000177,
            drug_source_value: drug_str.clone(),
            drug_name: Some(concept.concept_name.to_string()),
        });
    }

    let mut measurements = Vec::new();
    for (meas_key, meas_val) in &payload.vitals {
        let num_val = match meas_val {
            Value::Number(n) => n.as_f64().unwrap_or(0.0),
            Value::String(s) => s.parse::<f64>().unwrap_or(0.0),
            _ => continue,
        };
        let concept = resolve_concept(meas_key);
        measurements.push(MeasurementRow {
            measurement_id: hash_to_id(&format!("MEAS-{}-{}", person_id, meas_key)),
            person_id,
            measurement_concept_id: concept.concept_id,
            measurement_date: today.clone(),
            measurement_type_concept_id: 44818701,
            value_as_number: num_val,
            unit_concept_id: concept.unit_concept_id,
            measurement_source_value: format!("{}: {}", meas_key, num_val),
            measurement_name: Some(concept.concept_name.to_string()),
        });
    }

    Ok(Json(OmopTransformResponse {
        PERSON: person_row,
        VISIT_OCCURRENCE: visit_row,
        CONDITION_OCCURRENCE: conditions,
        DRUG_EXPOSURE: drugs,
        MEASUREMENT: measurements,
    }))
}

/// POST /v1/lakehouse/quality/audit
pub async fn audit_data_quality(
    State(_state): State<AppState>,
    Json(req): Json<QualityAuditRequest>,
) -> Result<Json<QualityAuditResponse>, (StatusCode, Json<Value>)> {
    let mut clean_batch = Vec::new();
    let mut quarantine_batch = Vec::new();
    let mut violation_counts: HashMap<String, usize> = HashMap::new();

    for mut rec in req.records {
        let mut violations = Vec::new();

        // 1. Primary Key Check
        let pid = rec.get("patient_id").and_then(|v| v.as_str());
        if pid.map_or(true, |s| s.trim().is_empty()) {
            violations.push("SDP_ERR_SCHEMA_NULL_PK: patient_id is required".to_string());
        }

        // 2. Age Check (if present)
        if let Some(age_val) = rec.get("age").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if age_val < 0.0 || age_val > 130.0 {
                violations.push(format!("SDP_ERR_PHYSIO_AGE_OOB: age={age_val} outside [0, 130]"));
            }
        }

        // 3. Heart Rate Bounds [30, 220]
        if let Some(hr_val) = rec.get("heart_rate").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if hr_val < 30.0 || hr_val > 220.0 {
                violations.push(format!("SDP_ERR_PHYSIO_HR_OOB: heart_rate={hr_val} outside [30, 220]"));
            }
        }

        // 4. Systolic BP Bounds [60, 250]
        if let Some(sbp_val) = rec.get("systolic_bp").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if sbp_val < 60.0 || sbp_val > 250.0 {
                violations.push(format!("SDP_ERR_PHYSIO_SBP_OOB: systolic_bp={sbp_val} outside [60, 250]"));
            }
        }

        // 5. Diastolic BP Bounds [35, 150]
        if let Some(dbp_val) = rec.get("diastolic_bp").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if dbp_val < 35.0 || dbp_val > 150.0 {
                violations.push(format!("SDP_ERR_PHYSIO_DBP_OOB: diastolic_bp={dbp_val} outside [35, 150]"));
            }
        }

        // 6. Blood Oxygen SpO2 Bounds [50, 100]
        if let Some(spo2_val) = rec.get("spo2").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if spo2_val < 50.0 || spo2_val > 100.0 {
                violations.push(format!("SDP_ERR_PHYSIO_SPO2_OOB: spo2={spo2_val} outside [50, 100]"));
            }
        }

        // 7. Fasting Blood Glucose Bounds [20, 800]
        if let Some(glu_val) = rec.get("fasting_glucose").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64))) {
            if glu_val < 20.0 || glu_val > 800.0 {
                violations.push(format!("SDP_ERR_PHYSIO_GLUCOSE_OOB: fasting_glucose={glu_val} outside [20, 800]"));
            }
        }

        if violations.is_empty() {
            if let Some(obj) = rec.as_object_mut() {
                obj.insert("status".to_string(), json!("PASSED_ALL_GATES"));
            }
            clean_batch.push(rec);
        } else {
            for v in &violations {
                let key = v.split(':').next().unwrap_or("UNKNOWN").to_string();
                *violation_counts.entry(key).or_insert(0) += 1;
            }
            let mut q_rec = rec.clone();
            if let Some(obj) = q_rec.as_object_mut() {
                obj.insert("_sdp_status".to_string(), json!("QUARANTINED"));
                obj.insert("_sdp_quarantine_timestamp".to_string(), json!(Utc::now().to_rfc3339()));
                obj.insert("_sdp_violation_count".to_string(), json!(violations.len()));
                obj.insert("_sdp_violations".to_string(), json!(violations));
                obj.insert("failure_reason".to_string(), json!(violations.join("; ")));
                obj.insert("raw_record".to_string(), rec);
            }
            quarantine_batch.push(q_rec);
        }
    }

    let total = clean_batch.len() + quarantine_batch.len();
    let clean_cnt = clean_batch.len();
    let quar_cnt = quarantine_batch.len();
    let pass_rate = if total > 0 { (clean_cnt as f64) / (total as f64) } else { 1.0 };
    let pass_rate_pct = (pass_rate * 10000.0).round() / 100.0;

    let summary = QualitySummary {
        protocol: "Spark Declarative Pipelines (SDP) & DLT Expectations".to_string(),
        total_records: total,
        clean_records: clean_cnt,
        clean_count: clean_cnt,
        quarantined_records: quar_cnt,
        quarantined_count: quar_cnt,
        pass_rate: (pass_rate * 100.0).round() / 100.0,
        pass_rate_pct,
        violation_breakdown: violation_counts,
        dlt_quarantine_table: "workspace.healthcare_bronze.quarantined_records".to_string(),
        silver_clean_table: "workspace.healthcare_silver.telemetry".to_string(),
    };

    let clean_sample = clean_batch.into_iter().take(5).collect();
    let quarantined_sample = quarantine_batch.into_iter().take(5).collect();

    Ok(Json(QualityAuditResponse {
        summary,
        clean_sample,
        quarantined_sample,
    }))
}

/// GET /v1/lakehouse/delta/history
pub async fn get_delta_history(
    State(_state): State<AppState>,
    Query(query): Query<DeltaHistoryQuery>,
) -> Result<Json<Vec<DeltaCommitLog>>, (StatusCode, Json<Value>)> {
    let mut reg = DELTA_REGISTRY.write().map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": format!("Registry lock failed: {}", e) })),
        )
    })?;

    let map = reg.get_or_insert_with(get_or_init_delta_registry);
    let commits = map.get(&query.table_name).cloned().unwrap_or_else(|| {
        vec![DeltaCommitLog {
            version: 0,
            timestamp: Utc::now().to_rfc3339(),
            operation: "INITIALIZE DELTA TABLE".to_string(),
            operation_parameters: json!({ "status": "bootstrap" }),
            user_metadata: Some("Auto-initialized table".to_string()),
            read_version: None,
            num_rows: Some(500),
            author: Some("system_bootstrap".to_string()),
        }]
    });

    Ok(Json(commits))
}

/// POST /v1/lakehouse/delta/time-travel
pub async fn post_delta_time_travel(
    State(state): State<AppState>,
    Json(payload): Json<TimeTravelRequest>,
) -> Result<Json<TimeTravelResponse>, (StatusCode, Json<Value>)> {
    handle_time_travel_internal(state, payload.table_name, payload.target_version).await
}

/// GET /v1/lakehouse/delta/time-travel
pub async fn get_delta_time_travel(
    State(state): State<AppState>,
    Query(query): Query<TimeTravelQuery>,
) -> Result<Json<TimeTravelResponse>, (StatusCode, Json<Value>)> {
    handle_time_travel_internal(state, query.table_name, query.target_version).await
}

async fn handle_time_travel_internal(
    _state: AppState,
    table_name: String,
    target_version: i64,
) -> Result<Json<TimeTravelResponse>, (StatusCode, Json<Value>)> {
    let mut reg = DELTA_REGISTRY.write().map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": format!("Registry lock failed: {}", e) })),
        )
    })?;

    let map = reg.get_or_insert_with(get_or_init_delta_registry);
    let history = map.get(&table_name).cloned().unwrap_or_default();
    let matched = history.iter().find(|h| h.version == target_version)
        .or_else(|| history.first());

    let (commit_ts, op) = match matched {
        Some(c) => (c.timestamp.clone(), c.operation.clone()),
        None => (Utc::now().to_rfc3339(), "SNAPSHOT_INSPECT".to_string()),
    };

    let sample_records = vec![
        json!({ "patient_id": "PAT-001", "age": 54, "systolic_bp": 138, "diastolic_bp": 88, "status": "stable", "version": target_version }),
        json!({ "patient_id": "PAT-002", "age": 62, "systolic_bp": 155, "diastolic_bp": 95, "status": "elevated", "version": target_version }),
        json!({ "patient_id": "PAT-003", "age": 48, "systolic_bp": 120, "diastolic_bp": 80, "status": "optimal", "version": target_version }),
        json!({ "patient_id": "PAT-004", "age": 71, "systolic_bp": 142, "diastolic_bp": 90, "status": "monitored", "version": target_version }),
    ];

    let row_count = sample_records.len();

    Ok(Json(TimeTravelResponse {
        table_name,
        version: target_version,
        queried_version: target_version,
        commit_timestamp: commit_ts,
        operation: op,
        rows_at_version: row_count,
        row_count,
        status: "SNAPSHOT_RETRIEVED".to_string(),
        data: sample_records,
    }))
}

/// POST /v1/lakehouse/delta/restore
pub async fn restore_table(
    State(_state): State<AppState>,
    Json(payload): Json<RestoreTableRequest>,
) -> Result<Json<RestoreTableResponse>, (StatusCode, Json<Value>)> {
    let mut reg = DELTA_REGISTRY.write().map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": format!("Registry lock failed: {}", e) })),
        )
    })?;

    let map = reg.get_or_insert_with(get_or_init_delta_registry);
    let history = map.entry(payload.table_name.clone()).or_insert_with(Vec::new);
    let new_version = history.len() as i64;
    let audit_id = format!("AUDIT-RESTORE-{}", Utc::now().timestamp());

    let restore_commit = DeltaCommitLog {
        version: new_version,
        timestamp: Utc::now().to_rfc3339(),
        operation: format!("RESTORE TO VERSION {}", payload.target_version),
        operation_parameters: json!({ "target_version": payload.target_version, "audit_id": audit_id }),
        user_metadata: Some("HIPAA-compliant rollback authorization".to_string()),
        read_version: Some(payload.target_version),
        num_rows: Some(1500),
        author: Some("clinician_authorized_admin".to_string()),
    };

    history.insert(0, restore_commit);

    Ok(Json(RestoreTableResponse {
        table_name: payload.table_name,
        restored_to_version: payload.target_version,
        new_commit_version: new_version,
        status: "SUCCESSFULLY_RESTORED".to_string(),
        hipaa_audit_log_id: audit_id,
    }))
}

/// GET /v1/lakehouse/delta/cdf
pub async fn read_change_data_feed(
    State(_state): State<AppState>,
    Query(query): Query<CdfQuery>,
) -> Result<Json<Vec<Value>>, (StatusCode, Json<Value>)> {
    let now = Utc::now().to_rfc3339();
    let records = vec![
        json!({
            "patient_id": "PAT-9912",
            "_change_type": "insert",
            "_commit_version": query.start_version,
            "_commit_timestamp": now,
            "systolic_bp": 142,
            "fasting_glucose": 155
        }),
        json!({
            "patient_id": "PAT-9912",
            "_change_type": "update_postimage",
            "_commit_version": query.end_version,
            "_commit_timestamp": now,
            "systolic_bp": 128,
            "fasting_glucose": 110
        }),
    ];
    Ok(Json(records))
}
