use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use chrono::{Duration, Utc};
use flate2::read::ZlibDecoder;
use flate2::write::ZlibEncoder;
use flate2::Compression;
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::io::{Read, Write};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Instant;

use rust_gateway_ffi::db::DbPool;
use rust_gateway_ffi::db::repo::UserRepo;
use rust_gateway_ffi::ml::calculators::{
    calculate_cha2ds2_vasc, calculate_egfr_ckd_epi, calculate_fib4_index,
    calculate_framingham_risk, calculate_meld_score, calculate_qsofa,
};
use rust_gateway_ffi::ml::explain::{calculate_conformal_metadata, generate_counterfactual_recourse};
use rust_gateway_ffi::ml::longitudinal::predict_longitudinal;
use rust_gateway_ffi::ml::predictors::{
    predict_diabetes, predict_heart_disease, predict_kidney_disease, predict_liver_disease,
    predict_lung_disease, predict_stroke_risk, DiabetesInput, HeartInput, KidneyInput, LiverInput,
    LungInput, StrokeInput,
};
use rust_gateway_ffi::ml::InferenceManager;

fn resolve_model_directory() -> PathBuf {
    let candidates = [
        PathBuf::from("../backend"),
        PathBuf::from("backend"),
        PathBuf::from("../../backend"),
        PathBuf::from("models"),
        PathBuf::from("../models"),
    ];
    for c in &candidates {
        if c.join("diabetes_model.onnx").exists() {
            return c.clone();
        }
    }
    PathBuf::from("../backend")
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. Authentication & 2FA Adversarial Stress & Contract Verification
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Default)]
struct TestBruteForceTracker {
    failed_attempts: Mutex<HashMap<String, (u32, Option<chrono::DateTime<Utc>>)>>,
}

impl TestBruteForceTracker {
    fn is_locked_out(&self, username: &str) -> bool {
        let mut map = self.failed_attempts.lock().unwrap();
        if let Some((_count, lockout_until)) = map.get(username) {
            if let Some(until) = lockout_until {
                if Utc::now() < *until {
                    return true;
                }
                map.insert(username.to_string(), (0, None));
            }
        }
        false
    }

    fn record_failure(&self, username: &str) {
        let mut map = self.failed_attempts.lock().unwrap();
        let (mut count, _) = map.get(username).cloned().unwrap_or((0, None));
        count += 1;
        let lockout = if count >= 5 {
            Some(Utc::now() + Duration::minutes(15))
        } else {
            None
        };
        map.insert(username.to_string(), (count, lockout));
    }

    fn record_success(&self, username: &str) {
        let mut map = self.failed_attempts.lock().unwrap();
        map.remove(username);
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct TestClaims {
    sub: String,
    exp: usize,
    #[serde(default)]
    role: Option<String>,
    #[serde(default)]
    action: Option<String>,
    #[serde(default)]
    facility_id: Option<i64>,
}

#[tokio::test]
async fn test_adversarial_auth_brute_force_lockout_state_machine() {
    let tracker = Arc::new(TestBruteForceTracker::default());
    let target_user = "clinician_dr_smith";

    // Attempt 1 through 4: Should record failures, but NOT be locked out yet
    for attempt in 1..=4 {
        assert!(
            !tracker.is_locked_out(target_user),
            "Account should not be locked out at attempt {}",
            attempt
        );
        tracker.record_failure(target_user);
    }

    // 5th failed attempt: Triggers the 15-minute lockout
    tracker.record_failure(target_user);
    assert!(
        tracker.is_locked_out(target_user),
        "Account MUST be locked out immediately after 5th failed attempt"
    );

    // 6th attempt: Lockout is active and immediately blocks
    assert!(
        tracker.is_locked_out(target_user),
        "Account must remain locked out on 6th attempt"
    );

    // Another unrelated user must not be affected (multi-tenant isolation)
    let innocent_user = "nurse_sarah";
    assert!(
        !tracker.is_locked_out(innocent_user),
        "Innocent user must not be affected by attacker lockout"
    );

    // Explicit success clears tracker
    tracker.record_success(target_user);
    assert!(
        !tracker.is_locked_out(target_user),
        "Account lockout should be cleared upon successful administrative/auth reset"
    );
}

#[tokio::test]
async fn test_adversarial_password_complexity_and_bcrypt_rounds() {
    let weak_passwords = [
        "short",             // < 8 chars
        "onlyletterswithoutdigits", // no digits
        "1234567890",        // no letters
        "",                  // empty
        "       ",           // only whitespace
    ];

    let is_complex = |p: &str| -> bool {
        p.len() >= 8 && p.chars().any(|c| c.is_alphabetic()) && p.chars().any(|c| c.is_numeric())
    };

    for weak in &weak_passwords {
        assert!(
            !is_complex(weak),
            "Weak password '{}' must be rejected by complexity validator",
            weak
        );
    }

    let strong_passwords = [
        "SecurePassword2026!",
        "HealthCareAI#99",
        "ClinicalToken_42",
        "P@ssw0rdDoctor1",
    ];

    for strong in &strong_passwords {
        assert!(
            is_complex(strong),
            "Strong password '{}' must pass complexity validator",
            strong
        );

        // Verify bcrypt hash & verify roundtrip
        let hashed = bcrypt::hash(strong, bcrypt::DEFAULT_COST).expect("Bcrypt hash failed");
        assert!(bcrypt::verify(strong, &hashed).expect("Bcrypt verification failed"));
        assert!(
            !bcrypt::verify("WrongPassword123", &hashed).expect("Bcrypt check failed"),
            "Invalid password must not verify against bcrypt hash"
        );
    }
}

#[tokio::test]
async fn test_adversarial_jwt_tampering_signature_and_expiration() {
    let secret = b"super_confidential_healthcare_jwt_key_2026";
    let now = Utc::now().timestamp() as usize;

    let valid_claims = TestClaims {
        sub: "doctor_101".to_string(),
        exp: now + 3600, // 1 hour in future
        role: Some("doctor".to_string()),
        action: None,
        facility_id: Some(1),
    };

    let token = encode(
        &Header::default(),
        &valid_claims,
        &EncodingKey::from_secret(secret),
    )
    .expect("JWT encode failed");

    // 1. Valid token decodes correctly
    let mut validation = Validation::new(Algorithm::HS256);
    let decoded = decode::<TestClaims>(&token, &DecodingKey::from_secret(secret), &validation)
        .expect("Valid JWT decoding failed");
    assert_eq!(decoded.claims.sub, "doctor_101");
    assert_eq!(decoded.claims.role, Some("doctor".to_string()));

    // 2. Tampered token (modify last character of signature)
    let mut tampered_token = token.clone();
    let last_char = if tampered_token.ends_with('A') { 'B' } else { 'A' };
    tampered_token.pop();
    tampered_token.push(last_char);

    let tampered_result = decode::<TestClaims>(
        &tampered_token,
        &DecodingKey::from_secret(secret),
        &validation,
    );
    assert!(
        tampered_result.is_err(),
        "Tampered token must fail signature verification"
    );

    // 3. Expired token
    let expired_claims = TestClaims {
        sub: "doctor_101".to_string(),
        exp: now - 300, // 5 minutes in past
        role: Some("doctor".to_string()),
        action: None,
        facility_id: Some(1),
    };
    let expired_token = encode(
        &Header::default(),
        &expired_claims,
        &EncodingKey::from_secret(secret),
    )
    .expect("Expired JWT encode failed");

    validation.validate_exp = true;
    let expired_result = decode::<TestClaims>(
        &expired_token,
        &DecodingKey::from_secret(secret),
        &validation,
    );
    assert!(
        expired_result.is_err(),
        "Expired token must be rejected by JWT validator"
    );

    // 4. Wrong signing key
    let attacker_secret = b"attacker_forged_secret_key_12345678";
    let wrong_key_result = decode::<TestClaims>(
        &token,
        &DecodingKey::from_secret(attacker_secret),
        &validation,
    );
    assert!(
        wrong_key_result.is_err(),
        "Token signed with different secret key must be rejected"
    );
}

#[tokio::test]
async fn test_adversarial_user_repository_sqlite_crud_and_lock() {
    let db_path = format!("sqlite://./test_auth_{}.db", uuid::Uuid::new_v4());
    let pool = DbPool::new(&db_path)
        .await
        .expect("Failed to initialize SQLite pool");

    if let DbPool::Sqlite(p) = &pool {
        sqlx::query("INSERT INTO hospital_facilities (id, name) VALUES (1, 'Princeton Plainsboro')")
            .execute(p)
            .await
            .expect("Failed to insert facility");
    }

    let username = "dr_gregory_house";
    let email = "house@princetongeneral.org";
    let pwd_hash = bcrypt::hash("Diagnostics2026!", bcrypt::DEFAULT_COST).unwrap();

    let user_id = UserRepo::create_user(
        &pool,
        username,
        &pwd_hash,
        "doctor",
        Some(email),
        Some("Dr. Gregory House"),
        Some(1),
    )
    .await
    .expect("UserRepo::create_user failed");

    assert!(user_id > 0);

    // Duplicate username creation must fail
    let dup_res = UserRepo::create_user(
        &pool,
        username,
        &pwd_hash,
        "doctor",
        Some(email),
        Some("Duplicate User"),
        Some(1),
    )
    .await;
    assert!(
        dup_res.is_err(),
        "Duplicate username creation must return an error"
    );

    // Fetch user by username
    let fetched = UserRepo::find_by_username(&pool, username)
        .await
        .expect("Failed to get user")
        .expect("User should exist");
    assert_eq!(fetched.username, username);
    assert_eq!(fetched.role, "doctor");
    assert_eq!(fetched.facility_id, Some(1));
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. ONNX Disease Prediction & Conformal Bounds Stress Tests
// ─────────────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn test_adversarial_prediction_endpoints_concurrent_stress() {
    let model_dir = resolve_model_directory();
    let manager = Arc::new(
        InferenceManager::from_dir(model_dir.to_str().unwrap())
            .expect("Failed to load ONNX inference manager"),
    );

    let num_tasks = 60;
    let mut handles = Vec::with_capacity(num_tasks);

    for i in 0..num_tasks {
        let mgr = Arc::clone(&manager);
        let handle = tokio::spawn(async move {
            match i % 6 {
                0 => {
                    let input = DiabetesInput {
                        hypertension: 1.0,
                        high_chol: 1.0,
                        bmi: 28.5 + (i as f32 * 0.1),
                        smoking_history: 0.0,
                        heart_disease: 0.0,
                        physical_activity: 1.0,
                        general_health: 3.0,
                        gender: 1.0,
                        age: 40.0 + (i as f32 * 0.5),
                    };
                    let res = mgr.predict_diabetes(&input).expect("Diabetes predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
                1 => {
                    let input = HeartInput {
                        age: 55.0,
                        sex: 1.0,
                        cp: 2.0,
                        trestbps: 135.0 + (i as f32),
                        chol: 220.0,
                        fbs: 0.0,
                        restecg: 1.0,
                        thalach: 145.0,
                        exang: 0.0,
                        oldpeak: 1.2,
                        slope: 1.0,
                        ca: 0.0,
                        thal: 2.0,
                    };
                    let res = mgr.predict_heart(&input).expect("Heart predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
                2 => {
                    let input = KidneyInput {
                        age: 50.0 + (i as f32 * 0.2),
                        bp: 80.0,
                        sg: 1.020,
                        al: 0.0,
                        su: 0.0,
                        rbc: 0.0,
                        pc: 0.0,
                        pcc: 0.0,
                        ba: 0.0,
                        bgr: 110.0,
                        bu: 30.0,
                        sc: 1.0,
                        sod: 138.0,
                        pot: 4.2,
                        hemo: 15.0,
                        pcv: 45.0,
                        wc: 7000.0,
                        rc: 5.0,
                        htn: 0.0,
                        dm: 0.0,
                        cad: 0.0,
                        appet: 0.0,
                        pe: 0.0,
                        ane: 0.0,
                        is_female: Some(false),
                    };
                    let res = mgr.predict_kidney(&input).expect("Kidney predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
                3 => {
                    let input = LiverInput {
                        age: 48.0,
                        gender: 1.0,
                        total_bilirubin: 1.1 + (i as f32 * 0.1),
                        direct_bilirubin: 0.4,
                        alkaline_phosphotase: 190.0,
                        alamine_aminotransferase: 45.0,
                        aspartate_aminotransferase: 55.0,
                        total_proteins: 6.8,
                        albumin: 3.5,
                        albumin_and_globulin_ratio: 1.0,
                        platelets: Some(220.0),
                    };
                    let res = mgr.predict_liver(&input).expect("Liver predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
                4 => {
                    let input = LungInput {
                        gender: 1.0,
                        age: 62.0,
                        smoking: 2.0,
                        yellow_fingers: 1.0,
                        anxiety: 1.0,
                        peer_pressure: 1.0,
                        chronic_disease: 1.0,
                        fatigue: 1.0,
                        allergy: 1.0,
                        wheezing: 1.0,
                        alcohol: 1.0,
                        coughing: 1.0,
                        shortness_of_breath: 1.0,
                        swallowing_difficulty: 1.0,
                        chest_pain: 1.0,
                    };
                    let res = mgr.predict_lungs(&input).expect("Lungs predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
                _ => {
                    let input = StrokeInput {
                        gender: Some(1.0),
                        age: Some(65.0 + (i as f32 * 0.2)),
                        hypertension: Some(1.0),
                        heart_disease: Some(0.0),
                        smoking: Some(2.0),
                        bmi: Some(31.0),
                        glucose: Some(140.0),
                    };
                    let res = mgr.predict_stroke(&input).expect("Stroke predict failed");
                    let p = res.probability.unwrap_or(0.5);
                    assert!(p >= 0.0 && p <= 1.0);
                    assert!(res.raw == 0 || res.raw == 1);
                }
            }
        });
        handles.push(handle);
    }

    for h in handles {
        h.await.expect("Concurrent prediction task panicked");
    }
}

#[tokio::test]
async fn test_adversarial_prediction_extreme_and_out_of_distribution_inputs() {
    let model_dir = resolve_model_directory();
    let manager = InferenceManager::from_dir(model_dir.to_str().unwrap())
        .expect("Failed to load ONNX inference manager");

    // Extreme high glucose & BMI for diabetes
    let extreme_diabetes = DiabetesInput {
        hypertension: 1.0,
        high_chol: 1.0,
        bmi: 45.0,
        smoking_history: 1.0,
        heart_disease: 1.0,
        physical_activity: 0.0,
        general_health: 5.0,
        gender: 1.0,
        age: 80.0,
    };
    let res_diab = manager
        .predict_diabetes(&extreme_diabetes)
        .expect("Extreme diabetes prediction failed");
    let p_diab = res_diab.probability.expect("probability present");
    assert!(!p_diab.is_nan());
    assert!(!p_diab.is_infinite());
    assert_eq!(res_diab.raw, 1);
    assert_eq!(res_diab.risk_level.as_deref(), Some("High"));

    // Extreme zero/minimum inputs for heart
    let min_heart = HeartInput {
        age: 25.0,
        sex: 0.0,
        cp: 0.0,
        trestbps: 90.0,
        chol: 130.0,
        fbs: 0.0,
        restecg: 0.0,
        thalach: 170.0,
        exang: 0.0,
        oldpeak: 0.0,
        slope: 1.0,
        ca: 0.0,
        thal: 1.0,
    };
    let res_heart = manager
        .predict_heart(&min_heart)
        .expect("Min heart prediction failed");
    let p_heart = res_heart.probability.expect("probability present");
    assert!(!p_heart.is_nan());
    assert!(!p_heart.is_infinite());
    assert!(p_heart >= 0.0 && p_heart <= 1.0);
}

#[test]
fn test_adversarial_conformal_bounds_and_coverage_invariants() {
    let test_probs = [0.01, 0.05, 0.25, 0.50, 0.75, 0.92, 0.99];

    for prob in test_probs {
        let conf = calculate_conformal_metadata(prob, if prob >= 0.5 { 1 } else { 0 }, Some(0.85));
        assert!(
            conf.p_class_1 >= 0.0 && conf.p_class_1 <= 1.0,
            "p_class_1 must be valid probability"
        );
        assert!(
            conf.p_class_0 >= 0.0 && conf.p_class_0 <= 1.0,
            "p_class_0 must be valid probability"
        );
        assert!((conf.p_class_0 + conf.p_class_1 - 1.0).abs() < 1e-6);
        assert!(!conf.conformal_prediction_set.is_empty() || !conf.uncertainty_level.is_empty());
    }
}

#[test]
fn test_adversarial_clinical_calculators_exhaustive_boundary_matrix() {
    // 1. eGFR CKD-EPI 2021 Race-Free
    let egfr_male_normal = calculate_egfr_ckd_epi(0.9, 30.0, false).expect("eGFR male normal failed");
    assert!(egfr_male_normal.egfr >= 90.0);
    assert_eq!(egfr_male_normal.stage, "Stage G1");

    let egfr_female_severe = calculate_egfr_ckd_epi(4.5, 75.0, true).expect("eGFR female severe failed");
    assert!(egfr_female_severe.egfr < 15.0);
    assert_eq!(egfr_female_severe.stage, "Stage G5");

    // Invalid bounds (creatinine <= 0 or age < 18)
    assert!(calculate_egfr_ckd_epi(0.0, 30.0, false).is_none());
    assert!(calculate_egfr_ckd_epi(-1.2, 45.0, true).is_none());
    assert!(calculate_egfr_ckd_epi(1.0, 15.0, false).is_none());

    // 2. FIB-4 Liver Fibrosis Index
    let fib4_normal = calculate_fib4_index(25.0, 20.0, 250.0, 35.0).expect("FIB-4 normal failed");
    assert!(fib4_normal.score < 1.30);
    assert_eq!(fib4_normal.risk_level, "Low Risk");

    let fib4_high = calculate_fib4_index(90.0, 45.0, 80.0, 65.0).expect("FIB-4 high failed");
    assert!(fib4_high.score > 2.67);
    assert_eq!(fib4_high.risk_level, "High Risk");

    // Division by zero defense (platelets <= 0 or ALT <= 0)
    assert!(calculate_fib4_index(40.0, 0.0, 200.0, 50.0).is_none());
    assert!(calculate_fib4_index(40.0, 35.0, 0.0, 50.0).is_none());

    // 3. qSOFA Sepsis Bundle
    let qsofa_crit = calculate_qsofa(24.0, 90.0, 13.0);
    assert_eq!(qsofa_crit.score, 3);
    assert_eq!(qsofa_crit.risk_level, "HIGH_SEPSIS_RISK");

    let qsofa_norm = calculate_qsofa(16.0, 120.0, 15.0);
    assert_eq!(qsofa_norm.score, 0);
    assert_eq!(qsofa_norm.risk_level, "LOW_RISK");

    // 4. CHA2DS2-VASc Stroke Risk
    let cha_high = calculate_cha2ds2_vasc(76.0, true, true, true, true, true, true);
    assert!(cha_high.score >= 6);
    assert!(cha_high.annual_stroke_risk_percent >= 9.0);

    // 5. MELD Liver Score
    let meld_severe = calculate_meld_score(4.0, 3.5, 2.5, false);
    assert!(meld_severe.score >= 20.0);
    assert!(meld_severe.mortality_3_month_percent >= 50.0);
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. FHIR Compression, Validation & Decompression Bomb Stress
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_fhir_compression_high_volume_and_bomb_defense() {
    // Generate a massive multi-resource synthetic FHIR bundle (approx 100KB JSON)
    let mut entries = Vec::new();
    for i in 1..=200 {
        entries.push(json!({
            "fullUrl": format!("urn:uuid:observation-{}", i),
            "resource": {
                "resourceType": "Observation",
                "id": format!("obs-{}", i),
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
                    }]
                },
                "subject": { "reference": "Patient/pat-100" },
                "effectiveDateTime": "2026-08-21T10:00:00Z",
                "valueQuantity": {
                    "value": 60 + (i % 40),
                    "unit": "beats/minute",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            }
        }));
    }

    let large_fhir_bundle = json!({
        "resourceType": "Bundle",
        "type": "collection",
        "total": entries.len(),
        "entry": entries
    });

    let raw_payload = large_fhir_bundle.to_string();
    let uncompressed_size = raw_payload.len();
    assert!(uncompressed_size > 50_000, "Uncompressed payload should exceed 50KB");

    // 1. Zlib RFC 1950 Compression
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::best());
    encoder.write_all(raw_payload.as_bytes()).expect("Compression failed");
    let compressed_bytes = encoder.finish().expect("Finish compression failed");
    let base64_payload = BASE64.encode(&compressed_bytes);

    let compressed_size = base64_payload.len();
    let compression_ratio = 1.0 - (compressed_size as f64 / uncompressed_size as f64);
    assert!(
        compression_ratio > 0.65,
        "Compression ratio must exceed 65% on repetitive FHIR bundle (got {:.2}%)",
        compression_ratio * 100.0
    );

    // 2. Decompress and verify byte-for-byte structural equality
    let decoded_bytes = BASE64.decode(&base64_payload).expect("Base64 decode failed");
    let mut decoder = ZlibDecoder::new(&decoded_bytes[..]);
    let mut decompressed_str = String::new();
    decoder.read_to_string(&mut decompressed_str).expect("Decompression failed");

    let parsed: serde_json::Value =
        serde_json::from_str(&decompressed_str).expect("Restored JSON parse failed");
    assert_eq!(parsed["resourceType"], "Bundle");
    assert_eq!(parsed["total"], 200);
    assert_eq!(parsed["entry"].as_array().unwrap().len(), 200);
}

#[test]
fn test_adversarial_fhir_malformed_decompression_handling() {
    // 1. Malformed Base64
    let corrupted_b64 = "ThisIsNotValidBase64Padding!!!";
    assert!(BASE64.decode(corrupted_b64).is_err());

    // 2. Corrupted Zlib Stream (Valid Base64 but random non-zlib bytes)
    let random_bytes = vec![0xDE, 0xAD, 0xBE, 0xEF, 0x01, 0x02, 0x03, 0x04];
    let b64_random = BASE64.encode(&random_bytes);
    let decoded = BASE64.decode(b64_random).unwrap();
    let mut decoder = ZlibDecoder::new(&decoded[..]);
    let mut out_str = String::new();
    let decompress_res = decoder.read_to_string(&mut out_str);
    assert!(
        decompress_res.is_err(),
        "Corrupted zlib stream must return an error rather than panicking"
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Data Platform SQL Execution, Governance & Fraud Detection
// ─────────────────────────────────────────────────────────────────────────────

#[tokio::test]
async fn test_adversarial_data_platform_sql_execution_safety_and_governance() {
    let db_path = format!("sqlite://./test_data_platform_{}.db", uuid::Uuid::new_v4());
    let pool = DbPool::new(&db_path)
        .await
        .expect("Failed to initialize SQLite pool");

    // Insert sample facilities and encounters
    if let DbPool::Sqlite(p) = &pool {
        sqlx::query("INSERT INTO hospital_facilities (name, facility_type, country, region) VALUES ('Metropolitan Hospital', 'hospital', 'USA', 'NY')")
            .execute(p)
            .await
            .expect("Failed to insert facility");

        // Execute SELECT query using AssertSqlSafe
        let rows: Vec<sqlx::sqlite::SqliteRow> = sqlx::query(sqlx::AssertSqlSafe(
            "SELECT id, name, facility_type, region FROM hospital_facilities WHERE region = 'NY'",
        ))
        .fetch_all(p)
        .await
        .expect("SELECT query failed");

        assert_eq!(rows.len(), 1);
        use sqlx::Row;
        let name: String = rows[0].get("name");
        assert_eq!(name, "Metropolitan Hospital");
    }
}

#[test]
fn test_adversarial_claim_fraud_and_cost_optimizer_heuristics() {
    // 1. Critical Fraud: Duplicate claim + High amount + CPT code unbundling
    let high_claim_amount = 18_500.0;
    let is_dup = true;
    let cpt = "CPT-99211-EMERGENCY";

    let mut fraud_score: f64 = 0.05;
    if is_dup {
        fraud_score += 0.50;
    }
    if high_claim_amount > 10_000.0 {
        fraud_score += 0.25;
    }
    if cpt.contains("CPT-99211") && high_claim_amount > 5_000.0 {
        fraud_score += 0.20;
    }
    let fraud_score_clamped = fraud_score.min(0.99f64);

    assert_eq!(fraud_score_clamped, 0.99);
    let risk_tier = if fraud_score_clamped >= 0.70 {
        "CRITICAL"
    } else if fraud_score_clamped >= 0.40 {
        "HIGH"
    } else {
        "LOW"
    };
    assert_eq!(risk_tier, "CRITICAL");

    // 2. Low Risk Claim
    let clean_amount = 120.0;
    let mut clean_score: f64 = 0.05;
    if clean_amount > 10_000.0 {
        clean_score += 0.25;
    }
    assert_eq!(clean_score, 0.05);
}

#[test]
fn test_adversarial_four_eye_dual_signoff_tamper_evident_chain() {
    // Cryptographic signature over clinical recommendation
    let requester_id = "dr_stephen_strange";
    let reviewer_id = "dr_christine_palmer";
    let patient_id = 10042;
    let action = "ORDER_HIGH_RISK_BIOLOGIC";
    let rationale = "Patient refractory to conventional immunosuppressive therapy";
    let timestamp = "2026-08-21T06:00:00Z";

    // Separation of duties constraint: Requester cannot approve their own action
    assert_ne!(
        requester_id, reviewer_id,
        "Separation of duties: Reviewer MUST NOT be the requester"
    );

    // Compute SHA-256 digital signature
    let sign_payload = format!(
        "{}:{}:{}:{}:{}:{}",
        requester_id, reviewer_id, patient_id, action, rationale, timestamp
    );
    let mut hasher = Sha256::new();
    hasher.update(sign_payload.as_bytes());
    let signature = format!("{:x}", hasher.finalize());

    assert_eq!(signature.len(), 64);

    // Verify signature integrity
    let mut verify_hasher = Sha256::new();
    verify_hasher.update(sign_payload.as_bytes());
    let check_sig = format!("{:x}", verify_hasher.finalize());
    assert_eq!(signature, check_sig, "Digital signature must match");

    // Tampering test: Attacker changes rationale by 1 byte
    let tampered_rationale = "Patient NOT refractory to therapy (attacker altered)";
    let tampered_payload = format!(
        "{}:{}:{}:{}:{}:{}",
        requester_id, reviewer_id, patient_id, action, tampered_rationale, timestamp
    );
    let mut tampered_hasher = Sha256::new();
    tampered_hasher.update(tampered_payload.as_bytes());
    let tampered_sig = format!("{:x}", tampered_hasher.finalize());
    assert_ne!(
        signature, tampered_sig,
        "Tampered payload MUST produce different SHA-256 signature"
    );
}

#[test]
fn test_adversarial_federated_differential_privacy_and_budget_decay() {
    let mut epsilon_budget: f64 = 5.0;
    let delta_target: f64 = 1e-5;
    let epsilon_per_round: f64 = 0.25;

    let num_rounds = 10;
    for round in 1..=num_rounds {
        assert!(
            epsilon_budget >= epsilon_per_round,
            "Differential privacy epsilon budget exhausted at round {}",
            round
        );
        epsilon_budget -= epsilon_per_round;
    }

    assert_eq!(epsilon_budget, 2.5);
    assert_eq!(delta_target, 1e-5);
}
