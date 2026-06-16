# clinical-tabular

[![PyPI version](https://badge.fury.io/py/clinical-tabular.svg)](https://badge.fury.io/py/clinical-tabular)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![sklearn compatible](https://img.shields.io/badge/sklearn-compatible-orange.svg)](https://scikit-learn.org)

**Production-ready tabular & temporal deep learning models for clinical decision support.**

`clinical-tabular` provides sklearn-compatible deep learning models purpose-built for healthcare tabular data, validated clinical risk calculators, conformal prediction for uncertainty quantification, and model evaluation utilities — all in a single, pip-installable package.

---

## ✨ Features

| Module | What it does |
|--------|-------------|
| **`models.FTTransformerClassifier`** | Feature Tokenizer Transformer — attention-based tabular classification |
| **`models.ClinicalTemporalLSTM`** | Bidirectional LSTM with temporal attention for longitudinal patient data |
| **`models.PyTorchTabularMLP`** | Simple but effective tabular MLP with BatchNorm and dropout |
| **`indices`** | Validated clinical risk calculators (eGFR CKD-EPI, FIB-4, Framingham) |
| **`calibration`** | Conformal prediction for calibrated uncertainty quantification |
| **`evaluation`** | Comprehensive model evaluation (AUC-ROC, sensitivity/specificity, feature importance) |

All models are **scikit-learn compatible** — they work with `Pipeline`, `GridSearchCV`, `cross_val_score`, and `VotingClassifier` out of the box.

---

## 🚀 Installation

```bash
# Core (indices, calibration, evaluation — no PyTorch required)
pip install clinical-tabular

# With PyTorch models
pip install clinical-tabular[torch]

# With evaluation extras (pandas, matplotlib)
pip install clinical-tabular[eval]

# Everything
pip install clinical-tabular[all]
```

---

## 📖 Quick Start

### FT-Transformer for Tabular Classification

```python
from clinical_tabular import FTTransformerClassifier
from sklearn.model_selection import cross_val_score

model = FTTransformerClassifier(
    d_embedding=32,
    depth=3,
    n_heads=4,
    epochs=20,
)

# Sklearn-compatible: works with cross-validation
scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
print(f"AUC-ROC: {scores.mean():.4f} ± {scores.std():.4f}")

# Fit and predict
model.fit(X_train, y_train)
proba = model.predict_proba(X_test)
```

### Longitudinal Patient Data with Temporal LSTM

```python
from clinical_tabular import ClinicalTemporalLSTM

# X shape: (n_patients, n_visits, n_features)
# Each patient has a sequence of clinical visits over time
lstm = ClinicalTemporalLSTM(hidden_dim=64, num_layers=2, patience=10)
lstm.fit(X_sequences, y_labels)

# Get predictions with interpretable attention weights
probs, attention_weights = lstm.predict_with_attention(X_test)
# attention_weights[i] shows which visits most influenced patient i's prediction
```

### Clinical Risk Calculators

```python
from clinical_tabular.indices import (
    calculate_egfr_ckd_epi,
    calculate_fib4_index,
    calculate_framingham_risk,
)

# eGFR (Kidney function) — 2021 CKD-EPI race-free equation
result = calculate_egfr_ckd_epi(age=65, gender=1, creatinine=1.2)
# {'egfr': 65.8, 'stage': 'Stage G2', 'description': 'Mildly decreased'}

# FIB-4 (Liver fibrosis)
result = calculate_fib4_index(age=50, ast=45, alt=30, platelets=200)
# {'score': 2.05, 'risk_level': 'Indeterminate Risk', ...}

# Framingham (10-year cardiovascular risk)
result = calculate_framingham_risk(
    age=55, gender=1, total_chol=240, hdl_chol=45,
    sbp=140, smoker=0, diabetes=0, hyp_treatment=1,
)
# {'risk_percent': 18.2, 'risk_level': 'Intermediate Risk', ...}
```

### Conformal Prediction (Uncertainty Quantification)

```python
from clinical_tabular.calibration import (
    compute_conformal_threshold,
    conformal_prediction_set,
    class_conditional_thresholds,
    get_triage_recommendation,
)

# Calibrate on holdout set
threshold = compute_conformal_threshold(y_cal, proba_cal[:, 1], alpha=0.05)

# Generate prediction sets for new patients
result = conformal_prediction_set(proba_positive=0.73, conformal_q=threshold)
# {'conformal_prediction_set': [1], 'uncertainty_status': 'Low Uncertainty', ...}

# Clinical triage guidance
triage = get_triage_recommendation(prediction_val=1, conformal_set=[1])
# 'Urgent Action: Patient exhibits strong canonical markers...'
```

### Model Evaluation

```python
from clinical_tabular.evaluation import evaluate_model

results = evaluate_model(model, X_test, y_test, feature_names, "diabetes")
# Returns: accuracy, AUC-ROC, sensitivity, specificity, confusion matrix,
#          feature importances, classification report
```

---

## 🏗️ Architecture

### FT-Transformer

```
Input (batch, n_features)
    │
    ▼
┌──────────────────────┐
│ Feature Tokenizer    │  ← Projects each feature into embedding space
│ (learned per-feature │
│  weights + biases)   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ [CLS] + Feature      │  ← Prepend learnable classification token
│ Token Sequence       │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Transformer Encoder  │  ← Pre-LN Multi-Head Attention × depth
│ (Self-Attention)     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ CLS → Linear(2)     │  ← Binary classification from CLS output
└──────────────────────┘
```

### Clinical Temporal LSTM

```
Input (batch, n_visits, n_features)
    │
    ▼
┌──────────────────────┐
│ Bidirectional LSTM   │  ← Forward + backward temporal dynamics
│ (2-layer, dropout)   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Temporal Attention   │  ← Bahdanau-style: learns which visits matter
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ LayerNorm + GELU     │  ← Classification with regularisation
│ → Linear(1)          │
└──────────────────────┘

Output: risk probability + per-visit attention weights
```

---

## 🔬 Use Cases

- **Hospital EHR integration** — Drop-in sklearn models for clinical decision support
- **Clinical trial analytics** — Temporal models for longitudinal patient outcomes
- **Risk stratification** — Validated clinical indices + ML ensemble predictions
- **Uncertainty-aware predictions** — Conformal prediction sets for regulatory compliance
- **Research** — Reproducible clinical ML baselines with standardised evaluation

---

## 📊 Comparison with Other Libraries

| Feature | clinical-tabular | tab-transformer-pytorch | pytorch-tabnet |
|---------|-----------------|------------------------|----------------|
| Sklearn compatible | ✅ | ❌ | ✅ |
| Longitudinal/temporal | ✅ | ❌ | ❌ |
| Clinical indices | ✅ | ❌ | ❌ |
| Conformal prediction | ✅ | ❌ | ❌ |
| Evaluation suite | ✅ | ❌ | ❌ |
| Pickle-safe | ✅ | N/A | ✅ |
| Healthcare-focused | ✅ | ❌ | ❌ |

---

## ⚕️ Medical Disclaimer

This library provides AI-assisted clinical decision support tools. **All outputs are intended for informational purposes only** and should not replace professional medical judgment. Always consult a qualified healthcare professional for diagnosis, treatment, or emergency care.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System/packages/clinical-tabular
pip install -e ".[all]"
pytest tests/ -v
```
