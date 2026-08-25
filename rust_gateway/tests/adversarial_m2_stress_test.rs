use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::thread;

use rust_gateway_ffi::ml::calculators::{
    calculate_cha2ds2_vasc, calculate_egfr_ckd_epi, calculate_fib4_index,
    calculate_framingham_risk, calculate_meld_score, calculate_qsofa,
};
use rust_gateway_ffi::ml::explain::{
    calculate_conformal_metadata, generate_counterfactual_recourse,
};
use rust_gateway_ffi::ml::longitudinal::{
    assess_trend, predict_longitudinal, visits_to_matrix,
};
use rust_gateway_ffi::ml::predictors::{
    predict_diabetes, predict_heart_disease,
    predict_kidney_disease, predict_liver_disease, predict_lung_disease, predict_stroke_risk,
    DiabetesInput, HeartInput, KidneyInput, LiverInput, LungInput, StrokeInput,
};
use rust_gateway_ffi::ml::scalers::{
    preprocess_kidney, preprocess_liver, preprocess_lungs, scale_vector, KIDNEY_OFFSET,
    KIDNEY_SCALE, LIVER_OFFSET, LIVER_SCALE, LUNGS_OFFSET, LUNGS_SCALE,
};
use rust_gateway_ffi::ml::{InferenceManager, ModelSessions};

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
// 1. Scaler & Static Preprocessing Precision & Boundary Stress Tests
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_scalers_random_and_extreme_vectors() {
    // Test 250 randomized pseudo-random vectors for Kidney scaler
    let mut state: u64 = 0x123456789ABCDEF0;
    let mut lcg = || -> f32 {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((state >> 32) as u32 as f32) / (u32::MAX as f32) * 500.0 - 100.0
    };

    for _ in 0..250 {
        let mut raw_kidney = [0.0f32; 24];
        for i in 0..24 {
            raw_kidney[i] = lcg();
        }
        let scaled = preprocess_kidney(&raw_kidney);
        for i in 0..24 {
            let expected = (raw_kidney[i] - KIDNEY_OFFSET[i]) * KIDNEY_SCALE[i];
            let diff = (scaled[i] - expected).abs();
            assert!(
                diff < 1e-6,
                "Kidney scaler precision failure at index {}: got {}, expected {}, diff {}",
                i,
                scaled[i],
                expected,
                diff
            );
        }
    }

    // Test Liver scaler with log1p and negative values
    for _ in 0..250 {
        let mut raw_liver = [0.0f32; 10];
        for i in 0..10 {
            raw_liver[i] = lcg();
        }
        let scaled = preprocess_liver(&raw_liver);
        let mut transformed = raw_liver;
        transformed[2] = (1.0 + transformed[2].max(0.0)).ln();
        transformed[4] = (1.0 + transformed[4].max(0.0)).ln();
        transformed[5] = (1.0 + transformed[5].max(0.0)).ln();
        transformed[9] = (1.0 + transformed[9].max(0.0)).ln();
        let expected = scale_vector(&transformed, &LIVER_OFFSET, &LIVER_SCALE);

        for i in 0..10 {
            let diff = (scaled[i] - expected[i]).abs();
            assert!(
                diff < 1e-6,
                "Liver scaler precision failure at index {}: got {}, expected {}, diff {}",
                i,
                scaled[i],
                expected[i],
                diff
            );
        }
    }

    // Test Lungs scaler with extreme ranges
    for _ in 0..250 {
        let mut raw_lungs = [0.0f32; 15];
        for i in 0..15 {
            raw_lungs[i] = lcg();
        }
        let scaled = preprocess_lungs(&raw_lungs);
        for i in 0..15 {
            let expected = (raw_lungs[i] - LUNGS_OFFSET[i]) * LUNGS_SCALE[i];
            let diff = (scaled[i] - expected).abs();
            assert!(
                diff < 1e-6,
                "Lungs scaler precision failure at index {}: got {}, expected {}, diff {}",
                i,
                scaled[i],
                expected,
                diff
            );
        }
    }

    // Boundary vectors: All Zeros
    let zeros_k = [0.0f32; 24];
    let scaled_zeros_k = preprocess_kidney(&zeros_k);
    assert!(!scaled_zeros_k[0].is_nan() && !scaled_zeros_k[0].is_infinite());

    let zeros_l = [0.0f32; 10];
    let scaled_zeros_l = preprocess_liver(&zeros_l);
    assert!(!scaled_zeros_l[2].is_nan() && !scaled_zeros_l[2].is_infinite());

    let zeros_lu = [0.0f32; 15];
    let scaled_zeros_lu = preprocess_lungs(&zeros_lu);
    assert!(!scaled_zeros_lu[0].is_nan() && !scaled_zeros_lu[0].is_infinite());
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Comprehensive ONNX Inference Parity & Contract Verification across 100+ Vectors
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_100_vectors_all_six_models() {
    let model_dir = resolve_model_directory();
    let sessions = ModelSessions::load_from_dir(&model_dir)
        .expect("Failed to load ONNX model sessions");

    let mut state: u64 = 0xCAFEBABEDEADBEEF;
    let mut rng = || -> f32 {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((state >> 32) as u32 as f32) / (u32::MAX as f32)
    };

    for i in 0..120 {
        // 1. Diabetes
        let d_inp = DiabetesInput {
            hypertension: if rng() > 0.5 { 1.0 } else { 0.0 },
            high_chol: if rng() > 0.5 { 1.0 } else { 0.0 },
            bmi: 15.0 + rng() * 35.0,
            smoking_history: if rng() > 0.5 { 1.0 } else { 0.0 },
            heart_disease: if rng() > 0.8 { 1.0 } else { 0.0 },
            physical_activity: if rng() > 0.5 { 1.0 } else { 0.0 },
            general_health: 1.0 + (rng() * 4.0).round(),
            gender: if rng() > 0.5 { 1.0 } else { 0.0 },
            age: 18.0 + rng() * 70.0,
        };
        let d_res = predict_diabetes(&sessions, &d_inp)
            .unwrap_or_else(|e| panic!("Diabetes inference failure at iter {}: {:?}", i, e));
        assert!(d_res.raw == 0 || d_res.raw == 1);
        let d_prob = d_res.probability.unwrap();
        assert!((0.0..=1.0).contains(&d_prob));
        assert!(d_res.confidence.unwrap() >= 0.0 && d_res.confidence.unwrap() <= 100.0);
        assert!(["High", "Moderate", "Low"].contains(&d_res.risk_level.as_deref().unwrap()));
        assert!(d_res.conformal_interval.is_some());
        assert_eq!(d_res.feature_attributions.as_ref().unwrap().len(), 9);

        // 2. Heart Disease
        let h_inp = HeartInput {
            age: 25.0 + rng() * 60.0,
            sex: if rng() > 0.5 { 1.0 } else { 0.0 },
            cp: (rng() * 3.0).round(),
            trestbps: 90.0 + rng() * 100.0,
            chol: 120.0 + rng() * 200.0,
            fbs: if rng() > 0.7 { 1.0 } else { 0.0 },
            restecg: (rng() * 2.0).round(),
            thalach: 70.0 + rng() * 130.0,
            exang: if rng() > 0.5 { 1.0 } else { 0.0 },
            oldpeak: rng() * 6.0,
            slope: (rng() * 2.0).round(),
            ca: (rng() * 3.0).round(),
            thal: (rng() * 3.0).round(),
        };
        let h_res = predict_heart_disease(&sessions, &h_inp)
            .unwrap_or_else(|e| panic!("Heart inference failure at iter {}: {:?}", i, e));
        assert!(h_res.raw == 0 || h_res.raw == 1);
        assert!(h_res.framingham.is_some());
        assert_eq!(h_res.feature_attributions.as_ref().unwrap().len(), 13);

        // 3. Kidney Disease
        let k_inp = KidneyInput {
            age: 18.0 + rng() * 70.0,
            bp: 50.0 + rng() * 100.0,
            sg: 1.005 + rng() * 0.025,
            al: (rng() * 5.0).round(),
            su: (rng() * 5.0).round(),
            rbc: if rng() > 0.5 { 1.0 } else { 0.0 },
            pc: if rng() > 0.5 { 1.0 } else { 0.0 },
            pcc: if rng() > 0.8 { 1.0 } else { 0.0 },
            ba: if rng() > 0.8 { 1.0 } else { 0.0 },
            bgr: 70.0 + rng() * 250.0,
            bu: 10.0 + rng() * 100.0,
            sc: 0.4 + rng() * 6.0,
            sod: 110.0 + rng() * 40.0,
            pot: 2.5 + rng() * 5.0,
            hemo: 5.0 + rng() * 13.0,
            pcv: 15.0 + rng() * 40.0,
            wc: 3000.0 + rng() * 15000.0,
            rc: 2.0 + rng() * 5.0,
            htn: if rng() > 0.5 { 1.0 } else { 0.0 },
            dm: if rng() > 0.5 { 1.0 } else { 0.0 },
            cad: if rng() > 0.8 { 1.0 } else { 0.0 },
            appet: if rng() > 0.5 { 1.0 } else { 0.0 },
            pe: if rng() > 0.7 { 1.0 } else { 0.0 },
            ane: if rng() > 0.7 { 1.0 } else { 0.0 },
            is_female: Some(rng() > 0.5),
        };
        let k_res = predict_kidney_disease(&sessions, &k_inp)
            .unwrap_or_else(|e| panic!("Kidney inference failure at iter {}: {:?}", i, e));
        assert!(k_res.raw == 0 || k_res.raw == 1);
        assert!(k_res.egfr.is_some());
        assert_eq!(k_res.feature_attributions.as_ref().unwrap().len(), 24);

        // 4. Liver Disease
        let l_inp = LiverInput {
            age: 18.0 + rng() * 70.0,
            gender: if rng() > 0.5 { 1.0 } else { 0.0 },
            total_bilirubin: 0.1 + rng() * 10.0,
            direct_bilirubin: 0.05 + rng() * 5.0,
            alkaline_phosphotase: 50.0 + rng() * 500.0,
            alamine_aminotransferase: 10.0 + rng() * 200.0,
            aspartate_aminotransferase: 10.0 + rng() * 200.0,
            total_proteins: 3.0 + rng() * 6.0,
            albumin: 1.0 + rng() * 4.0,
            albumin_and_globulin_ratio: 0.3 + rng() * 2.0,
            platelets: Some(50.0 + rng() * 350.0),
        };
        let l_res = predict_liver_disease(&sessions, &l_inp)
            .unwrap_or_else(|e| panic!("Liver inference failure at iter {}: {:?}", i, e));
        assert!(l_res.raw == 0 || l_res.raw == 1);
        assert!(l_res.fib4.is_some());
        assert_eq!(l_res.feature_attributions.as_ref().unwrap().len(), 10);

        // 5. Lung Disease
        let lu_inp = LungInput {
            gender: if rng() > 0.5 { 1.0 } else { 0.0 },
            age: 20.0 + rng() * 70.0,
            smoking: if rng() > 0.5 { 2.0 } else { 1.0 },
            yellow_fingers: if rng() > 0.5 { 2.0 } else { 1.0 },
            anxiety: if rng() > 0.5 { 2.0 } else { 1.0 },
            peer_pressure: if rng() > 0.5 { 2.0 } else { 1.0 },
            chronic_disease: if rng() > 0.5 { 2.0 } else { 1.0 },
            fatigue: if rng() > 0.5 { 2.0 } else { 1.0 },
            allergy: if rng() > 0.5 { 2.0 } else { 1.0 },
            wheezing: if rng() > 0.5 { 2.0 } else { 1.0 },
            alcohol: if rng() > 0.5 { 2.0 } else { 1.0 },
            coughing: if rng() > 0.5 { 2.0 } else { 1.0 },
            shortness_of_breath: if rng() > 0.5 { 2.0 } else { 1.0 },
            swallowing_difficulty: if rng() > 0.5 { 2.0 } else { 1.0 },
            chest_pain: if rng() > 0.5 { 2.0 } else { 1.0 },
        };
        let lu_res = predict_lung_disease(&sessions, &lu_inp)
            .unwrap_or_else(|e| panic!("Lungs inference failure at iter {}: {:?}", i, e));
        assert!(lu_res.raw == 0 || lu_res.raw == 1);
        assert_eq!(lu_res.feature_attributions.as_ref().unwrap().len(), 15);

        // 6. Stroke Risk
        let s_inp = StrokeInput {
            gender: Some(if rng() > 0.5 { 1.0 } else { 0.0 }),
            age: Some(18.0 + rng() * 75.0),
            hypertension: Some(if rng() > 0.7 { 1.0 } else { 0.0 }),
            heart_disease: Some(if rng() > 0.8 { 1.0 } else { 0.0 }),
            smoking: Some(if rng() > 0.5 { 1.0 } else { 0.0 }),
            bmi: Some(16.0 + rng() * 30.0),
            glucose: Some(60.0 + rng() * 200.0),
        };
        let s_res = predict_stroke_risk(&sessions, &s_inp)
            .unwrap_or_else(|e| panic!("Stroke inference failure at iter {}: {:?}", i, e));
        assert!(s_res.raw == 0 || s_res.raw == 1);
        assert_eq!(s_res.feature_attributions.as_ref().unwrap().len(), 7);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. Extreme Boundary, Missing Values & Edge Case Robustness
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_boundary_conditions_and_zero_inputs() {
    let model_dir = resolve_model_directory();
    let sessions = ModelSessions::load_from_dir(&model_dir)
        .expect("Failed to load ONNX model sessions");

    // All zeros input to all models
    let d_zeros = DiabetesInput {
        hypertension: 0.0, high_chol: 0.0, bmi: 0.0, smoking_history: 0.0,
        heart_disease: 0.0, physical_activity: 0.0, general_health: 0.0,
        gender: 0.0, age: 0.0,
    };
    let d_res = predict_diabetes(&sessions, &d_zeros).expect("Diabetes all-zeros failed");
    assert_eq!(d_res.raw, 0);

    let h_zeros = HeartInput {
        age: 0.0, sex: 0.0, cp: 0.0, trestbps: 0.0, chol: 0.0,
        fbs: 0.0, restecg: 0.0, thalach: 0.0, exang: 0.0,
        oldpeak: 0.0, slope: 0.0, ca: 0.0, thal: 0.0,
    };
    let h_res = predict_heart_disease(&sessions, &h_zeros).expect("Heart all-zeros failed");
    assert!(h_res.raw == 0 || h_res.raw == 1);

    let k_zeros = KidneyInput {
        age: 0.0, bp: 0.0, sg: 0.0, al: 0.0, su: 0.0, rbc: 0.0, pc: 0.0,
        pcc: 0.0, ba: 0.0, bgr: 0.0, bu: 0.0, sc: 0.0, sod: 0.0, pot: 0.0,
        hemo: 0.0, pcv: 0.0, wc: 0.0, rc: 0.0, htn: 0.0, dm: 0.0, cad: 0.0,
        appet: 0.0, pe: 0.0, ane: 0.0, is_female: None,
    };
    let k_res = predict_kidney_disease(&sessions, &k_zeros).expect("Kidney all-zeros failed");
    assert!(k_res.raw == 0 || k_res.raw == 1);
    assert!(k_res.egfr.is_none()); // eGFR should safely return None on Cr=0.0

    let l_zeros = LiverInput {
        age: 0.0, gender: 0.0, total_bilirubin: 0.0, direct_bilirubin: 0.0,
        alkaline_phosphotase: 0.0, alamine_aminotransferase: 0.0,
        aspartate_aminotransferase: 0.0, total_proteins: 0.0,
        albumin: 0.0, albumin_and_globulin_ratio: 0.0, platelets: None,
    };
    let l_res = predict_liver_disease(&sessions, &l_zeros).expect("Liver all-zeros failed");
    assert!(l_res.raw == 0 || l_res.raw == 1);
    assert!(l_res.fib4.is_none()); // FIB-4 should safely return None on zero inputs

    let lu_zeros = LungInput {
        gender: 0.0, age: 0.0, smoking: 0.0, yellow_fingers: 0.0, anxiety: 0.0,
        peer_pressure: 0.0, chronic_disease: 0.0, fatigue: 0.0, allergy: 0.0,
        wheezing: 0.0, alcohol: 0.0, coughing: 0.0, shortness_of_breath: 0.0,
        swallowing_difficulty: 0.0, chest_pain: 0.0,
    };
    let lu_res = predict_lung_disease(&sessions, &lu_zeros).expect("Lungs all-zeros failed");
    assert!(lu_res.raw == 0 || lu_res.raw == 1);

    // Stroke with all None values (defaults tested)
    let s_none = StrokeInput {
        gender: None, age: None, hypertension: None, heart_disease: None,
        smoking: None, bmi: None, glucose: None,
    };
    let s_res = predict_stroke_risk(&sessions, &s_none).expect("Stroke all-None failed");
    assert!(s_res.raw == 0 || s_res.raw == 1);

    // Extreme high inputs (stress numerical limits)
    let d_extreme = DiabetesInput {
        hypertension: 1.0, high_chol: 1.0, bmi: 999.0, smoking_history: 1.0,
        heart_disease: 1.0, physical_activity: 0.0, general_health: 5.0,
        gender: 1.0, age: 150.0,
    };
    let d_ext_res = predict_diabetes(&sessions, &d_extreme).expect("Diabetes extreme failed");
    assert_eq!(d_ext_res.raw, 1);
    assert_eq!(d_ext_res.risk_level.as_deref(), Some("High"));
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. Multi-Threaded Concurrent Inference Stress Test
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_multi_threaded_concurrency_stress() {
    let model_dir = resolve_model_directory();
    let manager = Arc::new(InferenceManager::from_dir(model_dir).expect("Failed to init manager"));

    let num_threads = 24;
    let iterations_per_thread = 100;
    let mut handles = Vec::with_capacity(num_threads);

    for t_idx in 0..num_threads {
        let mgr = Arc::clone(&manager);
        let handle = thread::spawn(move || {
            let mut state: u64 = 0x1122334455667788 ^ (t_idx as u64);
            let mut rng = || -> f32 {
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                ((state >> 32) as u32 as f32) / (u32::MAX as f32)
            };

            for _ in 0..iterations_per_thread {
                // Diabetes
                let d_inp = DiabetesInput {
                    hypertension: if rng() > 0.5 { 1.0 } else { 0.0 },
                    high_chol: if rng() > 0.5 { 1.0 } else { 0.0 },
                    bmi: 20.0 + rng() * 20.0,
                    smoking_history: if rng() > 0.5 { 1.0 } else { 0.0 },
                    heart_disease: 0.0,
                    physical_activity: 1.0,
                    general_health: 2.0,
                    gender: 1.0,
                    age: 45.0,
                };
                let d_res = mgr.predict_diabetes(&d_inp).expect("Concurrent diabetes failed");
                assert!(d_res.raw == 0 || d_res.raw == 1);

                // Kidney
                let k_inp = KidneyInput {
                    age: 50.0, bp: 80.0, sg: 1.020, al: 0.0, su: 0.0, rbc: 0.0,
                    pc: 0.0, pcc: 0.0, ba: 0.0, bgr: 110.0, bu: 30.0, sc: 1.0,
                    sod: 138.0, pot: 4.2, hemo: 15.0, pcv: 45.0, wc: 7000.0,
                    rc: 5.0, htn: 0.0, dm: 0.0, cad: 0.0, appet: 0.0, pe: 0.0,
                    ane: 0.0, is_female: Some(false),
                };
                let k_res = mgr.predict_kidney(&k_inp).expect("Concurrent kidney failed");
                assert!(k_res.raw == 0 || k_res.raw == 1);

                // Liver
                let l_inp = LiverInput {
                    age: 55.0, gender: 1.0, total_bilirubin: 0.8, direct_bilirubin: 0.2,
                    alkaline_phosphotase: 160.0, alamine_aminotransferase: 20.0,
                    aspartate_aminotransferase: 22.0, total_proteins: 7.0,
                    albumin: 3.5, albumin_and_globulin_ratio: 1.0,
                    platelets: Some(220.0),
                };
                let l_res = mgr.predict_liver(&l_inp).expect("Concurrent liver failed");
                assert!(l_res.raw == 0 || l_res.raw == 1);

                // Lungs
                let lu_inp = LungInput {
                    gender: 1.0, age: 60.0, smoking: 1.0, yellow_fingers: 1.0,
                    anxiety: 1.0, peer_pressure: 1.0, chronic_disease: 1.0,
                    fatigue: 1.0, allergy: 1.0, wheezing: 1.0, alcohol: 1.0,
                    coughing: 1.0, shortness_of_breath: 1.0,
                    swallowing_difficulty: 1.0, chest_pain: 1.0,
                };
                let lu_res = mgr.predict_lungs(&lu_inp).expect("Concurrent lungs failed");
                assert!(lu_res.raw == 0 || lu_res.raw == 1);
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().expect("Worker thread panicked during concurrent inference");
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Longitudinal Pipeline Missing Value Imputation & Trajectory Stress Tests
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_longitudinal_edge_cases() {
    // 1. Error on fewer than 2 visits
    let single_visit = vec![HashMap::new()];
    assert!(predict_longitudinal("diabetes", &single_visit).is_err());
    assert!(predict_longitudinal("diabetes", &[]).is_err());

    // 2. Error on invalid condition
    let v1 = HashMap::new();
    let v2 = HashMap::new();
    assert!(predict_longitudinal("unsupported_cancer_xyz", &[v1, v2]).is_err());

    // 3. Missing Value Imputation: forward-fill -> backward-fill -> zero-fill
    let mut visit_1 = HashMap::new();
    visit_1.insert("hypertension".to_string(), Some(1.0));
    visit_1.insert("bmi".to_string(), None); // forward-fill from nothing -> will backward-fill from visit 2

    let mut visit_2 = HashMap::new();
    visit_2.insert("hypertension".to_string(), None); // will forward-fill 1.0
    visit_2.insert("bmi".to_string(), Some(28.0));

    let feats = &["hypertension", "bmi", "high_chol"];
    let matrix = visits_to_matrix(&[visit_1, visit_2], feats);

    // hypertension: visit 1 = 1.0, visit 2 forward-filled = 1.0
    assert_eq!(matrix[0][0], 1.0);
    assert_eq!(matrix[1][0], 1.0);

    // bmi: visit 1 backward-filled = 28.0, visit 2 = 28.0
    assert_eq!(matrix[0][1], 28.0);
    assert_eq!(matrix[1][1], 28.0);

    // high_chol: not provided in any visit -> zero filled
    assert_eq!(matrix[0][2], 0.0);
    assert_eq!(matrix[1][2], 0.0);

    // 4. Trajectory Assessment: Improving vs Worsening vs Stable
    let improving_matrix = vec![
        vec![50.0, 50.0],
        vec![40.0, 40.0],
        vec![30.0, 30.0],
    ];
    assert_eq!(assess_trend(&improving_matrix), "IMPROVING");

    let worsening_matrix = vec![
        vec![20.0, 20.0],
        vec![30.0, 30.0],
        vec![40.0, 40.0],
    ];
    assert_eq!(assess_trend(&worsening_matrix), "WORSENING");

    let flat_matrix = vec![
        vec![25.0, 25.0],
        vec![25.0, 25.0],
        vec![25.0, 25.0],
    ];
    assert_eq!(assess_trend(&flat_matrix), "STABLE");

    // 5. 10-visit sequence stress test
    let mut sequence = Vec::new();
    for i in 0..10 {
        let mut v = HashMap::new();
        v.insert("age".to_string(), Some(50.0 + (i as f64)));
        v.insert("bmi".to_string(), Some(24.0 + (i as f64) * 0.5));
        v.insert("hypertension".to_string(), Some(if i > 5 { 1.0 } else { 0.0 }));
        v.insert("high_chol".to_string(), Some(0.0));
        v.insert("smoking_history".to_string(), Some(0.0));
        v.insert("heart_disease".to_string(), Some(0.0));
        v.insert("physical_activity".to_string(), Some(1.0));
        v.insert("general_health".to_string(), Some(2.0));
        v.insert("gender".to_string(), Some(1.0));
        sequence.push(v);
    }

    let resp = predict_longitudinal("diabetes", &sequence).unwrap();
    assert_eq!(resp.num_visits, 10);
    assert_eq!(resp.visit_attention.len(), 10);
    // Verify attention weights strictly increase
    for i in 1..10 {
        assert!(resp.visit_attention[i].weight > resp.visit_attention[i - 1].weight);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. Clinical Risk Calculators Edge Cases & Guidelines Verification
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_clinical_calculators_boundaries() {
    // 1. eGFR CKD-EPI 2021 race-free
    assert!(calculate_egfr_ckd_epi(0.0, 50.0, true).is_none());
    assert!(calculate_egfr_ckd_epi(-1.0, 50.0, false).is_none());
    assert!(calculate_egfr_ckd_epi(1.0, 17.0, true).is_none()); // pediatric age < 18 excluded

    let female_young = calculate_egfr_ckd_epi(0.7, 25.0, true).unwrap();
    assert_eq!(female_young.stage, "Stage G1");
    assert!(female_young.egfr >= 90.0);

    let severe_ckd = calculate_egfr_ckd_epi(6.0, 75.0, false).unwrap();
    assert_eq!(severe_ckd.stage, "Stage G5");
    assert!(severe_ckd.egfr < 15.0);

    // 2. FIB-4 Liver Fibrosis Index
    assert!(calculate_fib4_index(0.0, 30.0, 30.0, 200.0).is_none());
    assert!(calculate_fib4_index(50.0, 0.0, 30.0, 200.0).is_none());
    assert!(calculate_fib4_index(50.0, 30.0, 0.0, 200.0).is_none());
    assert!(calculate_fib4_index(50.0, 30.0, 30.0, 0.0).is_none());

    let low_fib4 = calculate_fib4_index(40.0, 20.0, 25.0, 280.0).unwrap();
    assert_eq!(low_fib4.risk_level, "Low Risk");

    let high_fib4 = calculate_fib4_index(60.0, 150.0, 50.0, 90.0).unwrap();
    assert_eq!(high_fib4.risk_level, "High Risk");

    // Age >= 65 threshold shift (2.0 vs 1.3)
    let senior_low = calculate_fib4_index(68.0, 30.0, 35.0, 200.0).unwrap();
    if senior_low.score < 2.00 {
        assert_eq!(senior_low.risk_level, "Low Risk");
    }

    // 3. Framingham 10-year CVD
    assert!(calculate_framingham_risk(0.0, false, 200.0, 50.0, 120.0, false, false, false).is_none());
    assert!(calculate_framingham_risk(50.0, false, 0.0, 50.0, 120.0, false, false, false).is_none());

    let low_cvd = calculate_framingham_risk(35.0, true, 160.0, 60.0, 110.0, false, false, false).unwrap();
    assert!(low_cvd.risk_percent < 5.0);

    let high_cvd = calculate_framingham_risk(70.0, false, 280.0, 35.0, 170.0, true, true, true).unwrap();
    assert!(high_cvd.risk_percent > 20.0);
    assert_eq!(high_cvd.risk_level, "High Risk");

    // 4. qSOFA
    let q0 = calculate_qsofa(18.0, 120.0, 15.0);
    assert_eq!(q0.score, 0);
    assert_eq!(q0.risk_level, "LOW_RISK");

    let q3 = calculate_qsofa(26.0, 85.0, 12.0);
    assert_eq!(q3.score, 3);
    assert_eq!(q3.risk_level, "HIGH_SEPSIS_RISK");

    // 5. CHA2DS2-VASc
    let cha_zero = calculate_cha2ds2_vasc(40.0, false, false, false, false, false, false);
    assert_eq!(cha_zero.score, 0);

    let cha_high = calculate_cha2ds2_vasc(78.0, true, true, true, true, true, true);
    assert!(cha_high.score >= 6);

    // 6. MELD score
    let meld_low = calculate_meld_score(0.8, 1.0, 0.9, false);
    assert!(meld_low.score < 10.0);
    assert_eq!(meld_low.risk_category, "Low (3-month mortality < 2%)");

    let meld_high = calculate_meld_score(4.0, 3.5, 3.0, true);
    assert!(meld_high.score >= 30.0);
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. Explainability, Conformal Sets & Recourse Stress Tests
// ─────────────────────────────────────────────────────────────────────────────

#[test]
fn test_adversarial_explainability_and_conformal() {
    // Extreme confidence conformal sets
    let p_0 = calculate_conformal_metadata(0.0, 0, None);
    assert_eq!(p_0.conformal_prediction_set, vec![0]);
    assert_eq!(p_0.uncertainty_level, "Low Uncertainty");

    let p_1 = calculate_conformal_metadata(1.0, 1, None);
    assert_eq!(p_1.conformal_prediction_set, vec![1]);
    assert_eq!(p_1.uncertainty_level, "Low Uncertainty");

    // Ambiguous borderline case (p = 0.50)
    let p_border = calculate_conformal_metadata(0.50, 1, Some(0.85));
    assert!(p_border.conformal_prediction_set.contains(&0) && p_border.conformal_prediction_set.contains(&1));
    assert_eq!(p_border.uncertainty_level, "High Uncertainty (Ambiguous Case)");

    // Counterfactual recourse with extreme values
    let feats = vec![
        "trestbps".to_string(),
        "chol".to_string(),
        "glucose".to_string(),
        "bmi".to_string(),
        "smoking".to_string(),
    ];
    let vals = vec![180.0, 320.0, 210.0, 42.0, 1.0];
    let recourse = generate_counterfactual_recourse(&feats, &vals, 0.95);
    assert_eq!(recourse.actionable_recommendations.len(), 5);
    assert!(recourse.target_achievable_risk <= 0.65);

    // Empty features fallback
    let empty_rec = generate_counterfactual_recourse(&[], &[], 0.30);
    assert!(!empty_rec.actionable_recommendations.is_empty());
}
