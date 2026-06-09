# AI Healthcare System — Open-Source Medical AI Platform

> Disease prediction (XGBoost, 89–92% accuracy) · RAG medical chatbot · Hospital management · FHIR R4 · FastAPI · React 19 · LangGraph · Ollama · Kubernetes · Terraform AWS

<!-- First 160 chars above = Google meta description. Keep keyword-rich and under 160 characters. -->

<div align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System">
    <img
      src="docs/assets/hero-banner.svg"
      alt="AI Healthcare System — open-source medical AI platform for disease prediction, clinical chatbot, hospital management, FHIR R4, FastAPI, React 19"
      width="100%"
    />
  </a>

  <br /><br />

  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml">
    <img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI build status" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml">
    <img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL security analysis" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="MIT license" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers">
    <img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="GitHub stars" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues">
    <img src="https://img.shields.io/github/issues/pavanbadempet/AI-Healthcare-System?style=flat-square&color=ef4444" alt="Open issues" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/releases">
    <img src="https://img.shields.io/github/v/release/pavanbadempet/AI-Healthcare-System?style=flat-square&color=8b5cf6" alt="Latest release" />
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/network/members">
    <img src="https://img.shields.io/github/forks/pavanbadempet/AI-Healthcare-System?style=flat-square&color=06b6d4" alt="GitHub forks" />
  </a>

  <br /><br />

  <p>
    <b>Open-source medical AI platform for disease prediction, clinical chatbot, and hospital management.</b><br />
    Built with FastAPI · React 19 · LangGraph · XGBoost · SHAP · Ollama · FHIR R4 · Kubernetes · Terraform AWS
  </p>

  <p>
    Accessible to students. Trusted by industry. Runs on a laptop. Scales to AWS EKS.
  </p>

  <br />

  <p>
    <!-- 🚀 Add your live URL here once deployed — single biggest conversion improvement -->
    <!-- <a href="https://your-app.onrender.com"><img src="https://img.shields.io/badge/🚀%20Live%20Demo-%E2%86%92-22c55e?style=for-the-badge" alt="Live Demo" /></a> &nbsp; -->
    <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick%20Start-%E2%86%92-0ea5e9?style=for-the-badge" alt="Quick Start — get running in 5 minutes" /></a>
    &nbsp;
    <a href="#-for-students--learners"><img src="https://img.shields.io/badge/For%20Students-%E2%86%92-f59e0b?style=for-the-badge" alt="Learning guide for students" /></a>
    &nbsp;
    <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-%E2%86%92-8b5cf6?style=for-the-badge" alt="System architecture" /></a>
    &nbsp;
    <a href="#-faq"><img src="https://img.shields.io/badge/FAQ-%E2%86%92-ef4444?style=for-the-badge" alt="Frequently asked questions" /></a>
  </p>

  <br />

  <!-- 📸 HIGHEST PRIORITY ACTION: add a real screenshot here and uncomment -->
  <!-- <img src="docs/assets/screenshot-dashboard.png" alt="AI Healthcare System dashboard — disease prediction, medical chatbot, hospital capacity" width="90%" /> -->

</div>

---

<!-- ============================================================
  GITHUB TOPICS TO SET (go to repo → About → gear icon → Topics)
  Copy-paste all 20 into GitHub Topics for maximum discoverability:

  machine-learning  healthcare  fastapi  react  langraph  xgboost
  disease-prediction  medical-ai  rag  llm  ollama  gemini
  hospital-management  fhir  python  typescript  docker  kubernetes
  healthcare-ai  clinical-decision-support

  GITHUB DESCRIPTION TO SET (140 chars max):
  "Open-source medical AI: disease prediction (XGBoost 92%), RAG chatbot, hospital ops, FHIR R4, FastAPI, React 19, Ollama, K8s, Terraform"

  GITHUB WEBSITE FIELD:
  https://github.com/pavanbadempet/AI-Healthcare-System#-quick-start
  ============================================================ -->

## What Is AI Healthcare System?

**AI Healthcare System** is a production-ready, open-source medical AI platform that combines machine learning disease prediction, a RAG-powered medical chatbot, and full hospital management — in a single, well-architected codebase.

Built to the standards used in real health-tech products, it covers five core capabilities:

1. **Machine learning disease prediction** — XGBoost and scikit-learn ensemble models trained on real public clinical datasets (BRFSS CDC, Cleveland UCI, ILPD, UCI CKD) with SHAP explainability and published accuracy (Heart Disease: 92%, Diabetes: 89%)
2. **RAG-powered medical chatbot** — a LangGraph multi-agent system that retrieves each patient's actual health records before answering, with scoped access control and citation tracking
3. **3-tier AI inference engine** — automatic fallback: Ollama (local, free, private) → Gemini (free cloud) → OpenAI/Anthropic, with zero vendor lock-in
4. **Full hospital operations** — pharmacy, billing, nursing, lab diagnostics, discharge planning, bed management, real-time capacity telemetry
5. **Healthcare standards** — FHIR R4, India ABDM consent lifecycle, DICOMweb/PACS, SMART on FHIR EHR integration

From a college final-year project in machine learning to enterprise-grade healthcare infrastructure — this codebase is designed to be both studied and deployed.

---

## Why This Project Stands Out

| Capability | This project | Typical healthcare AI repo |
|---|:---:|:---:|
| Real trained ML models — not mocked | ✅ 5 models | ⚠️ usually 1 |
| Published accuracy (Heart: 92%, Diabetes: 89%) | ✅ | ❌ |
| SHAP feature-level explainability | ✅ | ❌ |
| Clinician override with PHI-safe audit trail | ✅ | ❌ |
| Local AI (Ollama) — no API key required | ✅ | ❌ |
| 3-tier AI fallback — zero vendor lock-in | ✅ | ❌ single provider |
| RAG grounded in patient's own records | ✅ scoped, ACL-enforced | ❌ |
| LangGraph multi-node agent with safety guardrails | ✅ | ❌ |
| Complete hospital ops (pharmacy, billing, nursing...) | ✅ 8 modules | ❌ |
| Real-time WebSocket hospital telemetry | ✅ | ❌ |
| FHIR R4 · ABDM · DICOMweb · SMART on FHIR | ✅ | ❌ |
| 8-layer security middleware, zero PII in errors | ✅ | ❌ |
| Property-based testing with Hypothesis | ✅ ~90 test files | ❌ |
| Kubernetes HA + Terraform AWS EKS | ✅ | ❌ |
| AI governance inventory (WHO/FDA/EU AI Act) | ✅ | ❌ |

---

## For Students & Learners

This codebase teaches real engineering patterns used in production AI systems — not simplified examples. Whether you're building a final-year project, preparing for a machine learning or software engineering interview, or learning modern full-stack development, every module here is a reference implementation.

**Find the concept you want to learn:**

| Learning Goal | File | What You'll See |
|---|---|---|
| How ML models serve predictions via REST API | `backend/prediction.py` | XGBoost loading, feature scaling, inference endpoint |
| How Retrieval-Augmented Generation (RAG) works | `backend/rag.py` + `backend/chat_context.py` | Embedding, vector search, context assembly |
| How LangGraph multi-agent systems are built | `backend/agent.py` | Supervisor routing, researcher, analyst, guardrail nodes |
| How to make AI provider-agnostic | `backend/core_ai.py` | 3-tier fallback, retry logic, TTL caching |
| How SHAP explains ML predictions | `backend/explainability.py` | Feature attribution for clinical decisions |
| How JWT auth and role-based access control work | `backend/auth.py` | Token creation, RBAC enforcement, DI pattern |
| How to structure a large FastAPI application | `backend/main.py` + routers | Middleware stack, router mounting, startup lifecycle |
| How property-based testing finds hidden bugs | `tests/unit/` | Hypothesis — auto-generated test cases |
| How CI/CD pipelines automate quality and deployment | `.github/workflows/` | 8 real pipelines: CI, CodeQL, Docker, HuggingFace |
| How Terraform provisions production AWS infrastructure | `terraform/main.tf` | VPC, EKS, RDS, ElastiCache, S3, Route53 |

---

## For Industry Engineers

<details>
<summary><b>Architecture decisions and production rationale</b></summary>

| Decision | Rationale |
|---|---|
| **Single AI gateway (`core_ai.py`)** | All provider SDK imports isolated to one module. No route handler may call `google.generativeai`, `openai`, or `anthropic` directly. Enforces audit logging at the boundary. Provider fallback, retry with exponential backoff, and 30s TTL caching are all centralized. |
| **Version-controlled prompt registry** | No system prompts inline in route handlers. Every template is versioned, activatable, and A/B testable. Templates include instruction-hierarchy guardrails that treat retrieved patient data as untrusted clinical evidence. |
| **Hierarchical `AGENTS.md` context system** | Root rules + subtree-scoped files give AI coding agents focused, token-efficient context. Consistency enforced in CI via `scripts/sync_agent_adapters.py --check`. |
| **Pydantic v2 strict validation** | Input rejection with structured errors before any ML inference. All schemas co-located with routes in `schemas.py`. |
| **`DATABASE_URL` from environment** | Zero-change swap between SQLite WAL (dev) and PostgreSQL with psycopg2 connection pooling (prod). `postgres://` → `postgresql://` normalization on startup. |
| **`/v1` prefix + `X-Request-ID` tracing** | Forward-compatible versioning. Per-request correlation IDs for distributed tracing across services. |
| **`ExceptionMiddleware` outermost** | Guarantees zero PII in any 500 response regardless of exception origin, complementing the PHI-safe audit writer in `audit.py`. |
| **turbovec Rust SIMD vector backend** | Optional drop-in for scikit-learn cosine similarity. Automatic transparent fallback if unavailable. |

</details>

<details>
<summary><b>Security architecture — 8-layer middleware, HIPAA/GDPR alignment</b></summary>

**Middleware execution order:**

```
1. RequestTracingMiddleware    injects X-Request-ID for distributed tracing
2. APIVersioningMiddleware     /v1 routing and version negotiation
3. RateLimitMiddleware         60 req/min per IP (RATE_LIMIT_REQUESTS_PER_MINUTE env)
4. TrustedHostMiddleware       allowlist via ALLOWED_HOSTS
5. CORSMiddleware              origin-restricted via CORS_ORIGINS
6. SecurityHeadersMiddleware   X-Frame-Options · X-Content-Type-Options · nosniff
7. GZipMiddleware              response compression ≥ 1,000 bytes
8. ExceptionMiddleware         all errors sanitized — zero PII guaranteed in any response
```

**Auth and access control:** JWT HS256 (30-min expiry) · bcrypt password hashing · RBAC (patient / doctor / admin) enforced via `Depends(auth.get_current_user)`

**Privacy engineering:** Per-user `allow_data_collection` consent flag · patient deletion propagation across DB, vector store, ABDM consent lifecycle, and interoperability exports · mandatory medical disclaimers on all AI-generated health advice · PHI-safe audit events with no raw payloads in `audit.py`

**Compliance evidence surfaces** at `/v1/admin/*`: backup readiness · incident response readiness · retention policy readiness · security assurance readiness — anchored to WHO AI governance, FDA clinical decision-support transparency, and EU AI Act human-oversight principles

</details>

<details>
<summary><b>Healthcare interoperability — FHIR R4, India ABDM, DICOMweb, SMART on FHIR</b></summary>

| Standard | Module | What Is Implemented |
|---|---|---|
| **FHIR R4** | `fhir.py` | Patient, Encounter, Observation, DiagnosticReport, MedicationRequest, Invoice, CareEvent, Bundle serializers. SHA-256 signed export manifests. |
| **India ABDM** | `abdm.py` | Readiness checks · consent request generation · callback normalization · SHA-256 payload signing · `abdm_consent_events` table for PHI-safe lifecycle tracking |
| **DICOMweb / PACS** | `dicomweb.py` | QIDO-RS · WADO-RS metadata · STOW-RS endpoint planning (metadata links only, no raw image bytes stored) |
| **SMART on FHIR** | `smart_fhir.py` | Readiness checks · authorization URL generation for EHR launch flows |
| **LOINC / SNOMED / ICD-10** | `terminology.py` | Seed catalog for coding lookups and integration mapping |

</details>

<details>
<summary><b>Testing strategy — property-based, security, AI mocking</b></summary>

~90 unit test files. Key patterns:

- **Hypothesis property-based testing** — tests in `tests/unit/` generate thousands of randomized inputs to find edge cases automatically
- **All AI/embedding calls mocked** — no test requires an API key; all provider calls are stubbed. Full suite runs offline
- **Isolated databases** — every test uses a temp or in-memory DB; `healthcare.db` is never touched by tests
- **Adversarial security tests** — `test_prompt_injection_guardrails.py`, `test_core_ai_security.py`, `test_strict_auth.py`, `test_main_security.py` — explicit adversarial inputs tested

```bash
python -m pytest tests/ -v                        # full suite
python -m pytest tests/unit/ -v                   # unit tests only
python -m pytest tests/unit/ -k "security" -v     # security tests only
```

</details>

---

## Quick Start

**Requirements:** Python 3.11+ · Node.js 20.9+

### Option 1 — Docker (fastest, one command)

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
cp .env.example .env          # set GOOGLE_API_KEY and SECRET_KEY
docker compose up --build
```

Open **http://127.0.0.1:3000** — API docs at **http://127.0.0.1:8000/docs**

### Option 2 — Local development

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

pip install -r requirements.txt
npm --prefix frontend install

cp .env.example .env          # set GOOGLE_API_KEY and SECRET_KEY

# Terminal 1 — FastAPI backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — React 19 frontend
npm --prefix frontend run dev
```

| Service | URL |
|---|---|
| Frontend app | http://127.0.0.1:3000 |
| REST API | http://127.0.0.1:8000 |
| Interactive API explorer | http://127.0.0.1:8000/docs |

> **Run with no API key — fully private local AI.** Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, and set `OLLAMA_BASE_URL=http://127.0.0.1:11434`. All LLM inference runs on your machine. No internet required. HIPAA-friendly for sensitive workflows.

---

## Machine Learning Disease Prediction

Five ML models for clinical disease screening — trained on peer-reviewed public datasets used in academic research:

| Disease | Training Dataset | Algorithm | Features | Published Accuracy |
|---|---|---|---|---|
| **Diabetes Prediction** | BRFSS 2015 — CDC (250,000+ records) | XGBoost | 9 | **89%** |
| **Heart Disease Detection** | Cleveland Heart Disease — UCI | Voting Ensemble | 13 | **92%** |
| **Liver Disease Screening** | ILPD — Indian Liver Patient Dataset | Ensemble + Scaler | 10 | — |
| **Chronic Kidney Disease** | UCI CKD Dataset | Classifier + Scaler | 24 | — |
| **Lung Cancer / Respiratory Risk** | Lung Cancer Survey | Classifier + Scaler | 15 | — |

Every prediction returns a risk score, confidence percentage, and a **SHAP explanation** showing which clinical features drove the result — making predictions interpretable for clinicians, patients, and regulators:

```json
POST /v1/predict/explain/diabetes

{
  "prediction": "High Risk",
  "confidence": 89.3,
  "risk_level": "High",
  "top_features": [
    { "feature": "HbA1c_level",         "shap_value": 0.42, "direction": "increases_risk" },
    { "feature": "blood_glucose_level", "shap_value": 0.31, "direction": "increases_risk" },
    { "feature": "bmi",                 "shap_value": 0.18, "direction": "increases_risk" }
  ],
  "disclaimer": "AI-assisted screening only. Consult a qualified clinician for diagnosis and treatment."
}
```

Clinicians log override decisions (accepted / overridden / ignored) via `POST /v1/predict/reviews`. All events are written as PHI-safe `REVIEW_AI_PREDICTION` audit entries without raw payloads.

---

## RAG-Powered Medical Chatbot with LangGraph

The medical chatbot uses **Retrieval-Augmented Generation (RAG)** — it answers questions grounded in each patient's actual health history, not generic training data. Built on a **LangGraph multi-agent supervisor** with role-based scope enforcement.

### How the LangGraph agent routes queries

```
User message
  └─► Supervisor node     classifies intent
        ├─ "research"  ──► Researcher node    Tavily real-time medical search
        │                   eliminates LLM hallucination and knowledge cutoff
        ├─ "analyze"   ──► Analyst node        deterministic ML model calls
        │                   no hallucination on statistical risk scores
        ├─ "unsafe"    ──► Guardrail node      zero-latency rejection
        └─ "default"   ──► Generate node       core_ai.chat() + RAG context
```

### How patient data is retrieved (RAG pipeline)

```
User query
  ├─► Gemini text-embedding-004 (free)     query → vector
  ├─► turbovec Rust SIMD cosine search     find relevant records
  ├─► ACL scope enforcement                patient: own records only
  │                                        doctor/admin: global scope
  ├─► context assembly                     3,000 token budget · max 10 chunks
  └─► LLM via core_ai                      grounded response + citations
```

---

## 3-Tier AI Inference — Ollama, Gemini, OpenAI/Anthropic

**`backend/core_ai.py`** is the single gateway for all LLM and embedding calls in the platform. No other module imports a provider SDK.

```
Incoming AI request
│
├── x-ai-provider header present? ──► Cloud override (OpenAI / Anthropic / OpenRouter)
│
├── Ollama running locally?        ──► Tier A: local, free, private, HIPAA-friendly
│   fuzzy model matching · 3-attempt retry with backoff · dual-endpoint fallback
│
├── GOOGLE_API_KEY configured?     ──► Tier B: Gemini cloud, free tier
│   gemini-1.5-flash default · 30s TTL inference cache
│
└── all unavailable                ──► Tier C: OpenAI / Anthropic
```

Switch providers without changing application code — just environment variables.

---

## Hospital Management System

Eight modules covering the complete inpatient and outpatient clinical workflow:

| Module | Clinical Function |
|---|---|
| **`hospital_operations.py`** | OPD/IPD/emergency encounters · admissions · bed management · clinical orders · patient timelines |
| **`monitoring.py`** | Vitals capture · deterministic clinician-review flags · batch pattern analysis |
| **`diagnostics.py`** | Lab/radiology result lifecycle · clinician review workflow · diagnostic ops metrics |
| **`pharmacy.py`** | Medication inventory · prescription creation · pharmacist dispensing · stock tracking |
| **`billing.py`** | Billable service catalog · invoice issuance · payment collection · revenue reporting |
| **`discharge.py`** | Discharge summaries · admission finalization · bed release |
| **`nursing.py`** | Nursing task assignment · nurse worklists · care coordination |
| **`care_events.py`** | Role-scoped event feeds across the shared patient timeline |

Real-time hospital capacity data streams over `WS /v1/telemetry/stream` — bed census, department loads, ED wait times, and surge predictions every 2 seconds.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  React 19 Frontend (Vite 8 · TypeScript · Tailwind CSS 4)    │
│  React Router v7 · TanStack Query v5 · Zustand v5            │
└─────────────────────────────┬────────────────────────────────┘
                              │  REST · Server-Sent Events · WebSocket
┌─────────────────────────────▼────────────────────────────────┐
│  FastAPI Backend — all routes /v1 · X-Request-ID tracing     │
│                                                                │
│  Auth · Chat · Disease Prediction · SSE · Admin              │
│  Hospital Ops · Pharmacy · Billing · Nursing · Diagnostics   │
│  Discharge · Care Events · Interoperability · Telemetry      │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  8-Layer Security Middleware                           │  │
│  │  RequestTracing · Versioning · RateLimit              │  │
│  │  TrustedHost · CORS · SecurityHeaders                 │  │
│  │  GZip · ExceptionMasking (zero PII in all errors)     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core_ai.py — single AI provider gateway              │  │
│  │  Ollama (local) ──► Gemini (free) ──► Cloud           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Intelligence Layer                                    │  │
│  │  LangGraph Agent · RAG Pipeline · Prompt Registry     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│  Data Layer                                                    │
│  SQLite WAL / PostgreSQL · Vector Store · 5 ML Model .pkl    │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend API** | Python 3.11 · FastAPI · SQLAlchemy · Alembic · Pydantic v2 · uvicorn |
| **Frontend** | Vite 8 · React 19 · TypeScript · Tailwind CSS 4 · React Router v7 · TanStack Query v5 · Zustand v5 |
| **Machine Learning** | XGBoost · scikit-learn · SHAP explainability · joblib serialization |
| **AI / LLM Orchestration** | LangGraph · Google Gemini · Ollama · LangChain Core · OpenAI (optional) · Anthropic (optional) |
| **RAG / Vector Search** | Gemini `text-embedding-004` · turbovec Rust SIMD · cosine similarity |
| **Database** | SQLite (dev, WAL mode) · PostgreSQL (prod) · Redis (caching, rate limiting) |
| **Testing** | pytest · Hypothesis (property-based) · Vitest · Testing Library · Playwright |
| **Observability** | Prometheus · Grafana · Jaeger distributed tracing · MLflow |
| **Infrastructure** | Docker · Kubernetes · Terraform AWS (EKS + RDS + ElastiCache + S3 + Route53) · Render |
| **CI/CD** | GitHub Actions (8 workflows) · CodeQL SAST · Dependabot · GHCR |

---

## Frontend — React 19 Medical Dashboard

**Vite 8 · React 19 · TypeScript · Tailwind CSS 4 · React Router DOM v7**

| Route | Page |
|---|---|
| `/dashboard` | Patient health summary and recent prediction results |
| `/chat` | AI medical chatbot — SSE streaming, RAG context, personalized suggestions |
| `/predict` | Machine learning disease prediction hub |
| `/predict/diabetes` · `/heart` · `/liver` · `/kidney` · `/lungs` | Individual disease screeners with SHAP visualization |
| `/admin` | User management · audit logs · AI governance inventory · model cards |
| `/capacity` | Live hospital capacity dashboard over WebSocket |
| `/telemedicine` | Telemedicine appointment booking + Jitsi video integration |
| `/patients` · `/patients/:id` | Patient management for doctors and admins |
| `/profile` | Profile and data collection consent settings |
| `/pricing` | Subscription plan management (Razorpay) |
| `/infrastructure` | Backend operational health |

---

## REST API Reference

All endpoints prefixed `/v1`. Interactive explorer at **http://127.0.0.1:8000/docs**

<details>
<summary>Authentication and User Management</summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/signup` | — | Register new user account |
| `POST` | `/v1/token` | — | Login and receive JWT token |
| `GET` | `/v1/profile` | User | Retrieve own profile |
| `PUT` | `/v1/profile` | User | Update profile |
| `GET` | `/v1/users` | Admin | List all users |
| `GET` | `/v1/users/{id}/full` | Admin | Full user health dossier |

</details>

<details>
<summary>Disease Prediction and SHAP Explainability</summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/predict/diabetes` | — | Diabetes prediction (9 features · XGBoost · 89%) |
| `POST` | `/v1/predict/heart` | — | Heart disease detection (13 features · Ensemble · 92%) |
| `POST` | `/v1/predict/liver` | — | Liver disease screening (10 features) |
| `POST` | `/v1/predict/kidney` | — | Chronic kidney disease (24 features) |
| `POST` | `/v1/predict/lungs` | — | Lung cancer / respiratory risk (15 features) |
| `POST` | `/v1/predict/explain/{model}` | — | SHAP feature attribution |
| `POST` | `/v1/predict/reviews` | Doctor/Admin | Log clinician decision on AI prediction |
| `POST` | `/v1/admin/reload_models` | Admin | Hot-reload all ML models without restart |

</details>

<details>
<summary>AI Chatbot and LangGraph Agent</summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/chat` | User | LangGraph + RAG medical conversation |
| `POST` | `/v1/chat/stream` | User | SSE streaming chat with heartbeat keepalive |
| `GET` | `/v1/chat/history` | User | Last 100 messages |
| `DELETE` | `/v1/chat/history` | User | Clear chat history |
| `GET` | `/v1/chat/context` | User | Debug — view assembled RAG context |
| `GET` | `/v1/chat/suggestions` | User | Dynamic personalized starter questions |
| `GET` | `/v1/ai/models` | — | List locally available Ollama models |
| `POST` | `/v1/ai/models/pull` | Admin | Pull Ollama model with SSE progress |

</details>

<details>
<summary>Health Records, Vision AI, PDF Reports, Appointments</summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/records` | User | Save a health checkup result |
| `GET` | `/v1/records` | User | Retrieve all health records |
| `DELETE` | `/v1/records/{id}` | User | Delete a health record |
| `POST` | `/v1/analyze/report` | User | Vision AI — analyze lab report image |
| `GET` | `/v1/download/health-report` | User | Download personalized PDF health report |
| `POST` | `/v1/explain/` | User | Plain-language AI explanation of prediction |
| `POST` | `/v1/appointments/` | User | Book telemedicine appointment |
| `GET` | `/v1/appointments/doctors` | — | List available doctors |
| `POST` | `/v1/payments/create-order` | User | Create Razorpay payment order |
| `POST` | `/v1/payments/verify` | User | Verify Razorpay payment signature |

</details>

<details>
<summary>Admin, AI Governance, Compliance, and Telemetry</summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/admin/stats` | Admin | Platform-wide statistics |
| `GET` | `/v1/admin/ai-functions` | Admin | AI governance function inventory |
| `GET` | `/v1/admin/model-cards` | Admin | ML model and dataset transparency cards |
| `GET` | `/v1/admin/operational-health` | Admin | Full backend readiness report |
| `GET` | `/v1/admin/data-quality` | Admin | PHI-safe data quality report |
| `GET` | `/v1/admin/backup-readiness` | Admin | Backup and restore readiness |
| `GET` | `/v1/admin/incident-readiness` | Admin | Incident response readiness |
| `GET` | `/v1/admin/retention-readiness` | Admin | Data retention policy readiness |
| `GET` | `/v1/admin/security-assurance` | Admin | Security posture metadata |
| `GET` | `/v1/admin/privacy/deletion-plan/{id}` | Admin | Patient data deletion plan |
| `WS` | `/v1/telemetry/stream` | — | Real-time hospital capacity stream |
| `GET` | `/healthz` | — | API health check |

</details>

---

## Deployment — Local to AWS EKS

> ⚠️ Before production: `python scripts/production_readiness_check.py`
> Full gate: [`docs/PRODUCTION_READINESS_GATE.md`](docs/PRODUCTION_READINESS_GATE.md)

| Option | Command | Best For |
|---|---|---|
| **Docker Compose** | `docker compose up --build` | Local development and demos |
| **Enterprise Stack** | `docker compose -f docker-compose.enterprise.yml up` | Full local env: PostgreSQL · Redis · Prometheus · Grafana · Jaeger · MLflow |
| **Render** | Push to GitHub — auto-deploys via `render.yaml` | Free cloud hosting, zero DevOps config |
| **Kubernetes** | `kubectl apply -f k8s/` | HA deployment: 3 backend + 2 frontend replicas · HPA autoscaling |
| **Terraform on AWS** | `cd terraform && terraform apply` | Production: VPC · EKS · RDS · ElastiCache · S3 · EFS · ALB · Route53 |

---

## CI/CD Pipelines

| Workflow | Trigger | Purpose |
|---|---|---|
| **CI Tests** | Push / PR | Full pytest suite with coverage |
| **CodeQL Security Analysis** | Push / PR + weekly | SAST static analysis |
| **Docker Build** | Push / PR | Build and push to `ghcr.io` |
| **HuggingFace Sync** | Push to `main` | Deploy to HuggingFace Spaces |
| **Render Keep-Alive** | Scheduled | Prevent free-tier cold starts |
| **Label Sync** | Push to `main` | Sync GitHub issue labels |
| **Release Drafter** | Push / PR | Auto-generate changelog |
| **Stale Issue Bot** | Scheduled | Close inactive issues/PRs |

Dependabot: Python · npm · Docker · Actions. CODEOWNERS, issue/PR templates, FUNDING.yml.

---

## Environment Variables

**Minimum required:**

```bash
GOOGLE_API_KEY=...   # Free at https://aistudio.google.com — skip if using Ollama only
SECRET_KEY=...       # python -c "import secrets; print(secrets.token_hex(32))"
```

<details>
<summary>Full configuration reference</summary>

```bash
# Database
DATABASE_URL=sqlite:///./healthcare.db
# DATABASE_URL=postgresql://user:pass@host/dbname

# Local AI (Ollama — free, private, HIPAA-friendly)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120

# Gemini
GEMINI_MODEL=gemini-1.5-flash

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Security
ALLOWED_HOSTS=127.0.0.1
CORS_ORIGINS=http://127.0.0.1:3000
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Payments (optional)
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Cloud AI fallback (optional — only if Ollama + Gemini unavailable)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Healthcare interoperability connectors (disabled by default)
ABDM_ENABLED=false        # India ABDM
DICOMWEB_ENABLED=false    # DICOMweb/PACS
SMART_FHIR_ENABLED=false  # SMART on FHIR EHR launch
```

Full reference with backup, incident response, retention, and security metadata: [`.env.example`](.env.example)

</details>

---

## Project Structure

<details>
<summary>Full directory tree</summary>

```
AI-Healthcare-System/
├── backend/
│   ├── main.py                    # FastAPI app, 8-layer middleware, router mounting
│   ├── core_ai.py                 # 3-tier AI gateway — the only file that calls providers
│   ├── prediction.py              # 5 ML disease prediction endpoints + clinician audit
│   ├── models.py                  # SQLAlchemy ORM (20+ tables)
│   ├── schemas.py                 # Pydantic v2 schemas
│   ├── database.py                # Engine, SessionLocal, get_db()
│   ├── auth.py                    # JWT, bcrypt, RBAC
│   ├── agent.py                   # LangGraph medical agent
│   ├── chat.py                    # Synchronous chat + health records CRUD
│   ├── streaming_chat.py          # SSE streaming with heartbeat
│   ├── chat_context.py            # RAG context builder
│   ├── rag.py                     # Vector store + semantic search
│   ├── prompt_registry.py         # 6 versioned prompt templates
│   ├── ai_function_registry.py    # AI governance inventory
│   ├── model_cards.py             # ML model transparency cards
│   ├── hospital_operations.py     # Encounters, admissions, beds
│   ├── monitoring.py              # Vitals, clinician-review signals
│   ├── diagnostics.py             # Lab/radiology lifecycle
│   ├── pharmacy.py                # Inventory, prescriptions, dispensing
│   ├── billing.py                 # Invoicing and payments
│   ├── discharge.py               # Discharge summaries
│   ├── nursing.py                 # Nursing task management
│   ├── care_events.py             # Patient timeline feed
│   ├── interoperability.py        # Unified FHIR/ABDM/DICOM/SMART API
│   ├── fhir.py                    # FHIR R4 serializers
│   ├── abdm.py                    # India ABDM connector
│   ├── dicomweb.py                # DICOMweb/PACS connector
│   ├── smart_fhir.py              # SMART on FHIR helpers
│   ├── terminology.py             # LOINC/SNOMED CT/ICD-10-CM catalog
│   ├── admin.py                   # Admin panel routes
│   ├── telemetry.py               # WebSocket hospital metrics
│   ├── middleware.py              # Full middleware stack
│   ├── audit.py                   # PHI-safe audit writer
│   ├── security.py                # Rate limiting
│   ├── pdf_service.py             # Medical report PDF
│   ├── turbovec_store.py          # Rust SIMD vector backend
│   ├── explainability.py          # SHAP layer
│   └── train_*.py                 # 5 model training scripts
│
├── frontend/                      # Vite 8 + React 19 SPA
│   ├── src/pages/                 # 17 route pages
│   ├── src/components/            # Shared UI components
│   ├── src/lib/                   # API client and utilities
│   ├── src/__tests__/             # Vitest unit tests
│   └── tests/                     # Playwright E2E tests
│
├── tests/                         # pytest backend suite
│   ├── unit/                      # ~90 files — Hypothesis property-based tests
│   ├── integration/
│   └── e2e/
│
├── k8s/                           # Kubernetes manifests
├── terraform/                     # AWS IaC
├── airflow/                       # Data pipeline DAGs
├── monitoring/                    # Prometheus + Grafana configs
├── docs/                          # Architecture, runbooks, whitepapers
├── .github/workflows/             # 8 CI/CD pipelines
├── docker-compose.yml
├── docker-compose.enterprise.yml
├── Dockerfile
└── AGENTS.md                      # AI coding agent canonical instructions
```

</details>

---

## FAQ

Frequently asked questions about running, using, and extending this medical AI platform.

### How do I run this project without an API key?

Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, and set `OLLAMA_BASE_URL=http://127.0.0.1:11434` in your `.env`. Leave `GOOGLE_API_KEY` unset. The system will automatically route all inference through your local Ollama instance — free, private, and offline.

### Can I use this as a college final-year project?

Yes. This codebase is MIT licensed and designed to be studied. Every module has one clear responsibility and is well-commented. Start with [`AGENTS.md`](AGENTS.md) for the architectural overview, then follow the [For Students & Learners](#-for-students--learners) table to the specific files covering the concepts you need.

### How do I deploy this to the cloud for free?

Fork the repo, connect it to [Render](https://render.com), and push. The `render.yaml` configuration handles the deployment automatically on the free tier. For a full cloud setup, use `docker compose up --build` on any VPS, or `kubectl apply -f k8s/` on any Kubernetes cluster.

### Is this HIPAA compliant?

This platform implements HIPAA-oriented security controls: bcrypt password hashing, JWT authentication, RBAC, audit logging, PII-scrubbed error responses, and per-user data collection consent. The `docs/PRODUCTION_READINESS_GATE.md` and the admin readiness endpoints (`/v1/admin/backup-readiness`, `/v1/admin/security-assurance`) provide a compliance evidence surface. **Full HIPAA compliance for a production deployment requires additional organizational controls, BAAs, and a formal compliance review.**

### How do I add a new disease prediction model?

1. Add your training script to `backend/train_yourmodel.py`
2. Register the model in `backend/prediction.py` → `initialize_models()`
3. Add a Pydantic schema to `backend/schemas.py`
4. Create the prediction endpoint in `backend/prediction.py`
5. Add a model card entry to `backend/model_cards.py`
6. Write a unit test in `tests/unit/test_ml.py`

### How does the AI chatbot remember my health history?

The chatbot uses **RAG (Retrieval-Augmented Generation)**. When you ask a question, your past health records are embedded into vectors using Gemini `text-embedding-004`, searched by cosine similarity, assembled into context within a 3,000-token budget, and passed to the LLM alongside your question. Your data is scoped to your account only — doctors and admins have broader (configurable) access.

### How do I switch between Ollama, Gemini, and OpenAI?

The system switches automatically based on availability (Ollama first, then Gemini, then OpenAI/Anthropic). To force a specific provider for a single request, send the `x-ai-provider` header with your choice and the `x-ai-api-key` header with your key. To change the global default, update the relevant env variables in `.env`.

### What is FHIR R4 and why does this project implement it?

FHIR (Fast Healthcare Interoperability Resources) R4 is the international standard for exchanging healthcare data. Implementing it means patient records from this system can be exported to and imported from any FHIR-compatible EHR (Epic, Cerner, etc.) without custom integration work. The India ABDM connector extends this for the Indian health stack.

---

## Contributing to AI Healthcare System

Contributions are welcome — bug fixes, new ML models, documentation, translations, or new test cases.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Then follow [`AGENTS.md`](AGENTS.md) — the canonical instruction file for all code changes.

```bash
# Run before opening a pull request
python -m pytest tests/ -v
npm --prefix frontend run test
```

<a href="https://github.com/pavanbadempet/AI-Healthcare-System/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=pavanbadempet/AI-Healthcare-System&max=20" alt="Contributors to AI Healthcare System" />
</a>

<details>
<summary>Star History</summary>
<p align="center">
  <a href="https://star-history.com/#pavanbadempet/AI-Healthcare-System&Date">
    <img src="https://api.star-history.com/svg?repos=pavanbadempet/AI-Healthcare-System&type=Date" alt="AI Healthcare System GitHub star history chart" width="600" />
  </a>
</p>
</details>

---

## Related Resources

- [FastAPI documentation](https://fastapi.tiangolo.com/) — Python web framework used for the backend API
- [LangGraph documentation](https://langchain-ai.github.io/langgraph/) — multi-agent system powering the medical chatbot
- [XGBoost documentation](https://xgboost.readthedocs.io/) — gradient boosting framework used for disease prediction
- [SHAP documentation](https://shap.readthedocs.io/) — explainability library for ML predictions
- [Ollama](https://ollama.com/) — local LLM inference for private AI
- [FHIR R4 specification](https://hl7.org/fhir/R4/) — international healthcare data interoperability standard
- [India ABDM](https://abdm.gov.in/) — Ayushman Bharat Digital Mission for Indian health data

---

## License

MIT License — free to use, modify, and distribute.

Copyright © 2025 [Pavan Badempet](https://github.com/pavanbadempet), Shiva Prasad Anagondi, Prashanth Cheerala.

See [LICENSE](LICENSE) for full terms.

---

<div align="center">

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers">⭐ Star this project</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/fork">🍴 Fork it</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues/new/choose">🐛 Report an issue</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/discussions">💬 Start a discussion</a>
</p>

<sub>
Built with Python, FastAPI, React 19, LangGraph, XGBoost, Ollama, FHIR R4, and a commitment to making healthcare AI accessible to everyone.
</sub>

</div>
