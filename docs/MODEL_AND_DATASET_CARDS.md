# Model Cards — AI Healthcare Clinical Prediction Models

Model cards following the [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) standard (Mitchell et al., 2019). Each card documents the model's intended use, training data, evaluation metrics, known limitations, and ethical considerations.

> [!CAUTION]
> **Medical Disclaimer:** These models are screening aids, not diagnostic tools. They do not replace clinical judgment. All predictions must be reviewed by a qualified healthcare professional before any clinical decision. Do not use these models for emergency triage, definitive diagnosis, or treatment selection.

---

## Summary Table

| Model | Task | Algorithm | Features | Dataset | AUC-ROC | Sensitivity | Specificity |
|-------|------|-----------|----------|---------|---------|-------------|-------------|
| **Diabetes** | Binary screening | XGBoost (300 trees) | 9 | BRFSS 2015 (CDC) | See `eval_diabetes.json` | See artifact | See artifact |
| **Heart Disease** | Binary screening | XGBoost (300 trees) | 13 | BRFSS 2015 / Cleveland | See `eval_heart.json` | See artifact | See artifact |
| **Liver Disease** | Binary screening | XGBoost (200 trees) | 10 | ILPD (UCI) | See `eval_liver.json` | See artifact | See artifact |
| **Kidney Disease** | Binary screening | XGBoost (150 trees) | 24 | CKD (UCI) | See `eval_kidney.json` | See artifact | See artifact |
| **Lung Health** | Binary screening | XGBoost (150 trees) | 15 | Lung Cancer Survey | See `eval_lungs.json` | See artifact | See artifact |

> **Note:** Exact metric values are written to `backend/ml/eval_<model>.json` by the training scripts. Run `python -m backend.ml.train_diabetes` (or any training script) to regenerate artifacts with current data.

---

## 1. Diabetes Risk Screening

**File:** [`backend/train_diabetes.py`](../backend/train_diabetes.py) | **Artifact:** [`backend/diabetes_model.pkl`](../backend/diabetes_model.pkl)

### Intended Use
Population-level diabetes risk screening. Flags individuals who may benefit from further clinical evaluation (HbA1c test, fasting glucose). Not intended for diagnosis of Type 1, Type 2, or gestational diabetes.

### Training Data
- **Source:** CDC Behavioral Risk Factor Surveillance System (BRFSS) 2015
- **Size:** ~250,000 records (after preprocessing)
- **Features (9):** hypertension, high_chol, bmi, smoking_history, heart_disease, physical_activity, general_health, gender, age_bucket
- **Target:** Binary (0 = no diabetes, 1 = diabetes/prediabetes)
- **Class imbalance:** ~86% negative, ~14% positive — addressed via `scale_pos_weight`

### Architecture
- XGBoost gradient-boosted classifier
- 300 estimators, max_depth=6, learning_rate=0.05
- L1 regularization (alpha=0.1), L2 regularization (lambda=1.0)
- Subsampling: 80% rows, 80% columns per tree

### Evaluation Protocol
- 80/20 stratified train/test split (random_state=42)
- Metrics: Accuracy, AUC-ROC, sensitivity, specificity, confusion matrix
- Feature importance via `feature_importances_` (gain-based)
- SHAP explanations available via [`backend/ml/explainability.py`](../backend/ml/explainability.py)

### Known Limitations
- BRFSS is self-reported survey data — BMI, smoking, physical activity are subject to recall bias
- Binary target conflates prediabetes and diabetes
- No longitudinal validation (single-timepoint cross-sectional data)
- US population only — may not generalize to other demographics
- Does not incorporate lab values (HbA1c, fasting glucose) which are the clinical gold standard

### Ethical Considerations
- Age and gender are used as features — model may exhibit demographic disparities
- High sensitivity is prioritized over specificity (better to over-refer than miss a case)
- Model should never be the sole basis for clinical decisions

---

## 2. Heart Disease Screening

**File:** [`backend/train_heart.py`](../backend/train_heart.py) | **Artifact:** [`backend/heart_disease_model.pkl`](../backend/heart_disease_model.pkl)

### Intended Use
Heart disease risk screening using either Cleveland clinical features or BRFSS survey features (with column mapping). Flags individuals for further cardiac evaluation.

### Training Data
- **Primary:** BRFSS 2015 heart disease indicators (11 features, mapped to Cleveland schema)
- **Fallback:** Cleveland Heart Disease dataset (UCI, 303 records, 13 features)
- **Synthetic fallback:** Generated Cleveland-schema data if neither real dataset is available
- **Features (13):** age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
- **Class imbalance:** ~9.4% positive in BRFSS — addressed via `scale_pos_weight`

### Architecture
- XGBoost gradient-boosted classifier
- 300 estimators, max_depth=5, learning_rate=0.05
- Same regularization and subsampling as diabetes model

### Known Limitations
- BRFSS-to-Cleveland column mapping is a semantic approximation (e.g., `high_bp` → `cp`)
- Cleveland dataset is small (303 records) — overfitting risk if used directly
- Two features (`ca`, `thal`) are zero-filled when training on BRFSS data
- Does not use ECG waveform data, troponin levels, or imaging

---

## 3. Liver Disease Screening

**File:** [`backend/train_liver.py`](../backend/train_liver.py) | **Artifact:** [`backend/liver_disease_model.pkl`](../backend/liver_disease_model.pkl)

### Intended Use
Liver disease screening from routine blood panel results. Identifies patients who may benefit from hepatology referral.

### Training Data
- **Source:** Indian Liver Patient Dataset (ILPD, UCI Machine Learning Repository)
- **Size:** 583 records
- **Features (10):** Age, Gender, Total_Bilirubin, Direct_Bilirubin, Alkaline_Phosphotase, Alamine_Aminotransferase, Aspartate_Aminotransferase, Total_Proteins, Albumin, Albumin_and_Globulin_Ratio
- **Preprocessing:** Log1p transform on skewed features, RobustScaler normalization
- **Class imbalance:** Addressed via SMOTE-like upsampling of minority class (train set only)

### Architecture
- XGBoost, 200 estimators, max_depth=4, learning_rate=0.03
- Train/test split performed BEFORE upsampling (prevents data leakage)

### Known Limitations
- Very small dataset (583 records) — high variance in evaluation metrics
- Single-center Indian population — demographic generalization uncertain
- Does not include imaging (ultrasound, FibroScan) or viral hepatitis markers

---

## 4. Kidney Disease Screening

**File:** [`backend/train_kidney.py`](../backend/train_kidney.py) | **Artifact:** [`backend/kidney_model.pkl`](../backend/kidney_model.pkl)

### Intended Use
Chronic kidney disease (CKD) screening from laboratory and clinical indicators. Flags patients for nephrology evaluation and eGFR monitoring.

### Training Data
- **Source:** CKD Dataset (UCI Machine Learning Repository)
- **Size:** 400 records
- **Features (24):** age, bp, sg, al, su, rbc, pc, pcc, ba, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm, cad, appet, pe, ane
- **Preprocessing:** StandardScaler normalization

### Architecture
- XGBoost, 150 estimators, max_depth=4, learning_rate=0.05

### Known Limitations
- Very small dataset (400 records)
- 24 features for 400 samples risks overfitting (feature-to-sample ratio concern)
- Does not stage CKD (1–5) — binary classification only
- Missing value handling not documented in training script

---

## 5. Lung Health Screening

**File:** [`backend/train_lungs.py`](../backend/train_lungs.py) | **Artifact:** [`backend/lungs_model.pkl`](../backend/lungs_model.pkl)

### Intended Use
Lung cancer risk screening from symptom and lifestyle survey data. Flags individuals for chest imaging or pulmonary function testing.

### Training Data
- **Source:** Lung Cancer Survey dataset
- **Size:** ~309 records
- **Features (15):** GENDER, AGE, SMOKING, YELLOW_FINGERS, ANXIETY, PEER_PRESSURE, CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING, ALCOHOL_CONSUMING, COUGHING, SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN
- **Preprocessing:** StandardScaler normalization

### Architecture
- XGBoost, 150 estimators, max_depth=4, learning_rate=0.05

### Known Limitations
- Extremely small dataset (~309 records) — evaluation metrics have high variance
- Survey-based features (self-reported symptoms) are less reliable than imaging or biopsy
- Binary classification — does not distinguish lung cancer subtypes (NSCLC vs SCLC)
- Does not incorporate LDCT imaging, tumor markers, or spirometry

---

## Cross-Cutting Design Decisions

### Why XGBoost for All 5 Models?

See [ADR-015: XGBoost for Tabular Clinical Prediction](architecture-decisions.md#adr-015-xgboost-for-tabular-clinical-prediction) for the full trade-off analysis. Summary:

- Tabular clinical data with <30 features and <250K samples is the sweet spot for gradient-boosted trees
- XGBoost consistently outperforms neural networks on tabular data in this regime (Grinsztajn et al., 2022)
- Built-in `feature_importances_` supports model explainability (required for clinical trust)
- `scale_pos_weight` handles class imbalance without external resampling
- Serializes to small `.pkl` files — no GPU required for inference

### Explainability

All 5 models support SHAP (SHapley Additive exPlanations) feature attribution via [`backend/ml/explainability.py`](../backend/ml/explainability.py). SHAP values explain which features drove each individual prediction, critical for clinical trust.

### Evaluation Artifact Generation

Each training script calls `evaluate_and_save()` from [`backend/ml/evaluation.py`](../backend/ml/evaluation.py), which writes a JSON artifact (`backend/ml/eval_<model>.json`) containing:
- AUC-ROC score
- Sensitivity and specificity (at default threshold)
- Full classification report (precision, recall, F1 per class)
- Confusion matrix
- Feature importance ranking

To regenerate all evaluation artifacts:
```bash
python -m backend.train_diabetes
python -m backend.train_heart
python -m backend.train_kidney
python -m backend.train_liver
python -m backend.train_lungs
```

---

## Fairness & Limitations Acknowledgment

- **No external clinical validation:** These models have not been validated in a clinical trial or against an external patient cohort
- **No FDA clearance:** These models are not FDA-cleared or CE-marked medical devices
- **Demographic bias risk:** Training data demographics may not represent the target patient population
- **Small datasets:** 3 of 5 models are trained on <600 records — insufficient for reliable generalization claims
- **No longitudinal validation:** All models are trained on cross-sectional data — temporal drift is not accounted for

---

*Model cards last updated: 2026-06-11. Regenerate evaluation artifacts by running the training scripts.*
