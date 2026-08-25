use std::collections::HashMap;
use std::path::PathBuf;
use rust_gateway_ffi::ml::calculators::{
    calculate_cha2ds2_vasc, calculate_egfr_ckd_epi, calculate_fib4_index,
    calculate_framingham_risk, calculate_meld_score, calculate_qsofa,
};
use rust_gateway_ffi::ml::engine::ModelSessions;
use rust_gateway_ffi::ml::explain::{
    calculate_conformal_metadata, generate_counterfactual_recourse,
};
use rust_gateway_ffi::ml::longitudinal::predict_longitudinal;
use rust_gateway_ffi::ml::predictors::{
    predict_diabetes, predict_heart_disease, predict_kidney_disease,
    predict_liver_disease, predict_lung_disease, predict_stroke_risk,
    DiabetesInput, HeartInput, KidneyInput, LiverInput, LungInput, StrokeInput,
};
use rust_gateway_ffi::ml::scalers::{
    preprocess_kidney, preprocess_liver, preprocess_lungs,
};
use rust_gateway_ffi::ml::InferenceManager;

fn get_models_dir() -> PathBuf {
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

#[test]
fn test_kidney_scaler_numerical_parity() {
    let raw = [
        48.0, 80.0, 1.020, 1.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 121.0, 36.0, 1.2, 138.0, 4.4, 15.4, 44.0,
        7800.0, 5.2, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    ];
    let scaled = preprocess_kidney(&raw);

    // Ground truth from ONNX scaler session:
    // [0.1992645412683487, 0.22573284804821014, 0.3562830090522766, -0.3666794002056122]
    assert!((scaled[0] - 0.19926454).abs() < 1e-6, "Kidney feature 0 mismatch: {}", scaled[0]);
    assert!((scaled[1] - 0.22573285).abs() < 1e-6, "Kidney feature 1 mismatch: {}", scaled[1]);
    assert!((scaled[2] - 0.35628301).abs() < 1e-6, "Kidney feature 2 mismatch: {}", scaled[2]);
    assert!((scaled[3] - (-0.36667940)).abs() < 1e-6, "Kidney feature 3 mismatch: {}", scaled[3]);
}

#[test]
fn test_liver_scaler_numerical_parity() {
    let raw = [65.0, 1.0, 0.7, 0.1, 187.0, 16.0, 18.0, 6.8, 3.3, 0.9];
    let scaled = preprocess_liver(&raw);

    // Ground truth from ONNX scaler session with log1p:
    // [0.8695652484893799, 0.0, -0.2344653159379959, -0.18181820213794708]
    assert!((scaled[0] - 0.86956525).abs() < 1e-6, "Liver feature 0 mismatch: {}", scaled[0]);
    assert!((scaled[1] - 0.0).abs() < 1e-6, "Liver feature 1 mismatch: {}", scaled[1]);
    assert!((scaled[2] - (-0.23446532)).abs() < 1e-6, "Liver feature 2 mismatch: {}", scaled[2]);
    assert!((scaled[3] - (-0.18181820)).abs() < 1e-6, "Liver feature 3 mismatch: {}", scaled[3]);
}

#[test]
fn test_lungs_scaler_numerical_parity() {
    let raw = [
        1.0, 69.0, 1.0, 2.0, 2.0, 1.0, 1.0, 2.0,
        1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
    ];
    let scaled = preprocess_lungs(&raw);

    // Ground truth from ONNX scaler session:
    // [0.9525793194770813, 0.7718504667282104, 0.8808304071426392, 2.8889503479003906]
    assert!((scaled[0] - 0.95257932).abs() < 1e-6, "Lungs feature 0 mismatch: {}", scaled[0]);
    assert!((scaled[1] - 0.77185047).abs() < 1e-6, "Lungs feature 1 mismatch: {}", scaled[1]);
    assert!((scaled[2] - 0.88083041).abs() < 1e-6, "Lungs feature 2 mismatch: {}", scaled[2]);
    assert!((scaled[3] - 2.88895035).abs() < 1e-6, "Lungs feature 3 mismatch: {}", scaled[3]);
}

#[test]
fn test_all_models_onnx_inference_parity() {
    let model_dir = get_models_dir();
    let sessions = ModelSessions::load_from_dir(&model_dir)
        .expect("Failed to load ONNX model sessions from backend dir");

    // 1. Diabetes Model Parity
    let d_inp = DiabetesInput {
        hypertension: 1.0,
        high_chol: 1.0,
        bmi: 32.5,
        smoking_history: 1.0,
        heart_disease: 0.0,
        physical_activity: 0.0,
        general_health: 4.0,
        gender: 1.0,
        age: 55.0, // maps to bucket 8.0
    };
    let d_res = predict_diabetes(&sessions, &d_inp).expect("Diabetes prediction failed");
    assert_eq!(d_res.raw, 1);
    assert_eq!(d_res.prediction, "High Risk");
    assert_eq!(d_res.risk_level.as_deref(), Some("High"));
    // Ground truth p_pos = 0.81943768
    let d_prob = d_res.probability.unwrap();
    assert!((d_prob - 0.8194).abs() < 1e-3, "Diabetes prob mismatch: {}", d_prob);

    // 2. Heart Disease Model Parity
    let h_inp = HeartInput {
        age: 60.0,
        sex: 1.0,
        cp: 3.0,
        trestbps: 145.0,
        chol: 233.0,
        fbs: 1.0,
        restecg: 0.0,
        thalach: 150.0,
        exang: 0.0,
        oldpeak: 2.3,
        slope: 0.0,
        ca: 0.0,
        thal: 1.0,
    };
    let h_res = predict_heart_disease(&sessions, &h_inp).expect("Heart prediction failed");
    assert_eq!(h_res.raw, 1);
    assert_eq!(h_res.prediction, "Heart Disease Detected");
    assert!(h_res.framingham.is_some());

    // 3. Kidney Model Parity
    let k_inp = KidneyInput {
        age: 48.0,
        bp: 80.0,
        sg: 1.020,
        al: 1.0,
        su: 0.0,
        rbc: 0.0,
        pc: 0.0,
        pcc: 0.0,
        ba: 0.0,
        bgr: 121.0,
        bu: 36.0,
        sc: 1.2,
        sod: 138.0,
        pot: 4.4,
        hemo: 15.4,
        pcv: 44.0,
        wc: 7800.0,
        rc: 5.2,
        htn: 1.0,
        dm: 0.0,
        cad: 0.0,
        appet: 0.0,
        pe: 0.0,
        ane: 0.0,
        is_female: Some(false),
    };
    let k_res = predict_kidney_disease(&sessions, &k_inp).expect("Kidney prediction failed");
    assert_eq!(k_res.raw, 1);
    assert_eq!(k_res.prediction, "Chronic Kidney Disease Detected");
    assert!(k_res.egfr.is_some());
    // Ground truth p_pos = 0.59056133
    let k_prob = k_res.probability.unwrap();
    assert!((k_prob - 0.5906).abs() < 1e-3, "Kidney prob mismatch: {}", k_prob);

    // 4. Liver Model Parity
    let l_inp = LiverInput {
        age: 65.0,
        gender: 1.0,
        total_bilirubin: 0.7,
        direct_bilirubin: 0.1,
        alkaline_phosphotase: 187.0,
        alamine_aminotransferase: 16.0,
        aspartate_aminotransferase: 18.0,
        total_proteins: 6.8,
        albumin: 3.3,
        albumin_and_globulin_ratio: 0.9,
        platelets: Some(210.0),
    };
    let l_res = predict_liver_disease(&sessions, &l_inp).expect("Liver prediction failed");
    assert_eq!(l_res.raw, 1);
    assert_eq!(l_res.prediction, "Liver Disease Detected");
    assert!(l_res.fib4.is_some());
    // Ground truth p_pos = 0.63346654
    let l_prob = l_res.probability.unwrap();
    assert!((l_prob - 0.6335).abs() < 1e-3, "Liver prob mismatch: {}", l_prob);

    // 5. Lungs Model Parity
    let lu_inp = LungInput {
        gender: 1.0,
        age: 69.0,
        smoking: 1.0,
        yellow_fingers: 2.0,
        anxiety: 2.0,
        peer_pressure: 1.0,
        chronic_disease: 1.0,
        fatigue: 2.0,
        allergy: 1.0,
        wheezing: 2.0,
        alcohol: 2.0,
        coughing: 2.0,
        shortness_of_breath: 2.0,
        swallowing_difficulty: 2.0,
        chest_pain: 2.0,
    };
    let lu_res = predict_lung_disease(&sessions, &lu_inp).expect("Lungs prediction failed");
    assert_eq!(lu_res.raw, 1);
    assert_eq!(lu_res.prediction, "Respiratory Issue Detected");
    // Ground truth p_pos = 0.99498850
    let lu_prob = lu_res.probability.unwrap();
    assert!((lu_prob - 0.9950).abs() < 1e-3, "Lungs prob mismatch: {}", lu_prob);

    // 6. Stroke Model Parity
    let s_inp = StrokeInput {
        gender: Some(1.0),
        age: Some(67.0),
        hypertension: Some(1.0),
        heart_disease: Some(1.0),
        smoking: Some(1.0),
        bmi: Some(36.6),
        glucose: Some(228.69),
    };
    let s_res = predict_stroke_risk(&sessions, &s_inp).expect("Stroke prediction failed");
    assert_eq!(s_res.raw, 1);
    assert_eq!(s_res.prediction, "High Stroke Risk");
}

#[test]
fn test_inference_manager_unified_flow() {
    let model_dir = get_models_dir();
    let manager = InferenceManager::from_dir(model_dir).expect("Failed to init manager");

    let status = manager.health_check();
    assert!(status.all_healthy);

    // Test Clinical Calculators
    let egfr = calculate_egfr_ckd_epi(1.1, 55.0, true).unwrap();
    assert!(egfr.egfr > 50.0);

    let fib4 = calculate_fib4_index(50.0, 35.0, 30.0, 200.0).unwrap();
    assert!(fib4.score > 0.0);

    let framingham = calculate_framingham_risk(60.0, false, 220.0, 45.0, 140.0, true, false, false).unwrap();
    assert!(framingham.risk_percent > 5.0);

    let qsofa = calculate_qsofa(24.0, 95.0, 14.0);
    assert_eq!(qsofa.score, 3);
    assert_eq!(qsofa.risk_level, "HIGH_SEPSIS_RISK");

    let cha = calculate_cha2ds2_vasc(76.0, false, true, true, false, false, true);
    assert!(cha.score >= 5);

    let meld = calculate_meld_score(1.8, 2.5, 1.4, false);
    assert!(meld.score > 10.0);

    // Test Conformal Metadata
    let conf = calculate_conformal_metadata(0.92, 1, Some(0.85));
    assert_eq!(conf.conformal_prediction_set, vec![1]);

    // Test Counterfactual Recourse
    let feats = vec!["bp".to_string(), "chol".to_string(), "bmi".to_string()];
    let vals = vec![150.0, 240.0, 32.0];
    let recourse = generate_counterfactual_recourse(&feats, &vals, 0.88);
    assert_eq!(recourse.actionable_recommendations.len(), 3);
    assert!(recourse.target_achievable_risk < 0.88);
}

#[test]
fn test_longitudinal_prediction_full_pipeline() {
    let mut visit_1 = HashMap::new();
    visit_1.insert("hypertension".to_string(), Some(0.0));
    visit_1.insert("high_chol".to_string(), Some(0.0));
    visit_1.insert("bmi".to_string(), Some(24.0));
    visit_1.insert("smoking_history".to_string(), Some(0.0));
    visit_1.insert("heart_disease".to_string(), Some(0.0));
    visit_1.insert("physical_activity".to_string(), Some(1.0));
    visit_1.insert("general_health".to_string(), Some(2.0));
    visit_1.insert("gender".to_string(), Some(1.0));
    visit_1.insert("age".to_string(), Some(50.0));

    let mut visit_2 = HashMap::new();
    visit_2.insert("hypertension".to_string(), Some(1.0));
    visit_2.insert("high_chol".to_string(), Some(1.0));
    visit_2.insert("bmi".to_string(), Some(31.0));
    visit_2.insert("smoking_history".to_string(), Some(1.0));
    visit_2.insert("heart_disease".to_string(), Some(0.0));
    visit_2.insert("physical_activity".to_string(), Some(0.0));
    visit_2.insert("general_health".to_string(), Some(4.0));
    visit_2.insert("gender".to_string(), Some(1.0));
    visit_2.insert("age".to_string(), Some(51.0));

    let mut visit_3 = HashMap::new();
    visit_3.insert("hypertension".to_string(), Some(1.0));
    visit_3.insert("high_chol".to_string(), Some(1.0));
    visit_3.insert("bmi".to_string(), Some(35.0));
    visit_3.insert("smoking_history".to_string(), Some(1.0));
    visit_3.insert("heart_disease".to_string(), Some(1.0));
    visit_3.insert("physical_activity".to_string(), Some(0.0));
    visit_3.insert("general_health".to_string(), Some(5.0));
    visit_3.insert("gender".to_string(), Some(1.0));
    visit_3.insert("age".to_string(), Some(52.0));

    let res = predict_longitudinal("diabetes", &[visit_1, visit_2, visit_3])
        .expect("Longitudinal prediction failed");

    assert_eq!(res.num_visits, 3);
    assert_eq!(res.trend, "WORSENING");
    assert_eq!(res.visit_attention.len(), 3);
    assert!(res.visit_attention[2].weight > res.visit_attention[1].weight);
    assert!(res.visit_attention[1].weight > res.visit_attention[0].weight);
    assert_eq!(res.risk_label, "VERY HIGH");
}

#[test]
fn test_longitudinal_prediction_invariant_features_low_risk() {
    let mut visit_1 = HashMap::new();
    visit_1.insert("hypertension".to_string(), Some(0.0));
    visit_1.insert("high_chol".to_string(), Some(0.0));
    visit_1.insert("bmi".to_string(), Some(22.0));
    visit_1.insert("smoking_history".to_string(), Some(0.0));
    visit_1.insert("heart_disease".to_string(), Some(0.0));
    visit_1.insert("physical_activity".to_string(), Some(1.0));
    visit_1.insert("general_health".to_string(), Some(1.0));
    visit_1.insert("gender".to_string(), Some(0.0));
    visit_1.insert("age".to_string(), Some(30.0));

    let visit_2 = visit_1.clone();

    let res = predict_longitudinal("diabetes", &[visit_1, visit_2])
        .expect("Longitudinal prediction with invariant visits failed");

    assert_eq!(res.num_visits, 2);
    assert_eq!(res.trend, "STABLE");
    assert_eq!(res.risk_label, "LOW");
    assert!(res.risk_probability <= 0.20);
}

