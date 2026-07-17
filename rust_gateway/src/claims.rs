use axum::{
    http::StatusCode,
    response::IntoResponse,
    Json, Router,
    routing::post,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ProcedureLine {
    pub cpt: String,
    pub charge: f64,
    pub date: String,
    pub units: Option<u32>,
    pub diagnosis_pointer: Option<Vec<u32>>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CMS1500Claim {
    pub claim_id: String,
    pub patient_name: String,
    pub insurance_id: String,
    pub provider_name: String,
    pub provider_npi: String,
    pub provider_tax_id: String,
    pub diagnoses: Vec<String>,
    pub procedures: Vec<ProcedureLine>,
    pub place_of_service: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct DenialAnalysis {
    pub claim_id: String,
    pub denial_risk: String,
    pub warnings: Vec<String>,
    pub passed_preflight: bool,
}

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/preflight", post(analyse_claim))
}

async fn analyse_claim(
    Json(claim): Json<CMS1500Claim>,
) -> impl IntoResponse {
    let mut warnings = Vec::new();
    let mut denial_risk = "LOW".to_string();

    // 1. Structural Checks
    let npi = claim.provider_npi.trim();
    if npi.is_empty() || npi.len() != 10 || !npi.chars().all(|c| c.is_ascii_digit()) {
        warnings.push("Provider NPI must be exactly a 10-digit numeric value.".to_string());
        denial_risk = "HIGH".to_string();
    }

    let tax_id = claim.provider_tax_id.trim();
    if tax_id.is_empty() {
        warnings.push("Provider Tax ID / EIN is missing.".to_string());
        denial_risk = "HIGH".to_string();
    }

    if claim.insurance_id.trim().is_empty() {
        warnings.push("Patient Insurance Policy ID is missing.".to_string());
        denial_risk = "HIGH".to_string();
    }

    if claim.diagnoses.is_empty() {
        warnings.push("At least one ICD-10 diagnosis code must be present on the claim.".to_string());
        denial_risk = "HIGH".to_string();
    }

    // CPT Rules mapping
    let rules = {
        let mut r = HashMap::new();
        r.insert("90837", ("F", "Psychotherapy requires a behavioral health diagnosis (e.g., F32.x, F41.x)"));
        r.insert("90791", ("F", "Psychiatric diagnostic evaluation requires a behavioral health diagnosis"));
        r.insert("50200", ("N", "Renal biopsy requires a genitourinary / renal diagnosis (e.g., N18.x)"));
        r.insert("90935", ("N", "Hemodialysis requires a genitourinary / renal diagnosis (e.g., N18.x)"));
        r.insert("93000", ("I", "Electrocardiogram requires a circulatory / cardiac diagnosis (e.g., I25.x)"));
        r.insert("93015", ("I", "Cardiovascular stress test requires a circulatory / cardiac diagnosis"));
        r.insert("94010", ("J", "Spirometry / lung function test requires a respiratory diagnosis (e.g., J44.x)"));
        r
    };

    // 2. Procedure and Diagnosis Code Match Validation
    for proc in &claim.procedures {
        let cpt = proc.cpt.trim();
        if cpt.is_empty() {
            warnings.push("Procedure service line is missing CPT/HCPCS code.".to_string());
            denial_risk = "HIGH".to_string();
            continue;
        }

        if let Some(&(prefix, message)) = rules.get(cpt) {
            let mut matching_dx = false;
            for dx in &claim.diagnoses {
                if dx.trim().to_uppercase().starts_with(prefix) {
                    matching_dx = true;
                    break;
                }
            }

            if !matching_dx {
                warnings.push(format!(
                    "CPT {} Mismatch: {}. Claimed diagnoses: {:?}",
                    cpt, message, claim.diagnoses
                ));
                if denial_risk != "HIGH" {
                    denial_risk = "MEDIUM".to_string();
                }
            }
        }
    }

    let passed_preflight = warnings.is_empty();
    let analysis = DenialAnalysis {
        claim_id: claim.claim_id,
        denial_risk,
        warnings,
        passed_preflight,
    };

    (StatusCode::OK, Json(analysis))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_analyse_claim_passed() {
        let claim = CMS1500Claim {
            claim_id: "claim-001".to_string(),
            patient_name: "John Doe".to_string(),
            insurance_id: "INS-7788".to_string(),
            provider_name: "Dr. Alice Smith".to_string(),
            provider_npi: "1234567890".to_string(),
            provider_tax_id: "TX-556677".to_string(),
            diagnoses: vec!["I25.10".to_string(), "E11.9".to_string()],
            procedures: vec![ProcedureLine {
                cpt: "93000".to_string(),
                charge: 150.0,
                date: "2026-07-16".to_string(),
                units: Some(1),
                diagnosis_pointer: Some(vec![1]),
            }],
            place_of_service: Some("11".to_string()),
        };

        let response = analyse_claim(Json(claim)).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);
    }
}
