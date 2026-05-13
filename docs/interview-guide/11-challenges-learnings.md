# 11 — Challenges & Learnings

## Q: What was the hardest bug you encountered?

### Bug: Models were 0 bytes after cloning

**Symptom**: Fresh `git clone` → all models fail to load → every prediction returns 503.

**Root cause**: `.gitignore` contained `*.pkl`, which silently prevented model files from being committed. Git tracked them as empty stubs.

**Discovery**: Worked fine on my machine (models built locally), but broke on any fresh clone.

**Fix**: Removed `*.pkl` from `.gitignore`, force-added model files with `git add -f *.pkl`.

**Lesson**: Always test from a fresh clone. "Works on my machine" is not enough.

---

### Bug: 87% accuracy but 0% disease detection

**Symptom**: Diabetes model had 86.7% accuracy. Sounds great. But tested with 5 known diabetic patients — detected ZERO.

**Root cause**: Dataset is 86% healthy. Model learned to always say "healthy" → 86% accuracy by default.

**Fix**: Added `scale_pos_weight=6.16` to XGBoost. Accuracy dropped to 71.7%, but now it actually catches diabetic patients.

**Lesson**: Accuracy alone is meaningless for imbalanced datasets. Always check sensitivity (true positive rate).

---

### Bug: Lungs model returning wrong predictions

**Symptom**: Healthy patients classified as sick, sick patients classified as healthy — inverted results.

**Root cause**: The original survey dataset used `1=No, 2=Yes` encoding. My preprocessing converted to `0/1`, but the training data still had `1/2` values. Mismatch between training and inference encoding.

**Fix**: Standardized all inputs to `0/1` binary encoding in both training and API.

**Lesson**: Feature encoding must be IDENTICAL between training and inference. Even a shift of +1 can invert predictions.

---

### Bug: Heart model went from 5/5 to 0/5 detection

**Symptom**: After retraining heart model, it stopped detecting any disease.

**Root cause**: The BRFSS dataset has different column names than the Cleveland Heart Disease dataset the API expects. Column mapping was wrong — BMI was being used as "trestbps" (blood pressure), cholesterol as "fbs" (fasting blood sugar), etc.

**Fix**: Created a careful column mapping in `train_heart.py` that maps BRFSS fields to Cleveland schema fields.

**Lesson**: When using a dataset that doesn't match your API schema, document the mapping carefully.

---

### Bug: OneDrive corrupts model files

**Symptom**: After stopping the server with `Stop-Process -Force`, model files sometimes become corrupted (0 bytes or truncated).

**Root cause**: The project is on OneDrive. `Stop-Process -Force` kills Python while OneDrive is syncing the `.pkl` file → file gets corrupted.

**Fix**: Use graceful shutdown (Ctrl+C) instead of force kill. Retrain models after corruption.

**Lesson**: Don't put ML model files on cloud-synced directories during development.

---

## Q: What trade-offs did you make and why?

### 1. Accuracy vs. Sensitivity
- **Chose**: Lower accuracy (71.7%) with disease detection
- **Rejected**: Higher accuracy (86.7%) that misses all diseases
- **Why**: In medical screening, catching a sick patient is more important than overall accuracy. A false positive → patient sees a doctor (minor inconvenience). A false negative → disease goes undetected (potentially fatal).

### 2. SQLite vs. PostgreSQL
- **Chose**: SQLite for development
- **Rejected**: PostgreSQL everywhere
- **Why**: SQLite is zero-config — clone and run. No database server to install. The code is database-agnostic via SQLAlchemy, so switching to PostgreSQL for production is one env variable change.

### 3. SSE vs. WebSocket for chat
- **Chose**: Server-Sent Events
- **Rejected**: WebSockets
- **Why**: Chat streaming is unidirectional (server → client). SSE is simpler, works over standard HTTP, auto-reconnects, and doesn't need WebSocket upgrade handshake. WebSockets would add complexity with zero benefit.

### 4. Models in git vs. cloud storage
- **Chose**: Commit `.pkl` files to git
- **Rejected**: S3/GCS model storage
- **Why**: Total model size is ~1.6MB — trivial for git. Simpler deployment (no S3 credentials needed). For larger models (>100MB), I'd switch to cloud storage.

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

1. **Class imbalance is the #1 hidden bug in medical ML** — high accuracy can mean zero disease detection. Always check sensitivity.

2. **Model file management is harder than training** — `.gitignore` rules, cloud sync corruption, and force-kill can all destroy models.

3. **Medical AI MUST include disclaimers** — binary yes/no predictions without confidence scores or disclaimers are irresponsible.

4. **Reusable components save massive time** — PredictionForm handles all 5 diseases with zero code duplication.

5. **Test from a fresh clone** — "Works on my machine" is the most dangerous phrase in software engineering.

6. **Feature encoding must match** — A shift of +1 in categorical encoding can completely invert predictions.

7. **Middleware order matters** — FastAPI processes middleware in reverse order of addition. Getting this wrong breaks security.

---

## Q: How would you explain this to a non-technical person?

> "I built a website where you enter your health numbers — like blood pressure, BMI, and cholesterol — and it tells you if you might be at risk for diseases like diabetes or heart disease. It also shows how confident it is — like 'we're 94% sure you should see a doctor.' It has an AI chatbot that answers health questions too. It's like a health checkup you can do from home, but it always reminds you to see a real doctor."

---

## Q: What motivates you about this work?

> "A single line of code in the class balancing fix — `scale_pos_weight=6.16` — took the model from detecting zero diabetic patients to catching most of them. That one parameter could be the difference between someone getting treated early or being undiagnosed for years. That's what motivates me about healthcare AI — the impact per line of code is enormous."
