# Changelog

All notable changes to the AI Healthcare System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **clinical-tabular PyPI package** (`v0.1.0`) — Standalone, pip-installable library extracted from this project ([pypi.org/project/clinical-tabular](https://pypi.org/project/clinical-tabular/))
  - `FTTransformerClassifier` — sklearn-compatible Feature Tokenizer Transformer
  - `ClinicalTemporalLSTM` — Bidirectional LSTM with temporal attention for longitudinal patient data
  - `PyTorchTabularMLP` — Tabular MLP with BatchNorm and dropout
  - Clinical indices: eGFR (CKD-EPI 2021), FIB-4, Framingham risk
  - Conformal prediction utilities for calibrated uncertainty quantification
  - Model evaluation suite (AUC-ROC, sensitivity/specificity, feature importance)
- **Longitudinal prediction API** — 4 new endpoints (`/v1/predict/longitudinal/{diabetes,heart,liver,kidney}`) for temporal risk prediction from patient visit sequences
- **FT-Transformer ensemble integration** — 6-model hybrid voting classifier (XGBoost + LightGBM + CatBoost + RandomForest + PyTorch MLP + FT-Transformer)
- **TabPFN v2 integration** — Local foundation model for tabular data with API token management and graceful fallback
- GitHub Actions workflow for automated PyPI publishing on tag

### Changed
- Upgraded training pipelines (`train_diabetes.py`, `train_heart.py`, `train_liver.py`) to 6-model calibrated soft-voting ensemble
- All prediction endpoints now use class-conditional conformal prediction thresholds

## [1.0.0] - 2025-12-01

### Added
- Full-stack AI Healthcare System with FastAPI backend and React 19 frontend
- 5 ML clinical prediction models (Diabetes, Heart, Liver, Kidney, Lung Cancer)
- LangGraph-powered AI medical assistant with multi-turn conversation
- SHAP-based explainability for all predictions
- Conformal prediction for uncertainty quantification
- Clinical indices (eGFR CKD-EPI, FIB-4, Framingham Risk Score)
- FHIR R4 interoperability endpoints
- Hospital operations modules (Pharmacy, Billing, Discharge, Nursing, Diagnostics)
- Real-time monitoring and telemetry
- JWT authentication with role-based access control
- Docker + Kubernetes deployment configurations
- Comprehensive test suite (pytest + Vitest + Playwright)
- CI/CD with GitHub Actions (CodeQL, Dependabot, Release Drafter)
- 34-document technical documentation library
