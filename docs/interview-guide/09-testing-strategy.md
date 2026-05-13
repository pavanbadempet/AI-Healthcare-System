# 09 — Testing Strategy

## Q: How do you test this system?

**Three-layer testing pyramid:**

```
        ┌──────────┐
        │  E2E /   │    48 real-world records (77% accuracy)
        │Validation│
        ├──────────┤
        │Integration│   28 checks (API + edge cases + auth)
        │  Tests    │
        ├──────────┤
        │   Unit   │   141 tests (models, routes, services)
        │   Tests  │
        └──────────┘
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
# backend/test_enriched.py — 28 checks

# 1. Health check
r = httpx.get("http://127.0.0.1:8000/healthz")
assert r.status_code == 200

# 2. All 5 predictions return enriched responses
r = httpx.post("/predict/diabetes", json={...})
assert r.status_code == 200
assert "confidence" in r.json()
assert "risk_level" in r.json()
assert "disclaimer" in r.json()

# 3. Edge cases — missing fields return 422
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
