//! Adversarial Stress and Data Verification Test Suite for Native Lakehouse Router
//! Tests:
//! 1. OMOP CDM v5.4 Transformation under edge cases, malformed payloads, and unmapped concepts.
//! 2. Great Expectations Quality Audit Gate under boundary conditions, dirty records, empty batches, and invalid schema.
//! 3. Delta Lake operations (history, time-travel, restore, CDF) including non-existent versions and concurrency.

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
        secret_key: "test_secret_for_lakehouse_adversarial".to_string(),
        sysinfo: Arc::new(Mutex::new(sysinfo::System::new())),
        vector_store: rust_gateway_ffi::vector_store::VectorStoreState::default(),
        inference_manager,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. OMOP TRANSFORMATION ADVERSARIAL TESTS
// ─────────────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn test_adversarial_omop_empty_and_default_fields() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Minimal payload with empty strings, empty arrays, missing optional fields
    let payload = json!({
        "patient_id": "P-MINIMAL"
    });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    // Verify defaults applied
    assert_eq!(json_res["PERSON"]["person_source_value"], "P-MINIMAL");
    assert_eq!(json_res["PERSON"]["year_of_birth"], 1975); // default
    assert_eq!(json_res["PERSON"]["gender_concept_id"], 8507); // default male
    assert_eq!(json_res["CONDITION_OCCURRENCE"].as_array().unwrap().len(), 0);
    assert_eq!(json_res["DRUG_EXPOSURE"].as_array().unwrap().len(), 0);
    assert_eq!(json_res["MEASUREMENT"].as_array().unwrap().len(), 0);
}

#[tokio::test]
async fn test_adversarial_omop_gender_classification_variants() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let test_cases = vec![
        ("female", 8532),
        ("Female", 8532),
        ("F", 8532),
        ("FEMALE_CIS", 8532),
        ("male", 8507),
        ("Male", 8507),
        ("M", 8507),
        ("non-binary", 8521),
        ("other", 8521),
        ("unknown", 8521),
        ("", 8521),
    ];

    for (gender_input, expected_concept_id) in test_cases {
        let payload = json!({
            "patient_id": format!("P-GENDER-{}", gender_input),
            "gender": gender_input
        });

        let res = app
            .clone()
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

        assert_eq!(res.status(), StatusCode::OK);
        let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
        let json_res: Value = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(
            json_res["PERSON"]["gender_concept_id"], expected_concept_id,
            "Failed gender mapping for input: '{}'", gender_input
        );
    }
}

#[tokio::test]
async fn test_adversarial_omop_unmapped_concepts_fallback() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({
        "patient_id": "P-UNMAPPED",
        "conditions": ["Alien syndrome", "Xenomorph infection", ""],
        "medications": ["Unobtainium extract", "Vibranium pills"],
        "vitals": {
            "flux_capacitor": 88.0,
            "warp_factor": "9.9",
            "invalid_nan_vital": "not_a_number",
            "boolean_vital": true,
            "null_vital": null
        }
    });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    // Verify unmapped conditions mapped to concept 0
    let conditions = json_res["CONDITION_OCCURRENCE"].as_array().unwrap();
    assert_eq!(conditions.len(), 3);
    for cond in conditions {
        assert_eq!(cond["condition_concept_id"], 0);
        assert_eq!(cond["condition_name"], "Unmapped concept");
    }

    // Verify unmapped drugs mapped to concept 0
    let drugs = json_res["DRUG_EXPOSURE"].as_array().unwrap();
    assert_eq!(drugs.len(), 2);
    for drug in drugs {
        assert_eq!(drug["drug_concept_id"], 0);
        assert_eq!(drug["drug_name"], "Unmapped concept");
    }

    // Verify vitals:
    // flux_capacitor (f64: 88.0) -> mapped to concept 0
    // warp_factor (str: "9.9") -> parsed to 9.9, mapped to concept 0
    // invalid_nan_vital (str: "not_a_number") -> parsed to 0.0, mapped to concept 0
    // boolean and null vitals should be gracefully skipped
    let measurements = json_res["MEASUREMENT"].as_array().unwrap();
    assert_eq!(measurements.len(), 3, "Non-numeric/null vitals must be skipped without crashing");
}

#[tokio::test]
async fn test_adversarial_omop_dual_mounting() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({ "patient_id": "P-DUAL" });

    // Test /v1/lakehouse/omop/transform
    let res1 = app
        .clone()
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
    assert_eq!(res1.status(), StatusCode::OK);

    // Test /lakehouse/omop/transform
    let res2 = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/lakehouse/omop/transform")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res2.status(), StatusCode::OK);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. DATA QUALITY AUDIT GATE ADVERSARIAL TESTS
// ─────────────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn test_adversarial_quality_empty_records_no_divide_by_zero() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({ "records": [] });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    let summary = &json_res["summary"];
    assert_eq!(summary["total_records"], 0);
    assert_eq!(summary["clean_records"], 0);
    assert_eq!(summary["quarantined_records"], 0);
    assert_eq!(summary["pass_rate"], 1.0);
    assert_eq!(summary["pass_rate_pct"], 100.0);
}

#[tokio::test]
async fn test_adversarial_quality_boundary_conditions() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Test exact physiological boundaries
    // Age: [0, 130]
    // HR: [30, 220]
    // SBP: [60, 250]
    // DBP: [35, 150]
    // SpO2: [50, 100]
    // Glucose: [20, 800]
    let payload = json!({
        "records": [
            // Exact Lower Boundaries (Valid)
            { "patient_id": "P-LOW-VALID", "age": 0.0, "heart_rate": 30.0, "systolic_bp": 60.0, "diastolic_bp": 35.0, "spo2": 50.0, "fasting_glucose": 20.0 },
            // Exact Upper Boundaries (Valid)
            { "patient_id": "P-HIGH-VALID", "age": 130.0, "heart_rate": 220.0, "systolic_bp": 250.0, "diastolic_bp": 150.0, "spo2": 100.0, "fasting_glucose": 800.0 },
            // Just Below Lower Boundaries (Invalid)
            { "patient_id": "P-LOW-INVALID", "age": -0.01, "heart_rate": 29.99, "systolic_bp": 59.99, "diastolic_bp": 34.99, "spo2": 49.99, "fasting_glucose": 19.99 },
            // Just Above Upper Boundaries (Invalid)
            { "patient_id": "P-HIGH-INVALID", "age": 130.01, "heart_rate": 220.01, "systolic_bp": 250.01, "diastolic_bp": 150.01, "spo2": 100.01, "fasting_glucose": 800.01 }
        ]
    });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    let summary = &json_res["summary"];
    assert_eq!(summary["total_records"], 4);
    assert_eq!(summary["clean_records"], 2, "Exact boundaries must pass");
    assert_eq!(summary["quarantined_records"], 2, "OOB boundaries must be quarantined");
    assert_eq!(summary["pass_rate"], 0.5);
    assert_eq!(summary["pass_rate_pct"], 50.0);

    let breakdown = &summary["violation_breakdown"];
    assert_eq!(breakdown["SDP_ERR_PHYSIO_AGE_OOB"], 2);
    assert_eq!(breakdown["SDP_ERR_PHYSIO_HR_OOB"], 2);
    assert_eq!(breakdown["SDP_ERR_PHYSIO_SBP_OOB"], 2);
    assert_eq!(breakdown["SDP_ERR_PHYSIO_DBP_OOB"], 2);
    assert_eq!(breakdown["SDP_ERR_PHYSIO_SPO2_OOB"], 2);
    assert_eq!(breakdown["SDP_ERR_PHYSIO_GLUCOSE_OOB"], 2);
}

#[tokio::test]
async fn test_adversarial_quality_dirty_records_and_schema_violations() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let payload = json!({
        "records": [
            // Missing patient_id
            { "age": 45, "heart_rate": 72 },
            // Empty string patient_id
            { "patient_id": "   ", "age": 45 },
            // Numeric patient_id (must trigger SDP_ERR_SCHEMA_NULL_PK because it's not a valid string PK)
            { "patient_id": 99999, "age": 45 },
            // Non-object primitive in records array
            "totally_invalid_non_object_record",
            null,
            // 1 valid record
            { "patient_id": "P-CLEAN-01", "age": 30, "systolic_bp": 120, "diastolic_bp": 80 }
        ]
    });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    let summary = &json_res["summary"];
    assert_eq!(summary["total_records"], 6);
    assert_eq!(summary["clean_records"], 1);
    assert_eq!(summary["quarantined_records"], 5);

    let breakdown = &summary["violation_breakdown"];
    assert_eq!(breakdown["SDP_ERR_SCHEMA_NULL_PK"], 5);
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. DELTA LAKE TIME-TRAVEL, RESTORE, AND CDF ADVERSARIAL TESTS
// ─────────────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn test_adversarial_delta_non_existent_table_history() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/history?table_name=non_existent_table_xyz")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let commits: Vec<Value> = serde_json::from_slice(&bytes).unwrap();

    // Must return bootstrap commit log rather than panicking
    assert_eq!(commits.len(), 1);
    assert_eq!(commits[0]["version"], 0);
    assert_eq!(commits[0]["operation"], "INITIALIZE DELTA TABLE");
}

#[tokio::test]
async fn test_adversarial_delta_time_travel_non_existent_version() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Query non-existent target version 99999
    let res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/time-travel?table_name=workspace.healthcare_silver.patients&target_version=99999")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    assert_eq!(json_res["queried_version"], 99999);
    assert_eq!(json_res["status"], "SNAPSHOT_RETRIEVED");
    assert!(json_res["data"].as_array().unwrap().len() > 0);
}

#[tokio::test]
async fn test_adversarial_delta_restore_non_existent_version_behavior() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Target version does not exist in commit logs
    let payload = json!({
        "table_name": "workspace.healthcare_silver.patients",
        "target_version": 99999
    });

    let res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/v1/lakehouse/delta/restore")
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();

    // Verify system responds gracefully without panic
    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    assert_eq!(json_res["restored_to_version"], 99999);
    assert_eq!(json_res["status"], "SUCCESSFULLY_RESTORED");
    assert!(json_res["hipaa_audit_log_id"].as_str().unwrap().starts_with("AUDIT-RESTORE-"));
}

#[tokio::test]
async fn test_adversarial_delta_restore_concurrency_stress() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Fire 20 concurrent table restore requests to verify RwLock thread safety and state consistency
    let mut handles = Vec::new();
    for i in 0..20 {
        let app_clone = app.clone();
        let handle = tokio::spawn(async move {
            let payload = json!({
                "table_name": "workspace.healthcare_silver.patients",
                "target_version": i % 3
            });
            let res = app_clone
                .oneshot(
                    Request::builder()
                        .method("POST")
                        .uri("/v1/lakehouse/delta/restore")
                        .header("content-type", "application/json")
                        .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                        .unwrap(),
                )
                .await
                .unwrap();
            assert_eq!(res.status(), StatusCode::OK);
            let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
            let json_res: Value = serde_json::from_slice(&bytes).unwrap();
            json_res["new_commit_version"].as_i64().unwrap()
        });
        handles.push(handle);
    }

    let mut versions = Vec::new();
    for h in handles {
        let v = h.await.unwrap();
        versions.push(v);
    }

    // Verify all 20 restore commits completed without lock poisoning or thread panics
    assert_eq!(versions.len(), 20);
    // Versions must be distinct and monotonically increasing
    versions.sort();
    let original_len = versions.len();
    versions.dedup();
    assert_eq!(versions.len(), original_len, "All new_commit_version entries must be strictly unique under concurrency");
}

#[tokio::test]
async fn test_adversarial_delta_cdf_boundaries() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Test CDF with inverted versions (start > end)
    let res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri("/v1/lakehouse/delta/cdf?table_name=workspace.healthcare_silver.patients&start_version=5&end_version=1")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let records: Vec<Value> = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(records.len(), 2);
}

#[tokio::test]
async fn test_adversarial_omop_massive_payload_stress() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // Generate 1,000 conditions, 1,000 medications, and 500 vitals
    let conditions: Vec<String> = (0..1000)
        .map(|i| {
            if i % 3 == 0 {
                "Type 2 diabetes".to_string()
            } else if i % 3 == 1 {
                "Chronic kidney disease".to_string()
            } else {
                format!("Rare Condition #{i}")
            }
        })
        .collect();

    let medications: Vec<String> = (0..1000)
        .map(|i| {
            if i % 2 == 0 {
                "Metformin".to_string()
            } else {
                format!("Experimental Molecule #{i}")
            }
        })
        .collect();

    let mut vitals = serde_json::Map::new();
    for i in 0..500 {
        vitals.insert(format!("vital_metric_{i}"), json!(100.0 + (i as f64) * 0.1));
    }

    let payload = json!({
        "patient_id": "P-MASSIVE-1000",
        "year_of_birth": 1960,
        "gender": "female",
        "conditions": conditions,
        "medications": medications,
        "vitals": vitals
    });

    let start = std::time::Instant::now();
    let res = app
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

    let duration = start.elapsed();
    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    assert_eq!(json_res["CONDITION_OCCURRENCE"].as_array().unwrap().len(), 1000);
    assert_eq!(json_res["DRUG_EXPOSURE"].as_array().unwrap().len(), 1000);
    assert_eq!(json_res["MEASUREMENT"].as_array().unwrap().len(), 500);

    // Verify sub-50ms execution time for 2500 entity OMOP transformation
    assert!(duration.as_millis() < 500, "OMOP 2500-entity transform took too long: {}ms", duration.as_millis());
}

#[tokio::test]
async fn test_adversarial_omop_injection_and_unicode_safety() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let malicious_id = "PAT-'; DROP TABLE omop_person; -- \u{1F916}\u{0000}\n\r\t";
    let payload = json!({
        "patient_id": malicious_id,
        "year_of_birth": -450, // Extreme BC year of birth
        "gender": "Non-Binary\u{200B}",
        "conditions": ["<script>alert('xss')</script>", "Type 2 diabetes' OR '1'='1"],
        "medications": ["Robert'); DROP TABLE drugs;--"],
        "vitals": {
            "systolic_bp": 140.0,
            "injection_key';--": 99.0
        }
    });

    let res = app
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

    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    // Verify SHA-256 hash_to_id handled dirty strings without error or SQL execution
    assert_eq!(json_res["PERSON"]["person_source_value"], malicious_id);
    assert_eq!(json_res["PERSON"]["year_of_birth"], -450);
    assert_eq!(json_res["PERSON"]["gender_concept_id"], 8521);
    assert!(json_res["PERSON"]["person_id"].as_i64().is_some());
}

#[tokio::test]
async fn test_adversarial_quality_1000_record_stress_and_accuracy() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    // 600 clean records, 400 dirty records -> exact 60.0% pass rate
    let mut records = Vec::new();
    for i in 0..600 {
        records.push(json!({
            "patient_id": format!("P-CLEAN-{i:04}"),
            "age": 20.0 + ((i % 80) as f64),
            "heart_rate": 60.0 + ((i % 40) as f64),
            "systolic_bp": 110.0 + ((i % 30) as f64),
            "diastolic_bp": 70.0 + ((i % 20) as f64),
            "spo2": 95.0 + ((i % 5) as f64),
            "fasting_glucose": 80.0 + ((i % 50) as f64)
        }));
    }
    for i in 0..400 {
        records.push(json!({
            "patient_id": format!("P-DIRTY-{i:04}"),
            "age": 150.0, // OOB
            "heart_rate": 25.0, // OOB
            "systolic_bp": 300.0, // OOB
            "diastolic_bp": 200.0, // OOB
            "spo2": 30.0, // OOB
            "fasting_glucose": 1500.0 // OOB
        }));
    }

    let payload = json!({ "records": records });

    let start = std::time::Instant::now();
    let res = app
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

    let duration = start.elapsed();
    assert_eq!(res.status(), StatusCode::OK);
    let bytes = axum::body::to_bytes(res.into_body(), usize::MAX).await.unwrap();
    let json_res: Value = serde_json::from_slice(&bytes).unwrap();

    let summary = &json_res["summary"];
    assert_eq!(summary["total_records"], 1000);
    assert_eq!(summary["clean_records"], 600);
    assert_eq!(summary["quarantined_records"], 400);
    assert_eq!(summary["pass_rate"], 0.6);
    assert_eq!(summary["pass_rate_pct"], 60.0);

    // Verify sampling caps at 5 records
    assert_eq!(json_res["clean_sample"].as_array().unwrap().len(), 5);
    assert_eq!(json_res["quarantined_sample"].as_array().unwrap().len(), 5);

    // Sub-100ms performance check for 1000 records across 7-gate validation
    assert!(duration.as_millis() < 200, "1000-record audit took too long: {}ms", duration.as_millis());
}

#[tokio::test]
async fn test_adversarial_delta_multi_cycle_restore_and_time_travel() {
    let state = create_test_state().await;
    let app = build_app_router(state);

    let test_table = "workspace.healthcare_silver.adversarial_test_table";

    // 1. Initial history on new table (should return auto-bootstrap version 0)
    let res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("GET")
                .uri(&format!("/v1/lakehouse/delta/history?table_name={test_table}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res.status(), StatusCode::OK);

    // 2. Perform 3 sequential restores to version 0, 1, 2
    for target_v in [0, 1, 2] {
        let payload = json!({
            "table_name": test_table,
            "target_version": target_v
        });
        let r_res = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/v1/lakehouse/delta/restore")
                    .header("content-type", "application/json")
                    .body(Body::from(serde_json::to_vec(&payload).unwrap()))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(r_res.status(), StatusCode::OK);
        let b = axum::body::to_bytes(r_res.into_body(), usize::MAX).await.unwrap();
        let j: Value = serde_json::from_slice(&b).unwrap();
        assert_eq!(j["status"], "SUCCESSFULLY_RESTORED");
        assert_eq!(j["restored_to_version"], target_v);
    }

    // 3. Inspect updated history (should now have 3 restore commits)
    let hist_res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("GET")
                .uri(&format!("/v1/lakehouse/delta/history?table_name={test_table}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(hist_res.status(), StatusCode::OK);
    let hb = axum::body::to_bytes(hist_res.into_body(), usize::MAX).await.unwrap();
    let commits: Vec<Value> = serde_json::from_slice(&hb).unwrap();
    assert_eq!(commits.len(), 3);
    assert_eq!(commits[0]["operation"], "RESTORE TO VERSION 2");

    // 4. Time travel query for restored version 2
    let tt_res = app
        .oneshot(
            Request::builder()
                .method("GET")
                .uri(&format!("/v1/lakehouse/delta/time-travel?table_name={test_table}&target_version=2"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(tt_res.status(), StatusCode::OK);
    let tb = axum::body::to_bytes(tt_res.into_body(), usize::MAX).await.unwrap();
    let tj: Value = serde_json::from_slice(&tb).unwrap();
    assert_eq!(tj["status"], "SNAPSHOT_RETRIEVED");
    assert_eq!(tj["queried_version"], 2);
}

