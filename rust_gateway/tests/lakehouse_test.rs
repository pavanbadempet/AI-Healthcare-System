//! Integration Test: Native Rust Lakehouse Router (/v1/lakehouse)
//! Verifies OMOP CDM v5.4 relational transformations, Great Expectations data quality gates,
//! Delta Lake ACID commit history, time travel queries, and stateful table restore.

use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use serde_json::{json, Value};
use std::sync::{Arc, Mutex};
use tower::ServiceExt;

use rust_gateway_ffi::{
    routes::build_app_router,
    AppState,
};

async fn create_test_state() -> AppState {
    let pool = rust_gateway_ffi::db::DbPool::connect_lazy("sqlite::memory:").expect("lazy pool");
    let inference_manager = Arc::new(
        rust_gateway_ffi::ml::InferenceManager::new()
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("backend"))
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("../backend"))
            .or_else(|_| rust_gateway_ffi::ml::InferenceManager::from_dir("."))
            .unwrap_or_else(|_| {
                rust_gateway_ffi::ml::InferenceManager::from_dir("backend")
                    .or_else(|_| rust_gateway_ffi::ml::InferenceManager::new())
                    .expect("fallback inference manager")
            }),
    );
    AppState {
        http_client: reqwest::Client::new(),
        db_pool: pool,
        secret_key: "test_secret_for_lakehouse_tests".to_string(),
        sysinfo: Arc::new(Mutex::new(sysinfo::System::new())),
        vector_store: rust_gateway_ffi::vector_store::VectorStoreState::default(),
        inference_manager,
    }
}

#[tokio::test]
async fn test_omop_transform_snomed_rxnorm_loinc() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({
        "patient_id": "PAT-9810",
        "year_of_birth": 1975,
        "gender": "male",
        "conditions": ["Type 2 diabetes", "Essential hypertension", "Chronic kidney disease"],
        "medications": ["Metformin", "Lisinopril", "Atorvastatin"],
        "vitals": {
            "systolic_bp": 135.0,
            "diastolic_bp": 85.0,
            "heart_rate": 74.0,
            "fasting_glucose": 115.0,
            "spo2": 98.0
        }
    });

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/v1/lakehouse/omop/transform")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let res: Value = serde_json::from_slice(&bytes).unwrap();

    // 1. Validate PERSON table
    let person = &res["PERSON"];
    assert_eq!(person["gender_concept_id"], 8507); // Male
    assert_eq!(person["year_of_birth"], 1975);
    assert_eq!(person["race_concept_id"], 8527);
    assert_eq!(person["person_source_value"], "PAT-9810");

    // 2. Validate VISIT_OCCURRENCE table
    let visit = &res["VISIT_OCCURRENCE"];
    assert_eq!(visit["visit_concept_id"], 9202);
    assert_eq!(visit["visit_type_concept_id"], 32817);

    // 3. Validate CONDITION_OCCURRENCE mappings (SNOMED-CT)
    let conditions = res["CONDITION_OCCURRENCE"].as_array().expect("conditions array");
    assert_eq!(conditions.len(), 3);
    let condition_concepts: Vec<i64> = conditions
        .iter()
        .map(|c| c["condition_concept_id"].as_i64().unwrap())
        .collect();
    assert!(condition_concepts.contains(&201826)); // Type 2 diabetes
    assert!(condition_concepts.contains(&320128)); // Essential hypertension
    assert!(condition_concepts.contains(&443614)); // Chronic kidney disease

    // 4. Validate DRUG_EXPOSURE mappings (RxNorm)
    let drugs = res["DRUG_EXPOSURE"].as_array().expect("drugs array");
    assert_eq!(drugs.len(), 3);
    let drug_concepts: Vec<i64> = drugs
        .iter()
        .map(|d| d["drug_concept_id"].as_i64().unwrap())
        .collect();
    assert!(drug_concepts.contains(&1503297)); // Metformin
    assert!(drug_concepts.contains(&1308216)); // Lisinopril
    assert!(drug_concepts.contains(&1545958)); // Atorvastatin

    // 5. Validate MEASUREMENT mappings (LOINC)
    let measurements = res["MEASUREMENT"].as_array().expect("measurements array");
    assert_eq!(measurements.len(), 5);
    let meas_concepts: Vec<i64> = measurements
        .iter()
        .map(|m| m["measurement_concept_id"].as_i64().unwrap())
        .collect();
    assert!(meas_concepts.contains(&3004249)); // Systolic BP
    assert!(meas_concepts.contains(&3012888)); // Diastolic BP
    assert!(meas_concepts.contains(&3027018)); // Heart rate
    assert!(meas_concepts.contains(&3004501)); // Fasting glucose
    assert!(meas_concepts.contains(&40762499)); // SpO2
}

#[tokio::test]
async fn test_quality_gate_partitioning() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({
        "records": [
            { "patient_id": "P-101", "age": 45, "systolic_bp": 120, "diastolic_bp": 80, "heart_rate": 72, "spo2": 99 },
            { "patient_id": "P-102", "age": 62, "systolic_bp": 135, "diastolic_bp": 88, "heart_rate": 68, "spo2": 97 },
            { "patient_id": "P-103", "age": 28, "systolic_bp": 110, "diastolic_bp": 70, "heart_rate": 80, "spo2": 98 },
            { "patient_id": "P-ERR-01", "age": -5, "systolic_bp": 320, "diastolic_bp": 180, "heart_rate": 280, "spo2": 40 }
        ]
    });

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/v1/lakehouse/quality/audit")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(response.into_body(), usize::MAX).await.unwrap();
    let res: Value = serde_json::from_slice(&bytes).unwrap();

    let summary = &res["summary"];
    assert_eq!(summary["total_records"], 4);
    assert_eq!(summary["clean_records"], 3);
    assert_eq!(summary["quarantined_records"], 1);
    assert_eq!(summary["pass_rate"], 0.75);
    assert_eq!(summary["pass_rate_pct"], 75.0);

    let breakdown = &summary["violation_breakdown"];
    assert!(breakdown["SDP_ERR_PHYSIO_AGE_OOB"].as_u64().unwrap() >= 1);
    assert!(breakdown["SDP_ERR_PHYSIO_SBP_OOB"].as_u64().unwrap() >= 1);

    let quarantined_sample = res["quarantined_sample"].as_array().expect("quarantined sample");
    assert_eq!(quarantined_sample.len(), 1);
    assert_eq!(quarantined_sample[0]["_sdp_status"], "QUARANTINED");
    assert!(quarantined_sample[0]["failure_reason"].as_str().unwrap().contains("SDP_ERR_PHYSIO_SBP_OOB"));
}

#[tokio::test]
async fn test_delta_history_and_restore_cycle() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // 1. Initial history fetch
    let history_res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/history?table_name=workspace.healthcare_silver.patients")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(history_res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(history_res.into_body(), usize::MAX).await.unwrap();
    let commits: Vec<Value> = serde_json::from_slice(&bytes).unwrap();
    assert!(commits.len() >= 3);
    assert_eq!(commits[0]["version"], 2);

    // 2. Perform table restore to version 1
    let restore_payload = json!({
        "table_name": "workspace.healthcare_silver.patients",
        "target_version": 1
    });

    let restore_res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/v1/lakehouse/delta/restore")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&restore_payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(restore_res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(restore_res.into_body(), usize::MAX).await.unwrap();
    let restore_json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(restore_json["status"], "SUCCESSFULLY_RESTORED");
    assert_eq!(restore_json["restored_to_version"], 1);
    assert!(restore_json["hipaa_audit_log_id"].as_str().unwrap().starts_with("AUDIT-RESTORE-"));

    // 3. Verify history now has new restore commit prepended
    let history_res2 = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/history?table_name=workspace.healthcare_silver.patients")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(history_res2.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(history_res2.into_body(), usize::MAX).await.unwrap();
    let commits2: Vec<Value> = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(commits2[0]["operation"], "RESTORE TO VERSION 1");
    assert_eq!(commits2[0]["read_version"], 1);
}

#[tokio::test]
async fn test_delta_time_travel_snapshot() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // 1. POST time travel
    let tt_payload = json!({
        "table_name": "workspace.healthcare_silver.patients",
        "target_version": 0
    });

    let post_res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/v1/lakehouse/delta/time-travel")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&tt_payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(post_res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(post_res.into_body(), usize::MAX).await.unwrap();
    let post_json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(post_json["status"], "SNAPSHOT_RETRIEVED");
    assert_eq!(post_json["queried_version"], 0);
    assert_eq!(post_json["row_count"], 4);

    // 2. GET time travel
    let get_res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/time-travel?table_name=workspace.healthcare_silver.patients&target_version=1")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(get_res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(get_res.into_body(), usize::MAX).await.unwrap();
    let get_json: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(get_json["status"], "SNAPSHOT_RETRIEVED");
    assert_eq!(get_json["queried_version"], 1);
}

#[tokio::test]
async fn test_delta_change_data_feed() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/cdf?table_name=workspace.healthcare_silver.patients&start_version=0&end_version=2")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let records: Vec<Value> = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(records.len(), 2);
    assert_eq!(records[0]["_change_type"], "insert");
    assert_eq!(records[1]["_change_type"], "update_postimage");
}
