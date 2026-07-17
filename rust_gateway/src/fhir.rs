use axum::{routing::post, Json, Router};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Serialize, Deserialize, Debug)]
pub struct FHIRValidationResponse {
    pub valid: bool,
    pub resource_type: String,
    pub errors: Vec<String>,
}

pub fn router() -> Router<crate::AppState> {
    Router::new().route("/validate", post(validate_handler))
}

async fn validate_handler(
    Json(payload): Json<Value>,
) -> (axum::http::StatusCode, Json<FHIRValidationResponse>) {
    let res = validate_fhir_resource_sync(&payload);
    let status_code = if res.valid {
        axum::http::StatusCode::OK
    } else if res.errors.first().map(|s| s.contains("Missing resourceType")).unwrap_or(false) {
        axum::http::StatusCode::BAD_REQUEST
    } else {
        axum::http::StatusCode::UNPROCESSABLE_ENTITY
    };
    (status_code, Json(res))
}

pub fn validate_fhir_resource_sync(payload: &Value) -> FHIRValidationResponse {
    let mut errors = Vec::new();

    let resource_type = match payload.get("resourceType").and_then(|v| v.as_str()) {
        Some(t) => t.to_string(),
        None => {
            return FHIRValidationResponse {
                valid: false,
                resource_type: "Unknown".to_string(),
                errors: vec!["Missing resourceType".to_string()],
            };
        }
    };

    let id = payload.get("id").and_then(|v| v.as_str()).unwrap_or("");
    if id.trim().is_empty() {
        errors.push("Invalid FHIR resource: id is missing or empty".to_string());
    }

    match resource_type.as_str() {
        "Patient" => {
            // Patient needs a name list
            match payload.get("name") {
                Some(name_val) => {
                    if let Some(arr) = name_val.as_array() {
                        if arr.is_empty() {
                            errors.push("Patient resource must contain a non-empty name list".to_string());
                        }
                    } else {
                        errors.push("Patient resource name must be an array".to_string());
                    }
                }
                None => {
                    // Check if it's a placeholder (only has resourceType and id)
                    let is_placeholder = payload.as_object()
                        .map(|obj| obj.len() <= 2)
                        .unwrap_or(false);
                    if !is_placeholder {
                        errors.push("Patient resource must contain a non-empty name list".to_string());
                    }
                }
            }
            if let Some(gender) = payload.get("gender") {
                if let Some(g_str) = gender.as_str() {
                    if !matches!(g_str, "male" | "female" | "other" | "unknown") {
                        errors.push("Patient resource must contain a valid gender code".to_string());
                    }
                } else {
                    errors.push("Patient gender must be a string".to_string());
                }
            }
        }
        "Observation" => {
            if let Some(status) = payload.get("status").and_then(|v| v.as_str()) {
                if !matches!(status, "registered" | "preliminary" | "final" | "amended" | "corrected") {
                    errors.push("Observation must contain a valid status".to_string());
                }
            }
            if let Some(code) = payload.get("code") {
                if code.is_object() {
                    let has_coding = code.get("coding").is_some();
                    let has_text = code.get("text").is_some();
                    if !has_coding && !has_text {
                        errors.push("Observation must contain a valid coding or text block".to_string());
                    }
                } else {
                    errors.push("Observation code must be a JSON object".to_string());
                }
            }
            if payload.get("subject").and_then(|v| v.get("reference")).is_none() {
                errors.push("Observation must contain a valid subject reference".to_string());
            }
            if payload.get("valueQuantity").is_none() && payload.get("component").is_none() {
                errors.push("Observation must include a value or component".to_string());
            }
        }
        "Encounter" => {
            if let Some(status) = payload.get("status").and_then(|v| v.as_str()) {
                if !matches!(status, "planned" | "arrived" | "triaged" | "in-progress" | "onleave" | "finished" | "cancelled" | "open" | "closed" | "unknown") {
                    errors.push("Encounter must contain a valid status".to_string());
                }
            }
            if payload.get("class").and_then(|v| v.get("code")).is_none() {
                errors.push("Encounter must contain a valid class code".to_string());
            }
            if payload.get("subject").and_then(|v| v.get("reference")).is_none() {
                errors.push("Encounter must contain a valid subject reference".to_string());
            }
        }
        "MedicationRequest" => {
            if let Some(status) = payload.get("status").and_then(|v| v.as_str()) {
                if !matches!(status, "active" | "on-hold" | "cancelled" | "completed" | "entered-in-error" | "stopped" | "draft" | "unknown") {
                    errors.push("MedicationRequest must contain a valid status".to_string());
                }
            }
            if let Some(intent) = payload.get("intent").and_then(|v| v.as_str()) {
                if !matches!(intent, "proposal" | "plan" | "order" | "original-order" | "reflex-order" | "filler-order" | "instance-order" | "option") {
                    errors.push("MedicationRequest must contain a valid intent".to_string());
                }
            }
            if payload.get("subject").and_then(|v| v.get("reference")).is_none() {
                errors.push("MedicationRequest must contain a valid subject reference".to_string());
            }
        }
        "DiagnosticReport" => {
            if let Some(status) = payload.get("status").and_then(|v| v.as_str()) {
                if !matches!(status, "registered" | "partial" | "preliminary" | "final" | "amended" | "corrected" | "cancelled") {
                    errors.push("DiagnosticReport must contain a valid status".to_string());
                }
            }
            if let Some(code) = payload.get("code") {
                if code.is_object() {
                    let has_coding = code.get("coding").is_some();
                    let has_text = code.get("text").is_some();
                    if !has_coding && !has_text {
                        errors.push("DiagnosticReport must contain a valid coding or text block".to_string());
                    }
                } else {
                    errors.push("DiagnosticReport code must be a JSON object".to_string());
                }
            }
            if payload.get("subject").and_then(|v| v.get("reference")).is_none() {
                errors.push("DiagnosticReport must contain a valid subject reference".to_string());
            }
        }
        _ => {
            errors.push(format!("Unsupported resource type: {}", resource_type));
        }
    }

    let valid = errors.is_empty();
    FHIRValidationResponse {
        valid,
        resource_type,
        errors,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[tokio::test]
    async fn test_validate_valid_patient() {
        let payload = json!({
            "resourceType": "Patient",
            "id": "pat1",
            "name": [{"text": "John Doe"}],
            "gender": "male"
        });
        let (status, Json(res)) = validate_handler(Json(payload)).await;
        assert_eq!(status, axum::http::StatusCode::OK);
        assert!(res.valid);
        assert_eq!(res.errors.len(), 0);
    }

    #[tokio::test]
    async fn test_validate_invalid_patient_gender() {
        let payload = json!({
            "resourceType": "Patient",
            "id": "pat1",
            "name": [{"text": "John Doe"}],
            "gender": "alien"
        });
        let (status, Json(res)) = validate_handler(Json(payload)).await;
        assert_eq!(status, axum::http::StatusCode::UNPROCESSABLE_ENTITY);
        assert!(!res.valid);
        assert_eq!(res.errors[0], "Patient resource must contain a valid gender code");
    }
}
