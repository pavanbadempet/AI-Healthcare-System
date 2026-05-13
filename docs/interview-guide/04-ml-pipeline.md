# 04 — Machine Learning Pipeline

## Q: Describe all 5 ML models.

| Model | Algorithm | Dataset | Records | Features | Accuracy | Key Challenge |
|---|---|---|---|---|---|---|
| Diabetes | XGBoost | BRFSS 2015 (CDC) | 253,680 | 9 | 71.7% | 86% class imbalance |
| Heart | XGBoost | BRFSS 2015 (mapped) | 253,680 | 13 | 73.9% | 90% class imbalance |
| Liver | Random Forest | ILPD (Indian) | 30,691 | 10 | ~72% | Skewed features |
| Kidney | SVM (RBF) | UCI CKD | 400 | 24 | ~93% | Small dataset, missing values |
| Lungs | SVM (RBF) | Lung Cancer Survey | 309 | 15 | ~88% | Very small dataset |

---

## Q: Why different algorithms for different diseases?

**XGBoost for Diabetes & Heart** (large datasets):
- 253K records — enough data for gradient boosting
- Tabular data with mixed feature types — XGBoost handles natively
- `scale_pos_weight` handles class imbalance without resampling
- Fast training (~3 seconds)

**SVM for Kidney & Lungs** (small datasets):
- Only 400 and 309 records — deep learning would overfit
- SVM finds optimal decision boundary even with limited data
- RBF kernel captures non-linear patterns
- StandardScaler required (SVM is distance-based)

**Random Forest for Liver** (medium dataset):
- 30K records — medium size
- Log transform needed for skewed enzyme values
- Random Forest handles non-linearity well
- Less prone to overfitting than single decision tree

---

## Q: Explain class imbalance and why it matters.

**The problem:**
In BRFSS diabetes data: 86% healthy, 14% diabetic.
In BRFSS heart data: 90% healthy, 10% have heart disease.

If a model just predicts "healthy" for everyone:
- Diabetes: 86% accuracy — looks great!
- Heart: 90% accuracy — looks amazing!
- But it detects **ZERO** sick patients — completely useless.

**The fix — `scale_pos_weight`:**
```python
neg_count = (Y_train == 0).sum()   # 174,595 healthy
pos_count = (Y_train == 1).sum()   # 28,349 diabetic
scale_weight = neg_count / pos_count  # 6.16

model = xgb.XGBClassifier(
    scale_pos_weight=scale_weight,  # Tell XGBoost: missing a diabetic 
    ...                              # is 6x worse than a false alarm
)
```

**Results:**

| Metric | Before (no balancing) | After (balanced) |
|---|---|---|
| Overall accuracy | 86.7% | 71.7% |
| Disease detection (sensitivity) | ~0% | ~60% |
| Useful for screening? | NO | YES |

**Why accuracy dropped but the model got BETTER:**
The old model just said "healthy" for everyone. The new model actually identifies at-risk patients, at the cost of some false positives. In medical screening, **false positives are safer than false negatives** — a false positive means the patient sees a doctor unnecessarily. A false negative means a sick patient goes undiagnosed.

---

## Q: Walk through the training pipeline step by step.

```python
# Example: train_diabetes.py

# 1. LOAD DATA
df = pd.read_parquet("data/processed/diabetes.parquet")
# 253,680 records from BRFSS 2015 CDC survey

# 2. COLUMN MAPPING (dataset-specific)
df = df.rename(columns=DIABETES_DATASET_MAP)
# HighBP → hypertension, HighChol → high_chol, etc.

# 3. FEATURE SELECTION
X = df[DIABETES_FEATURES]  # 9 features
Y = df["diabetes"]          # Target: 0=healthy, 1=prediabetic, 2=diabetic

# 4. TRAIN/TEST SPLIT
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# 5. CLASS BALANCING
neg = (Y_train == 0).sum()
pos = (Y_train == 1).sum() + (Y_train == 2).sum()
weight = neg / pos  # 6.16

# 6. MODEL TRAINING
model = xgb.XGBClassifier(
    n_estimators=200,        # 200 boosting rounds
    max_depth=6,             # Tree depth limit
    learning_rate=0.1,       # Step size
    scale_pos_weight=weight, # Class balancing
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train, Y_train)

# 7. EVALUATION
y_pred = model.predict(X_test)
accuracy = accuracy_score(Y_test, y_pred)  # 71.7%

# 8. SAVE MODEL
with open("diabetes_model.pkl", "wb") as f:
    pickle.dump(model, f)
```

---

## Q: What preprocessing does each model need?

### Diabetes
- Age → bucket (0-13 categories): `18-24=1, 25-29=2, ... 80+=13`
- Columns renamed from BRFSS to canonical names
- No scaling needed (XGBoost is tree-based)

### Heart
- BRFSS columns mapped to Cleveland schema:
  ```python
  # BRFSS column → Cleveland column name
  high_bp → cp, bmi → trestbps, high_chol → chol,
  smoker → fbs, gen_hlth → restecg, phys_activity → thalach,
  stroke → exang, diabetes → oldpeak, hvy_alcohol → slope
  ```
- No scaling needed (XGBoost)

### Liver
- **Log transform** on skewed features:
  ```python
  skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 
            'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
  for col in skewed:
      df[col] = np.log1p(df[col])  # log(1+x) to handle zeros
  ```
- **StandardScaler** on all features

### Kidney
- **StandardScaler** on all 24 features
- Missing value imputation during training

### Lungs
- **StandardScaler** on all 15 features
- Binary encoding (0/1, NOT 1/2 as in original survey)

---

## Q: How does predict_proba work and why is it important?

```python
# model.predict() → Binary: 0 or 1
prediction = model.predict([[features]])[0]  # Returns: 1

# model.predict_proba() → Probabilities per class
proba = model.predict_proba([[features]])[0]
# Returns: [0.058, 0.942]
# → 5.8% chance healthy, 94.2% chance disease
```

**Why it matters:**
- A prediction of "Disease" with 51% confidence is VERY different from 99% confidence
- Doctors need to know HOW SURE the model is
- Risk level thresholds:
  - <40% → Low risk (green) → "Probably fine, but monitor"
  - 40-75% → Moderate risk (amber) → "Worth investigating"
  - >75% → High risk (red) → "See a doctor soon"

---

## Q: How did you validate model correctness?

**Three levels:**

### Level 1: Train/Test Split (Standard)
```python
X_train, X_test = train_test_split(X, Y, test_size=0.2)
accuracy = accuracy_score(Y_test, model.predict(X_test))
```

### Level 2: Synthetic Test Cases
Manually created known healthy/unhealthy patterns:
```python
# Obviously healthy person
test("Young healthy", "Low Risk", {"hypertension":0, "bmi":22, "age":25, ...})

# Obviously sick person
test("Elderly risk", "High Risk", {"hypertension":1, "bmi":45, "age":75, ...})
```

### Level 3: Real Dataset Records (Most Important)
```python
# Pull ACTUAL records from training data with KNOWN labels
df = pd.read_parquet("data/processed/diabetes.parquet")

# Take 5 healthy + 5 diabetic records
for row in df[df["diabetes"]==0].head(5):
    test("BRFSS healthy", "Low Risk", row_to_api_payload(row))

for row in df[df["diabetes"]==1].head(5):
    test("BRFSS diabetic", "High Risk", row_to_api_payload(row))
```

**Results: 48 records tested, 37 correct (77%)**

---

## Q: What is the model loading strategy?

```python
# prediction.py
diabetes_model = None
heart_model = None
# ... etc

def initialize_models():
    """Called ONCE at startup via lifespan event"""
    global diabetes_model, heart_model, ...
    
    for filename in ['diabetes_model.pkl', 'heart_disease_model.pkl', ...]:
        path = os.path.join(BACKEND_DIR, filename)
        with open(path, 'rb') as f:
            model = pickle.load(f)
        # Assign to global variable
```

**Key decisions:**
- Models loaded into **RAM at startup** — prediction takes ~2ms
- NOT loaded per-request (would be ~200ms each time)
- If a model file is missing/corrupt → that endpoint returns 503, others still work
- Total model size: ~1.6MB (small enough for git)

---

## Q: Could you improve accuracy? How?

| Approach | Expected Improvement | Effort |
|---|---|---|
| Hyperparameter tuning (Optuna) | +3-5% | Medium |
| Feature engineering (interactions) | +2-4% | Medium |
| Ensemble (XGB + RF + LightGBM) | +3-7% | High |
| More data (full BRFSS 400K) | +1-3% | Low |
| Deep learning (TabNet) | +5-10% | High |
| SMOTE oversampling | +2-5% | Low |

**Why I didn't:**
77% on real records is already clinically useful for a **screening** tool. The purpose isn't to replace diagnosis — it's to flag at-risk patients for further evaluation. Over-engineering accuracy past 80% has diminishing returns for a portfolio project.
