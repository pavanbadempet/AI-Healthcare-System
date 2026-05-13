# 03 — Backend Deep Dive

## Q: Explain the backend architecture.

FastAPI application with modular design:

```
Request → Middleware Stack (7 layers) → Router → Handler → Response
                                           ↓
                              Database / ML Model / AI Service
```

**40+ modules** organized by responsibility:
- **Core**: `main.py`, `database.py`, `models.py`, `schemas.py`
- **Auth**: `auth.py`, `security.py`
- **Prediction**: `prediction.py`, `features.py`, 5× `train_*.py`
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
# Pydantic validates AUTOMATICALLY — no manual checking
class DiabetesInput(BaseModel):
    hypertension: int
    bmi: float
    age: float

@router.post("/predict/diabetes")
def predict(data: DiabetesInput):  # Invalid input → 422 automatically
    ...
```

---

## Q: Explain the middleware stack in detail.

```python
# Order matters — last added runs FIRST
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
Request → RateLimit → TrustedHost → CORS → SecurityHeaders → GZip → Exception → Logging → Route
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
Only allows `127.0.0.1` and `aio-health-backend.onrender.com`. Blocks requests with other `Host` headers → prevents host header injection.

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
# Database session — created per request, always closed
def get_db():
    db = SessionLocal()
    try:
        yield db          # Provide to handler
    finally:
        db.close()        # Always cleanup, even on error

# Auth — decoded from JWT token
def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)):
    user = verify_and_get_user(token, db)
    return user

# Route handler — FastAPI auto-provides both dependencies
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
Route Handler → core_ai.generate() → Gemini API
                                    → Ollama (fallback)
```

**Benefits:**
1. **Single point of change** — Switch AI providers by editing one file
2. **Centralized error handling** — Retries, timeouts, fallbacks
3. **Rate limiting** — Control AI API costs
4. **API key management** — One place for all secrets
5. **Testability** — Mock one function to disable all AI calls

---

## Q: What is the Prompt Registry?

```python
# prompt_registry.py — ALL system prompts live here
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
- Lifespan is a context manager — guaranteed cleanup
- Models loaded ONCE at startup, not per-request
- Startup failures prevent the app from accepting requests
