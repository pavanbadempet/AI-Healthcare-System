# 📦 clinical-tabular — Healthcare Tabular & Temporal Deep Learning

[![PyPI version](https://badge.fury.io/py/clinical-tabular.svg)](https://pypi.org/project/clinical-tabular)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![sklearn compatible](https://img.shields.io/badge/sklearn-compatible-orange.svg)](https://scikit-learn.org)

> Production-ready, scikit-learn compatible tabular & temporal deep learning models, clinical risk calculators, and conformal prediction systems for clinical decision support.

---

## 🔬 Core Highlights

`clinical-tabular` provides high-fidelity, validated machine learning estimators and equations purpose-built for regulated medical environments. It brings state-of-the-art architectures (like FT-Transformer and temporal LSTMs with attention) directly into the familiar scikit-learn API ecosystem.

---

## ✨ Features Registry

| Module | What it does | Key Features |
|--------|-------------|:---|
| **`models.FTTransformerClassifier`** | Feature Tokenizer Transformer | Tabular attention-based classification, feature embeddings |
| **`models.ClinicalTemporalLSTM`** | Temporal Bidirectional LSTM | Handles sequence data, visits history, and outputs attention weights |
| **`models.PyTorchTabularMLP`** | Tabular Multilayer Perceptron | Dense model with BatchNorm, dropout, and residual pathways |
| **`indices`** | Clinical Calculators | Validated calculators: eGFR (CKD-EPI 2021), FIB-4, Framingham |
| **`calibration`** | Conformal Prediction | Calibrated uncertainty sets, risk coverage, medical triage routing |
| **`evaluation`** | Diagnostics & Validation | ROC-AUC, sensitivity/specificity optimization, confusion matrices |

---

## 🚀 Installation

```bash
# Core package (calculators, conformal prediction, and evaluation)
pip install clinical-tabular

# Include PyTorch Deep Learning models
pip install clinical-tabular[torch]

# Include evaluation & visualization tools (pandas, matplotlib)
pip install clinical-tabular[eval]

# Install all features and dependencies
pip install clinical-tabular[all]
```

---

## 📖 Code Reference & Quick Start

### 1. FT-Transformer for Tabular Risk Screening
```python
from clinical_tabular.models import FTTransformerClassifier
from sklearn.model_selection import cross_val_score

# Instantiate the estimator (fully scikit-learn compatible)
model = FTTransformerClassifier(
    d_embedding=32,
    depth=3,
    n_heads=4,
    epochs=20,
    batch_size=256,
)

# Use inside standard scikit-learn workflows
scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
print(f"Mean CV AUC-ROC: {scores.mean():.4f}")

# Fit and extract probabilities
model.fit(X_train, y_train)
probabilities = model.predict_proba(X_test)
```

### 2. Clinical Temporal LSTM for Longitudinal EHR Records
```python
from clinical_tabular.models import ClinicalTemporalLSTM

# Input Shape: (n_patients, n_visits, n_features)
# Fits temporal parameters over sequences of patient encounters
lstm = ClinicalTemporalLSTM(
    hidden_dim=64,
    num_layers=2,
    epochs=15,
    patience=5
)
lstm.fit(X_sequences, y_labels)

# Predict patient risk alongside visit-specific attention weights
risks, attention_weights = lstm.predict_with_attention(X_test)
# attention_weights[i] maps which historical visits most drove patient i's risk score
```

### 3. Validated Clinical Calculators
```python
from clinical_tabular.indices import (
    calculate_egfr_ckd_epi,
    calculate_fib4_index,
    calculate_framingham_risk,
)

# eGFR (2021 Race-Free CKD-EPI Creatinine Equation)
egfr_res = calculate_egfr_ckd_epi(age=62, gender=1, creatinine=1.3)
# Returns: {'egfr': 57.4, 'stage': 'Stage G3a', 'description': 'Mildly to moderately decreased'}

# FIB-4 Index (Non-invasive liver fibrosis screening)
fib4_res = calculate_fib4_index(age=48, ast=55, alt=42, platelets=180)
# Returns: {'score': 2.34, 'risk_level': 'Indeterminate Risk'}

# Framingham 10-Year Cardiovascular Risk Score
cvd_res = calculate_framingham_risk(
    age=55, gender=1, total_chol=220, hdl_chol=45,
    sbp=135, smoker=1, diabetes=0, hyp_treatment=1
)
# Returns: {'risk_percent': 21.4, 'risk_level': 'High Risk'}
```

### 4. Conformal Prediction (Calibrated Uncertainty Triage)
Provides a mathematical guarantee that the true clinical label lies within the returned prediction set with high probability (e.g., 95%).
```python
from clinical_tabular.calibration import (
    compute_conformal_threshold,
    conformal_prediction_set,
    get_triage_recommendation,
)

# 1. Calibrate on holdout calibration set
threshold = compute_conformal_threshold(y_calib, proba_calib[:, 1], alpha=0.05)

# 2. Generate calibrated prediction sets for test patients
result = conformal_prediction_set(proba_positive=0.88, conformal_q=threshold)
# Returns: {'conformal_prediction_set': [1], 'uncertainty_status': 'Low Uncertainty'}

# 3. Secure clinical triage routing
triage = get_triage_recommendation(prediction_val=1, conformal_set=result['conformal_prediction_set'])
# Returns: 'Urgent Action: Patient exhibits strong canonical markers...'
```

---

## 🛠️ Package Building & Distribution

To build the wheel and source distribution locally for packaging and publishing:

### 1. Set Up Development Environment
```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System/packages/clinical-tabular
pip install -e ".[all]"
```

### 2. Run Test Suite
```bash
pytest tests/ -v
```

### 3. Compile Wheels
```bash
pip install build
python -m build
```
This generates the package archives under the `dist/` directory, ready to be uploaded to PyPI using twine.

---

## ⚕️ Medical Disclaimer

This library provides clinical decision support tools. All calculations, predictions, and recommendations are intended for educational and research support purposes only. They must not replace professional clinical judgment, diagnosis, treatment, or emergency patient care.
