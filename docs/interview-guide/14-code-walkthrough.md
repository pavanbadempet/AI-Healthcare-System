# 14 — Code Walkthrough Guide

> When interviewers say "Walk me through your code" — this is exactly what to show.

---

## Walkthrough 1: The Prediction Pipeline (Most Important)

### Show this flow: Form → API → Model → Response

**Start at the frontend** (`predict/diabetes/page.tsx`):
```tsx
// Each disease page is 30 lines — just field configs + API call
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
- "Pydantic validates input automatically — missing fields return 422"
- "predict_proba gives us confidence, not just yes/no"
- "Medical disclaimer is always included per healthcare compliance rules"

**Then show the training script** (`train_diabetes.py`):
```python
# Class balancing — THE key technique
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
# Order matters — last added runs FIRST
app.add_middleware(LoggingMiddleware)           # 7
app.add_middleware(ExceptionMiddleware)          # 6
app.add_middleware(GZipMiddleware)               # 5
app.add_middleware(SecurityHeadersMiddleware)    # 4
app.add_middleware(CORSMiddleware, ...)          # 3
app.add_middleware(TrustedHostMiddleware, ...)   # 2
app.add_middleware(RateLimitMiddleware)          # 1
```

**Point out**: 
- "7 layers of defense — rate limiting, host validation, CORS, security headers, compression, error masking, logging"
- "Exception middleware returns UUID error ID — never exposes stack traces"
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
- "RAG injects patient-specific context — AI knows the patient's history"
- "SSE streaming — tokens appear in real-time, not all at once"
- "Prompts come from the registry, never inline — maintainable and testable"

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
- "bcrypt + salt — industry standard password security"
- "JWT is stateless — no server-side session storage needed"
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

# 2. Edge case — model unavailable
def test_predict_model_unavailable(client):
    response = client.post("/predict/diabetes", json={...})
    assert response.status_code == 503

# 3. Validation — missing fields
def test_predict_invalid_input(client):
    response = client.post("/predict/diabetes", json={"hypertension": 1})
    assert response.status_code == 422

# 4. Real-world validation
# 48 actual patient records from training data
# 77% match ground truth labels
```

**Point out**: "Three testing layers — unit, integration, real-world validation. 141 + 28 + 48 = 217 total checks."

---

## File-by-File Impact Map

When asked "which files are most important?":

| Priority | File | Why |
|---|---|---|
| 1 | `prediction.py` | Core business logic — 5 prediction endpoints |
| 2 | `main.py` | Architecture decisions — middleware, lifespan, routing |
| 3 | `PredictionForm.tsx` | Reusable component pattern — handles all 5 diseases |
| 4 | `api.ts` | API client with auto-auth injection |
| 5 | `train_diabetes.py` | Class balancing technique |
| 6 | `auth.py` | JWT + bcrypt security |
| 7 | `core_ai.py` | AI gateway pattern |
| 8 | `globals.css` | Design system tokens |
