## 2026-08-21T05:33:30Z

### Milestone 2: Native Rust ONNX Runtime ML Inference Engine & Preprocessing Scalers (Replacement Worker)
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\sub_orch_m2_2
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md
**Project Spec**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\PROJECT.md
**ML Survey Specification**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_ml_2\ml_survey.md

**Objective**:
Implement the native Rust ONNX runtime ML inference engine in `rust_gateway/` using the `ort` crate, loading existing `.onnx` models for Diabetes, Heart Disease, Kidney, Liver, Lungs, and Stroke, with native Rust static vector preprocessing scalers and clinical risk calculators (zero Python dependency, <1e-6 error tolerance).

**Instructions**:
1. Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `ml_survey.md`.
2. Update `rust_gateway/Cargo.toml` with `ort = { version = "2.0.0-rc.9", features = ["load-dynamic", "ndarray"] }` (or compatible version), `ndarray = "0.16"`.
3. Implement `rust_gateway/src/ml/`:
   - `scalers.rs`: Native static const arrays and $(X - \text{offset}) \times \text{scale}$ affine transformation functions for Kidney (24 features), Liver (10 features with `log1p` on indices `[2, 4, 5, 9]`), Lungs (15 features).
   - `engine.rs`: ONNX Runtime environment and session manager caching models (`backend/diabetes_model.onnx`, `backend/heart_disease_model.onnx`, `backend/kidney_model.onnx`, `backend/liver_disease_model.onnx`, `backend/lungs_model.onnx`, `backend/stroke_model.onnx`).
   - `predictors.rs`: Strongly typed prediction handlers for:
     - `predict_diabetes(features)` -> prediction, probability, risk_level, confidence
     - `predict_heart_disease(features)` -> prediction, probability (ZipMap extraction), risk_level
     - `predict_kidney_disease(features)` -> scaler + prediction + probability
     - `predict_liver_disease(features)` -> log1p + scaler + prediction + probability
     - `predict_lung_disease(features)` -> scaler + prediction + probability
     - `predict_stroke_risk(features)` -> prediction + probability
   - `longitudinal.rs`: Longitudinal feature extraction, temporal trend slope calculation, forward/backfill imputation, and temporal heuristic scoring across organs.
   - `calculators.rs`: Native eGFR (CKD-EPI 2021), FIB-4, and Framingham risk calculations.
   - `explain.rs`: Fast tree-attribution and counterfactual generation in pure Rust.
   - `mod.rs`: Module exports and high-level `InferenceManager` struct.
4. Verify exact numerical parity against Python / ONNX runtime sessions (<1e-6 tolerance).
5. Add unit tests in `rust_gateway/` verifying all models and scalers. Run `cargo check` and `cargo test`.
6. Write `handoff.md` and send completion message to parent when done.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-08-21T05:34:50Z
**Sender**: 74d136cc-39dd-45dd-af20-212b57727b1c
**Context**: Milestone 2 Native Rust ONNX ML Inference Engine implementation.
**Content**: Please resume and complete the implementation of Milestone 2 starting from updating `rust_gateway/Cargo.toml` and creating the `rust_gateway/src/ml/` modules per your checklist.
**Action**: Implement all ML modules, scalers, predictors, and calculators, run cargo check/test, and write handoff.md.
