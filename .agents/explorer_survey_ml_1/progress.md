# Progress — ML & ONNX Inference Explorer

Last visited: 2026-08-21T05:15:00Z

## Status
Starting investigation of ML models, ONNX files, scalers, and Rust ONNX runtime architecture.

## Checklist
- [x] Initialized BRIEFING.md & progress.md
- [ ] Scan repository for all ML models (.onnx, .pkl, .joblib, etc.) and prediction code
- [ ] Inspect backend/prediction.py, backend/core_ai.py, backend/routes/prediction.py, backend/routes/longitudinal_prediction.py
- [ ] Document Diabetes model: features, order, types, scaler params, tensor shapes, post-processing
- [ ] Document Heart Disease model: features, order, types, scaler params, tensor shapes, post-processing
- [ ] Document Kidney Disease model: features, order, types, scaler params, tensor shapes, post-processing
- [ ] Document Liver Disease model: features, order, types, scaler params, tensor shapes, post-processing
- [ ] Document Lung Disease model: features, order, types, scaler params, tensor shapes, post-processing
- [ ] Document Stroke Risk & Longitudinal Prediction models / fallback logic
- [ ] Document native Rust ort inference architecture and scaler implementation
- [ ] Write ml_survey.md and handoff.md
- [ ] Send completion message to parent
