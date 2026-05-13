# 13 — FAANG Interview Strategies

> How to present this project to impress at Google, Amazon, Microsoft, Meta, or any top company.

---

## The Golden Rule: NEVER Just Describe — Always Show DEPTH

**Bad answer**: "I used XGBoost to predict diabetes."
**FAANG answer**: "I chose XGBoost over neural nets because the dataset is tabular with 253K records and severe class imbalance at 6:1. XGBoost handles this natively with `scale_pos_weight`, and its gradient-boosted trees excel on structured data — outperforming deep learning for tabular problems according to the Grinsztajn et al. 2022 benchmark. I validated with 48 real patient records and achieved 77% accuracy."

---

## How to Structure EVERY Answer: STAR+I

| Step | What | Example |
|---|---|---|
| **S** - Situation | Set the context | "The diabetes dataset had 86% healthy, 14% diabetic records" |
| **T** - Task | What needed to be done | "I needed a screening model that actually catches diabetic patients" |
| **A** - Action | What YOU did (technical) | "I added scale_pos_weight=6.16 and switched from accuracy to sensitivity" |
| **R** - Result | Quantify the outcome | "Disease detection went from 0/5 to 4/5 known diabetic patients" |
| **I** - Impact/Insight | What you learned | "This taught me that accuracy alone is meaningless for imbalanced medical data" |

---

## System Design Questions (THE Most Important Round)

### Q: "Design a disease prediction system that handles 1M requests/day"

**Your answer framework:**

#### Step 1: Requirements (2 minutes)
```
Functional:
- Users submit health metrics → get prediction + confidence
- Support 5 disease models
- Real-time AI chat
- User auth + records

Non-functional:
- Latency: <100ms per prediction
- Availability: 99.9%
- Throughput: 1M req/day = ~12 req/sec average, ~100 req/sec peak
- Data privacy: HIPAA compliant
```

#### Step 2: High-Level Design (5 minutes)
```
                    ┌────────────────┐
                    │   CDN (Vercel) │
                    │   Frontend     │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ API Gateway    │  Rate limiting, auth
                    │ (Kong/Nginx)   │
                    └───────┬────────┘
                     ┌──────┼──────┐
                     │      │      │
              ┌──────▼┐ ┌───▼──┐ ┌─▼─────┐
              │Predict │ │Chat  │ │Auth   │
              │Service │ │Service│ │Service│
              └───┬────┘ └──┬───┘ └──┬────┘
                  │         │        │
           ┌──────▼──┐  ┌───▼──┐  ┌──▼──┐
           │Model    │  │Gemini│  │ DB  │
           │Server   │  │ API  │  │(PG) │
           │(TF Serve)│  └──────┘  └─────┘
           └─────────┘
```

#### Step 3: Deep Dive (10 minutes)
**Model Serving:**
- "Instead of pickle in RAM, I'd use TensorFlow Serving or Triton Inference Server"
- "Models versioned in S3: `s3://models/diabetes/v3/model.onnx`"
- "A/B testing: 90% traffic to v2, 10% to v3 — compare accuracy"
- "Canary deployment: roll out new model to 1% first"

**Caching:**
- "Redis cache for identical predictions — same inputs = same output"
- "Cache key: `hash(model_name + sorted(features))` → TTL 1 hour"
- "Reduces model inference calls by ~40% for repeat queries"

**Database:**
- "PostgreSQL with read replicas for /records queries"
- "Write-ahead log for prediction audit trail"
- "JSONB column for flexible health data storage"

**Scaling:**
- "Horizontal scaling: 3 API instances behind load balancer"
- "Model server scales independently — GPU instances for heavy models"
- "Chat service scales separately (SSE connections are long-lived)"

#### Step 4: Trade-offs (2 minutes)
- "Chose SSE over WebSocket for simplicity — sufficient for unidirectional streaming"
- "Chose PostgreSQL over NoSQL — structured health data benefits from relational integrity"
- "Chose ONNX over pickle — cross-platform, language-agnostic model format"

---

### Q: "How would you ensure this system is reliable?"

```
1. MONITORING
   - Prometheus metrics: request latency, error rate, model inference time
   - Grafana dashboards: real-time health
   - PagerDuty alerts: if p99 latency > 200ms or error rate > 1%

2. CIRCUIT BREAKER
   - If Gemini API fails 5x in 1 minute → stop calling, use fallback
   - Pattern: closed → open → half-open → closed

3. GRACEFUL DEGRADATION
   - Gemini down → Ollama local LLM → static FAQ responses
   - Database down → predictions still work (models in RAM)
   - Redis down → bypass cache, direct to service

4. HEALTH CHECKS
   - /healthz endpoint: checks DB connection + model loaded
   - Kubernetes liveness probe: restart if unhealthy
   - Readiness probe: don't route traffic until models loaded

5. DATA BACKUP
   - PostgreSQL: daily automated backups
   - Model files: versioned in S3 with 30-day retention
   - User data: encrypted at rest (AES-256)
```

---

## Behavioral Questions (STAR Format)

### Q: "Tell me about a time you faced a difficult technical challenge."

> **S**: I was building an AI healthcare system with a diabetes prediction model trained on 253K CDC records.
> 
> **T**: The model showed 86.7% accuracy during evaluation, which seemed great. But when I tested it with 5 known diabetic patients from the dataset, it detected zero of them.
> 
> **A**: I investigated and found severe class imbalance — 86% of records were healthy. The model learned to just predict "healthy" for everything, getting 86% accuracy by default. I researched class balancing techniques and implemented `scale_pos_weight=6.16` in XGBoost, which tells the algorithm that missing a diabetic patient is 6x worse than a false alarm.
> 
> **R**: Disease detection went from 0% to ~60%. Overall accuracy dropped to 71.7%, but the model now actually catches at-risk patients.
> 
> **I**: This taught me that accuracy alone is a misleading metric for imbalanced datasets. In healthcare, sensitivity (catching sick patients) matters more than overall accuracy. I now always check class distribution before evaluating any model.

---

### Q: "Tell me about a time you had to make a trade-off."

> **S**: I needed to choose between higher accuracy (86.7%) and actual disease detection capability for a medical screening tool.
> 
> **T**: The stakeholder value was in catching at-risk patients early, not in having a high accuracy number.
> 
> **A**: I intentionally accepted a 15-point accuracy drop by adding class balancing. I also added confidence scores and risk levels so users understand HOW confident the model is, and medical disclaimers so they know it's a screening tool, not a diagnosis.
> 
> **R**: The system now detects ~60% of positive cases (up from 0%) and every prediction comes with a confidence percentage. The trade-off was explicitly documented.
> 
> **I**: In production ML, optimizing for the right metric is more important than optimizing for a vanity metric. I'd rather ship a 72% accurate model that saves lives than an 87% one that catches no one.

---

### Q: "Tell me about a time you debugged a complex issue."

> **S**: After deploying the heart disease model, it went from detecting 5/5 known cases to 0/5 — a complete regression.
> 
> **T**: I needed to find why the same model on the same data was now giving inverted results.
> 
> **A**: I systematically debugged: (1) Checked model file wasn't corrupted — it was fine. (2) Checked API endpoint — requests were reaching the model. (3) Printed raw features being sent to the model vs. what training expected. Found the bug: the BRFSS dataset has different column names than the Cleveland Heart Disease schema our API uses. The column mapping was wrong — BMI was being interpreted as blood pressure.
> 
> **R**: Fixed the column mapping in `train_heart.py`, retrained, and detection went back to 5/5.
> 
> **I**: Feature alignment between training and inference is critical. Even if the model is perfect, sending features in the wrong order or with wrong encoding will produce garbage predictions. I now always have a test that validates feature alignment.

---

## Power Phrases That Impress FAANG Interviewers

| Instead of saying... | Say this... |
|---|---|
| "I used XGBoost" | "I chose XGBoost because it's the state-of-the-art for tabular data with class imbalance" |
| "I added error handling" | "I implemented a 7-layer middleware stack with rate limiting, security headers, and error masking" |
| "I tested it" | "I validated with 3 testing layers: 141 unit tests, 28 integration checks, and 48 real-world patient records" |
| "It's a healthcare app" | "It's a clinical-grade screening system with confidence scoring, risk stratification, and medical disclaimers" |
| "I used React" | "I built a reusable component architecture — one PredictionForm component powers all 5 disease pages" |
| "I stored data" | "I used SQLAlchemy ORM with dependency injection for session lifecycle management" |
| "I did authentication" | "I implemented OAuth2 with JWT tokens, bcrypt password hashing, and role-based access control" |
| "I deployed it" | "The system is deployment-ready with Docker support, environment-based configuration, and CI/CD pipeline design" |

---

## Questions YOU Should Ask the Interviewer

These show senior-level thinking:

1. "How does your team handle model versioning and A/B testing in production?"
2. "What's your approach to monitoring ML model drift in production?"
3. "How do you balance feature velocity with technical debt in healthcare compliance?"
4. "What's the biggest challenge your team faces with real-time data pipelines?"
5. "How does your team handle PII/PHI in development and staging environments?"

---

## Red Flags to Avoid

| Don't... | Do... |
|---|---|
| Say "I just followed a tutorial" | Say "I researched multiple approaches and chose X because..." |
| Give one-word answers | Always give context → action → result |
| Skip trade-offs | Always mention what you considered AND rejected |
| Ignore failure modes | Always discuss what happens when things break |
| Forget security | Always mention auth, PII protection, HIPAA awareness |
| Present without numbers | Always quantify: 253K records, 77% accuracy, 141 tests, 9ms latency |
