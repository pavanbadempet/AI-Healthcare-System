# 01 â€” Project Overview

## Q: Give me a 2-minute elevator pitch of your project.

I built a **full-stack AI Healthcare System** that uses machine learning to predict 5 diseases â€” diabetes, heart disease, liver disease, chronic kidney disease, and lung cancer.

The **frontend** is a Next.js 16 app with a professional dark medical theme, 21 routes, and real-time streaming AI chat. The **backend** is FastAPI with JWT authentication, role-based access control, and 5 ML prediction endpoints that return not just yes/no, but confidence scores and risk levels.

Each model was trained on real medical datasets â€” BRFSS (253K CDC records), Indian Liver Patient Dataset, UCI Chronic Kidney Disease, and Lung Cancer Survey data. I handled class imbalance using `scale_pos_weight` in XGBoost, validated predictions against 48 real patient records (77% accuracy), and every prediction includes a medical disclaimer.

The system also has a **RAG-powered AI chatbot** using Google Gemini that can answer health questions with personalized context from the patient's records. It streams responses in real-time using Server-Sent Events.

The whole thing has 141 unit tests passing, 28 integration checks with 0 bugs, and is deployed on GitHub.

---

## Q: What exactly does the system do?

The system has 4 core capabilities:

### 1. Disease Prediction (5 models)
Users enter health metrics (BMI, blood pressure, cholesterol, etc.) into a form. The ML model analyzes the inputs and returns:
- **Prediction**: "High Risk" or "Low Risk" (or disease-specific labels)
- **Confidence**: Percentage (e.g., 94.2%)
- **Risk Level**: Low / Moderate / High
- **Medical Disclaimer**: "This is an AI screening tool, not a diagnosis"

### 2. AI Health Chatbot
- Powered by Google Gemini API
- Uses RAG (Retrieval-Augmented Generation) to include patient context
- Streams responses token-by-token using SSE
- Includes medical disclaimers in every response

### 3. Patient Management
- User profiles with medical info (blood type, height, weight, etc.)
- Health records stored per user
- Prediction history saved and viewable
- Admin panel with system stats

### 4. Telemedicine
- Book appointments with doctors
- Doctor listings with specializations
- Appointment status tracking

---

## Q: Why did you choose healthcare?

Three reasons:

1. **Impact**: Healthcare is the highest-impact domain for AI. A prediction that catches early-stage diabetes could literally save someone's life.

2. **Technical Challenge**: Healthcare ML has unique problems not found in e-commerce or social media:
   - Severe class imbalance (90% healthy, 10% sick)
   - Regulatory requirements (HIPAA, medical disclaimers)
   - Explainability requirements (can't just say "trust me")
   - High cost of false negatives (missed disease is worse than false alarm)

3. **Portfolio Value**: Healthcare AI demonstrates maturity â€” handling real-world data issues, security considerations, and ethical responsibilities that simple CRUD apps don't.

---

## Q: What technologies did you use and why?

| Layer | Technology | Why |
|---|---|---|
| Frontend | **Next.js 16** | App Router, SSR, file-based routing, Turbopack bundler |
| UI State | **Zustand** | Lightweight (10 lines vs Redux's 50+), sufficient for auth state |
| Styling | **Tailwind + CSS Variables** | Utility classes + full control via design tokens |
| Animation | **Framer Motion** | Smooth transitions, exit animations, layout animations |
| Backend | **FastAPI** | Async, auto-docs, Pydantic validation, 10x faster than Flask |
| Database | **SQLAlchemy + SQLite** | ORM abstraction, zero-config dev, PostgreSQL for prod |
| ML | **XGBoost** | Best for tabular data, handles class imbalance natively |
| ML | **scikit-learn (SVM)** | Best for small high-dimensional datasets |
| AI | **Google Gemini** | Multimodal, fast, good medical knowledge |
| Auth | **JWT + bcrypt** | Stateless auth, secure password hashing |
| Streaming | **SSE** | Simpler than WebSockets for unidirectional serverâ†’client |

---

## Q: What makes this different from other healthcare prediction projects on GitHub?

Most projects on GitHub are just:
```
1. Load CSV
2. Train model
3. Print accuracy
4. Done
```

Mine is a **complete production system**:

| Feature | Typical Project | My Project |
|---|---|---|
| Models | 1 | 5 |
| Output | "Accuracy: 86%" | Confidence %, risk level, disclaimer |
| Frontend | Streamlit / None | Next.js with dark medical UI |
| Auth | None | JWT with role-based access |
| Chat | None | RAG + Gemini + SSE streaming |
| Tests | None | 141 unit + 28 integration |
| Class balance | Ignored | scale_pos_weight tuning |
| Deployment | Jupyter notebook | GitHub + Render ready |
| Validation | Train/test split only | 48 real patient records |

---

## Q: Walk me through the user flow.

1. **Landing**: User arrives at the homepage, sees system overview
2. **Login**: Enters credentials â†’ JWT token stored in browser
3. **Dashboard**: Sees health stats overview, recent predictions
4. **Predict**: Selects a disease model (e.g., Diabetes)
5. **Form**: Fills in health metrics (BMI, BP, cholesterol, etc.)
6. **Submit**: Clicks "Execute Clinical Assessment"
7. **Loading**: Animated spinner with progress bar
8. **Results**: Confidence bar (animated), risk level badge, prediction text
9. **Disclaimer**: Medical disclaimer always shown
10. **Chat**: Can ask AI follow-up questions about the result
11. **Records**: Prediction saved to health records history

---

## Q: What are the numbers?

| Metric | Value |
|---|---|
| Frontend routes | 21 |
| Backend modules | 40+ |
| ML models | 5 (+ 3 scalers = 8 files) |
| Training records | 538,760 total across all datasets |
| API endpoints | 20+ |
| Unit tests | 141 passing |
| Integration checks | 28 passing |
| Real-world validation | 48 records, 77% accuracy |
| Model total size | ~1.6 MB |
| Lines of code | ~15,000+ |


---

# 04 â€” Machine Learning Pipeline

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
- 253K records â€” enough data for gradient boosting
- Tabular data with mixed feature types â€” XGBoost handles natively
- `scale_pos_weight` handles class imbalance without resampling
- Fast training (~3 seconds)

**SVM for Kidney & Lungs** (small datasets):
- Only 400 and 309 records â€” deep learning would overfit
- SVM finds optimal decision boundary even with limited data
- RBF kernel captures non-linear patterns
- StandardScaler required (SVM is distance-based)

**Random Forest for Liver** (medium dataset):
- 30K records â€” medium size
- Log transform needed for skewed enzyme values
- Random Forest handles non-linearity well
- Less prone to overfitting than single decision tree

---

## Q: Explain class imbalance and why it matters.

**The problem:**
In BRFSS diabetes data: 86% healthy, 14% diabetic.
In BRFSS heart data: 90% healthy, 10% have heart disease.

If a model just predicts "healthy" for everyone:
- Diabetes: 86% accuracy â€” looks great!
- Heart: 90% accuracy â€” looks amazing!
- But it detects **ZERO** sick patients â€” completely useless.

**The fix â€” `scale_pos_weight`:**
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
The old model just said "healthy" for everyone. The new model actually identifies at-risk patients, at the cost of some false positives. In medical screening, **false positives are safer than false negatives** â€” a false positive means the patient sees a doctor unnecessarily. A false negative means a sick patient goes undiagnosed.

---

## Q: Walk through the training pipeline step by step.

```python
# Example: train_diabetes.py

# 1. LOAD DATA
df = pd.read_parquet("data/processed/diabetes.parquet")
# 253,680 records from BRFSS 2015 CDC survey

# 2. COLUMN MAPPING (dataset-specific)
df = df.rename(columns=DIABETES_DATASET_MAP)
# HighBP â†’ hypertension, HighChol â†’ high_chol, etc.

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
- Age â†’ bucket (0-13 categories): `18-24=1, 25-29=2, ... 80+=13`
- Columns renamed from BRFSS to canonical names
- No scaling needed (XGBoost is tree-based)

### Heart
- BRFSS columns mapped to Cleveland schema:
  ```python
  # BRFSS column â†’ Cleveland column name
  high_bp â†’ cp, bmi â†’ trestbps, high_chol â†’ chol,
  smoker â†’ fbs, gen_hlth â†’ restecg, phys_activity â†’ thalach,
  stroke â†’ exang, diabetes â†’ oldpeak, hvy_alcohol â†’ slope
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
# model.predict() â†’ Binary: 0 or 1
prediction = model.predict([[features]])[0]  # Returns: 1

# model.predict_proba() â†’ Probabilities per class
proba = model.predict_proba([[features]])[0]
# Returns: [0.058, 0.942]
# â†’ 5.8% chance healthy, 94.2% chance disease
```

**Why it matters:**
- A prediction of "Disease" with 51% confidence is VERY different from 99% confidence
- Doctors need to know HOW SURE the model is
- Risk level thresholds:
  - <40% â†’ Low risk (green) â†’ "Probably fine, but monitor"
  - 40-75% â†’ Moderate risk (amber) â†’ "Worth investigating"
  - >75% â†’ High risk (red) â†’ "See a doctor soon"

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
- Models loaded into **RAM at startup** â€” prediction takes ~2ms
- NOT loaded per-request (would be ~200ms each time)
- If a model file is missing/corrupt â†’ that endpoint returns 503, others still work
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
77% on real records is already clinically useful for a **screening** tool. The purpose isn't to replace diagnosis â€” it's to flag at-risk patients for further evaluation. Over-engineering accuracy past 80% has diminishing returns for a portfolio project.


---

# 03 â€” Backend Deep Dive

## Q: Explain the backend architecture.

FastAPI application with modular design:

```
Request â†’ Middleware Stack (7 layers) â†’ Router â†’ Handler â†’ Response
                                           â†“
                              Database / ML Model / AI Service
```

**40+ modules** organized by responsibility:
- **Core**: `main.py`, `database.py`, `models.py`, `schemas.py`
- **Auth**: `auth.py`, `security.py`
- **Prediction**: `prediction.py`, `features.py`, 5Ã— `train_*.py`
- **AI/Chat**: `core_ai.py`, `prompt_registry.py`, `chat.py`, `streaming_chat.py`, `rag.py`, `chat_context.py`, `agent.py`
- **Services**: `admin.py`, `appointments.py`, `payments.py`, `report.py`, `pdf_service.py`, `email_service.py`, `vision_service.py`
- **Enterprise**: `compliance.py`, `enterprise_features.py`, `telemetry.py`

---

## Q: Why FastAPI over Django or Flask?

| Feature | Flask | Django | FastAPI |
|---|---|---|---|
| Speed | Sync (slow) | Sync (slow) | Async (fast) |
| Type safety | None | None | Pydantic + type hints |
| Auto-docs | No | No | Swagger UI auto-generated |
| Validation | Manual | Forms | Automatic from schemas |
| Learning curve | Low | High | Medium |
| Boilerplate | Medium | High | Low |

**FastAPI specific wins:**
```python
# Pydantic validates AUTOMATICALLY â€” no manual checking
class DiabetesInput(BaseModel):
    hypertension: int
    bmi: float
    age: float

@router.post("/predict/diabetes")
def predict(data: DiabetesInput):  # Invalid input â†’ 422 automatically
    ...
```

---

## Q: Explain the middleware stack in detail.

```python
# Order matters â€” last added runs FIRST
app.add_middleware(LoggingMiddleware)        # 7. Log every request
app.add_middleware(ExceptionMiddleware)       # 6. Catch unhandled errors
app.add_middleware(GZipMiddleware)            # 5. Compress responses >1KB
app.add_middleware(SecurityHeadersMiddleware) # 4. X-Frame-Options, etc.
app.add_middleware(CORSMiddleware, ...)       # 3. Allow frontend origin
app.add_middleware(TrustedHostMiddleware, ..) # 2. Host whitelist
app.add_middleware(RateLimitMiddleware)       # 1. Block excessive requests
```

**Execution order** (first to last):
```
Request â†’ RateLimit â†’ TrustedHost â†’ CORS â†’ SecurityHeaders â†’ GZip â†’ Exception â†’ Logging â†’ Route
```

Each middleware explained:

### 1. RateLimitMiddleware
```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path not in ["/", "/docs", "/healthz"]:
            security.limiter.check(request, client_ip)
        return await call_next(request)
```
Skips static/health endpoints. Returns 429 if limit exceeded.

### 2. TrustedHostMiddleware
Only allows `127.0.0.1` and `aio-health-backend.onrender.com`. Blocks requests with other `Host` headers â†’ prevents host header injection.

### 3. CORSMiddleware
```python
allow_origins=["http://127.0.0.1:3000"],  # Only our frontend
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
```

### 4. SecurityHeadersMiddleware
```python
response.headers["X-Frame-Options"] = "DENY"           # No iframe embedding
response.headers["X-Content-Type-Options"] = "nosniff"  # No MIME sniffing
```

### 5. GZipMiddleware
Compresses responses >1KB. Reduces bandwidth for large JSON responses.

### 6. ExceptionMiddleware
```python
class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger.error(f"Error {error_id}: {e}")
            return JSONResponse(status_code=500, content={"detail": f"Error: {error_id}"})
```
**Key**: Returns UUID error ID, never exposes stack traces to client.

### 7. LoggingMiddleware
```python
logger.info(f"{request.method} {request.url.path} - {response.status_code} ({ms:.0f}ms)")
# Output: POST /predict/diabetes - 200 (9ms)
```

---

## Q: How does authentication work?

### Login Flow:
```python
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401)
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}
```

### JWT Token Structure:
```json
{
  "sub": "admin",           // Username
  "role": "admin",          // Role (admin/doctor/patient)
  "exp": 1747138800         // Expiry timestamp
}
```

### Protected Endpoint:
```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    return user

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user  # Only accessible with valid JWT
```

### Password Security:
```python
# Never store plaintext passwords
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verify: bcrypt handles salt extraction automatically
bcrypt.checkpw(password.encode(), stored_hash)
```

---

## Q: How does dependency injection work in FastAPI?

```python
# Database session â€” created per request, always closed
def get_db():
    db = SessionLocal()
    try:
        yield db          # Provide to handler
    finally:
        db.close()        # Always cleanup, even on error

# Auth â€” decoded from JWT token
def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)):
    user = verify_and_get_user(token, db)
    return user

# Route handler â€” FastAPI auto-provides both dependencies
@router.get("/records")
def get_records(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Record).filter(Record.user_id == user.id).all()
```

**Why this matters:**
- Database sessions are NEVER leaked (finally block)
- Auth is NEVER forgotten (Depends enforces it)
- Each request is isolated (own session, own user context)
- Easy to mock in tests (override dependencies)

---

## Q: Explain the prediction endpoint in detail.

```python
@router.post("/predict/diabetes")
def predict_diabetes(data: schemas.DiabetesInput):
    # 1. Check model is loaded
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Model not available")
    
    # 2. Feature engineering
    age_bucket = get_age_bucket(data.age)  # Convert age to 0-13 bucket
    input_list = [data.hypertension, data.high_chol, data.bmi, ...]
    
    # 3. Binary prediction
    prediction = diabetes_model.predict([input_list])[0]  # 0 or 1
    
    # 4. Confidence score
    proba = diabetes_model.predict_proba([input_list])[0]
    confidence = round(proba[1] * 100, 1)  # Disease probability %
    
    # 5. Risk level mapping
    risk_level = "High" if confidence >= 75 else "Moderate" if confidence >= 40 else "Low"
    
    # 6. Return enriched response
    return {
        "prediction": "High Risk" if prediction >= 1 else "Low Risk",
        "raw": int(prediction),
        "confidence": confidence,
        "risk_level": risk_level,
        "disclaimer": "This is an AI-assisted screening tool..."
    }
```

---

## Q: What is `core_ai.py` and why is it important?

It's the **single gateway** for ALL external AI calls. Architecture rule: **no route handler should ever call Gemini/OpenAI directly**.

```
Route Handler â†’ core_ai.generate() â†’ Gemini API
                                    â†’ Ollama (fallback)
```

**Benefits:**
1. **Single point of change** â€” Switch AI providers by editing one file
2. **Centralized error handling** â€” Retries, timeouts, fallbacks
3. **Rate limiting** â€” Control AI API costs
4. **API key management** â€” One place for all secrets
5. **Testability** â€” Mock one function to disable all AI calls

---

## Q: What is the Prompt Registry?

```python
# prompt_registry.py â€” ALL system prompts live here
SYSTEM_PROMPTS = {
    "health_chat": """You are a medical AI assistant. 
        Always include disclaimers. Never diagnose.
        Recommend seeing a doctor for serious symptoms.""",
    
    "report_analysis": """Analyze this lab report.
        Identify abnormal values. Explain in simple terms.""",
    
    "prediction_explanation": """Explain why this prediction 
        was made based on the input features."""
}
```

**Rules:**
- Never inline prompts in route handlers
- All prompts are named, versioned, documented
- Easy to A/B test different prompts
- Medical disclaimers baked into system prompts

---

## Q: How does the lifespan event work?

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    create_default_admin()         # Seed admin user
    prediction.initialize_models() # Load all 8 ML model files
    yield                          # App runs here
    # SHUTDOWN
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

**Why lifespan over @app.on_event?**
- `on_event` is deprecated in newer FastAPI
- Lifespan is a context manager â€” guaranteed cleanup
- Models loaded ONCE at startup, not per-request
- Startup failures prevent the app from accepting requests


---

# 02 â€” Frontend Deep Dive

## Q: Explain your frontend architecture.

```
frontend/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ app/                          # Next.js App Router
â”‚   â”‚   â”œâ”€â”€ layout.tsx                # Root layout (fonts, providers)
â”‚   â”‚   â”œâ”€â”€ page.tsx                  # Landing (redirects to dashboard)
â”‚   â”‚   â”œâ”€â”€ globals.css               # Design tokens (CSS variables)
â”‚   â”‚   â”œâ”€â”€ login/page.tsx            # Public: login form
â”‚   â”‚   â”œâ”€â”€ signup/page.tsx           # Public: registration
â”‚   â”‚   â””â”€â”€ (protected)/             # Auth-guarded route group
â”‚   â”‚       â”œâ”€â”€ layout.tsx            # Shared sidebar + topbar
â”‚   â”‚       â”œâ”€â”€ dashboard/page.tsx    # Stats overview
â”‚   â”‚       â”œâ”€â”€ predict/
â”‚   â”‚       â”‚   â”œâ”€â”€ page.tsx          # Disease selection hub
â”‚   â”‚       â”‚   â”œâ”€â”€ diabetes/         # Diabetes form
â”‚   â”‚       â”‚   â”œâ”€â”€ heart/            # Heart disease form
â”‚   â”‚       â”‚   â”œâ”€â”€ liver/            # Liver disease form
â”‚   â”‚       â”‚   â”œâ”€â”€ kidney/           # Kidney disease form
â”‚   â”‚       â”‚   â””â”€â”€ lungs/            # Lung cancer form
â”‚   â”‚       â”œâ”€â”€ chat/page.tsx         # AI chatbot
â”‚   â”‚       â”œâ”€â”€ profile/page.tsx      # User profile
â”‚   â”‚       â”œâ”€â”€ admin/page.tsx        # Admin panel
â”‚   â”‚       â”œâ”€â”€ patients/page.tsx     # Patient records
â”‚   â”‚       â”œâ”€â”€ pricing/page.tsx      # Subscription plans
â”‚   â”‚       â”œâ”€â”€ telemedicine/page.tsx  # Appointments
â”‚   â”‚       â”œâ”€â”€ capacity/page.tsx     # Hospital capacity
â”‚   â”‚       â”œâ”€â”€ infrastructure/page.tsx # System monitoring
â”‚   â”‚       â””â”€â”€ about/page.tsx        # About page
â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ layout/
â”‚   â”‚   â”‚   â”œâ”€â”€ Sidebar.tsx           # Navigation sidebar
â”‚   â”‚   â”‚   â””â”€â”€ TopBar.tsx            # Top navigation
â”‚   â”‚   â”œâ”€â”€ predict/
â”‚   â”‚   â”‚   â””â”€â”€ PredictionForm.tsx    # Reusable prediction component
â”‚   â”‚   â””â”€â”€ chat/
â”‚   â”‚       â””â”€â”€ ChatInterface.tsx     # Streaming chat UI
â”‚   â””â”€â”€ lib/
â”‚       â”œâ”€â”€ api.ts                    # API client (all backend calls)
â”‚       â”œâ”€â”€ store.ts                  # Zustand auth store
â”‚       â””â”€â”€ useTelemetry.ts           # Usage tracking hook
```

---

## Q: Why Next.js 16 instead of plain React?

| Feature | Plain React | Next.js |
|---|---|---|
| Routing | Need React Router | Built-in file-based routing |
| SSR/SEO | Manual setup | Built-in |
| Code splitting | Manual | Automatic per-route |
| Bundler | Webpack/Vite | Turbopack (10x faster) |
| Layouts | Manual nesting | App Router layout system |
| API routes | Need separate backend | Built-in (not used â€” we have FastAPI) |

**Key reason**: The `(protected)` route group. All 11 authenticated pages share a sidebar layout **without** duplicating code. The parentheses in the folder name mean it doesn't appear in the URL.

---

## Q: Explain the `(protected)` route group pattern.

```
app/
â”œâ”€â”€ login/page.tsx          â†’ /login (no sidebar)
â”œâ”€â”€ signup/page.tsx         â†’ /signup (no sidebar)
â””â”€â”€ (protected)/
    â”œâ”€â”€ layout.tsx          â†’ Wraps ALL children with sidebar + topbar
    â”œâ”€â”€ dashboard/page.tsx  â†’ /dashboard (has sidebar)
    â”œâ”€â”€ predict/page.tsx    â†’ /predict (has sidebar)
    â””â”€â”€ admin/page.tsx      â†’ /admin (has sidebar)
```

The `(protected)` folder is a **route group** â€” it organizes code without affecting URLs. The `layout.tsx` inside it wraps every child page with the sidebar and topbar. If a user isn't authenticated, this layout redirects to `/login`.

---

## Q: How does state management work?

I use **Zustand** for global state. The store holds:

```typescript
interface AuthStore {
  token: string | null;
  user: UserProfile | null;
  setToken: (token: string) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
}
```

**Why Zustand over Redux?**
- Redux: ~50 lines for store + slice + reducers + selectors + provider
- Zustand: ~10 lines, no provider needed, built-in persistence

**How auth token injection works:**
```typescript
// In api.ts
let getToken: (() => string | null) | null = null;
export function setTokenGetter(fn: () => string | null) { getToken = fn; }

// In root layout, on mount:
setTokenGetter(() => useAuthStore.getState().token);

// Every API call auto-injects:
function authHeaders() {
  const token = getToken?.();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
```

---

## Q: Explain the PredictionForm component in detail.

It's a **single reusable component** used by all 5 disease pages. Props:

```typescript
interface PredictionFormProps {
  title: string;              // "Diabetes Risk Assessment"
  description: string;        // "Enter patient metrics..."
  fields: Field[];            // Array of form field configs
  onSubmit: (data) => Promise<PredictionResult>;  // API call
}

interface Field {
  name: string;       // "bmi"
  label: string;      // "Body Mass Index"
  type: "number" | "select";
  options?: { label: string; value: number }[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  tooltip?: string;
}
```

**How each disease page uses it:**
```tsx
// diabetes/page.tsx
<PredictionForm
  title="Diabetes Risk Assessment"
  fields={[
    { name: "bmi", label: "BMI", type: "number", min: 10, max: 60 },
    { name: "gender", label: "Gender", type: "select", 
      options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
    // ... 7 more fields
  ]}
  onSubmit={predictDiabetes}
/>
```

**Features inside PredictionForm:**
1. **CustomSelect** â€” Styled dropdown that replaces ugly native OS selects
2. **Validation** â€” Checks all fields before submit
3. **Loading animation** â€” Spinning icon + progress bar
4. **Confidence bar** â€” Animated fill with color coding:
   - Green (<40%) = Low risk
   - Amber (40-75%) = Moderate risk
   - Red (>75%) = High risk
5. **Risk level badge** â€” "LOW" / "MODERATE" / "HIGH" with color
6. **Medical disclaimer** â€” Always shown below results

---

## Q: How does the streaming chat work?

```
User types message
    â†“
Frontend sends POST /chat/stream
    â†“
Backend returns text/event-stream
    â†“
Frontend reads with ReadableStream
    â†“
Each chunk: data: {"token":"word","status":"streaming"}
    â†“
Append token to UI in real-time
    â†“
Final chunk: {"status":"complete"}
    â†“
Stop reading
```

**Frontend code pattern:**
```typescript
export function streamChat(message, history, onChunk, onDone, onError) {
  const controller = new AbortController();  // Cancel support
  
  fetch('/chat/stream', {
    method: 'POST',
    headers: { ...authHeaders() },
    body: JSON.stringify({ message, history }),
    signal: controller.signal,
  })
  .then(async (res) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const text = decoder.decode(value);
      for (const line of text.split('\n')) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          onChunk(data);  // Append token to UI
        }
      }
    }
    onDone();
  });
  
  return () => controller.abort();  // Cancel function
}
```

**Why SSE over WebSockets?**
- Chat streaming is **unidirectional** (server â†’ client only during response)
- SSE uses standard HTTP â€” no upgrade handshake needed
- Works through proxies and load balancers without special config
- Browser has built-in reconnection
- Simpler error handling

---

## Q: Explain your CSS design system.

I use **CSS custom properties** (variables) for a consistent medical dark theme:

```css
:root {
  /* Surface Hierarchy (5 levels) */
  --bg-primary: #000000;        /* Page backgrounds */
  --bg-secondary: #0a0a0a;      /* Panels, sidebars */
  --bg-card: #111111;           /* Cards, inputs */
  --bg-card-hover: #171717;     /* Hover states */
  --bg-elevated: #1a1a1a;       /* Modals, overlays */

  /* Status Colors (3 states Ã— 3 variants each) */
  --danger: #ef4444;            /* High risk */
  --danger-muted: rgba(239, 68, 68, 0.1);
  --danger-border: rgba(239, 68, 68, 0.3);
  --warning: #f59e0b;           /* Moderate risk */
  --warning-muted: rgba(245, 158, 11, 0.1);
  --warning-border: rgba(245, 158, 11, 0.3);
  --success: #10b981;           /* Low risk */
  --success-muted: rgba(16, 185, 129, 0.1);
  --success-border: rgba(16, 185, 129, 0.2);
}
```

**Why CSS variables over Tailwind config?**
- Full runtime control â€” can change theme without rebuild
- Works with Framer Motion animations
- Component-level overrides possible
- No Tailwind class name bloat for complex color schemes

---

## Q: How do you handle responsive design?

1. **Grid system**: `grid-cols-1 lg:grid-cols-12` â€” single column on mobile, 12-column on desktop
2. **Sidebar**: Collapses to hamburger menu on mobile
3. **Prediction form**: 2-column grid â†’ 1-column on small screens
4. **Results panel**: Stacks below form on mobile with `scrollIntoView()`:
   ```typescript
   useEffect(() => {
     if (result && window.innerWidth < 1024) {
       resultRef.current?.scrollIntoView({ behavior: "smooth" });
     }
   }, [result]);
   ```

---

## Q: What animations do you use?

| Animation | Library | Where |
|---|---|---|
| Page transitions | Framer Motion | `AnimatePresence` on route changes |
| Form field entrance | Framer Motion | `initial={{ opacity: 0, y: 10 }}` |
| Confidence bar fill | Framer Motion | `animate={{ width: "94.2%" }}` |
| Loading spinner | Framer Motion | `animate={{ rotate: 360 }}` infinite |
| Button progress | Framer Motion | `animate={{ width: "100%" }}` linear |
| Dropdown open/close | Framer Motion | `AnimatePresence` with y-offset |
| Error messages | Framer Motion | Height animation (0 â†’ auto) |

---

## Q: How does the API client work?

`api.ts` provides a typed wrapper around `fetch`:

```typescript
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),          // Auto-inject JWT
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // Parse error detail (string or array of validation errors)
    throw new Error(errorMessage);
  }

  return res.json();
}
```

**Key design decisions:**
- **Auto-injects auth** â€” No need to pass token manually
- **Type-safe** â€” Generic `<T>` return type
- **Error parsing** â€” Handles both string errors and Pydantic validation arrays
- **Centralized** â€” Change base URL in one place for deployment


---

# 05 â€” AI & Chat System (Complete Deep-Dive)

> Everything about how the AI chatbot works â€” RAG, Gemini, streaming, prompts, fallbacks.

---

## Q: How does the AI chatbot work? Explain the FULL architecture.

### The Complete Flow (7 Steps):

```
User types: "What diet should I follow for diabetes?"
    â†“
Step 1: Frontend sends POST /chat/stream with message + auth token
    â†“
Step 2: Backend extracts user_id from JWT token
    â†“
Step 3: RAG Search â€” find relevant patient records in vector store
         Query: "diet diabetes" â†’ Finds: "Patient has diabetes prediction: High Risk"
    â†“
Step 4: Prompt Building â€” combine system prompt + RAG context + user message + history
         System prompt: "You are a medical AI assistant..."
         Context: "This patient was assessed as High Risk for diabetes"
         User: "What diet should I follow for diabetes?"
         History: [previous messages]
    â†“
Step 5: Gemini API Call â€” send assembled prompt, request streaming
    â†“
Step 6: SSE Streaming â€” each token streamed back as Server-Sent Event
         data: {"token": "For", "status": "streaming"}
         data: {"token": " diabetes", "status": "streaming"}
         data: {"token": " management", "status": "streaming"}
         ...
         data: {"status": "complete"}
    â†“
Step 7: Frontend renders tokens in real-time as they arrive
```

---

## Q: What is RAG and why do you use it? Explain with a detailed example.

**RAG = Retrieval-Augmented Generation**

### The Problem Without RAG:
```
User: "What should I eat?"
AI (without RAG): "Here's a general healthy diet: fruits, vegetables, lean protein..."
                   â† GENERIC. Doesn't know the patient has diabetes.
```

### The Solution With RAG:
```
User: "What should I eat?"
RAG Search: Finds patient record â†’ "Diabetes: High Risk, BMI: 35, Age: 55"
AI (with RAG): "Given your diabetes risk assessment (High Risk) and BMI of 35, 
                I recommend focusing on low-glycemic foods: non-starchy vegetables,
                whole grains, lean proteins. Avoid sugary drinks and refined carbs.
                Please consult your doctor for a personalized plan."
                â† PERSONALIZED. Knows the patient's actual condition.
```

### How RAG Works Internally:

```python
# Step 1: When a prediction is made, store it as an embedding
def store_health_record(user_id: int, record_type: str, prediction: str):
    text = f"Patient health record: {record_type} assessment result: {prediction}"
    embedding = compute_embedding(text)  # Convert text to 768-dim vector
    vector_store.add(
        embedding=embedding,
        metadata={"user_id": user_id, "type": record_type},
        text=text
    )

# Step 2: When user asks a question, search for relevant records
def search_context(query: str, user_id: int, top_k: int = 5) -> list[str]:
    query_embedding = compute_embedding(query)
    
    # Search vector store â€” find records most similar to the question
    results = vector_store.search(
        query_embedding,
        filter={"user_id": user_id},  # Only this patient's records!
        top_k=top_k
    )
    
    return [r.text for r in results]
    # Returns: ["Patient health record: diabetes assessment: High Risk",
    #           "Patient health record: heart assessment: Healthy Heart"]

# Step 3: Build the prompt with retrieved context
def build_prompt(user_message: str, context: list[str], history: list) -> str:
    return f"""
{SYSTEM_PROMPT}

=== PATIENT HEALTH CONTEXT ===
{chr(10).join(context)}

=== CONVERSATION HISTORY ===
{format_history(history)}

=== CURRENT QUESTION ===
{user_message}

Remember: Always include a medical disclaimer. Never provide definitive diagnoses.
"""
```

### Why RAG Instead of Fine-Tuning?

| Approach | RAG | Fine-Tuning |
|---|---|---|
| Data needed | Just store records | Thousands of training examples |
| Update speed | Instant (add record â†’ searchable) | Hours/days to retrain |
| Cost | ~$0 (vector store is local) | $100+ per fine-tune |
| Patient-specific | Yes (filter by user_id) | No (model-level) |
| Privacy | Records stay in YOUR database | Records sent to OpenAI/Google |
| My choice | **YES** | No |

---

## Q: How does SSE streaming work? Show the real implementation.

### What is SSE?

**SSE (Server-Sent Events)** = Server pushes data to client over a standard HTTP connection. Unlike WebSocket, it's unidirectional (server â†’ client only).

### Backend Implementation:

```python
# backend/streaming_chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

router = APIRouter()

class ChatStreamRequest(BaseModel):
    message: str
    history: list = []

@router.post("/chat/stream")
async def stream_chat(request: ChatStreamRequest):
    """Stream AI response token-by-token via SSE."""
    
    async def generate():
        try:
            # 1. RAG: Find relevant patient context
            context = rag_search(request.message, user_id=get_current_user_id())
            
            # 2. Build prompt from registry (NEVER inline prompts)
            prompt = prompt_registry.build_chat_prompt(
                user_message=request.message,
                context=context,
                history=request.history
            )
            
            # 3. Call Gemini via core_ai.py (NEVER call API directly)
            model = core_ai.get_model()
            response = model.generate_content(prompt, stream=True)
            
            # 4. Stream each token as SSE event
            for chunk in response:
                if chunk.text:
                    event_data = json.dumps({
                        "token": chunk.text,
                        "status": "streaming"
                    })
                    yield f"data: {event_data}\n\n"
            
            # 5. Send completion signal
            yield f"data: {json.dumps({'status': 'complete'})}\n\n"
            
        except Exception as e:
            # Stream error to client instead of breaking connection
            error_data = json.dumps({
                "error": "AI service temporarily unavailable",
                "status": "error"
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )
```

### Frontend Implementation:

```typescript
// frontend/src/lib/api.ts

export async function streamChat(
    message: string,
    history: ChatMessage[],
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify({ message, history }),
    });

    if (!response.ok) {
        onError('Failed to connect to AI');
        return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.status === 'streaming' && data.token) {
                    onToken(data.token);  // Append token to chat UI
                } else if (data.status === 'complete') {
                    onComplete();
                } else if (data.status === 'error') {
                    onError(data.error);
                }
            }
        }
    }
}
```

### Why SSE Over WebSocket?

| Feature | SSE | WebSocket |
|---|---|---|
| Direction | Server â†’ Client only | Bidirectional |
| Protocol | Standard HTTP | WebSocket upgrade handshake |
| Auto-reconnect | Built-in | Must implement manually |
| Proxy support | Works through all proxies | Some proxies block |
| Complexity | Simple | Complex |
| My use case | Chat streaming (server sends tokens) | Not needed |

**Decision**: Chat is unidirectional â€” the server streams tokens to the client. SSE is simpler, auto-reconnects, and works through all HTTP proxies. WebSocket adds complexity with zero benefit for this use case.

---

## Q: What is core_ai.py and why can't route handlers call AI directly?

### The Rule (from AGENTS.md):
> "All AI inference must go through `backend/core_ai.py` â€” never call provider APIs directly."

### What core_ai.py Does:

```python
# backend/core_ai.py

import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

_model = None

def get_model():
    """Singleton pattern â€” one model instance for the entire app."""
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-pro")
        logger.info("Gemini model initialized")
    return _model

def generate(prompt: str, stream: bool = False):
    """Central AI gateway â€” all AI calls go through here."""
    model = get_model()
    try:
        return model.generate_content(prompt, stream=stream)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        # Fallback to Ollama local LLM
        return _fallback_ollama(prompt)

def _fallback_ollama(prompt: str):
    """If Gemini is down, try local Ollama."""
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama2", "prompt": prompt},
            timeout=30
        )
        return response.json()["response"]
    except Exception:
        return "AI service is temporarily unavailable. Your prediction results are still accessible."
```

### Why This Pattern? 5 Reasons:

1. **Provider abstraction**: Switch from Gemini to OpenAI by changing ONE function. No route handler changes.

2. **Centralized error handling**: Retries, timeouts, and fallback chain (Gemini â†’ Ollama â†’ error message) in one place.

3. **Cost control**: Add rate limiting, usage tracking, token counting in one place:
   ```python
   def generate(prompt, stream=False):
       if daily_token_count > MAX_DAILY_TOKENS:
           raise QuotaExceeded("Daily AI quota reached")
       # ... generate
   ```

4. **Testing**: Mock ONE function to disable all AI in tests:
   ```python
   @pytest.fixture
   def mock_ai(monkeypatch):
       monkeypatch.setattr("backend.core_ai.generate", lambda p, **k: "Mock response")
   ```

5. **API key safety**: Key is loaded once in core_ai, never scattered across route files.

---

## Q: What are system prompts and how does prompt_registry.py work?

### The Rule:
> "Prompts are owned by `prompt_registry.py` â€” never inline system prompts in route handlers."

### How It Works:

```python
# backend/prompt_registry.py

HEALTH_CHAT_SYSTEM_PROMPT = """You are a medical AI assistant for the AI Healthcare System.

RULES YOU MUST FOLLOW:
1. Always include a medical disclaimer at the end of your response
2. Never provide definitive diagnoses â€” say "may indicate" not "you have"
3. Recommend consulting a healthcare professional for serious concerns
4. Use evidence-based information from medical literature
5. Be empathetic and supportive in tone
6. If patient context is provided, personalize your response
7. For medication questions, always say "consult your doctor"
8. Never share or reference other patients' data

DISCLAIMER TO INCLUDE:
"Note: This is AI-generated health information, not medical advice. 
Please consult a qualified healthcare professional for clinical decisions."
"""

HEALTH_CHAT_WITH_CONTEXT = """
{system_prompt}

=== PATIENT HEALTH CONTEXT ===
The following are this patient's health assessment results from our system:
{context}

=== CONVERSATION HISTORY ===
{history}

=== PATIENT'S QUESTION ===
{user_message}
"""

def build_chat_prompt(user_message: str, context: list[str], history: list) -> str:
    """Build a complete prompt from components. SINGLE SOURCE OF TRUTH."""
    return HEALTH_CHAT_WITH_CONTEXT.format(
        system_prompt=HEALTH_CHAT_SYSTEM_PROMPT,
        context="\n".join(context) if context else "No health records found.",
        history=_format_history(history),
        user_message=user_message
    )
```

### Why a Registry?

| Without Registry | With Registry |
|---|---|
| Prompts scattered across 10+ files | Single file, easy to find |
| Duplicate disclaimers | Disclaimer defined once |
| Hard to A/B test prompts | Swap prompts in one place |
| Inconsistent tone | Consistent medical guidelines |
| No version control for prompts | Full git history of prompt changes |

---

## Q: How does the Ollama fallback work? Show the complete chain.

```
User sends message
    â†“
Try Gemini API (cloud)
    â”œâ”€â”€ Success â†’ Stream response back
    â””â”€â”€ Fail (timeout, API key invalid, quota exceeded)
        â†“
    Try Ollama (local LLM on localhost:11434)
        â”œâ”€â”€ Success â†’ Return local response
        â””â”€â”€ Fail (Ollama not running)
            â†“
        Return friendly error:
        "AI chat is temporarily unavailable. 
         Your prediction results are still accessible."
```

**Key insight**: Prediction endpoints DON'T need Gemini. They use LOCAL ML models (.pkl files in RAM). Only the chat feature depends on the AI API. So even if both Gemini AND Ollama are down, users can still:
- Run disease predictions
- View their health records
- Manage their profile
- See previous prediction results

This means the system **degrades gracefully** instead of going completely down.

---

## Q: What's the difference between a chat response and a prediction response?

| | Chat Response | Prediction Response |
|---|---|---|
| Source | Gemini AI (cloud) or Ollama (local) | XGBoost/SVM model (.pkl in RAM) |
| Latency | 2-10 seconds (LLM generation) | ~9ms (model inference) |
| Streaming | Yes (SSE, token-by-token) | No (single JSON response) |
| Deterministic | No (LLM is probabilistic) | Yes (same input = same output) |
| Internet needed | Yes (for Gemini) | No (model is local) |
| Cost | ~$0.001 per query (Gemini tokens) | $0 (local computation) |
| Personalized | Yes (RAG context from records) | No (purely input-based) |
| Disclaimer | In the AI response text | In the JSON response field |


---

# 06 â€” Database Design (Complete Deep-Dive)

> Everything about the database layer â€” schema, ORM, sessions, migrations, queries.

---

## Q: What database do you use and why?

### Development: SQLite
- **Zero configuration** â€” `pip install` and it works. No database server to install.
- **Single file** â€” entire database is `healthcare.db`. Easy to delete and recreate.
- **Fast for reads** â€” perfect for single-user development.
- **Limitation** â€” single writer at a time (no concurrent writes).

### Production: PostgreSQL
- **Concurrent writes** â€” multiple users can write simultaneously.
- **Connection pooling** â€” handles 100+ concurrent connections.
- **ACID compliance** â€” full transactional integrity for patient data.
- **Just change one environment variable:**
  ```bash
  # Development (default)
  DATABASE_URL=sqlite:///./healthcare.db
  
  # Production (Neon managed PostgreSQL)
  DATABASE_URL=postgresql://user:pass@ep-cool-name.neon.tech/healthcare
  ```

### How the switch works (zero code changes):

```python
# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This ONE line reads the env variable â€” same code for SQLite and PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")

# SQLAlchemy handles the difference internally
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

---

## Q: Show me the complete database schema with all fields.

### Users Table (the core entity):

```python
# backend/models.py

class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, index=True)
    hashed_password = Column(String, nullable=False)  # bcrypt hash, NEVER plaintext
    
    # Profile
    full_name = Column(String, default="")
    role = Column(String, default="patient")  # "admin" | "doctor" | "patient"
    gender = Column(String, default="")
    dob = Column(String, default="")          # Date of birth
    blood_type = Column(String, default="")   # A+, B-, O+, etc.
    height = Column(String, default="")       # In cm or feet
    weight = Column(String, default="")       # In kg or lbs
    about_me = Column(String, default="")     # Free text bio
    
    # Subscription (tiered access)
    plan_tier = Column(String, default="free")        # "free" | "pro" | "enterprise"
    subscription_expiry = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    records = relationship("HealthRecord", back_populates="owner")
```

**Why these fields?**
- `hashed_password`: bcrypt with salt â€” even if database is stolen, passwords are safe
- `role`: Role-based access control â€” admin sees all, patient sees only their own
- `plan_tier`: Subscription tiers for premium features (not enforced yet)
- `index=True` on username/email: Database creates B-tree index â†’ O(log n) lookups instead of O(n) full scan

### Health Records Table:

```python
class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    record_type = Column(String)    # "diabetes" | "heart" | "liver" | "kidney" | "lungs"
    data = Column(JSON)             # Raw input values: {"bmi": 35, "age": 55, ...}
    prediction = Column(String)     # "High Risk" | "Healthy Heart" | etc.
    confidence = Column(Float)      # 94.2 (percentage)
    risk_level = Column(String)     # "High" | "Moderate" | "Low"
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to user
    owner = relationship("User", back_populates="records")
```

**Why JSON column for `data`?**
- Each disease has different input fields (diabetes: 9 features, kidney: 24 features)
- JSON column stores any shape of data without schema changes
- Alternative: separate table per disease â€” more normalized but more complex

### Appointments Table:

```python
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    
    appointment_date = Column(DateTime)
    status = Column(String, default="scheduled")  # "scheduled" | "completed" | "cancelled"
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Q: How do you handle database sessions? Explain dependency injection.

### The Session Lifecycle:

```python
# backend/database.py

def get_db():
    """Yield a database session, guaranteed to close even on error."""
    db = SessionLocal()
    try:
        yield db       # Provide session to the route handler
    finally:
        db.close()     # ALWAYS close â€” prevents connection leaks
```

### How It's Used in Route Handlers:

```python
# backend/auth.py

from fastapi import Depends
from sqlalchemy.orm import Session

@router.post("/signup")
def signup(
    username: str,
    password: str,
    db: Session = Depends(get_db)  # FastAPI auto-calls get_db()
):
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    
    # Create user
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    user = User(username=username, hashed_password=hashed.decode())
    db.add(user)
    db.commit()          # Save to database
    db.refresh(user)     # Reload with generated ID
    
    return {"id": user.id, "username": user.username}
    # After return â†’ finally block closes the session
```

### Why Dependency Injection?

```python
# WITHOUT DI (bad â€” session leak risk):
@router.get("/records")
def get_records():
    db = SessionLocal()
    records = db.query(Record).all()
    db.close()  # What if the query throws an error? Session LEAKS!
    return records

# WITH DI (good â€” guaranteed cleanup):
@router.get("/records")
def get_records(db: Session = Depends(get_db)):
    return db.query(Record).all()
    # Session auto-closes via finally block, even on error
```

**Benefits:**
1. **No session leaks** â€” `finally` guarantees cleanup
2. **Testable** â€” override `get_db` with a test database in tests
3. **DRY** â€” don't write session open/close in every handler
4. **FastAPI auto-handles** â€” just declare `db: Session = Depends(get_db)`

---

## Q: How do you handle database migrations?

### Smart Migration on Startup:

```python
# backend/database.py

def run_migrations():
    """Check and add missing columns on startup.
    This is called during FastAPI lifespan, before any requests."""
    
    inspector = inspect(engine)
    
    # Check if tables exist at all
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
        return
    
    # Check for missing columns
    existing_columns = {col['name'] for col in inspector.get_columns("users")}
    
    required_columns = {
        "about_me": "TEXT DEFAULT ''",
        "plan_tier": "VARCHAR DEFAULT 'free'",
        "subscription_expiry": "TIMESTAMP",
        "gender": "VARCHAR DEFAULT ''",
        "dob": "VARCHAR DEFAULT ''",
        "blood_type": "VARCHAR DEFAULT ''",
        "height": "VARCHAR DEFAULT ''",
        "weight": "VARCHAR DEFAULT ''",
    }
    
    with engine.connect() as conn:
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                logger.info(f"Added column: users.{col_name}")
        conn.commit()
```

### Why Not Alembic?

| | Our Approach | Alembic |
|---|---|---|
| Complexity | ~30 lines of code | Full migration framework |
| Files | Zero migration files | Migration scripts per change |
| Team collaboration | Simple (one dev) | Essential (multiple devs) |
| Rollback | Manual | Built-in `alembic downgrade` |
| Production use | OK for small projects | Required for large teams |

**Decision**: For this project size, startup migration is simpler. I'd switch to Alembic for a team project with multiple developers and production deployments.

---

## Q: Show me example database queries from the actual app.

### Get user's health records with filtering:
```python
@router.get("/records")
def get_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record_type: str = None,
    limit: int = 50
):
    query = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id  # Only own records
    )
    
    if record_type:
        query = query.filter(HealthRecord.record_type == record_type)
    
    return query.order_by(HealthRecord.timestamp.desc()).limit(limit).all()
```

### Admin: Get all users with record counts:
```python
@router.get("/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(
        User.id,
        User.username,
        User.role,
        func.count(HealthRecord.id).label("record_count")
    ).outerjoin(HealthRecord).group_by(User.id).all()
    
    return [{"id": u.id, "username": u.username, "role": u.role, 
             "records": u.record_count} for u in users]
```

### Save prediction result:
```python
def save_prediction(db: Session, user_id: int, disease: str, 
                     data: dict, prediction: str, confidence: float):
    record = HealthRecord(
        user_id=user_id,
        record_type=disease,
        data=data,           # JSON: {"bmi": 35, "age": 55, ...}
        prediction=prediction,  # "High Risk"
        confidence=confidence,  # 94.2
        risk_level="High" if confidence >= 75 else "Moderate" if confidence >= 40 else "Low"
    )
    db.add(record)
    db.commit()
    return record
```

---

## Q: What is SQLAlchemy and how does it prevent SQL injection?

### ORM = Object-Relational Mapping

```python
# WITHOUT ORM (raw SQL â€” vulnerable to injection):
username = request.form["username"]
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
# If username = "admin'; DROP TABLE users; --" â†’ DATABASE DESTROYED

# WITH SQLAlchemy ORM (safe):
user = db.query(User).filter(User.username == username).first()
# SQLAlchemy parameterizes: SELECT * FROM users WHERE username = ?
# The username value is NEVER concatenated into the SQL string
```

### How SQLAlchemy Works Under the Hood:

```python
# Python ORM code:
db.query(User).filter(User.role == "admin").order_by(User.created_at.desc()).limit(10)

# Translates to SQL:
SELECT * FROM users WHERE role = 'admin' ORDER BY created_at DESC LIMIT 10

# The translation happens via Dialect:
# SQLite dialect â†’ SQLite SQL
# PostgreSQL dialect â†’ PostgreSQL SQL
# Same Python code â†’ different SQL based on DATABASE_URL
```

---

## Q: How would you migrate from SQLite to PostgreSQL in production?

### Step-by-step:

```bash
# 1. Set up PostgreSQL (e.g., on Neon.tech)
# Get connection string: postgresql://user:pass@host/dbname

# 2. Set environment variable
export DATABASE_URL="postgresql://user:pass@ep-cool.neon.tech/healthcare"

# 3. Start the app â€” it auto-creates tables and runs migrations
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 4. Migrate existing data (if needed)
python scripts/migrate_sqlite_to_postgres.py
```

### Migration script:
```python
import sqlite3
import psycopg2

# Read from SQLite
sqlite_conn = sqlite3.connect("healthcare.db")
users = sqlite_conn.execute("SELECT * FROM users").fetchall()

# Write to PostgreSQL
pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
for user in users:
    pg_conn.execute("INSERT INTO users VALUES (%s, %s, ...)", user)
pg_conn.commit()
```

**What changes**: Nothing in the application code. Only the `DATABASE_URL` environment variable. SQLAlchemy handles all dialect differences internally.


---

# 07 â€” Security & Compliance

> Every security concept in your project explained from scratch with examples.

---

## Q: How do you handle authentication and authorization?

First, understand the difference:
- **Authentication** = WHO are you? (Login with username + password)
- **Authorization** = WHAT can you do? (Admin can see all patients; patient can only see their own records)

### Authentication Flow (Step by Step):

```
Step 1: User enters username + password on the login page
            â†“
Step 2: Frontend sends POST /login with credentials
        Body: username=pavan&password=secret123
        Format: application/x-www-form-urlencoded (this is the OAuth2 spec format,
                not JSON â€” because OAuth2 standard requires form-encoded login)
            â†“
Step 3: Backend receives the request
        Looks up "pavan" in the database
        Finds: hashed_password = "$2b$12$LJ3qPe7x8Vk9J4..."
            â†“
Step 4: bcrypt.checkpw("secret123", stored_hash)
        bcrypt takes the entered password, applies the SAME salt
        from the stored hash, hashes it, and compares.
        If they match â†’ password is correct
        If not â†’ return 401 Unauthorized
            â†“
Step 5: Create JWT token
        payload = {
            "sub": "pavan",       # Who this token belongs to
            "role": "patient",    # What they can do
            "exp": 1718000000     # When this token expires (24 hours from now)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        # SECRET_KEY = a long random string only the server knows
        # HS256 = HMAC-SHA256 signing algorithm
            â†“
Step 6: Return token to frontend
        {"access_token": "eyJhbGciOiJIUzI1NiJ9.eyJ...", "token_type": "bearer"}
            â†“
Step 7: Frontend stores token in localStorage
        Every future request includes:
        Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJ...
            â†“
Step 8: On every API call, backend middleware:
        a) Extracts the token from Authorization header
        b) Decodes it with SECRET_KEY
        c) Checks if it's expired
        d) Extracts username and role
        e) Now knows WHO is making the request and WHAT they can do
```

### What is JWT? (JSON Web Token)

A JWT is a string with 3 parts separated by dots:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwYXZhbiIsImV4cCI6MTcxOH0.abc123signature
â†‘ HEADER                â†‘ PAYLOAD                              â†‘ SIGNATURE

HEADER (base64 encoded):
{
    "alg": "HS256",     # Algorithm used for signing
    "typ": "JWT"        # Token type
}

PAYLOAD (base64 encoded):
{
    "sub": "pavan",     # Subject (who this token is for)
    "role": "patient",  # User's role
    "exp": 1718000000   # Expiry timestamp (Unix epoch)
}

SIGNATURE:
HMAC-SHA256(
    base64(header) + "." + base64(payload),
    SECRET_KEY   # Only the server knows this string
)
```

**Why is the signature important?** If someone intercepts the token and changes "patient" to "admin" in the payload, the signature won't match anymore. The server recalculates the signature using the secret key and compares â€” if they don't match, the token is rejected. You can't forge a valid token without knowing the SECRET_KEY.

**Why JWT over sessions?**

| Feature | JWT (your project) | Sessions |
|---|---|---|
| Where stored | Client (localStorage) | Server (in memory or database) |
| Server state | Stateless â€” nothing stored | Stateful â€” session table |
| Scaling | Easy â€” any server can verify | Hard â€” need shared session store |
| Database hit per request | None (just decode token) | Yes (lookup session ID) |
| Revocation | Hard (wait for expiry) | Easy (delete from server) |
| Mobile-friendly | Yes (just send header) | Harder (cookies are complex on mobile) |

**JWT code in your project:**
```python
# backend/auth.py

from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")
ALGORITHM = "HS256"

def create_token(username: str, role: str) -> str:
    """Create a JWT token after successful login."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decode JWT and return the current user. Called on every protected route."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

---

### What is bcrypt? (Password Hashing)

**The problem**: If you store passwords as plain text and your database gets hacked:

```
BAD â€” plain text passwords:
| username | password    |
|----------|-------------|
| pavan    | secret123   |  â† Hacker reads this directly
| alice    | mypassword  |  â† Every password exposed

GOOD â€” bcrypt hashed passwords:
| username | hashed_password                                          |
|----------|----------------------------------------------------------|
| pavan    | $2b$12$LJ3qPe7x8Vk9J4nZ1mD5Oe3xYz.KN1aBc2dEf3gH4iJ5kL |
| alice    | $2b$12$Mn5oP1qR2sT3uV4wX5yZ6a7bC8dE9fG0hI1jK2lM3nO4pQ5r |
```

**How bcrypt works (step by step):**

```
1. SIGNUP â€” User enters password "secret123"
        â†“
2. bcrypt generates a RANDOM SALT: "$2b$12$LJ3qPe7x8Vk9J4nZ1mD5O"
   (Salt = random string added to the password before hashing.
    This means even if two users have the SAME password "secret123",
    their hashes will be DIFFERENT because different salts.)
        â†“
3. bcrypt hashes: hash("secret123" + salt) using Blowfish cipher
   This takes ~100ms ON PURPOSE (see "Why intentionally slow?" below)
        â†“
4. Store in database: "$2b$12$LJ3qPe7x8Vk9J4nZ1mD5Oe3xYz.KN1aBc..."
   The stored string contains: algorithm ($2b) + cost ($12) + salt + hash
        â†“
5. LOGIN â€” User enters password "secret123" again
        â†“
6. bcrypt extracts the salt from the stored hash
   Re-hashes: hash("secret123" + same_salt)
   Compares: does the new hash match the stored hash?
   If yes â†’ password correct. If no â†’ wrong password.
```

**Why intentionally slow?** At 100ms per hash, an attacker can only try ~10 passwords per second. With a fast hash like MD5 (which takes microseconds), an attacker could try BILLIONS of passwords per second. The slowness IS the security.

```python
# Your code in backend/auth.py:
import bcrypt

# During signup:
password = "secret123"
salt = bcrypt.gensalt()  # Random salt, different each time
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
# Store 'hashed' in the database

# During login:
entered_password = "secret123"
stored_hash = user.hashed_password.encode('utf-8')  # From database

if bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash):
    # Password correct â†’ create JWT token
    token = create_token(user.username, user.role)
    return {"access_token": token}
else:
    raise HTTPException(status_code=401, detail="Incorrect password")
```

---

### Authorization (Role-Based Access Control)

After authentication tells us WHO the user is, authorization determines WHAT they can do:

```python
# Patient can only see THEIR OWN records:
@router.get("/my-records")
def get_my_records(
    current_user: User = Depends(get_current_user),  # Auth check
    db: Session = Depends(get_db)
):
    # Filter by current_user.id â€” can NEVER see another patient's data
    return db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id
    ).all()

# Admin can see ALL records:
@router.get("/admin/all-records")
def get_all_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(HealthRecord).all()
```

**The key**: A patient calling `/admin/all-records` gets 403 Forbidden. A patient calling `/my-records` only gets THEIR records because the query always filters by `current_user.id`.

---

## Q: How do you prevent common web attacks?

| Attack | What It Is (Simply) | How Your System Prevents It |
|---|---|---|
| **SQL Injection** | Attacker puts SQL code in input fields: `username = "'; DROP TABLE users; --"`. If you build SQL strings with user input, the attacker's SQL executes. | **SQLAlchemy ORM** â€” NEVER builds SQL strings from user input. All values are parameterized: `WHERE username = ?` (the `?` is filled in safely by the database driver). |
| **XSS (Cross-Site Scripting)** | Attacker injects JavaScript into your page: `<script>steal(cookies)</script>`. If the page renders this, the script runs in every visitor's browser. | **React auto-escapes** â€” All text rendered via JSX is escaped. `<script>` becomes `&lt;script&gt;` (visible text, not executable code). |
| **CSRF (Cross-Site Request Forgery)** | Attacker tricks your browser into making requests to your API while you're logged in (e.g., a hidden form on an evil site that submits to your `/delete-account` endpoint). Works because browsers auto-attach cookies. | **JWT in headers, not cookies** â€” Your API doesn't use cookies. The JWT token is sent in the `Authorization` header, which browsers don't auto-attach. A malicious site can't add custom headers to cross-origin requests. |
| **Clickjacking** | Attacker loads your site in an invisible iframe, puts fake buttons on top. User thinks they're clicking "Play Video" but actually clicking "Delete My Account" on your hidden site. | **`X-Frame-Options: DENY`** header â€” Browsers refuse to load your site in any iframe. The SecurityHeadersMiddleware adds this to every response. |
| **Brute Force** | Attacker tries thousands of password combinations rapidly until one works. | **Rate limiting** â€” After too many requests from the same IP, further requests are blocked. Also, **bcrypt is slow by design** â€” each password check takes ~100ms, limiting attacker to ~10 attempts/second. |
| **Information Disclosure** | Attacker triggers an error to see stack traces, file paths, or database queries in the error response. This reveals your tech stack, file structure, and potential vulnerabilities. | **ExceptionMiddleware** catches ALL unhandled errors. Returns a UUID error ID to the user: `{"detail": "Error: a1b2c3d4"}`. The actual stack trace is logged server-side only. No file paths, no SQL queries, no PII in the response. |
| **Password Theft** | Attacker gets database access (SQL injection, backup theft, insider). If passwords are in plain text, every account is compromised. | **bcrypt hashing** â€” Even with full database access, attacker sees `$2b$12$LJ3q...`, NOT the actual password. The hash is one-way â€” you cannot reverse it back to the password. |
| **Token Theft** | Attacker intercepts the JWT token (network sniffing, XSS). | **HTTPS in production** encrypts all traffic â€” tokens can't be intercepted. **24-hour expiry** limits the damage window. **No sensitive data in token** â€” even if stolen, it only contains username and role, not passwords or health data. |

---

## Q: What is HIPAA and how does your system address it?

**HIPAA** (Health Insurance Portability and Accountability Act) is a US law that says: "If you handle patient health data, you MUST protect it." Violating HIPAA can result in fines up to $1.5 million per incident.

HIPAA has three types of safeguards:

### 1. Technical Safeguards (what your CODE does):

| Requirement | What It Means | Your Implementation |
|---|---|---|
| Access controls | Only authorized people can access data | JWT + role-based auth: patients see only their records |
| Audit trail | Log who accessed what and when | LoggingMiddleware logs every request with timestamp and user ID |
| Encryption in transit | Data encrypted while traveling over the network | HTTPS in production (TLS certificate) |
| Encryption at rest | Data encrypted while stored | PostgreSQL encryption (Neon manages this) |
| Automatic logoff | Sessions expire after inactivity | JWT tokens expire after 24 hours |
| Unique user identification | Each user has a unique identity | Username + hashed password, unique user ID |

### 2. Administrative Safeguards (NOT in your code, but know about them):
- Employee training on data handling
- Designated privacy officer
- Regular risk assessments
- Business associate agreements with third parties (like Neon for database)

### 3. Physical Safeguards (NOT in your code):
- Locked server rooms
- Screen locks on workstations
- Secure disposal of hardware

**Your honest answer in an interview:**
> "My system implements the technical safeguards: JWT auth with role-based access control, bcrypt password hashing, HTTPS encryption, audit logging, and PII protection in error messages. Full HIPAA compliance also requires administrative and physical safeguards â€” staff training, risk assessments, and third-party audits â€” which are organizational, not code. I'm aware of the full picture, but my focus was on building the technical foundation."

---

## Q: How do you handle PII (Personally Identifiable Information)?

**PII** = Any data that can identify a specific person. In healthcare: names, dates of birth, health conditions, medical history.

**Your rules (from AGENTS.md):**
> "Never log or expose PII in error messages or debug output."

```python
# BAD â€” PII in error log (HIPAA violation):
logger.error(f"Failed prediction for {user.full_name}, DOB: {user.dob}, "
             f"health data: {patient_data}")
# If logs are compromised, attacker sees: "John Smith, DOB: 1980-05-15, BMI: 35"

# GOOD â€” generic error with tracking ID:
error_id = str(uuid.uuid4())[:8]  # Generate: "a1b2c3d4"
logger.error(f"Prediction error [{error_id}]: model={disease_type}, "
             f"user_id={user.id}")
# Log shows: "Prediction error [a1b2c3d4]: model=diabetes, user_id=42"
# No name, no DOB, no health data. Use error_id to find details in secure logs.

# Return to user:
return JSONResponse(
    status_code=500,
    content={"detail": f"Internal error. Reference: {error_id}"}
)
# User sees: "Internal error. Reference: a1b2c3d4"
# They can report this ID to support. Support can look up the secure server log.
```

**Where PII protection is enforced:**

| Location | Protection |
|---|---|
| API error responses | UUID error ID, never stack traces |
| Server logs | User ID only, never names/DOB/health data |
| AI chat responses | Medical disclaimers required |
| Database | Passwords bcrypt-hashed, health data access-controlled |
| Frontend | React auto-escapes, no PII in URL parameters |
| Git repository | `.env` file in `.gitignore`, secrets never committed |

---

## Q: What are your 7 middleware layers?

**Middleware** = Code that runs BEFORE your route handler processes a request and AFTER it sends a response. Like security checkpoints at an airport â€” every request passes through all of them.

```
                                    Request arrives from client
                                              â†“
Layer 1: CORS Middleware
         "Is this request coming from an ALLOWED origin?"
         Your frontend (localhost:3000) is allowed.
         A random malicious site (evil.com) is blocked.
         CORS = Cross-Origin Resource Sharing.
                                              â†“
Layer 2: Rate Limiting Middleware
         "Has this IP made too many requests recently?"
         If yes â†’ 429 Too Many Requests (blocks brute force attacks)
         If no â†’ let it through
                                              â†“
Layer 3: TrustedHost Middleware
         "Is the Host header a trusted domain?"
         Allows: localhost, 127.0.0.1, your-app.render.com
         Blocks: Host header attacks where attacker sets Host to evil.com
                                              â†“
Layer 4: Security Headers Middleware
         Adds defensive headers to EVERY response:
         X-Frame-Options: DENY          (prevent clickjacking)
         X-Content-Type-Options: nosniff (prevent MIME sniffing)
         X-XSS-Protection: 1           (legacy XSS filter)
                                              â†“
Layer 5: Exception Middleware
         Wraps everything in try/catch.
         If ANY unhandled error occurs anywhere:
         â†’ Log the full stack trace server-side
         â†’ Return generic error with UUID to client
         â†’ NEVER expose internal details to the user
                                              â†“
Layer 6: Request ID Middleware
         Generates a UUID for this request: "req-a1b2c3d4"
         Attaches it to logs, headers, and error messages.
         If user reports a bug: "I got error a1b2c3d4"
         You can search logs for exactly that request.
                                              â†“
Layer 7: Timing Middleware
         Records: start_time = now()
         After response: elapsed = now() - start_time
         Adds header: X-Process-Time: 0.009
         Logs: "GET /predict/diabetes completed in 9ms"
         This is how you know prediction takes ~9ms.
                                              â†“
                                    YOUR ROUTE HANDLER
                                    (predict_diabetes, login, etc.)
                                              â†“
                                    Response goes back through
                                    all layers in reverse order
                                              â†“
                                    Client receives response
```


---

# 08 â€” System Design

## Q: Draw the system architecture.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     HTTP/SSE      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  â”‚ â†â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â†’  â”‚         FastAPI Backend       â”‚
â”‚   Next.js 16     â”‚                    â”‚                              â”‚
â”‚   Frontend       â”‚                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                  â”‚                    â”‚  â”‚ Auth    â”‚  â”‚ Predict  â”‚  â”‚
â”‚  - 21 Routes     â”‚                    â”‚  â”‚ (JWT)   â”‚  â”‚ (5 ML)   â”‚  â”‚
â”‚  - Zustand       â”‚                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚  - Framer Motion â”‚                    â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  - SSE Chat      â”‚                    â”‚  â”‚ Chat    â”‚  â”‚ Admin    â”‚  â”‚
â”‚                  â”‚                    â”‚  â”‚ (RAG)   â”‚  â”‚ Routes   â”‚  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                    â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
                                        â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
                                        â”‚  â”‚Payments â”‚  â”‚ Reports  â”‚  â”‚
                                        â”‚  â”‚(Razorpay)â”‚ â”‚ (PDF)    â”‚  â”‚
                                        â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
                                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                              â”‚      â”‚         â”‚
                                              â–¼      â–¼         â–¼
                                        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                        â”‚ SQLite â”‚ â”‚.pklâ”‚ â”‚ Gemini  â”‚
                                        â”‚   DB   â”‚ â”‚ ML â”‚ â”‚  API    â”‚
                                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Q: How would you scale this to 10,000 concurrent users?

### Current Architecture (single server):
- SQLite (single writer)
- Single Uvicorn process
- Models in local RAM
- ~50 req/sec capacity

### Scaled Architecture:

```
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”
            â”‚  CDN     â”‚  (Vercel/CloudFront)
            â”‚ Frontend â”‚
            â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                 â”‚
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”
         â”‚  Load Balancer â”‚  (Nginx / AWS ALB)
         â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”
         â”‚       â”‚       â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”â”Œâ”€â”€â”€â–¼â”€â”€â”â”Œâ”€â”€â”€â–¼â”€â”€â”
    â”‚ API 1 â”‚â”‚API 2 â”‚â”‚API 3 â”‚  (3+ Uvicorn workers)
    â””â”€â”€â”€â”¬â”€â”€â”€â”˜â””â”€â”€â”¬â”€â”€â”€â”˜â””â”€â”€â”¬â”€â”€â”€â”˜
        â”‚       â”‚       â”‚
    â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”
    â”‚    PostgreSQL + Redis   â”‚
    â”‚   (Connection pooling)  â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

| Layer | Change | Why |
|---|---|---|
| Database | SQLite â†’ PostgreSQL | Concurrent writes, connection pooling |
| Cache | Add Redis | Session cache, rate limiting, query cache |
| Backend | Multiple workers | Handle concurrent requests |
| Load balancer | Nginx | Distribute requests across workers |
| Frontend | CDN | Static assets served from edge |
| ML Models | Shared memory / model server | Don't load per-worker |
| Tasks | Celery + Redis | Async PDF generation, emails |

## Q: How would you add a new disease model?

**5 steps, ~2 hours of work:**

1. **Training script** â€” `backend/train_parkinsons.py`
   - Load dataset, preprocess, train, save `.pkl`

2. **Feature names** â€” `backend/features.py`
   ```python
   PARKINSONS_FEATURES = ["tremor", "rigidity", "bradykinesia", ...]
   ```

3. **Pydantic schema** â€” `backend/schemas.py`
   ```python
   class ParkinsonsInput(BaseModel):
       tremor: int
       rigidity: float
       ...
   ```

4. **Prediction endpoint** â€” `backend/prediction.py`
   ```python
   @router.post("/predict/parkinsons")
   def predict_parkinsons(data: ParkinsonsInput):
       ...
   ```

5. **Frontend page** â€” `frontend/src/app/(protected)/predict/parkinsons/page.tsx`
   - Just pass field configs to `PredictionForm` component

## Q: How would you handle model versioning?

```
s3://models/
â”œâ”€â”€ diabetes/
â”‚   â”œâ”€â”€ v1/model.pkl        # Original
â”‚   â”œâ”€â”€ v2/model.pkl        # Class-balanced
â”‚   â””â”€â”€ v3/model.pkl        # Hyperparameter tuned
â”œâ”€â”€ heart/
â”‚   â”œâ”€â”€ v1/model.pkl
â”‚   â””â”€â”€ v2/model.pkl
â””â”€â”€ manifest.json           # Which version is active
```

**A/B testing:**
- Route 90% traffic to v2, 10% to v3
- Compare accuracy on real predictions
- Promote v3 if better, rollback if worse

## Q: What if Gemini API goes down?

**Fallback chain:**
1. Try Gemini API â†’ if timeout/error
2. Try Ollama (local LLM) â†’ if not available
3. Return friendly error: "AI chat is temporarily unavailable. Your prediction results are still available."

**Key**: Prediction endpoints DON'T depend on Gemini. They use local ML models. Chat is the only feature that needs the AI API.

## Q: Explain the complete request lifecycle.

```
1. User clicks "Execute Clinical Assessment"
2. React handleSubmit() validates form
3. predictDiabetes() â†’ apiFetch('/predict/diabetes', {body: data})
4. apiFetch injects Authorization header
5. fetch() sends HTTP POST

--- BACKEND ---
6. RateLimitMiddleware â†’ check IP isn't blocked
7. TrustedHostMiddleware â†’ verify Host header
8. CORSMiddleware â†’ add CORS headers
9. SecurityHeadersMiddleware â†’ add X-Frame-Options
10. GZipMiddleware â†’ (will compress response)
11. ExceptionMiddleware â†’ try/catch wrapper
12. LoggingMiddleware â†’ start timer

13. FastAPI routing â†’ /predict/diabetes
14. Pydantic validates DiabetesInput schema
    â†’ Missing field? Return 422 with field name
15. predict_diabetes() handler runs
16. Check diabetes_model is loaded â†’ else 503
17. Feature engineering (age â†’ bucket)
18. model.predict([features]) â†’ 0 or 1
19. model.predict_proba([features]) â†’ [0.06, 0.94]
20. Map to risk_level: 94.2% = "High"
21. Build response JSON

22. LoggingMiddleware â†’ log "POST /predict/diabetes - 200 (9ms)"
23. GZipMiddleware â†’ compress if >1KB
24. Response sent

--- FRONTEND ---
25. apiFetch receives JSON
26. setResult(response)
27. React re-renders result panel
28. Framer Motion animates confidence bar
29. Risk level badge appears
30. Medical disclaimer shown
```

## Q: What are the trade-offs in your design?

| Decision | Chose | Alternative | Why |
|---|---|---|---|
| Accuracy vs Sensitivity | Lower accuracy (71%) | Higher accuracy (87%) | Detecting disease > overall accuracy |
| SQLite vs PostgreSQL | SQLite | PostgreSQL | Zero-config for dev, easy demos |
| SSE vs WebSocket | SSE | WebSocket | Simpler for unidirectional streaming |
| Zustand vs Redux | Zustand | Redux | Less boilerplate for small state |
| JWT vs Sessions | JWT | Server sessions | Stateless, scales without session store |
| Models in git | Yes | S3/cloud | Small enough (1.6MB), simpler deployment |
| Pickle vs ONNX | Pickle | ONNX | Simpler, Python-only deployment |


---

# 09 â€” Testing Strategy

## Q: How do you test this system?

**Three-layer testing pyramid:**

```
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  E2E /   â”‚    48 real-world records (77% accuracy)
        â”‚Validationâ”‚
        â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
        â”‚Integrationâ”‚   28 checks (API + edge cases + auth)
        â”‚  Tests    â”‚
        â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
        â”‚   Unit   â”‚   141 tests (models, routes, services)
        â”‚   Tests  â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

| Layer | Count | What it tests | Speed |
|---|---|---|---|
| Unit | 141 | Individual functions, mocked dependencies | ~10 sec |
| Integration | 28 | Full API requests, real server | ~5 sec |
| Validation | 48 | Real patient records vs ground truth | ~10 sec |

---

## Q: Show me a unit test example.

```python
# tests/unit/test_strict_prediction.py

def test_predict_diabetes_success(client, mock_model):
    """Test diabetes prediction returns correct format."""
    mock_model.predict.return_value = [1]
    mock_model.predict_proba.return_value = [[0.1, 0.9]]
    
    response = client.post("/predict/diabetes", json={
        "hypertension": 1, "high_chol": 1, "bmi": 35,
        "smoking_history": 1, "heart_disease": 0,
        "physical_activity": 0, "general_health": 4,
        "gender": 1, "age": 55
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "risk_level" in data
    assert "disclaimer" in data

def test_predict_diabetes_model_unavailable(client):
    """Test graceful error when model not loaded."""
    # Model set to None
    response = client.post("/predict/diabetes", json={...})
    assert response.status_code == 503
    assert "not available" in response.json()["detail"].lower()

def test_predict_diabetes_invalid_input(client):
    """Test Pydantic validation catches missing fields."""
    response = client.post("/predict/diabetes", json={"hypertension": 1})
    assert response.status_code == 422  # Validation error
```

---

## Q: How do you mock AI calls in tests?

```python
# tests/conftest.py
import os
os.environ["TESTING"] = "1"  # Disable ExceptionMiddleware

@pytest.fixture
def mock_model(monkeypatch):
    """Replace real ML model with a mock."""
    mock = MagicMock()
    mock.predict.return_value = [0]
    mock.predict_proba.return_value = [[0.8, 0.2]]
    monkeypatch.setattr("backend.prediction.diabetes_model", mock)
    return mock

@pytest.fixture
def mock_genai(monkeypatch):
    """Replace Gemini API with a mock."""
    mock_response = MagicMock()
    mock_response.text = "This is a test response. Please consult a doctor."
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    monkeypatch.setattr("backend.core_ai.get_model", lambda: mock_model)
    return mock_model
```

**Why mock?**
- Tests don't depend on API keys (per AGENTS.md)
- Tests are fast (no network calls)
- Tests are free (no API costs)
- Tests are reliable (no flaky network issues)

---

## Q: Show me the integration test.

```python
# backend/test_enriched.py â€” 28 checks

# 1. Health check
r = httpx.get("http://127.0.0.1:8000/healthz")
assert r.status_code == 200

# 2. All 5 predictions return enriched responses
r = httpx.post("/predict/diabetes", json={...})
assert r.status_code == 200
assert "confidence" in r.json()
assert "risk_level" in r.json()
assert "disclaimer" in r.json()

# 3. Edge cases â€” missing fields return 422
r = httpx.post("/predict/diabetes", json={"hypertension": 1})
assert r.status_code == 422

# 4. Extreme values don't crash
r = httpx.post("/predict/diabetes", json={...bmi=0, age=0...})
assert r.status_code == 200

# 5. Auth endpoints work
r = httpx.post("/token", data={"username":"admin","password":"admin123"})
assert r.status_code == 200
token = r.json()["access_token"]

# 6. Protected endpoints reject unauthenticated requests
r = httpx.get("/profile")  # No token
assert r.status_code == 401

# 7. Frontend is accessible
r = httpx.get("http://127.0.0.1:3000")
assert r.status_code == 200
```

---

## Q: How do you validate ML model accuracy?

```python
# backend/test_predictions.py

# Pull REAL records from training data
df = pd.read_parquet("data/processed/diabetes.parquet")

# Take records with KNOWN labels
healthy = df[df["diabetes"] == 0].head(5)   # Known healthy
diabetic = df[df["diabetes"] == 1].head(5)  # Known diabetic

# Send through live API
for _, row in healthy.iterrows():
    response = httpx.post("/predict/diabetes", json=row_to_payload(row))
    expected = "Low Risk"
    actual = response.json()["prediction"]
    match = expected in actual
    
# Results: 48 records, 37 matched (77% accuracy)
```

---

## Q: What test categories do you have?

| File | Tests | What |
|---|---|---|
| `test_auth.py` | 15 | Login, signup, profile, JWT |
| `test_prediction.py` | 18 | All 5 models + edge cases |
| `test_rag.py` | 8 | Vector store CRUD |
| `test_vision.py` | 10 | Lab report analysis |
| `test_training.py` | 3 | Model training scripts |
| `test_strict_*.py` | 30+ | Error handling, unavailable models |
| `test_enriched.py` | 28 | Full integration checks |
| `test_predictions.py` | 48 | Real-world validation |

---

## Q: How do you run tests?

```bash
# All unit tests
python -m pytest tests/ -v
# Output: 141 passed in 10.08s

# Integration tests (requires running server)
python backend/test_enriched.py
# Output: 28 passed, 0 bugs

# Real-world validation (requires running server)
python backend/test_predictions.py
# Output: 37/48 correct (77%)
```


---

# 10 â€” Deployment & DevOps

> How the application goes from your laptop to the internet â€” every step explained.

---

## Q: How is your application deployed?

### The Architecture:

```
YOUR LAPTOP (Development)
â”œâ”€â”€ Frontend: Next.js on localhost:3000
â”œâ”€â”€ Backend: FastAPI on 127.0.0.1:8000
â””â”€â”€ Database: SQLite file (healthcare.db)

                    â†“ git push â†’ GitHub â†’ deploy

THE INTERNET (Production)
â”œâ”€â”€ Frontend: Vercel (free tier)
â”‚   â””â”€â”€ https://your-app.vercel.app
â”‚   â””â”€â”€ Built from /frontend folder
â”‚   â””â”€â”€ Connects to backend API via NEXT_PUBLIC_API_URL
â”‚
â”œâ”€â”€ Backend: Render (free tier)
â”‚   â””â”€â”€ https://your-api.onrender.com
â”‚   â””â”€â”€ Runs: uvicorn backend.main:app --host 0.0.0.0 --port 8000
â”‚   â””â”€â”€ Docker container with all dependencies
â”‚
â””â”€â”€ Database: Neon (managed PostgreSQL)
    â””â”€â”€ postgresql://user:pass@ep-cool.neon.tech/healthcare
    â””â”€â”€ Free tier: 0.5GB storage, auto-suspend after 5 min idle
```

### What is Docker? (Explained Simply)

**Problem**: "It works on my machine!" â€” Your app works on your laptop but breaks on the server because of different Python versions, missing packages, or OS differences.

**Solution**: Docker packages your application + ALL its dependencies into a container â€” a standardized box that runs identically everywhere.

**Analogy**: Shipping containers in the real world. Before containers, cargo was loaded loosely onto ships â€” things broke, got mixed up, were hard to move. Shipping containers standardized everything. Docker does the same for software.

```dockerfile
# Dockerfile â€” recipe for building the container

# Step 1: Start from a known base image (Python 3.11 on Linux)
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# This installs EXACT versions of every package
# --no-cache-dir saves disk space in the container

# Step 4: Copy your application code
COPY backend/ ./backend/
COPY data/ ./data/

# Step 5: Expose port 8000 (where FastAPI listens)
EXPOSE 8000

# Step 6: Command to run when container starts
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Docker concepts:**
- **Image**: The blueprint (your Dockerfile baked into a binary). Like a recipe.
- **Container**: A running instance of an image. Like the actual cake made from the recipe.
- **Registry**: Where images are stored (Docker Hub, GitHub Container Registry). Like a recipe book.
- **Layer**: Each instruction in Dockerfile creates a layer. Layers are cached â€” if `requirements.txt` hasn't changed, Docker reuses the cached layer instead of reinstalling everything.

### What is Docker Compose?

Docker Compose runs MULTIPLE containers together. Your app needs frontend + backend + database:

```yaml
# docker-compose.yml
version: "3.8"

services:
  backend:
    build: .                        # Build from Dockerfile
    ports:
      - "8000:8000"                 # Map host:container port
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/healthcare
      - GEMINI_API_KEY=${GEMINI_API_KEY}  # From .env file
    depends_on:
      - db                          # Start database FIRST

  db:
    image: postgres:16              # Official PostgreSQL image
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=healthcare
    volumes:
      - pgdata:/var/lib/postgresql/data  # Persist data across restarts

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

volumes:
  pgdata:  # Named volume for database persistence
```

**Run everything with ONE command:**
```bash
docker-compose up -d
# Starts: PostgreSQL â†’ Backend â†’ Frontend
# -d = detached (runs in background)
```

---

## Q: How do you handle environment configuration?

**The problem**: Development and production need different settings. You can't hardcode "localhost" in production or production database URLs in development.

**The solution**: Environment variables. Same code, different config.

```python
# backend/database.py
import os

# ONE line of code handles both environments:
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
#                        â†‘                â†‘
#                   If env var exists     If env var is NOT set
#                   (production)          (development default)
```

### Environment Variable Comparison:

| Variable | Development | Production |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./healthcare.db` | `postgresql://user:pass@neon.tech/db` |
| `SECRET_KEY` | `dev-fallback-key` | `a8f2k9x1m...` (random 64 chars) |
| `GEMINI_API_KEY` | Your API key | Production API key |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | `https://your-api.onrender.com` |
| `DEBUG` | `true` | `false` |

### How environment variables are managed:

```bash
# LOCAL DEVELOPMENT â€” .env file (NEVER committed to git!)
# .env
DATABASE_URL=sqlite:///./healthcare.db
SECRET_KEY=dev-fallback-key-not-for-production
GEMINI_API_KEY=AIzaSy...your-key...

# .gitignore includes:
.env          # NEVER commit secrets to git!
*.db          # Don't commit SQLite database
__pycache__/  # Don't commit compiled Python files

# PRODUCTION â€” Set in Render/Vercel dashboard
# Render â†’ Service â†’ Environment â†’ Add Variable
# DATABASE_URL = postgresql://...
# SECRET_KEY = (generated secure random string)
```

**Security rule**: NEVER commit `.env` to git. If you accidentally commit a secret, rotate it immediately â€” git history retains it forever even after deletion.

---

## Q: What is CI/CD?

**CI (Continuous Integration)** = Automatically test code when you push to GitHub.
**CD (Continuous Deployment)** = Automatically deploy code when tests pass.

```
Developer pushes code
        â†“
GitHub Actions runs:
  â”œâ”€â”€ Install dependencies
  â”œâ”€â”€ Run linting (code style checks)
  â”œâ”€â”€ Run pytest (141 unit tests + 28 integration)
  â”‚     â”œâ”€â”€ All pass? â†’ Continue
  â”‚     â””â”€â”€ Any fail? â†’ STOP. Don't deploy. Notify developer.
  â””â”€â”€ All green? â†’ Deploy automatically
        â†“
Render pulls latest code â†’ Builds Docker image â†’ Deploys
Vercel pulls latest code â†’ Builds Next.js â†’ Deploys
```

### What a GitHub Actions workflow looks like:

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]        # Run on every push to main
  pull_request:
    branches: [main]        # Run on every PR targeting main

jobs:
  test:
    runs-on: ubuntu-latest  # Free Linux VM from GitHub

    steps:
      - uses: actions/checkout@v4          # Download your code

      - uses: actions/setup-python@v5      # Install Python
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt  # Install dependencies

      - run: python -m pytest tests/ -v       # Run all tests
        env:
          DATABASE_URL: sqlite:///./test.db   # Use test database
          # Tests must NOT depend on external APIs (mock everything)
```

---

## Q: How does Render deployment work?

```
1. You push code to GitHub
        â†“
2. Render detects the push (webhook)
        â†“
3. Render builds your Docker image
   - Installs Python 3.11
   - pip install -r requirements.txt
   - Copies your code
        â†“
4. Render starts the container
   - Runs: uvicorn backend.main:app --host 0.0.0.0 --port 8000
   - Sets environment variables from dashboard
        â†“
5. Render routes traffic to your container
   - URL: https://your-api.onrender.com
   - Free tier: spins down after 15 minutes of inactivity
   - First request after spin-down takes ~30 seconds (cold start)
```

**Cold start** = When Render spins down your service to save resources, the next request has to wait for the container to start up again. This is normal on free tier. On paid tier, the service stays warm.

---

## Q: What's the difference between Vercel and Render?

| | Vercel | Render |
|---|---|---|
| Best for | Frontend (Next.js, React) | Backend (APIs, Docker) |
| Your usage | Next.js frontend | FastAPI backend |
| Free tier | Very generous | 750 hours/month |
| Cold starts | None (edge functions) | ~30 seconds on free tier |
| Custom domain | Yes | Yes |
| SSL/HTTPS | Automatic | Automatic |
| Build process | Next.js optimized | Docker-based |

---

## Q: How do you ensure development and production are in sync?

| Practice | Implementation |
|---|---|
| Same code, different config | Environment variables (`DATABASE_URL`, `SECRET_KEY`) |
| Same dependencies | `requirements.txt` pinned versions (`fastapi==0.115.12`) |
| Same runtime | Docker ensures identical Python version and OS |
| Same database schema | SQLAlchemy creates tables on startup, runs migrations |
| Same tests | CI runs the exact same test suite before every deploy |
| Same API contract | Pydantic models validate requests in both environments |


---

# 11 â€” Challenges & Learnings

## Q: What was the hardest bug you encountered?

### Bug: Models were 0 bytes after cloning

**Symptom**: Fresh `git clone` â†’ all models fail to load â†’ every prediction returns 503.

**Root cause**: `.gitignore` contained `*.pkl`, which silently prevented model files from being committed. Git tracked them as empty stubs.

**Discovery**: Worked fine on my machine (models built locally), but broke on any fresh clone.

**Fix**: Removed `*.pkl` from `.gitignore`, force-added model files with `git add -f *.pkl`.

**Lesson**: Always test from a fresh clone. "Works on my machine" is not enough.

---

### Bug: 87% accuracy but 0% disease detection

**Symptom**: Diabetes model had 86.7% accuracy. Sounds great. But tested with 5 known diabetic patients â€” detected ZERO.

**Root cause**: Dataset is 86% healthy. Model learned to always say "healthy" â†’ 86% accuracy by default.

**Fix**: Added `scale_pos_weight=6.16` to XGBoost. Accuracy dropped to 71.7%, but now it actually catches diabetic patients.

**Lesson**: Accuracy alone is meaningless for imbalanced datasets. Always check sensitivity (true positive rate).

---

### Bug: Lungs model returning wrong predictions

**Symptom**: Healthy patients classified as sick, sick patients classified as healthy â€” inverted results.

**Root cause**: The original survey dataset used `1=No, 2=Yes` encoding. My preprocessing converted to `0/1`, but the training data still had `1/2` values. Mismatch between training and inference encoding.

**Fix**: Standardized all inputs to `0/1` binary encoding in both training and API.

**Lesson**: Feature encoding must be IDENTICAL between training and inference. Even a shift of +1 can invert predictions.

---

### Bug: Heart model went from 5/5 to 0/5 detection

**Symptom**: After retraining heart model, it stopped detecting any disease.

**Root cause**: The BRFSS dataset has different column names than the Cleveland Heart Disease dataset the API expects. Column mapping was wrong â€” BMI was being used as "trestbps" (blood pressure), cholesterol as "fbs" (fasting blood sugar), etc.

**Fix**: Created a careful column mapping in `train_heart.py` that maps BRFSS fields to Cleveland schema fields.

**Lesson**: When using a dataset that doesn't match your API schema, document the mapping carefully.

---

### Bug: OneDrive corrupts model files

**Symptom**: After stopping the server with `Stop-Process -Force`, model files sometimes become corrupted (0 bytes or truncated).

**Root cause**: The project is on OneDrive. `Stop-Process -Force` kills Python while OneDrive is syncing the `.pkl` file â†’ file gets corrupted.

**Fix**: Use graceful shutdown (Ctrl+C) instead of force kill. Retrain models after corruption.

**Lesson**: Don't put ML model files on cloud-synced directories during development.

---

## Q: What trade-offs did you make and why?

### 1. Accuracy vs. Sensitivity
- **Chose**: Lower accuracy (71.7%) with disease detection
- **Rejected**: Higher accuracy (86.7%) that misses all diseases
- **Why**: In medical screening, catching a sick patient is more important than overall accuracy. A false positive â†’ patient sees a doctor (minor inconvenience). A false negative â†’ disease goes undetected (potentially fatal).

### 2. SQLite vs. PostgreSQL
- **Chose**: SQLite for development
- **Rejected**: PostgreSQL everywhere
- **Why**: SQLite is zero-config â€” clone and run. No database server to install. The code is database-agnostic via SQLAlchemy, so switching to PostgreSQL for production is one env variable change.

### 3. SSE vs. WebSocket for chat
- **Chose**: Server-Sent Events
- **Rejected**: WebSockets
- **Why**: Chat streaming is unidirectional (server â†’ client). SSE is simpler, works over standard HTTP, auto-reconnects, and doesn't need WebSocket upgrade handshake. WebSockets would add complexity with zero benefit.

### 4. Models in git vs. cloud storage
- **Chose**: Commit `.pkl` files to git
- **Rejected**: S3/GCS model storage
- **Why**: Total model size is ~1.6MB â€” trivial for git. Simpler deployment (no S3 credentials needed). For larger models (>100MB), I'd switch to cloud storage.

### 5. Monolith vs. Microservices
- **Chose**: Single FastAPI app
- **Rejected**: Separate services for auth, predictions, chat
- **Why**: For this scale, a monolith is simpler to develop, deploy, and debug. Microservices add network overhead, service discovery, and distributed tracing complexity.

---

## Q: What would you do differently?

| What | Current | I'd Change To | Why |
|---|---|---|---|
| Database | SQLite | PostgreSQL from day 1 | Avoid migration issues |
| Model format | Pickle | ONNX | Cross-platform, language-agnostic |
| Feature store | Ad-hoc | Feast | Consistent feature engineering |
| CI/CD | Manual | GitHub Actions | Automated testing on every push |
| Monitoring | Basic logging | Prometheus + Grafana | Real-time health metrics |
| Dev environment | Local | Docker Compose | One command to start everything |
| Model explanations | Limited | SHAP on every prediction | Show feature importance |

---

## Q: What did you learn from this project?

1. **Class imbalance is the #1 hidden bug in medical ML** â€” high accuracy can mean zero disease detection. Always check sensitivity.

2. **Model file management is harder than training** â€” `.gitignore` rules, cloud sync corruption, and force-kill can all destroy models.

3. **Medical AI MUST include disclaimers** â€” binary yes/no predictions without confidence scores or disclaimers are irresponsible.

4. **Reusable components save massive time** â€” PredictionForm handles all 5 diseases with zero code duplication.

5. **Test from a fresh clone** â€” "Works on my machine" is the most dangerous phrase in software engineering.

6. **Feature encoding must match** â€” A shift of +1 in categorical encoding can completely invert predictions.

7. **Middleware order matters** â€” FastAPI processes middleware in reverse order of addition. Getting this wrong breaks security.

---

## Q: How would you explain this to a non-technical person?

> "I built a website where you enter your health numbers â€” like blood pressure, BMI, and cholesterol â€” and it tells you if you might be at risk for diseases like diabetes or heart disease. It also shows how confident it is â€” like 'we're 94% sure you should see a doctor.' It has an AI chatbot that answers health questions too. It's like a health checkup you can do from home, but it always reminds you to see a real doctor."

---

## Q: What motivates you about this work?

> "A single line of code in the class balancing fix â€” `scale_pos_weight=6.16` â€” took the model from detecting zero diabetic patients to catching most of them. That one parameter could be the difference between someone getting treated early or being undiagnosed for years. That's what motivates me about healthcare AI â€” the impact per line of code is enormous."


---

# 14 â€” Code Walkthrough Guide

> When interviewers say "Walk me through your code" â€” this is exactly what to show.

---

## Walkthrough 1: The Prediction Pipeline (Most Important)

### Show this flow: Form â†’ API â†’ Model â†’ Response

**Start at the frontend** (`predict/diabetes/page.tsx`):
```tsx
// Each disease page is 30 lines â€” just field configs + API call
<PredictionForm
  title="Diabetes Risk Assessment"
  fields={[
    { name: "bmi", label: "BMI", type: "number", min: 10, max: 60 },
    { name: "hypertension", label: "Hypertension", type: "select",
      options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
    // ... 7 more fields
  ]}
  onSubmit={predictDiabetes}  // From api.ts
/>
```

**Point out**: "One component handles all 5 diseases. Each page just passes different field configs. Zero code duplication."

**Then show the API client** (`lib/api.ts`):
```typescript
export async function predictDiabetes(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
}
```

**Point out**: "Auto-injects auth token, handles errors, type-safe generics."

**Then show the backend endpoint** (`prediction.py`):
```python
@router.post("/predict/diabetes")
def predict_diabetes(data: schemas.DiabetesInput):
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Model not available")
    
    age_bucket = get_age_bucket(data.age)
    input_list = [data.hypertension, data.high_chol, data.bmi, 
                  data.smoking_history, data.heart_disease,
                  data.physical_activity, data.general_health,
                  data.gender, age_bucket]
    
    prediction = diabetes_model.predict([input_list])[0]
    confidence = _get_confidence(diabetes_model, input_list)
    risk_level = "High" if confidence >= 75 else "Moderate" if confidence >= 40 else "Low"
    
    return {
        "prediction": "High Risk" if prediction >= 1 else "Low Risk",
        "raw": int(prediction),
        "confidence": confidence,
        "risk_level": risk_level,
        "disclaimer": MEDICAL_DISCLAIMER
    }
```

**Point out**: 
- "Pydantic validates input automatically â€” missing fields return 422"
- "predict_proba gives us confidence, not just yes/no"
- "Medical disclaimer is always included per healthcare compliance rules"

**Then show the training script** (`train_diabetes.py`):
```python
# Class balancing â€” THE key technique
neg = (Y_train == 0).sum()   # 174,595
pos = (Y_train == 1).sum()   # 28,349
weight = neg / pos            # 6.16

model = xgb.XGBClassifier(scale_pos_weight=weight)
model.fit(X_train, Y_train)
```

**Point out**: "This one parameter took disease detection from 0% to 60%."

---

## Walkthrough 2: The Middleware Stack

**Show `main.py` lines 130-178**:

```python
# Order matters â€” last added runs FIRST
app.add_middleware(LoggingMiddleware)           # 7
app.add_middleware(ExceptionMiddleware)          # 6
app.add_middleware(GZipMiddleware)               # 5
app.add_middleware(SecurityHeadersMiddleware)    # 4
app.add_middleware(CORSMiddleware, ...)          # 3
app.add_middleware(TrustedHostMiddleware, ...)   # 2
app.add_middleware(RateLimitMiddleware)          # 1
```

**Point out**: 
- "7 layers of defense â€” rate limiting, host validation, CORS, security headers, compression, error masking, logging"
- "Exception middleware returns UUID error ID â€” never exposes stack traces"
- "This is enterprise-grade middleware architecture"

---

## Walkthrough 3: The Streaming Chat

**Show `streaming_chat.py`**:
```python
@router.post("/chat/stream")
async def stream_chat(request: ChatStreamRequest):
    async def generate():
        # 1. RAG search for patient context
        context = rag.search(request.message, user_id)
        
        # 2. Build prompt from registry
        prompt = prompt_registry.build(request.message, context)
        
        # 3. Stream from Gemini
        for chunk in model.generate_content(prompt, stream=True):
            yield f"data: {json.dumps({'token': chunk.text})}\n\n"
        
        yield f"data: {json.dumps({'status': 'complete'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Point out**:
- "RAG injects patient-specific context â€” AI knows the patient's history"
- "SSE streaming â€” tokens appear in real-time, not all at once"
- "Prompts come from the registry, never inline â€” maintainable and testable"

---

## Walkthrough 4: Authentication Flow

**Show `auth.py`**:
```python
# Password hashing (signup)
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# JWT creation (login)
token = jwt.encode({"sub": username, "role": role, "exp": expiry}, SECRET_KEY)

# Token verification (every protected request)
def get_current_user(token = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return db.query(User).filter(User.username == payload["sub"]).first()
```

**Point out**:
- "bcrypt + salt â€” industry standard password security"
- "JWT is stateless â€” no server-side session storage needed"
- "Dependency injection ensures auth is never forgotten on protected routes"

---

## What to Show When They Say "Show Me Your Tests"

```python
# 1. Unit test with mocking
def test_predict_diabetes_success(client, mock_model):
    mock_model.predict.return_value = [1]
    mock_model.predict_proba.return_value = [[0.1, 0.9]]
    response = client.post("/predict/diabetes", json={...})
    assert response.status_code == 200
    assert response.json()["confidence"] == 90.0

# 2. Edge case â€” model unavailable
def test_predict_model_unavailable(client):
    response = client.post("/predict/diabetes", json={...})
    assert response.status_code == 503

# 3. Validation â€” missing fields
def test_predict_invalid_input(client):
    response = client.post("/predict/diabetes", json={"hypertension": 1})
    assert response.status_code == 422

# 4. Real-world validation
# 48 actual patient records from training data
# 77% match ground truth labels
```

**Point out**: "Three testing layers â€” unit, integration, real-world validation. 141 + 28 + 48 = 217 total checks."

---

## File-by-File Impact Map

When asked "which files are most important?":

| Priority | File | Why |
|---|---|---|
| 1 | `prediction.py` | Core business logic â€” 5 prediction endpoints |
| 2 | `main.py` | Architecture decisions â€” middleware, lifespan, routing |
| 3 | `PredictionForm.tsx` | Reusable component pattern â€” handles all 5 diseases |
| 4 | `api.ts` | API client with auto-auth injection |
| 5 | `train_diabetes.py` | Class balancing technique |
| 6 | `auth.py` | JWT + bcrypt security |
| 7 | `core_ai.py` | AI gateway pattern |
| 8 | `globals.css` | Design system tokens |


---

# 15 â€” Exhaustive Q&A with Real Code Examples

> Every answer here uses ACTUAL code from the real codebase with file paths and line numbers.
> This is the "I want to know EVERYTHING" file.

---

## SECTION A: PREDICTION PIPELINE (The Core of the Project)

### Q: Walk me through exactly what happens when someone predicts diabetes. Show me the real code.

**Step 1 â€” Frontend form submission** (`frontend/src/components/predict/PredictionForm.tsx`, line 40):
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
            return;  // Stop â€” don't send invalid data
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

**Step 2 â€” API client sends request** (`frontend/src/lib/api.ts`, line 223):
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

**Step 3 â€” Backend receives and validates** (`backend/schemas.py`):
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
If ANY field is missing or wrong type â†’ FastAPI auto-returns 422:
```json
{"detail": [{"loc": ["body", "bmi"], "msg": "field required", "type": "value_error.missing"}]}
```

**Step 4 â€” Prediction logic** (`backend/prediction.py`, line 217-240):
```python
@router.post("/predict/diabetes", response_model=Dict[str, Any])
def predict_diabetes(data: schemas.DiabetesInput) -> Dict[str, Any]:
    # GUARD: Check model loaded
    if not diabetes_model:
        raise HTTPException(status_code=503, detail="Diabetes Model not available")
    try:
        # FEATURE ENGINEERING: Convert age to BRFSS bucket
        age_bucket = get_age_bucket(data.age)  # 55 years â†’ bucket 7
        
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
            prediction = prediction.item()  # numpy scalar â†’ Python int
        
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

**Step 5 â€” Confidence calculation** (`backend/prediction.py`, line 133-148):
```python
def _get_confidence(model, input_data):
    """Extract prediction probability from model."""
    try:
        proba = model.predict_proba(input_data)[0]
        # proba = [0.058, 0.942]  â†’ 5.8% healthy, 94.2% disease
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

**Step 6 â€” Frontend displays result** (`frontend/src/components/predict/PredictionForm.tsx`, line 337):
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
    Y = (df['diabetes'] >= 1).astype(int)  # 1 or 2 â†’ positive
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

**Diabetes** â€” age bucketing only:
```python
# prediction.py, line 115-129
def get_age_bucket(age: float) -> int:
    if age <= 24: return 1
    elif age <= 29: return 2
    # ... 
    else: return 13
```

**Liver** â€” log transform + scaling:
```python
# prediction.py, line 286-292
skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 
          'Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
for col in skewed:
    df[col] = np.log1p(df[col])  # log(1+x) handles zeros safely

X_scaled = liver_scaler.transform(df)  # StandardScaler
```
**Why log transform?** Bilirubin ranges from 0.1 to 75.0 â€” extreme skew. Log compresses the range so the model isn't dominated by outliers.

**Kidney/Lungs** â€” StandardScaler only:
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
**Why?** Client sees `"Error: a3f2b1c9"` â€” no stack traces, no PII leakage. Dev can search logs by error ID.

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
            description="BRFSS 2015 CDC Dataset â€¢ 253,680 Records â€¢ XGBoost Classifier"
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

**Impact**: 5 diseases Ã— ~200 lines each = 1,000 lines saved. One bug fix applies to all 5.

---

## SECTION G: REAL API RESPONSES

### Q: Show me actual API responses from the live system.

**Diabetes â€” High Risk:**
```json
{
    "prediction": "High Risk",
    "raw": 1,
    "confidence": 94.2,
    "risk_level": "High",
    "disclaimer": "This is an AI-assisted screening tool, not a medical diagnosis. Please consult a qualified healthcare professional for clinical decisions."
}
```

**Heart â€” Healthy (but moderate confidence):**
```json
{
    "prediction": "Healthy Heart",
    "raw": 0,
    "confidence": 47.3,
    "risk_level": "Moderate",
    "disclaimer": "This is an AI-assisted screening tool..."
}
```

**Lungs â€” Very high confidence:**
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
| Middleware layers | 7 | Rate limit â†’ Logging |
| CSS variables | ~25 | Design tokens |
| Lines of code | ~15,000+ | Full stack |


---


