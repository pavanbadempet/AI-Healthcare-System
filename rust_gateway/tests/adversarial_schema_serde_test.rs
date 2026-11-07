//! Adversarial Schema Serde Cross-Validation Test
//! Verifies JSON deserialization parity and tolerance of extra fields produced by Python DTOs.

use serde_json::json;

use rust_gateway_ffi::ml::predictors::{
    DiabetesInput, HeartInput, KidneyInput,
};
use rust_gateway_ffi::models::governance::{DataCatalogDataset, SchemaContract};
use rust_gateway_ffi::models::records::AuditLog;
use rust_gateway_ffi::routes::intelligence::ExplainabilityResponse;
use rust_gateway_ffi::routes::prediction::PredictionReviewCreate;

#[test]
fn test_rust_heart_input_deserializes_exact_13_features() {
    let payload = json!({
        "age": 63.0,
        "sex": 1.0,
        "cp": 3.0,
        "trestbps": 145.0,
        "chol": 233.0,
        "fbs": 1.0,
        "restecg": 0.0,
        "thalach": 150.0,
        "exang": 0.0,
        "oldpeak": 2.3,
        "slope": 0.0,
        "ca": 0.0,
        "thal": 1.0
    });

    let heart: HeartInput = serde_json::from_value(payload).expect("Deserialization of exact 13 features must succeed");
    assert_eq!(heart.age, 63.0);
    assert_eq!(heart.sex, 1.0);
    assert_eq!(heart.chol, 233.0);
}

#[test]
fn test_rust_heart_input_ignores_python_extra_fields() {
    let payload = json!({
        "age": 63.0,
        "sex": 1.0,
        "cp": 3.0,
        "trestbps": 145.0,
        "chol": 233.0,
        "fbs": 1.0,
        "restecg": 0.0,
        "thalach": 150.0,
        "exang": 0.0,
        "oldpeak": 2.3,
        "slope": 0.0,
        "ca": 0.0,
        "thal": 1.0,
        "hdl": 50.0,
        "smoker": 0,
        "hyp_treatment": 0,
        "extra_unknown_field": "test"
    });

    let heart: Result<HeartInput, _> = serde_json::from_value(payload);
    assert!(heart.is_ok(), "HeartInput must ignore extra fields like hdl, smoker, hyp_treatment");
    let heart = heart.unwrap();
    assert_eq!(heart.thalach, 150.0);
}

#[test]
fn test_rust_heart_input_rejects_missing_required_field() {
    let payload = json!({
        "age": 63.0,
        "sex": 1.0,
        // cp is missing!
        "trestbps": 145.0,
        "chol": 233.0,
        "fbs": 1.0,
        "restecg": 0.0,
        "thalach": 150.0,
        "exang": 0.0,
        "oldpeak": 2.3,
        "slope": 0.0,
        "ca": 0.0,
        "thal": 1.0
    });

    let heart: Result<HeartInput, _> = serde_json::from_value(payload);
    assert!(heart.is_err(), "Missing cp must fail deserialization");
}

#[test]
fn test_rust_diabetes_input_deserialization() {
    let payload = json!({
        "hypertension": 1.0,
        "high_chol": 1.0,
        "bmi": 28.5,
        "smoking_history": 0.0,
        "heart_disease": 0.0,
        "physical_activity": 1.0,
        "general_health": 2.0,
        "gender": 1.0,
        "age": 55.0
    });

    let diabetes: DiabetesInput = serde_json::from_value(payload).expect("Valid diabetes payload must succeed");
    assert_eq!(diabetes.bmi, 28.5);
    assert_eq!(diabetes.age, 55.0);
}

#[test]
fn test_rust_diabetes_input_rejects_missing_feature() {
    let payload = json!({
        "hypertension": 1.0,
        "high_chol": 1.0,
        // bmi is missing
        "smoking_history": 0.0,
        "heart_disease": 0.0,
        "physical_activity": 1.0,
        "general_health": 2.0,
        "gender": 1.0,
        "age": 55.0
    });

    let res: Result<DiabetesInput, _> = serde_json::from_value(payload);
    assert!(res.is_err(), "Missing bmi must cause deserialization failure");
}

#[test]
fn test_rust_kidney_input_is_female_and_extra_gender_field() {
    // 24 features + is_female + Python extra gender field
    let payload = json!({
        "age": 48.0, "bp": 80.0, "sg": 1.020, "al": 1.0, "su": 0.0,
        "rbc": 0.0, "pc": 0.0, "pcc": 0.0, "ba": 0.0,
        "bgr": 121.0, "bu": 36.0, "sc": 1.2, "sod": 135.0, "pot": 4.5, "hemo": 15.4,
        "pcv": 44.0, "wc": 7800.0, "rc": 5.2, "htn": 1.0, "dm": 1.0, "cad": 0.0,
        "appet": 0.0, "pe": 0.0, "ane": 0.0,
        "is_female": true,
        "gender": 0 // Python legacy field
    });

    let kidney: KidneyInput = serde_json::from_value(payload).expect("KidneyInput deserialization must succeed");
    assert_eq!(kidney.is_female, Some(true));
    assert_eq!(kidney.sc, 1.2);
}

#[test]
fn test_rust_prediction_review_create_parity_and_extra_fields() {
    let payload = json!({
        "patient_id": 42,
        "prediction_type": "heart",
        "model_prediction": "Positive",
        "clinician_agree": false,
        "notes": "Stress test ordered",
        "revised_diagnosis": "Angina",
        "decision": "overridden", // Python legacy
        "review_note": "Stress test ordered", // Python legacy
        "clinical_use_category": "clinician_review" // Python legacy
    });

    let review: PredictionReviewCreate = serde_json::from_value(payload).expect("Review deserialization must succeed");
    assert_eq!(review.patient_id, 42);
    assert_eq!(review.clinician_agree, false);
    assert_eq!(review.notes.as_deref(), Some("Stress test ordered"));
}

#[test]
fn test_rust_audit_log_deserialization_with_null_details() {
    let payload = json!({
        "id": 1,
        "facility_id": null,
        "admin_id": 99,
        "target_user_id": null,
        "action": "EXPORT_AUDIT",
        "timestamp": null,
        "details": null,
        "is_deleted": 0,
        "deleted_at": null
    });

    let log: AuditLog = serde_json::from_value(payload).expect("AuditLog deserialization must succeed");
    assert_eq!(log.admin_id, 99);
    assert_eq!(log.details, None);
}

#[test]
fn test_rust_explainability_response_deserialization() {
    let payload = json!({
        "prediction_id": 501,
        "model_name": "heart_onnx",
        "base_value": 0.15,
        "predicted_value": 0.85,
        "feature_contributions": [
            {
                "feature_name": "chol",
                "feature_value": 260.0,
                "shap_value": 0.35,
                "impact": "POSITIVE"
            }
        ],
        "conformal_prediction": {
            "alpha": 0.05,
            "lower_bound": 0.78,
            "upper_bound": 0.92,
            "prediction_set": ["High Risk"]
        }
    });

    let resp: ExplainabilityResponse = serde_json::from_value(payload).expect("Explainability deserialization must succeed");
    assert_eq!(resp.prediction_id, 501);
    assert_eq!(resp.base_value, 0.15);
    assert_eq!(resp.feature_contributions.len(), 1);
    assert_eq!(resp.conformal_prediction.alpha, 0.05);
}

#[test]
fn test_rust_data_governance_float_types() {
    let contract_payload = json!({
        "id": 1,
        "contract_id": "cntr_test",
        "name": "Contract A",
        "version": 1,
        "producer": "lab",
        "consumer": "ehr",
        "schema_definition": "{}",
        "required_fields": "[]",
        "compatibility_mode": "BACKWARD",
        "sla_freshness_minutes": 1440,
        "quality_threshold": 0.975,
        "created_at": null,
        "updated_at": null
    });

    let contract: SchemaContract = serde_json::from_value(contract_payload).expect("SchemaContract deserialization must succeed");
    assert_eq!(contract.quality_threshold, 0.975);

    let dataset_payload = json!({
        "id": 1,
        "dataset_id": "ds_test",
        "name": "Dataset A",
        "description": null,
        "owner": "analytics",
        "schema_definition": "{}",
        "tags": "[]",
        "sla_hours": 24,
        "freshness_field": "ts",
        "quality_score": 0.9995,
        "row_count": 10000,
        "size_bytes": 500000,
        "location": null,
        "format": "parquet",
        "created_at": null,
        "updated_at": null
    });

    let dataset: DataCatalogDataset = serde_json::from_value(dataset_payload).expect("DataCatalogDataset deserialization must succeed");
    assert_eq!(dataset.quality_score, 0.9995);
}
