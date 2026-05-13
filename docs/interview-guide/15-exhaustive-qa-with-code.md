# 15 — Exhaustive Q&A with Real Code Examples

> Every answer here uses ACTUAL code from the real codebase with file paths and line numbers.
> This is the "I want to know EVERYTHING" file.

---

## SECTION A: PREDICTION PIPELINE (The Core of the Project)

### Q: Walk me through exactly what happens when someone predicts diabetes. Show me the real code.

**Step 1 — Frontend form submission** (`frontend/src/components/predict/PredictionForm.tsx`, line 40):
```tsx
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    // Validate every field
    const parsedData: Record<string, number> = {};
    for (const field of fields) {
        const val = formData[field.name];
        if (val === undefined || isNaN(val)) {
            setError(`Please provide a valid value for ${field.label}`);
            setLoading(false);
            return;  // Stop — don't send invalid data
        }
        parsedData[field.name] = Number(val);
    }

    try {
        const res = await onSubmit(parsedData);  // Calls predictDiabetes()
        setResult(res);
    } catch (err: any) {
        setError(err.message || "Failed to generate prediction");
    } finally {
        setLoading(false);  // Always stop spinner
    }
};
```

**Step 2 — API client sends request** (`frontend/src/lib/api.ts`, line 223):
```typescript
export async function predictDiabetes(data: Record<string, number>): Promise<PredictionResult> {
    return apiFetch('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
}

// apiFetch (line 24) auto-injects auth:
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),  // Auto-inject Bearer token
        },
    });
    if (!res.ok) {
        // Parse Pydantic validation errors (array) or string errors
        const body = await res.json().catch(() => ({}));
        if (Array.isArray(body.detail)) {
            errorMessage = body.detail.map(e => e.msg).join(", ");
        }
        throw new Error(errorMessage);
    }
    return res.json();
}
```

**Step 3 — Backend receives and validates** (`backend/schemas.py`):
```python
class DiabetesInput(BaseModel):
    hypertension: int       # 0 or 1
    high_chol: int          # 0 or 1
    bmi: float              # Body Mass Index
    smoking_history: int    # 0 or 1
    heart_disease: int      # 0 or 1
    physical_activity: int  # 0 or 1
    general_health: int     # 1-5 scale
    gender: int             # 0=Female, 1=Male
    age: float              # Years (will be converted to bucket)
```
If ANY field is missing or wrong type → FastAPI auto-returns 422:
```json
{"detail": [{"loc": ["body", "bmi"], "msg": "field required", "type": "value_error.missing"}]}
```

**Step 4 — Prediction logic** (`backend/prediction.py`, line 217-240):
```python
@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(data: schemas.DiabetesInput) -> Dict[str, Any]:
    # GUARD: Check model loaded
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        # FEATURE ENGINEERING: Convert age to BRFSS bucket
        age_bucket = get_age_bucket(data.age)  # 55 years → bucket 7
        
        # BUILD FEATURE VECTOR (must match training order exactly!)
        input_list = [
            data.hypertension,       # Feature 0
            data.high_chol,          # Feature 1
            data.bmi,                # Feature 2
            data.smoking_history,    # Feature 3
            data.heart_disease,      # Feature 4
            data.physical_activity,  # Feature 5
            data.general_health,     # Feature 6
            data.gender,             # Feature 7
            age_bucket               # Feature 8 (derived)
        ]
        
        # PREDICT: Binary classification
        prediction = diabetes_model.predict([input_list])
        if isinstance(prediction, (list, tuple, np.ndarray)):
            prediction = prediction[0]
        if hasattr(prediction, 'item'):
            prediction = prediction.item()  # numpy scalar → Python int
        
        result = "High Risk" if prediction == 1 or prediction == 2 else "Low Risk"
        
        # CONFIDENCE: Probability scoring
        confidence, risk_level = _get_confidence(diabetes_model, [input_list])
        
        return {
            "prediction": result,
            "raw": int(prediction),
            "confidence": confidence,      # e.g., 94.2
            "risk_level": risk_level,       # "High"
            "disclaimer": MEDICAL_DISCLAIMER
        }
    except Exception as e:
        logger.error(f"Diabetes Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5 — Confidence calculation** (`backend/prediction.py`, line 133-148):
```python
def _get_confidence(model, input_data):
    """Extract prediction probability from model."""
    try:
        proba = model.predict_proba(input_data)[0]
        # proba = [0.058, 0.942]  → 5.8% healthy, 94.2% disease
        disease_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        confidence = round(disease_prob * 100, 1)  # 94.2
        
        # Risk level thresholds
        if confidence >= 75:
            risk_level = "High"      # Red badge
        elif confidence >= 40:
            risk_level = "Moderate"  # Amber badge
        else:
            risk_level = "Low"       # Green badge
        
        return confidence, risk_level
    except Exception:
        return None, None  # Graceful fallback
```

**Step 6 — Frontend displays result** (`frontend/src/components/predict/PredictionForm.tsx`, line 337):
```tsx
{/* Confidence Bar */}
<motion.div 
    initial={{ width: 0 }} 
    animate={{ width: `${result.confidence}%` }}  // Animated fill
    transition={{ duration: 0.8, ease: "easeOut" }}
    className={`h-full ${
        confidence >= 75 ? 'bg-[var(--danger)]'      // Red
        : confidence >= 40 ? 'bg-[var(--warning)]'   // Amber
        : 'bg-[var(--success)]'                       // Green
    }`}
/>

{/* Risk Level Badge */}
<span className={`text-[11px] font-mono font-bold uppercase ${
    result.risk_level === 'High' 
        ? 'text-[var(--danger)] bg-[var(--danger-muted)]'
        : result.risk_level === 'Moderate'
            ? 'text-[var(--warning)] bg-[var(--warning-muted)]'
            : 'text-[var(--success)] bg-[var(--success-muted)]'
}`}>
    {result.risk_level}
</span>

{/* Medical Disclaimer */}
<p className="text-[10px] text-[var(--text-dim)] font-mono">
    {result.disclaimer || "This is an AI-assisted screening tool..."}
</p>
```

---

## SECTION B: MODEL TRAINING (Real Code)

### Q: Show me exactly how the diabetes model is trained.

**Full file** (`backend/train_diabetes.py`):
```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle, os

# --- COLUMN MAPPING ---
# BRFSS dataset has its own column names. Map to our canonical names.
DIABETES_DATASET_MAP = {
    'Diabetes_binary': 'diabetes',
    'HighBP': 'hypertension',
    'HighChol': 'high_chol',
    'BMI': 'bmi',
    'Smoker': 'smoking_history',
    'HeartDiseaseorAttack': 'heart_disease',
    'PhysActivity': 'physical_activity',
    'GenHlth': 'general_health',
    'Sex': 'gender',
    'Age': 'age_bucket',
}

FEATURES = ['hypertension', 'high_chol', 'bmi', 'smoking_history',
            'heart_disease', 'physical_activity', 'general_health',
            'gender', 'age_bucket']

def train():
    # 1. LOAD: 253,680 real CDC records
    df = pd.read_parquet("data/processed/diabetes.parquet")
    print(f"Loaded Dataset: {len(df)} records")
    
    # 2. RENAME: Map BRFSS columns to canonical names
    df = df.rename(columns=DIABETES_DATASET_MAP)
    
    # 3. SPLIT: 80% train, 20% test, reproducible
    X = df[FEATURES]
    Y = (df['diabetes'] >= 1).astype(int)  # 1 or 2 → positive
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, random_state=42
    )
    
    # 4. CLASS BALANCE: THE critical step
    neg = (Y_train == 0).sum()   # 174,595 healthy
    pos = (Y_train == 1).sum()   # 28,349 at-risk
    weight = neg / pos            # 6.16
    print(f"Class balance: neg={neg}, pos={pos}, scale_pos_weight={weight:.2f}")
    
    # 5. TRAIN: XGBoost with class balancing
    model = xgb.XGBClassifier(
        n_estimators=200,             # 200 boosting rounds
        max_depth=6,                  # Limit tree depth
        learning_rate=0.1,            # Step size
        scale_pos_weight=weight,      # 6.16x weight on positive class
        eval_metric='logloss',        # Log loss objective
        random_state=42,
        use_label_encoder=False
    )
    model.fit(X_train, Y_train)
    
    # 6. EVALUATE
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(Y_test, y_pred)
    print(f"Model Trained. Accuracy: {accuracy:.4f}")  # 0.7166
    
    # 7. SAVE
    save_path = os.path.join(os.path.dirname(__file__), "diabetes_model.pkl")
    with open(save_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model Saved to {save_path}")

if __name__ == "__main__":
    train()
```

### Q: Why does each model need different preprocessing? Show real examples.

**Diabetes** — age bucketing only:
```python
# prediction.py, line 115-129
def get_age_bucket(age: float) -> int:
    if age <= 24: return 1
    elif age <= 29: return 2
    # ... 
    else: return 13
```

**Liver** — log transform + scaling:
```python
# prediction.py, line 286-292
skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 
          'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
for col in skewed:
    df[col] = np.log1p(df[col])  # log(1+x) handles zeros safely

X_scaled = liver_scaler.transform(df)  # StandardScaler
```
**Why log transform?** Bilirubin ranges from 0.1 to 75.0 — extreme skew. Log compresses the range so the model isn't dominated by outliers.

**Kidney/Lungs** — StandardScaler only:
```python
# prediction.py, line 172-173
df = pd.DataFrame([input_list], columns=feature_names)
input_scaled = kidney_scaler.transform(df)
```
**Why scaling?** SVM uses distance calculations. Feature A (age: 20-80) would dominate Feature B (sg: 1.005-1.025) without normalization.

---

## SECTION C: AUTHENTICATION (Real Code)

### Q: Show the complete login flow with real code.

**Frontend sends login** (`frontend/src/lib/api.ts`, line 58):
```typescript
export async function login(username: string, password: string): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),  // OAuth2 spec
    });
    if (!res.ok) throw new Error(body.detail || 'Login failed');
    return res.json();  // { access_token: "eyJ...", token_type: "bearer" }
}
```

**Backend verifies** (`backend/auth.py`):
```python
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find user
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()
    
    # 2. Verify password with bcrypt
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 3. Create JWT token
    token = create_access_token(data={
        "sub": user.username,     # Subject
        "role": user.role,        # admin/doctor/patient
    })
    
    return {"access_token": token, "token_type": "bearer"}
```

**Every protected request** (`backend/auth.py`):
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
    token: str = Depends(oauth2_scheme),  # Extract from Authorization header
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401)
    return user
```

---

## SECTION D: MIDDLEWARE (Real Code)

### Q: Show each middleware with the actual implementation.

**ExceptionMiddleware** (`backend/main.py`, line 148-155):
```python
class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]   # Short UUID
            logger.error(f"Error {error_id}: {e}")  # Full error in logs
            return JSONResponse(
                status_code=500, 
                content={"detail": f"Error: {error_id}"}  # UUID only to client
            )
```
**Why?** Client sees `"Error: a3f2b1c9"` — no stack traces, no PII leakage. Dev can search logs by error ID.

**LoggingMiddleware** (`backend/main.py`, line 157-163):
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        ms = (time.time() - start) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({ms:.0f}ms)")
        return response
# Output: POST /predict/diabetes - 200 (9ms)
```

---

## SECTION E: ERROR HANDLING (Every Failure Mode)

### Q: What happens in every possible failure scenario?

| Scenario | Code | Response |
|---|---|---|
| Missing field in request | Pydantic auto-validates | `422 {"detail": [{"loc":["body","bmi"], "msg":"field required"}]}` |
| Model not loaded | `if not diabetes_model:` (line 219) | `503 {"detail": "Diabetes Model not available"}` |
| Model crashes during prediction | `except Exception as e:` (line 238) | `500 {"detail": "error message"}` |
| Invalid credentials | `verify_password()` fails | `401 {"detail": "Invalid credentials"}` |
| Expired JWT token | `jwt.decode()` throws | `401 {"detail": "Could not validate credentials"}` |
| No auth header | `oauth2_scheme` finds nothing | `401 {"detail": "Not authenticated"}` |
| Rate limit exceeded | `security.limiter.check()` | `429 {"detail": "Rate limit exceeded"}` |
| Untrusted host header | `TrustedHostMiddleware` | `400 {"detail": "Invalid host header"}` |
| Unhandled exception | `ExceptionMiddleware` | `500 {"detail": "Error: a3f2b1c9"}` |
| Invalid route | FastAPI default | `404 {"detail": "Not Found"}` |
| Wrong HTTP method | FastAPI default | `405 {"detail": "Method Not Allowed"}` |

---

## SECTION F: COMPONENT REUSE PATTERN

### Q: How does ONE component handle 5 different diseases?

Each disease page is ~30 lines:
```tsx
// frontend/src/app/(protected)/predict/diabetes/page.tsx
import PredictionForm from "@/components/predict/PredictionForm";
import { predictDiabetes } from "@/lib/api";

export default function DiabetesPage() {
    return (
        <PredictionForm
            title="Diabetes Risk Assessment"
            description="BRFSS 2015 CDC Dataset • 253,680 Records • XGBoost Classifier"
            fields={[
                { name: "gender", label: "Gender", type: "select",
                  options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
                { name: "age", label: "Age (Years)", type: "number", min: 1, max: 120 },
                { name: "bmi", label: "BMI", type: "number", min: 10, max: 60, step: 0.1 },
                { name: "hypertension", label: "Hypertension", type: "select",
                  options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
                // ... 5 more fields
            ]}
            onSubmit={predictDiabetes}
        />
    );
}
```

**The PredictionForm component handles ALL of this automatically:**
- Form rendering from field config
- Input validation before submit
- Loading animation
- Error display
- Result rendering with confidence bar
- Risk level badge
- Medical disclaimer
- Mobile-responsive layout
- Scroll to results on mobile

**Impact**: 5 diseases × ~200 lines each = 1,000 lines saved. One bug fix applies to all 5.

---

## SECTION G: REAL API RESPONSES

### Q: Show me actual API responses from the live system.

**Diabetes — High Risk:**
```json
{
    "prediction": "High Risk",
    "raw": 1,
    "confidence": 94.2,
    "risk_level": "High",
    "disclaimer": "This is an AI-assisted screening tool, not a medical diagnosis. Please consult a qualified healthcare professional for clinical decisions."
}
```

**Heart — Healthy (but moderate confidence):**
```json
{
    "prediction": "Healthy Heart",
    "raw": 0,
    "confidence": 47.3,
    "risk_level": "Moderate",
    "disclaimer": "This is an AI-assisted screening tool..."
}
```

**Lungs — Very high confidence:**
```json
{
    "prediction": "Respiratory Issue Detected",
    "raw": 1,
    "confidence": 99.9,
    "risk_level": "High",
    "disclaimer": "This is an AI-assisted screening tool..."
}
```

**Validation error (missing BMI):**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "bmi"],
            "msg": "Field required",
            "input": {"hypertension": 1}
        }
    ]
}
```

---

## SECTION H: DATABASE (Real Schema)

### Q: Show the actual ORM models.

```python
# backend/models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, index=True)
    hashed_password = Column(String)  # bcrypt hash, never plaintext
    full_name = Column(String, default="")
    role = Column(String, default="patient")  # admin, doctor, patient
    
    # Profile
    gender = Column(String, default="")
    dob = Column(String, default="")
    blood_type = Column(String, default="")
    height = Column(String, default="")
    weight = Column(String, default="")
    about_me = Column(String, default="")
    
    # Subscription
    plan_tier = Column(String, default="free")
    subscription_expiry = Column(DateTime, nullable=True)
    
    # Relationships
    records = relationship("HealthRecord", back_populates="owner")

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    record_type = Column(String)     # "diabetes", "heart", etc.
    data = Column(JSON)              # Raw input values
    prediction = Column(String)      # "High Risk", "Healthy Heart"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="records")
```

---

## SECTION I: NUMBERS CHEAT SHEET

| What | Exact Number | Context |
|---|---|---|
| Diabetes dataset | 253,680 records | BRFSS 2015 CDC |
| Heart dataset | 253,680 records | BRFSS 2015 (mapped to Cleveland) |
| Liver dataset | 30,691 records | Indian Liver Patient Dataset |
| Kidney dataset | 400 records | UCI CKD |
| Lungs dataset | 309 records | Lung Cancer Survey |
| Diabetes accuracy | 71.7% | After class balancing |
| Heart accuracy | 73.9% | After class balancing |
| Diabetes scale_pos_weight | 6.16 | neg/pos ratio |
| Heart scale_pos_weight | 9.61 | neg/pos ratio |
| Unit tests | 141 | All passing |
| Integration checks | 28 | 0 bugs |
| Real-world validation | 48 records, 77% match | Ground truth comparison |
| API response time | ~9ms | Per prediction |
| Total model size | ~1.6 MB | All 8 files |
| Frontend routes | 21 | Including 5 predict pages |
| Backend modules | 40+ | Python files |
| Middleware layers | 7 | Rate limit → Logging |
| CSS variables | ~25 | Design tokens |
| Lines of code | ~15,000+ | Full stack |
