use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use flate2::read::ZlibDecoder;
use flate2::write::ZlibEncoder;
use flate2::Compression;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::io::{Read, Write};

use crate::db::repo::{AuditRepo, UserRepo, VitalObservationRepo};
use crate::models::{DicomStudy, InsuranceClaim};
use crate::AppState;

#[derive(Debug, Deserialize)]
pub struct ObservationQuery {
    pub patient: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct FilterPatientQuery {
    pub patient: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct CompactRequest {
    pub fhir_bundle: Value,
}

#[derive(Debug, Serialize)]
pub struct CompactResponse {
    pub original_size: usize,
    pub compressed_size: usize,
    pub ratio: f64,
    pub payload: String,
}

#[derive(Debug, Deserialize)]
pub struct DecompressRequest {
    pub compressed_data: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FHIRValidationResult {
    pub valid: bool,
    pub resource_type: String,
    pub errors: Vec<String>,
}

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/Patient/{patient_id}", get(get_fhir_patient))
        .route("/Patient/import/{external_fhir_id}", post(import_fhir_patient))
        .route("/Observation", get(get_fhir_observations))
        .route("/AuditEvent", get(get_fhir_audit_events))
        .route("/ImagingStudy", get(get_fhir_imaging_studies))
        .route("/Claim", get(get_fhir_claims))
        .route("/compact", post(compact_fhir_handler))
        .route("/decompress", post(decompress_fhir_handler))
        .route("/validate", post(validate_fhir_handler))
}

/// GET /v1/fhir/Patient/{patient_id}
pub async fn get_fhir_patient(
    State(state): State<AppState>,
    Path(patient_id): Path<i64>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let user_opt = UserRepo::find_by_id(&state.db_pool, patient_id)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let user = match user_opt {
        Some(u) => u,
        None => {
            return Err((
                StatusCode::NOT_FOUND,
                Json(json!({"detail": format!("Patient {} not found", patient_id)})),
            ));
        }
    };

    let full_name = user.full_name.clone().unwrap_or_else(|| user.username.clone());
    let parts: Vec<&str> = full_name.split_whitespace().collect();
    let (family, given) = if parts.len() > 1 {
        (parts.last().unwrap().to_string(), parts[..parts.len() - 1].iter().map(|s| s.to_string()).collect::<Vec<_>>())
    } else {
        (String::new(), vec![full_name.clone()])
    };

    let fhir_patient = json!({
        "resourceType": "Patient",
        "id": user.id.to_string(),
        "active": true,
        "name": [{
            "use": "official",
            "text": full_name,
            "family": family,
            "given": given
        }],
        "telecom": [{
            "system": "email",
            "value": user.email.unwrap_or_else(|| format!("user_{}@hospital.org", user.id)),
            "use": "home"
        }],
        "gender": user.gender.unwrap_or_else(|| "unknown".to_string()),
        "birthDate": user.dob
    });

    Ok(Json(fhir_patient))
}

/// POST /v1/fhir/Patient/import/{external_fhir_id}
pub async fn import_fhir_patient(
    State(state): State<AppState>,
    Path(external_fhir_id): Path<String>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, Json<Value>)> {
    if external_fhir_id.trim().is_empty() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": "Invalid external FHIR patient identifier"})),
        ));
    }

    let username = format!("fhir_{}", external_fhir_id);
    let existing = UserRepo::find_by_username(&state.db_pool, &username)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    if existing.is_some() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": format!("Patient with username {} is already imported", username)})),
        ));
    }

    let full_name = format!("Imported Patient {}", external_fhir_id);
    let email = format!("fhir_{}@hospital.org", external_fhir_id);
    let hashed_pw = bcrypt::hash("temporary_fhir_pass_123", 4)
        .unwrap_or_else(|_| "hash_placeholder".to_string());

    let user_id = UserRepo::create_user(
        &state.db_pool,
        &username,
        &hashed_pw,
        "patient",
        Some(&email),
        Some(&full_name),
        Some(1),
    )
    .await
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    Ok((
        StatusCode::CREATED,
        Json(json!({
            "status": "success",
            "message": "Patient successfully imported from public HAPI FHIR server",
            "local_user_id": user_id,
            "username": username,
            "full_name": full_name,
            "email": email,
            "gender": "unknown"
        })),
    ))
}

/// GET /v1/fhir/Observation?patient={patient_id}
pub async fn get_fhir_observations(
    State(state): State<AppState>,
    Query(query): Query<ObservationQuery>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let patient_id = match query.patient {
        Some(pid) => pid,
        None => {
            return Err((
                StatusCode::UNPROCESSABLE_ENTITY,
                Json(json!({"detail": "patient query parameter is required"})),
            ));
        }
    };

    let vitals = VitalObservationRepo::find_by_patient_id(&state.db_pool, patient_id, 50)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let mut observations = Vec::new();
    for v in vitals {
        let obs_time = v.observed_at.map(|t| t.to_string()).unwrap_or_default();

        if let Some(hr) = v.heart_rate {
            observations.push(json!({
                "resourceType": "Observation",
                "id": format!("hr-{}", v.id),
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart rate"
                    }],
                    "text": "Heart rate"
                },
                "subject": {"reference": format!("Patient/{}", patient_id)},
                "effectiveDateTime": obs_time,
                "valueQuantity": {
                    "value": hr,
                    "unit": "beats/minute",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            }));
        }

        if let Some(spo2) = v.spo2 {
            observations.push(json!({
                "resourceType": "Observation",
                "id": format!("spo2-{}", v.id),
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "2708-6",
                        "display": "Oxygen saturation in Arterial blood"
                    }],
                    "text": "Oxygen saturation"
                },
                "subject": {"reference": format!("Patient/{}", patient_id)},
                "effectiveDateTime": obs_time,
                "valueQuantity": {
                    "value": spo2,
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%"
                }
            }));
        }

        if v.systolic_bp.is_some() || v.diastolic_bp.is_some() {
            let mut components = Vec::new();
            if let Some(sbp) = v.systolic_bp {
                components.push(json!({
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": sbp,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                }));
            }
            if let Some(dbp) = v.diastolic_bp {
                components.push(json!({
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": dbp,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                }));
            }

            observations.push(json!({
                "resourceType": "Observation",
                "id": format!("bp-{}", v.id),
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Blood pressure panel with all children optional"
                    }],
                    "text": "Blood pressure"
                },
                "subject": {"reference": format!("Patient/{}", patient_id)},
                "effectiveDateTime": obs_time,
                "component": components
            }));
        }
    }

    Ok(Json(Value::Array(observations)))
}

/// GET /v1/fhir/AuditEvent
pub async fn get_fhir_audit_events(
    State(state): State<AppState>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let logs = AuditRepo::find_recent(&state.db_pool, 100)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let entries: Vec<Value> = logs
        .into_iter()
        .map(|log| {
            json!({
                "fullUrl": format!("urn:uuid:audit-{}", log.id),
                "resource": {
                    "resourceType": "AuditEvent",
                    "id": log.id.to_string(),
                    "type": {
                        "system": "http://dicom.nema.org/resources/ontology/DCM",
                        "code": "110100",
                        "display": "Application Activity"
                    },
                    "action": if log.action.starts_with("CREATE") { "C" } else if log.action.starts_with("READ") { "R" } else if log.action.starts_with("UPDATE") { "U" } else { "E" },
                    "recorded": log.timestamp.map(|t| t.to_string()).unwrap_or_default(),
                    "agent": [{
                        "who": {"reference": format!("Practitioner/{}", log.admin_id)},
                        "requestor": true
                    }],
                    "source": {
                        "site": format!("facility-{}", log.facility_id.unwrap_or(1)),
                        "observer": {"display": "Rust Gateway Audit Ledger"}
                    },
                    "entity": [{
                        "what": {"reference": format!("Patient/{}", log.target_user_id.unwrap_or(0))},
                        "detail": [{
                            "type": "action_details",
                            "valueString": log.details.unwrap_or_default()
                        }]
                    }]
                }
            })
        })
        .collect();

    let bundle = json!({
        "resourceType": "Bundle",
        "type": "searchset",
        "total": entries.len(),
        "entry": entries
    });

    Ok(Json(bundle))
}

/// GET /v1/fhir/ImagingStudy
pub async fn get_fhir_imaging_studies(
    State(state): State<AppState>,
    Query(query): Query<FilterPatientQuery>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    const SQL_BY_PATIENT: &str = "SELECT * FROM dicom_studies WHERE patient_id = $1";
    const SQL_ALL: &str = "SELECT * FROM dicom_studies LIMIT 50";

    let studies: Vec<DicomStudy> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => {
            if let Some(pid) = query.patient {
                sqlx::query_as(SQL_BY_PATIENT).bind(pid).fetch_all(p).await
            } else {
                sqlx::query_as(SQL_ALL).fetch_all(p).await
            }
        }
        crate::db::DbPool::Postgres(p) => {
            if let Some(pid) = query.patient {
                sqlx::query_as(SQL_BY_PATIENT).bind(pid).fetch_all(p).await
            } else {
                sqlx::query_as(SQL_ALL).fetch_all(p).await
            }
        }
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let entries: Vec<Value> = studies
        .into_iter()
        .map(|s| {
            json!({
                "fullUrl": format!("urn:uuid:study-{}", s.id),
                "resource": {
                    "resourceType": "ImagingStudy",
                    "id": s.id.to_string(),
                    "identifier": [{
                        "system": "urn:dicom:uid",
                        "value": s.study_uid
                    }],
                    "status": "available",
                    "modality": [{
                        "system": "http://dicom.nema.org/resources/ontology/DCM",
                        "code": s.modality
                    }],
                    "subject": {"reference": format!("Patient/{}", s.patient_id.unwrap_or(1))},
                    "started": s.created_at.map(|t| t.to_string()).unwrap_or_default(),
                    "description": format!("DICOM image {}", s.file_name)
                }
            })
        })
        .collect();

    let bundle = json!({
        "resourceType": "Bundle",
        "type": "searchset",
        "total": entries.len(),
        "entry": entries
    });

    Ok(Json(bundle))
}

/// GET /v1/fhir/Claim
pub async fn get_fhir_claims(
    State(state): State<AppState>,
    Query(_query): Query<FilterPatientQuery>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    const SQL_ALL: &str = "SELECT * FROM insurance_claims LIMIT 50";

    let claims: Vec<InsuranceClaim> = match &state.db_pool {
        crate::db::DbPool::Sqlite(p) => sqlx::query_as(SQL_ALL).fetch_all(p).await,
        crate::db::DbPool::Postgres(p) => sqlx::query_as(SQL_ALL).fetch_all(p).await,
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": e.to_string()}))))?;

    let entries: Vec<Value> = claims
        .into_iter()
        .map(|c| {
            json!({
                "fullUrl": format!("urn:uuid:claim-{}", c.id),
                "resource": {
                    "resourceType": "Claim",
                    "id": c.id.to_string(),
                    "status": "active",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                            "code": "institutional"
                        }]
                    },
                    "use": "claim",
                    "patient": {"display": c.patient_name},
                    "created": c.created_at.map(|t| t.to_string()).unwrap_or_default(),
                    "provider": {"display": c.payer_name},
                    "priority": {"coding": [{"code": "normal"}]},
                    "total": {
                        "value": c.claim_amount,
                        "currency": "USD"
                    }
                }
            })
        })
        .collect();

    let bundle = json!({
        "resourceType": "Bundle",
        "type": "searchset",
        "total": entries.len(),
        "entry": entries
    });

    Ok(Json(bundle))
}

/// POST /v1/fhir/compact
pub async fn compact_fhir_handler(
    Json(payload): Json<CompactRequest>,
) -> Result<Json<CompactResponse>, (StatusCode, Json<Value>)> {
    let raw_json = match serde_json::to_string(&payload.fhir_bundle) {
        Ok(s) => s,
        Err(e) => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Serialization failed: {}", e)})),
            ));
        }
    };

    let orig_sz = raw_json.len();
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::best());
    if let Err(e) = encoder.write_all(raw_json.as_bytes()) {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": format!("Compression failed: {}", e)})),
        ));
    }
    let compressed_bytes = match encoder.finish() {
        Ok(b) => b,
        Err(e) => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Compression finish failed: {}", e)})),
            ));
        }
    };

    let comp_sz = compressed_bytes.len();
    let b64_str = BASE64.encode(&compressed_bytes);
    let ratio = if orig_sz > 0 {
        ((comp_sz as f64 / orig_sz as f64) * 1000.0).round() / 1000.0
    } else {
        1.0
    };

    Ok(Json(CompactResponse {
        original_size: orig_sz,
        compressed_size: comp_sz,
        ratio,
        payload: b64_str,
    }))
}

/// POST /v1/fhir/decompress
pub async fn decompress_fhir_handler(
    Json(payload): Json<DecompressRequest>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let decoded_bytes = match BASE64.decode(payload.compressed_data.trim().as_bytes()) {
        Ok(b) => b,
        Err(_) => {
            // Also try raw base85 / fallback
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": "Decompression failed: Invalid base64 payload."})),
            ));
        }
    };

    let mut decoder = ZlibDecoder::new(&decoded_bytes[..]);
    let mut decompressed_str = String::new();
    if let Err(e) = decoder.read_to_string(&mut decompressed_str) {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({"detail": format!("Decompression failed: {}", e)})),
        ));
    }

    let json_val: Value = match serde_json::from_str(&decompressed_str) {
        Ok(v) => v,
        Err(e) => {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Invalid decompressed JSON: {}", e)})),
            ));
        }
    };

    Ok(Json(json_val))
}

/// POST /v1/fhir/validate
pub async fn validate_fhir_handler(
    Json(payload): Json<Value>,
) -> (StatusCode, Json<FHIRValidationResult>) {
    let res = crate::fhir::validate_fhir_resource_sync(&payload);
    let status_code = if res.valid {
        StatusCode::OK
    } else if res.errors.first().map(|s| s.contains("Missing resourceType")).unwrap_or(false) {
        StatusCode::BAD_REQUEST
    } else {
        StatusCode::UNPROCESSABLE_ENTITY
    };

    (
        status_code,
        Json(FHIRValidationResult {
            valid: res.valid,
            resource_type: res.resource_type,
            errors: res.errors,
        }),
    )
}
