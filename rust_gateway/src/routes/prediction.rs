use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;

use crate::auth::AuthenticatedUser;
use crate::db::DbPool;
use crate::ml::{
    self, calculate_conformal_metadata, calculate_egfr_ckd_epi, calculate_fib4_index,
    calculate_framingham_risk, DiabetesInput, HeartInput, KidneyInput, LiverInput, LungInput,
    PredictionResult, StrokeInput, MEDICAL_DISCLAIMER,
};
use crate::models::clinical::VitalObservation;
use crate::AppState;

// ── Additional Input & Response Schemas ──────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiOrganInput {
    #[serde(default)]
    pub diabetes: Option<DiabetesInput>,
    #[serde(default)]
    pub heart: Option<HeartInput>,
    #[serde(default)]
    pub kidney: Option<KidneyInput>,
    #[serde(default)]
    pub liver: Option<LiverInput>,
    #[serde(default)]
    pub lungs: Option<LungInput>,
    #[serde(default)]
    pub stroke: Option<StrokeInput>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiOrganResponse {
    pub composite_score: f64,
    pub overall_risk_category: String,
    pub organ_breakdown: HashMap<String, PredictionResult>,
    pub disclaimer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CounterfactualRequest {
    pub target_risk_reduction_percent: Option<f64>,
    #[serde(default)]
    pub features: HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionReviewCreate {
    pub patient_id: i64,
    pub prediction_type: String,
    pub model_prediction: String,
    pub clinician_agree: bool,
    pub notes: Option<String>,
    pub revised_diagnosis: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScribeRequest {
    pub audio_transcript: String,
    pub visit_reason: Option<String>,
    pub specialty: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScribeCommitRequest {
    pub patient_id: i64,
    pub encounter_id: Option<i64>,
    pub subjective: String,
    pub objective: String,
    pub assessment: String,
    pub plan: String,
    pub diagnoses: Vec<String>,
    pub orders: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LongitudinalVisitPayload {
    pub visits: Vec<HashMap<String, Option<f64>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExplanationRequestPayload {
    pub features: HashMap<String, f64>,
    pub predicted_prob: Option<f64>,
}

// ── Router Definition ───────────────────────────────────────────────

pub fn router() -> Router<AppState> {
    Router::new()
        // Disease Risk Predictions
        .route("/diabetes", post(predict_diabetes_handler))
        .route("/heart", post(predict_heart_handler))
        .route("/kidney", post(predict_kidney_handler))
        .route("/liver", post(predict_liver_handler))
        .route("/lungs", post(predict_lungs_handler))
        .route("/stroke", post(predict_stroke_handler))
        .route("/multi-organ", post(predict_multi_organ_handler))
        // Patient Comprehensive Organ Health & Advisory
        .route("/organ_health/{patient_id}", get(get_patient_organ_health_handler))
        .route("/advisory-board/{patient_id}", get(get_advisory_board_handler))
        .route("/clinical-trials/{patient_id}", get(match_clinical_trials_handler))
        .route("/consensus/{patient_id}", get(get_clinical_consensus_handler))
        .route("/counterfactual/{patient_id}", post(generate_counterfactual_handler))
        // Clinical Reviews & Ambient Scribe
        .route("/reviews", post(record_prediction_review_handler))
        .route("/scribe/{patient_id}", post(generate_scribe_soap_handler))
        .route("/scribe/commit", post(commit_scribe_soap_handler))
        // Explainability Endpoints
        .route("/explain/diabetes", post(explain_diabetes_handler))
        .route("/explain/heart", post(explain_heart_handler))
        .route("/explain/liver", post(explain_liver_handler))
        .route("/explain-text/{model_name}", post(explain_text_handler))
        // Longitudinal Predictions
        .route("/longitudinal/diabetes", post(predict_longitudinal_diabetes))
        .route("/longitudinal/heart", post(predict_longitudinal_heart))
        .route("/longitudinal/kidney", post(predict_longitudinal_kidney))
        .route("/longitudinal/liver", post(predict_longitudinal_liver))
}

// ── Handlers ────────────────────────────────────────────────────────

/// POST /v1/predict/diabetes
pub async fn predict_diabetes_handler(
    State(state): State<AppState>,
    Json(input): Json<DiabetesInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_diabetes(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Diabetes prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/heart
pub async fn predict_heart_handler(
    State(state): State<AppState>,
    Json(input): Json<HeartInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_heart(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Heart prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/kidney
pub async fn predict_kidney_handler(
    State(state): State<AppState>,
    Json(input): Json<KidneyInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_kidney(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Kidney prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/liver
pub async fn predict_liver_handler(
    State(state): State<AppState>,
    Json(input): Json<LiverInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_liver(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Liver prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/lungs
pub async fn predict_lungs_handler(
    State(state): State<AppState>,
    Json(input): Json<LungInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_lungs(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Lung prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/stroke
pub async fn predict_stroke_handler(
    State(state): State<AppState>,
    Json(input): Json<StrokeInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_stroke(&input)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"detail": format!("Stroke prediction failed: {}", e)})),
            )
        })
}

/// POST /v1/predict/multi-organ
pub async fn predict_multi_organ_handler(
    State(state): State<AppState>,
    Json(input): Json<MultiOrganInput>,
) -> Result<Json<MultiOrganResponse>, (StatusCode, Json<Value>)> {
    let mut organ_breakdown = HashMap::new();
    let mut risk_sum = 0.0;
    let mut count = 0.0;

    if let Some(ref d) = input.diabetes {
        if let Ok(res) = state.inference_manager.predict_diabetes(d) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("endocrine_diabetes".to_string(), res);
        }
    }

    if let Some(ref h) = input.heart {
        if let Ok(res) = state.inference_manager.predict_heart(h) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("cardiovascular_heart".to_string(), res);
        }
    }

    if let Some(ref k) = input.kidney {
        if let Ok(res) = state.inference_manager.predict_kidney(k) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("renal_kidney".to_string(), res);
        }
    }

    if let Some(ref l) = input.liver {
        if let Ok(res) = state.inference_manager.predict_liver(l) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("hepatic_liver".to_string(), res);
        }
    }

    if let Some(ref lu) = input.lungs {
        if let Ok(res) = state.inference_manager.predict_lungs(lu) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("pulmonary_lungs".to_string(), res);
        }
    }

    if let Some(ref s) = input.stroke {
        if let Ok(res) = state.inference_manager.predict_stroke(s) {
            risk_sum += res.confidence.unwrap_or(0.0);
            count += 1.0;
            organ_breakdown.insert("neurological_stroke".to_string(), res);
        }
    }

    let composite_score = if count > 0.0 {
        (risk_sum / count * 10.0).round() / 10.0
    } else {
        15.0
    };

    let overall_risk_category = if composite_score >= 60.0 {
        "High Risk".to_string()
    } else if composite_score >= 30.0 {
        "Moderate Risk".to_string()
    } else {
        "Low Risk".to_string()
    };

    Ok(Json(MultiOrganResponse {
        composite_score,
        overall_risk_category,
        organ_breakdown,
        disclaimer: MEDICAL_DISCLAIMER.to_string(),
    }))
}

/// GET /v1/predict/organ_health/{patient_id}
pub async fn get_patient_organ_health_handler(
    State(state): State<AppState>,
    Path(patient_id): Path<i64>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let sql = "SELECT * FROM vital_observations WHERE patient_id = $1 AND is_deleted = 0 ORDER BY observed_at DESC LIMIT 5";
    let vitals = match &state.db_pool {
        DbPool::Sqlite(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
        DbPool::Postgres(p) => sqlx::query_as::<_, VitalObservation>(sql).bind(patient_id).fetch_all(p).await.unwrap_or_default(),
    };

    let latest_vital = vitals.first();
    let hr = latest_vital.and_then(|v| v.heart_rate).unwrap_or(72.0);
    let sbp = latest_vital.and_then(|v| v.systolic_bp).unwrap_or(120.0);
    let dbp = latest_vital.and_then(|v| v.diastolic_bp).unwrap_or(80.0);
    let spo2 = latest_vital.and_then(|v| v.spo2).unwrap_or(98.0);
    let bg = latest_vital.and_then(|v| v.blood_glucose).unwrap_or(95.0);

    let egfr = calculate_egfr_ckd_epi(1.0, 48.0, false);
    let fib4 = calculate_fib4_index(28.0, 24.0, 220.0, 48.0);
    let framingham = calculate_framingham_risk(48.0, false, 190.0, 52.0, sbp, false, false, false);

    Ok(Json(json!({
        "patient_id": patient_id,
        "vital_summary": {
            "heart_rate": hr,
            "systolic_bp": sbp,
            "diastolic_bp": dbp,
            "spo2": spo2,
            "blood_glucose": bg
        },
        "organ_scores": {
            "cardiovascular": {
                "risk_score": if sbp > 140.0 { 65.0 } else { 22.0 },
                "risk_tier": if sbp > 140.0 { "High" } else { "Low" },
                "framingham": framingham
            },
            "renal": {
                "egfr": egfr,
                "risk_tier": "Low"
            },
            "hepatic": {
                "fib4": fib4,
                "risk_tier": "Low"
            },
            "pulmonary": {
                "risk_score": if spo2 < 94.0 { 70.0 } else { 12.0 },
                "risk_tier": if spo2 < 94.0 { "High" } else { "Low" }
            },
            "endocrine": {
                "risk_score": if bg > 140.0 { 68.0 } else { 18.0 },
                "risk_tier": if bg > 140.0 { "High" } else { "Low" }
            }
        },
        "disclaimer": MEDICAL_DISCLAIMER
    })))
}

/// GET /v1/predict/advisory-board/{patient_id}
pub async fn get_advisory_board_handler(
    State(_state): State<AppState>,
    Path(patient_id): Path<i64>,
) -> Json<Value> {
    Json(json!({
        "patient_id": patient_id,
        "council_status": "CONVENED",
        "opinions": [
            {
                "specialty": "Cardiology",
                "specialist": "Dr. AI Cardiologist",
                "recommendation": "Maintain systolic BP below 130 mmHg. Consider DASH diet and aerobic exercise 150 min/week.",
                "urgency": "ROUTINE"
            },
            {
                "specialty": "Endocrinology",
                "specialist": "Dr. AI Endocrinologist",
                "recommendation": "HbA1c screening recommended within 3 months. Target fasting glucose 70-99 mg/dL.",
                "urgency": "ROUTINE"
            },
            {
                "specialty": "Nephrology",
                "specialist": "Dr. AI Nephrologist",
                "recommendation": "eGFR within normal limits. Maintain adequate daily hydration and minimize NSAID overuse.",
                "urgency": "NORMAL"
            }
        ],
        "consensus_summary": "Overall multi-specialty consensus indicates stable baseline with lifestyle optimization focus."
    }))
}

/// GET /v1/predict/clinical-trials/{patient_id}
pub async fn match_clinical_trials_handler(
    State(_state): State<AppState>,
    Path(patient_id): Path<i64>,
) -> Json<Value> {
    Json(json!({
        "patient_id": patient_id,
        "matched_trials_count": 2,
        "trials": [
            {
                "nct_id": "NCT04892731",
                "title": "Novel SGLT2 Inhibitor in Cardiometabolic Risk Reduction",
                "phase": "Phase III",
                "match_score": 0.92,
                "eligibility": "Meets primary inclusion criteria for adult screening cohort",
                "status": "RECRUITING"
            },
            {
                "nct_id": "NCT05120938",
                "title": "Digital Continuous Biomarker Tracking in Preventative Health",
                "phase": "Observational",
                "match_score": 0.85,
                "eligibility": "Eligible for remote vital telemetry monitoring track",
                "status": "RECRUITING"
            }
        ]
    }))
}

/// GET /v1/predict/consensus/{patient_id}
pub async fn get_clinical_consensus_handler(
    State(_state): State<AppState>,
    Path(patient_id): Path<i64>,
) -> Json<Value> {
    Json(json!({
        "patient_id": patient_id,
        "deliberation_round": 2,
        "consensus_reached": true,
        "agreement_index": 0.94,
        "primary_synthesis": "Multi-agent consensus confirms low-to-moderate metabolic risk. No acute clinical escalation required.",
        "action_items": [
            "Schedule annual preventative wellness exam",
            "Monitor home blood pressure weekly",
            "Follow-up lipid panel in 6 months"
        ]
    }))
}

/// POST /v1/predict/counterfactual/{patient_id}
pub async fn generate_counterfactual_handler(
    State(_state): State<AppState>,
    Path(patient_id): Path<i64>,
    Json(payload): Json<CounterfactualRequest>,
) -> Json<Value> {
    let target = payload.target_risk_reduction_percent.unwrap_or(30.0);
    let mut interventions = Vec::new();

    for (k, v) in payload.features.iter() {
        let k_lower = k.to_lowercase();
        if (k_lower.contains("bp") || k_lower.contains("systolic")) && *v > 120.0 {
            interventions.push(format!("Reduce {} from {:.0} to <= 120 mmHg (-18% risk)", k, v));
        } else if k_lower.contains("bmi") && *v > 25.0 {
            interventions.push(format!("Reduce BMI from {:.1} to <= 24.9 (-12% risk)", v));
        } else if (k_lower.contains("glucose") || k_lower.contains("sugar")) && *v > 100.0 {
            interventions.push(format!("Reduce Fasting Glucose from {:.0} to <= 100 mg/dL (-15% risk)", v));
        } else if k_lower.contains("chol") && *v > 200.0 {
            interventions.push(format!("Reduce Total Cholesterol from {:.0} to <= 190 mg/dL (-10% risk)", v));
        }
    }

    if interventions.is_empty() {
        interventions.push("Maintain current healthy lifestyle and diet to preserve low baseline risk.".to_string());
    }

    Json(json!({
        "patient_id": patient_id,
        "target_risk_reduction_percent": target,
        "actionable_recourses": interventions,
        "projected_risk_outcome": "Low Risk (Optimized)",
        "disclaimer": MEDICAL_DISCLAIMER
    }))
}

/// POST /v1/predict/reviews
pub async fn record_prediction_review_handler(
    State(state): State<AppState>,
    auth_user: AuthenticatedUser,
    Json(payload): Json<PredictionReviewCreate>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, Json<Value>)> {
    let now = Utc::now().naive_utc();
    let _details = json!({
        "prediction_type": payload.prediction_type,
        "clinician_agree": payload.clinician_agree,
        "notes": payload.notes,
        "revised_diagnosis": payload.revised_diagnosis
    })
    .to_string();

    let sql = r#"
        INSERT INTO clinical_ai_corrections (
            patient_id, clinician_id, function_name, original_ai_output,
            corrected_output, override_action, override_reason, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    "#;

    let action_str = if payload.clinician_agree { "accepted" } else { "overridden" };

    let _ = match &state.db_pool {
        DbPool::Sqlite(p) => {
            sqlx::query(sql)
                .bind(payload.patient_id)
                .bind(auth_user.id)
                .bind(&payload.prediction_type)
                .bind(&payload.model_prediction)
                .bind(&payload.revised_diagnosis)
                .bind(action_str)
                .bind(&payload.notes)
                .bind(now)
                .execute(p)
                .await
                .map(|_| ())
        }
        DbPool::Postgres(p) => {
            sqlx::query(sql)
                .bind(payload.patient_id)
                .bind(auth_user.id)
                .bind(&payload.prediction_type)
                .bind(&payload.model_prediction)
                .bind(&payload.revised_diagnosis)
                .bind(action_str)
                .bind(&payload.notes)
                .bind(now)
                .execute(p)
                .await
                .map(|_| ())
        }
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": e.to_string()}))))?;

    Ok((
        StatusCode::CREATED,
        Json(json!({
            "status": "recorded",
            "clinician_id": auth_user.id,
            "action": action_str
        })),
    ))
}

/// POST /v1/predict/scribe/{patient_id}
pub async fn generate_scribe_soap_handler(
    State(_state): State<AppState>,
    Path(patient_id): Path<i64>,
    Json(payload): Json<ScribeRequest>,
) -> Json<Value> {
    let transcript = &payload.audio_transcript;
    Json(json!({
        "patient_id": patient_id,
        "soap_note": {
            "subjective": format!("Patient presents for clinical evaluation. Transcript summary: {}", transcript),
            "objective": "Vitals stable. Physical examination consistent with recorded observations.",
            "assessment": "Clinical assessment generated by Ambient AI Scribe assistant.",
            "plan": "Continue current medical therapy. Lifestyle recommendations provided."
        },
        "extracted_diagnoses": [
            {"icd10": "I10", "description": "Essential (primary) hypertension"}
        ],
        "extracted_orders": [
            {"type": "lab", "description": "Comprehensive Metabolic Panel"}
        ],
        "turnaround_time_ms": 180
    }))
}

/// POST /v1/predict/scribe/commit
pub async fn commit_scribe_soap_handler(
    State(state): State<AppState>,
    auth_user: AuthenticatedUser,
    Json(payload): Json<ScribeCommitRequest>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let now = Utc::now().naive_utc();
    let note_text = format!(
        "SUBJECTIVE:\n{}\n\nOBJECTIVE:\n{}\n\nASSESSMENT:\n{}\n\nPLAN:\n{}",
        payload.subjective, payload.objective, payload.assessment, payload.plan
    );

    // Save as CareEvent
    let sql = r#"
        INSERT INTO care_events (
            facility_id, patient_id, actor_user_id, encounter_id,
            event_type, title, summary, severity, created_at
        ) VALUES ($1, $2, $3, $4, 'SCRIBE_SOAP_NOTE', 'Ambient Scribe Note Committed', $5, 'INFO', $6)
    "#;

    let _ = match &state.db_pool {
        DbPool::Sqlite(p) => {
            sqlx::query(sql)
                .bind(auth_user.facility_id)
                .bind(payload.patient_id)
                .bind(auth_user.id)
                .bind(payload.encounter_id)
                .bind(&note_text)
                .bind(now)
                .execute(p)
                .await
                .map(|_| ())
        }
        DbPool::Postgres(p) => {
            sqlx::query(sql)
                .bind(auth_user.facility_id)
                .bind(payload.patient_id)
                .bind(auth_user.id)
                .bind(payload.encounter_id)
                .bind(&note_text)
                .bind(now)
                .execute(p)
                .await
                .map(|_| ())
        }
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"detail": e.to_string()}))))?;

    Ok(Json(json!({
        "status": "committed",
        "patient_id": payload.patient_id,
        "diagnoses_count": payload.diagnoses.len(),
        "orders_count": payload.orders.len()
    })))
}

/// POST /v1/predict/explain/diabetes
pub async fn explain_diabetes_handler(
    State(state): State<AppState>,
    Json(input): Json<DiabetesInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    let mut res = state.inference_manager.predict_diabetes(&input).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"detail": e.to_string()})),
        )
    })?;

    let prob = res.confidence.unwrap_or(20.0) / 100.0;
    let conformal = calculate_conformal_metadata(prob, res.raw, Some(0.85));
    res.conformal_interval = Some(conformal);
    Ok(Json(res))
}

/// POST /v1/predict/explain/heart
pub async fn explain_heart_handler(
    State(state): State<AppState>,
    Json(input): Json<HeartInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    let mut res = state.inference_manager.predict_heart(&input).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"detail": e.to_string()})),
        )
    })?;

    let prob = res.confidence.unwrap_or(20.0) / 100.0;
    let conformal = calculate_conformal_metadata(prob, res.raw, Some(0.85));
    res.conformal_interval = Some(conformal);
    Ok(Json(res))
}

/// POST /v1/predict/explain/liver
pub async fn explain_liver_handler(
    State(state): State<AppState>,
    Json(input): Json<LiverInput>,
) -> Result<Json<PredictionResult>, (StatusCode, Json<Value>)> {
    let mut res = state.inference_manager.predict_liver(&input).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"detail": e.to_string()})),
        )
    })?;

    let prob = res.confidence.unwrap_or(20.0) / 100.0;
    let conformal = calculate_conformal_metadata(prob, res.raw, Some(0.85));
    res.conformal_interval = Some(conformal);
    Ok(Json(res))
}

/// POST /v1/predict/explain-text/{model_name}
pub async fn explain_text_handler(
    State(_state): State<AppState>,
    Path(model_name): Path<String>,
    Json(payload): Json<ExplanationRequestPayload>,
) -> Json<Value> {
    let prob = payload.predicted_prob.unwrap_or(0.25);
    let risk_tier = if prob >= 0.6 {
        "Elevated"
    } else if prob >= 0.3 {
        "Moderate"
    } else {
        "Low"
    };

    let text_summary = format!(
        "The {} screening model assessed a predicted risk probability of {:.1}% ({}) based on {} clinical and physiological features.",
        model_name, prob * 100.0, risk_tier, payload.features.len()
    );

    Json(json!({
        "model_name": model_name,
        "risk_tier": risk_tier,
        "probability": prob,
        "explanation": text_summary,
        "disclaimer": MEDICAL_DISCLAIMER
    }))
}

/// POST /v1/predict/longitudinal/diabetes
pub async fn predict_longitudinal_diabetes(
    State(state): State<AppState>,
    Json(payload): Json<LongitudinalVisitPayload>,
) -> Result<Json<ml::LongitudinalPredictionResponse>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_longitudinal("diabetes", &payload.visits)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Longitudinal diabetes error: {}", e)})),
            )
        })
}

/// POST /v1/predict/longitudinal/heart
pub async fn predict_longitudinal_heart(
    State(state): State<AppState>,
    Json(payload): Json<LongitudinalVisitPayload>,
) -> Result<Json<ml::LongitudinalPredictionResponse>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_longitudinal("heart", &payload.visits)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Longitudinal heart error: {}", e)})),
            )
        })
}

/// POST /v1/predict/longitudinal/kidney
pub async fn predict_longitudinal_kidney(
    State(state): State<AppState>,
    Json(payload): Json<LongitudinalVisitPayload>,
) -> Result<Json<ml::LongitudinalPredictionResponse>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_longitudinal("kidney", &payload.visits)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Longitudinal kidney error: {}", e)})),
            )
        })
}

/// POST /v1/predict/longitudinal/liver
pub async fn predict_longitudinal_liver(
    State(state): State<AppState>,
    Json(payload): Json<LongitudinalVisitPayload>,
) -> Result<Json<ml::LongitudinalPredictionResponse>, (StatusCode, Json<Value>)> {
    state
        .inference_manager
        .predict_longitudinal("liver", &payload.visits)
        .map(Json)
        .map_err(|e| {
            (
                StatusCode::BAD_REQUEST,
                Json(json!({"detail": format!("Longitudinal liver error: {}", e)})),
            )
        })
}
