# 01 — Project Overview

## Q: Give me a 2-minute elevator pitch of your project.

I built a **full-stack AI Healthcare System** that uses machine learning to predict 5 diseases — diabetes, heart disease, liver disease, chronic kidney disease, and lung cancer.

The **frontend** is a Next.js 16 app with a professional dark medical theme, 21 routes, and real-time streaming AI chat. The **backend** is FastAPI with JWT authentication, role-based access control, and 5 ML prediction endpoints that return not just yes/no, but confidence scores and risk levels.

Each model was trained on real medical datasets — BRFSS (253K CDC records), Indian Liver Patient Dataset, UCI Chronic Kidney Disease, and Lung Cancer Survey data. I handled class imbalance using `scale_pos_weight` in XGBoost, validated predictions against 48 real patient records (77% accuracy), and every prediction includes a medical disclaimer.

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

3. **Portfolio Value**: Healthcare AI demonstrates maturity — handling real-world data issues, security considerations, and ethical responsibilities that simple CRUD apps don't.

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
| Streaming | **SSE** | Simpler than WebSockets for unidirectional server→client |

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
2. **Login**: Enters credentials → JWT token stored in browser
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
