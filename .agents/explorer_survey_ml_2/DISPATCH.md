## 2026-08-21T05:21:00Z

### Survey Task: ML Models, ONNX Runtime Inference & Scalers Survey (Replacement Explorer)
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_ml_2
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md

**Objective**:
Map all ML models, ONNX files, scalers, preprocessing pipelines, inference endpoints, and contracts across the system.

**Instructions**:
1. Read `ORIGINAL_REQUEST.md`.
2. Inspect `backend/prediction.py`, `backend/core_ai.py`, `backend/routes/prediction.py`, `backend/routes/longitudinal_prediction.py`, and any other prediction/ML code.
3. Locate and inspect all `.onnx` model files in `backend/` or `models/` (diabetes, heart disease, kidney disease, liver disease, lung disease, stroke risk, longitudinal models, etc.) and all associated scaler files (`*.pkl`, `*.joblib`, `*.json`, `*.onnx` scalers).
4. Extract the exact input feature lists, feature order, data types, scaler parameters (mean, std / min, max / quantiles), ONNX input/output node names, tensor shapes, and threshold/probability post-processing rules for each model:
   - Diabetes
   - Heart Disease
   - Kidney Disease
   - Liver Disease
   - Lung Disease
   - Stroke Risk
   - Longitudinal Prediction
5. Detail how `ort` (ONNX Runtime for Rust) should load and run these models in Axum/Tokio with native Rust preprocessing scalers to achieve zero Python dependency and 100% numerical parity (within 1e-6 tolerance).
6. Write your comprehensive survey report to `c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_ml_2\ml_survey.md` and a self-contained summary in `handoff.md`.
7. Send message to orchestrator when finished.
