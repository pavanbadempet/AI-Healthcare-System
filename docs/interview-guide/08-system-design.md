# 08 — System Design

## Q: Draw the system architecture.

```
┌──────────────────┐     HTTP/SSE      ┌──────────────────────────────┐
│                  │ ←───────────────→  │         FastAPI Backend       │
│   Next.js 16     │                    │                              │
│   Frontend       │                    │  ┌─────────┐  ┌──────────┐  │
│                  │                    │  │ Auth    │  │ Predict  │  │
│  - 21 Routes     │                    │  │ (JWT)   │  │ (5 ML)   │  │
│  - Zustand       │                    │  └─────────┘  └──────────┘  │
│  - Framer Motion │                    │  ┌─────────┐  ┌──────────┐  │
│  - SSE Chat      │                    │  │ Chat    │  │ Admin    │  │
│                  │                    │  │ (RAG)   │  │ Routes   │  │
└──────────────────┘                    │  └─────────┘  └──────────┘  │
                                        │  ┌─────────┐  ┌──────────┐  │
                                        │  │Payments │  │ Reports  │  │
                                        │  │(Razorpay)│ │ (PDF)    │  │
                                        │  └─────────┘  └──────────┘  │
                                        └──────────────────────────────┘
                                              │      │         │
                                              ▼      ▼         ▼
                                        ┌────────┐ ┌────┐ ┌─────────┐
                                        │ SQLite │ │.pkl│ │ Gemini  │
                                        │   DB   │ │ ML │ │  API    │
                                        └────────┘ └────┘ └─────────┘
```

## Q: How would you scale this to 10,000 concurrent users?

### Current Architecture (single server):
- SQLite (single writer)
- Single Uvicorn process
- Models in local RAM
- ~50 req/sec capacity

### Scaled Architecture:

```
            ┌─────────┐
            │  CDN     │  (Vercel/CloudFront)
            │ Frontend │
            └────┬─────┘
                 │
         ┌───────┴───────┐
         │  Load Balancer │  (Nginx / AWS ALB)
         └───────┬───────┘
         ┌───────┼───────┐
         │       │       │
    ┌────▼──┐┌───▼──┐┌───▼──┐
    │ API 1 ││API 2 ││API 3 │  (3+ Uvicorn workers)
    └───┬───┘└──┬───┘└──┬───┘
        │       │       │
    ┌───▼───────▼───────▼───┐
    │    PostgreSQL + Redis   │
    │   (Connection pooling)  │
    └────────────────────────┘
```

| Layer | Change | Why |
|---|---|---|
| Database | SQLite → PostgreSQL | Concurrent writes, connection pooling |
| Cache | Add Redis | Session cache, rate limiting, query cache |
| Backend | Multiple workers | Handle concurrent requests |
| Load balancer | Nginx | Distribute requests across workers |
| Frontend | CDN | Static assets served from edge |
| ML Models | Shared memory / model server | Don't load per-worker |
| Tasks | Celery + Redis | Async PDF generation, emails |

## Q: How would you add a new disease model?

**5 steps, ~2 hours of work:**

1. **Training script** — `backend/train_parkinsons.py`
   - Load dataset, preprocess, train, save `.pkl`

2. **Feature names** — `backend/features.py`
   ```python
   PARKINSONS_FEATURES = ["tremor", "rigidity", "bradykinesia", ...]
   ```

3. **Pydantic schema** — `backend/schemas.py`
   ```python
   class ParkinsonsInput(BaseModel):
       tremor: int
       rigidity: float
       ...
   ```

4. **Prediction endpoint** — `backend/prediction.py`
   ```python
   @router.post("/predict/parkinsons")
   def predict_parkinsons(data: ParkinsonsInput):
       ...
   ```

5. **Frontend page** — `frontend/src/app/(protected)/predict/parkinsons/page.tsx`
   - Just pass field configs to `PredictionForm` component

## Q: How would you handle model versioning?

```
s3://models/
├── diabetes/
│   ├── v1/model.pkl        # Original
│   ├── v2/model.pkl        # Class-balanced
│   └── v3/model.pkl        # Hyperparameter tuned
├── heart/
│   ├── v1/model.pkl
│   └── v2/model.pkl
└── manifest.json           # Which version is active
```

**A/B testing:**
- Route 90% traffic to v2, 10% to v3
- Compare accuracy on real predictions
- Promote v3 if better, rollback if worse

## Q: What if Gemini API goes down?

**Fallback chain:**
1. Try Gemini API → if timeout/error
2. Try Ollama (local LLM) → if not available
3. Return friendly error: "AI chat is temporarily unavailable. Your prediction results are still available."

**Key**: Prediction endpoints DON'T depend on Gemini. They use local ML models. Chat is the only feature that needs the AI API.

## Q: Explain the complete request lifecycle.

```
1. User clicks "Execute Clinical Assessment"
2. React handleSubmit() validates form
3. predictDiabetes() → apiFetch('/predict/diabetes', {body: data})
4. apiFetch injects Authorization header
5. fetch() sends HTTP POST

--- BACKEND ---
6. RateLimitMiddleware → check IP isn't blocked
7. TrustedHostMiddleware → verify Host header
8. CORSMiddleware → add CORS headers
9. SecurityHeadersMiddleware → add X-Frame-Options
10. GZipMiddleware → (will compress response)
11. ExceptionMiddleware → try/catch wrapper
12. LoggingMiddleware → start timer

13. FastAPI routing → /predict/diabetes
14. Pydantic validates DiabetesInput schema
    → Missing field? Return 422 with field name
15. predict_diabetes() handler runs
16. Check diabetes_model is loaded → else 503
17. Feature engineering (age → bucket)
18. model.predict([features]) → 0 or 1
19. model.predict_proba([features]) → [0.06, 0.94]
20. Map to risk_level: 94.2% = "High"
21. Build response JSON

22. LoggingMiddleware → log "POST /predict/diabetes - 200 (9ms)"
23. GZipMiddleware → compress if >1KB
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
