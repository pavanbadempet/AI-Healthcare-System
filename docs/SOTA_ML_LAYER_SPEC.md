# SOTA Accelerated ML Inference & Drift Specification

This document specifies the ONNX Runtime compilation, Platt scaling probability calibration, SHAP explanations, and data drift detection standards.

```
┌─────────────────────────────────────────────────────────────┐
│          ONNX Runtime Sub-Millisecond Inference Engine      │
│  - Quantized ONNX model graph execution                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Platt Calibration & SHAP Feature Attributions     │
│  - Platt probability scaling + local SHAP feature scores    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Key ML Layer Standards

1. **Sub-Millisecond ONNX Inference (`predict_readmission_risk`)**:
   - Executes quantized ONNX model graphs for sub-millisecond clinical risk scoring.
2. **Platt Scaling Probability Calibration (`calibrate_probability`)**:
   - Calibrates raw neural net / GBDT scores into mathematically true posterior probabilities.
3. **Statistical Feature Data Drift Detection (`detect_feature_drift`)**:
   - Detects covariate shift ($P(X)$ drift) continuously to trigger automated model retraining pipelines.
