# AI Healthcare System — Open-Source Medical AI Platform

> Disease prediction · RAG-powered clinical chat · Hospital management · FHIR R4 · FastAPI · React 19 · LangGraph · XGBoost · Ollama · Kubernetes · Terraform AWS

<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System — open-source medical AI platform for disease prediction, RAG chatbot, hospital management, FHIR R4, FastAPI, React 19" width="100%"/>

<br/>

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI build status" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL security analysis" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="MIT license" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="GitHub stars" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues"><img src="https://img.shields.io/github/issues/pavanbadempet/AI-Healthcare-System?style=flat-square&color=ef4444" alt="Open issues" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/pulls"><img src="https://img.shields.io/github/issues-pr/pavanbadempet/AI-Healthcare-System?style=flat-square&color=8b5cf6" alt="Pull requests" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/network/members"><img src="https://img.shields.io/github/forks/pavanbadempet/AI-Healthcare-System?style=flat-square&color=06b6d4" alt="GitHub forks" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vite_8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite 8" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge&logo=chainlink&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
  <img src="https://img.shields.io/badge/XGBoost-189FDD?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost" />
</p>
<p>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes" />
  <img src="https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white" alt="Terraform" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus" />
</p>

<p>
  <!-- 🚀 Uncomment once deployed -->
  <!-- <a href="https://your-app.onrender.com"><strong>Live Demo →</strong></a> &middot; -->
  <a href="#-quick-start"><strong>Quick Start</strong></a> &middot;
  <a href="#-architecture"><strong>Architecture</strong></a> &middot;
  <a href="#-ml-models"><strong>ML Models</strong></a> &middot;
  <a href="#-3-tier-ai-engine"><strong>AI Engine</strong></a> &middot;
  <a href="#-rag-pipeline"><strong>RAG Pipeline</strong></a> &middot;
  <a href="#-api-reference"><strong>API Docs</strong></a> &middot;
  <a href="#-deployment"><strong>Deploy</strong></a> &middot;
  <a href="#-faq"><strong>FAQ</strong></a>
</p>

</div>

<img src="docs/assets/divider.svg" alt="" width="100%"/>

<!-- ============================================================
  GITHUB TOPICS TO SET (repo → About → gear icon → Topics):
  machine-learning  healthcare  fastapi  react  langgraph  xgboost
  disease-prediction  medical-ai  rag  llm  ollama  gemini
  hospital-management  fhir  python  typescript  docker  kubernetes
  healthcare-ai  clinical-decision-support

  GITHUB DESCRIPTION (140 chars):
  "Open-source medical AI: disease prediction (XGBoost 92%), RAG chatbot, hospital ops, FHIR R4, FastAPI, React 19, Ollama, K8s, Terraform"
  ============================================================ -->

## What Is This?

**AI Healthcare System** is an open-source medical AI platform that combines machine learning disease prediction, a RAG-powered clinical chatbot, and hospital management workflows — in a single codebase. It covers more ground than most single-purpose healthcare AI repositories and is designed to be both studied and deployed.

It runs on a laptop with no API keys (via Ollama), scales to Kubernetes, and ships with Terraform for AWS. Whether you're a student exploring how these systems are built or an engineer evaluating architecture patterns, the code is the documentation.

<table>
<tr>
<td width="33%" valign="top">

### 5 ML Diagnostic Models
Diabetes, Heart, Liver, Kidney, Lungs — trained on real clinical datasets (BRFSS CDC, Cleveland UCI, ILPD, UCI CKD) with SHAP explainability and confidence scoring. Heart disease model: 92% accuracy. Diabetes model: 89% accuracy on the test split.

</td>
<td width="33%" valign="top">

### 3-Tier AI Inference
**Ollama → Gemini → Cloud** automatic fallback. Run fully offline via Ollama, use Gemini's free tier for cloud, or override to OpenAI/Anthropic per request via headers. No vendor lock-in in the application code.

</td>
<td width="33%" valign="top">

### RAG Medical Chatbot
LangGraph multi-agent system + Gemini embeddings + scoped vector store. Answers are grounded in each patient's own health records with citation tracking, a 3,000-token context budget, and role-based scope control.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### Hospital Operations Modules
OPD/IPD encounters, pharmacy inventory, lab diagnostics, nursing tasks, discharge planning, bed management, and billing — 8 modules across the care continuum, with real-time capacity telemetry over WebSocket.

</td>
<td width="33%" valign="top">

### Security and Audit
JWT + bcrypt, RBAC (patient/doctor/admin), 8-layer middleware stack, per-IP rate limiting, PII-scrubbed error responses, and audit logging designed with HIPAA/GDPR controls in mind.

</td>
<td width="33%" valign="top">

### Deployment Options
Docker Compose for local dev, an enterprise stack with PostgreSQL/Redis/Prometheus/Grafana, Render PaaS, Kubernetes (3-replica HA), and Terraform for AWS EKS + RDS + ElastiCache.

</td>
</tr>
</table>

<img src="docs/assets/divider.svg" alt="" width="100%"/>

## What Works End-to-End Today

This section is honest about what's fully wired up vs what's a reference/connector implementation.

**Fully functional**
- Disease prediction for all 5 models with SHAP explanations and clinician audit logging
- RAG chatbot with patient-scoped vector retrieval and SSE streaming
- LangGraph agent with supervisor routing and guardrails
- Auth, RBAC, and the full 8-layer middleware stack
- All 8 hospital operations modules (pharmacy, billing, nursing, diagnostics, discharge, bed management)
- Real-time hospital telemetry over WebSocket
- PDF health report generation and Vision AI lab report analysis
- Docker Compose, Kubernetes manifests, and Terraform AWS configs
- CI/CD with 8 GitHub Actions workflows including CodeQL SAST

**Reference / connector implementations** *(working code, but require external system integration to use in production)*
- **FHIR R4 serializers** — produce valid FHIR bundles, but no live EHR connection out of the box
- **India ABDM connector** — consent request generation and callback handling, but requires ABDM sandbox credentials
- **DICOMweb / PACS** — metadata and endpoint planning only; no PACS server bundled
- **SMART on FHIR** — authorization URL generation; no EHR launch context without an EHR
- **Razorpay payments** — wired up but requires live Razorpay credentials
- **Tavily research agent node** — works when `TAVILY_API_KEY` is set; degrades gracefully without it

## Design Scope

This project demonstrates a complete healthcare AI system at the architectural level. It is not a certified medical device and makes no clinical diagnostic claims. All predictions include mandatory disclaimers. If you're building for regulated clinical use, it provides a solid foundation and reference point — full HIPAA/CE compliance requires additional organizational controls, audits, and a formal regulatory pathway.

<img src="docs/assets/divider.svg" alt="" width="100%"/>

<details>
<summary><strong>Table of Contents</strong></summary>

- [What Is This?](#what-is-this)
- [What Works End-to-End Today](#what-works-end-to-end-today)
- [Exploring the Codebase](#exploring-the-codebase)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [ML Models](#-ml-models)
- [3-Tier AI Engine](#-3-tier-ai-engine)
- [RAG Pipeline](#-rag-pipeline)
- [LangGraph Medical Agent](#-langgraph-medical-agent)
- [Prompt Registry](#-prompt-registry)
- [Hospital Operations](#-hospital-operations)
- [Interoperability — FHIR · ABDM · DICOM · SMART](#-interoperability--fhir--abdm--dicom--smart)
- [Frontend](#-frontend)
- [API Reference](#-api-reference)
- [Database Layer](#-database-layer)
- [Security Posture](#-security-posture)
- [CI/CD Pipelines](#-cicd-pipelines)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

</details>

---

## Exploring the Codebase

Each module in this project has a single responsibility and is named after what it does. If you want to understand a specific concept, here's where to look:

- **How ML predictions are served via REST** → `backend/prediction.py` — model loading with `initialize_models()`, feature scaling, endpoint wiring
- **How RAG works in practice** → `backend/rag.py` and `backend/chat_context.py` — embedding, cosine search, ACL scoping, token-budgeted context assembly
- **How a LangGraph agent is structured** → `backend/agent.py` — supervisor node, researcher, analyst, guardrail, and generate nodes with a `CoreAIWrapper` adapter
- **How to swap AI providers without touching application code** → `backend/core_ai.py` — the full fallback chain, retry logic, and 30s TTL caching
- **How SHAP makes ML predictions explainable** → `backend/explainability.py` — feature attribution computed at inference time
- **How JWT auth and role-based access work** → `backend/auth.py` — token creation, `get_current_user()` dependency, RBAC enforcement
- **How a large FastAPI app is structured** → `backend/main.py` — middleware stack ordering, router mounting, lifespan startup
- **How property-based testing finds edge cases** → `tests/unit/` — Hypothesis strategies generating thousands of inputs automatically
- **How CI/CD pipelines are set up** → `.github/workflows/` — eight real pipelines covering CI, CodeQL, Docker, and HuggingFace sync
- **How Terraform provisions cloud infrastructure** → `terraform/main.tf` — VPC, EKS cluster, RDS, ElastiCache, S3, Route53

The [`AGENTS.md`](AGENTS.md) file documents the architectural rules that govern the whole system — useful reading before contributing or extending anything.

<details>
<summary><b>Architecture decisions — for engineers evaluating this as a reference</b></summary>

| Decision | Rationale |
|---|---|
| **Single AI gateway (`core_ai.py`)** | All provider SDK imports isolated to one module. No route handler may call `google.generativeai`, `openai`, or `anthropic` directly. Enforces audit logging and centralizes retry, fallback, and 30s TTL caching. |
| **Version-controlled prompt registry** | No system prompts inline in handlers. Every template is versioned, activatable, A/B testable. Templates include instruction-hierarchy guardrails treating retrieved patient content as untrusted clinical evidence. |
| **Pydantic v2 strict validation** | Input rejection with structured errors before any ML inference. |
| **`DATABASE_URL` from env** | Zero-change swap from SQLite WAL (dev) to PostgreSQL with psycopg2 pooling (prod). `postgres://` → `postgresql://` normalization on startup. |
| **`/v1` prefix + `X-Request-ID`** | Forward-compatible versioning. Per-request correlation IDs for distributed tracing. |
| **ExceptionMiddleware outermost** | Guarantees zero PII in any 500 response regardless of exception origin. |

</details>

---

## ⚡ Quick Start

**Requirements:** Python 3.11+ · Node.js 20.9+

**Option A — Docker (one command)**

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
cp .env.example .env          # set GOOGLE_API_KEY + SECRET_KEY
docker compose up --build
```

**Option B — Local dev**

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
python -m pip install -r requirements.txt
npm --prefix frontend install
cp .env.example .env          # set GOOGLE_API_KEY + SECRET_KEY

# Terminal 1 — FastAPI backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — React 19 frontend
npm --prefix frontend run dev
```

| Service | URL |
|---|---|
| Frontend app | http://127.0.0.1:3000 |
| REST API | http://127.0.0.1:8000 |
| Interactive API docs | http://127.0.0.1:8000/docs |

> **Zero API keys, fully private.** Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, and set `OLLAMA_BASE_URL=http://127.0.0.1:11434`. All inference runs locally — nothing leaves your machine. HIPAA-friendly.

---

## 🏗 Architecture

```mermaid
graph TB
    subgraph Frontend["FRONTEND — Vite 8 · React 19 · TypeScript · Tailwind CSS 4"]
        FE["React Router v7 · Dashboard · Chat · Predict · Admin · Capacity · Telemedicine"]
    end

    subgraph Backend["FASTAPI BACKEND  (/v1 versioned · X-Request-ID tracing)"]
        subgraph Services["API Routers"]
            AUTH["Auth (JWT/RBAC)"] --- CHAT["Chat (LangGraph)"] --- PRED["Predict (5 ML)"] --- STREAM["SSE Stream"]
            ADMIN["Admin"] --- REPORT["Reports + Vision AI"] --- PAY["Payments"] --- APPT["Appointments"]
            HOSP["Hospital Ops"] --- TELE["Telemetry WS"] --- INTEROP["Interoperability"] --- ENT["Enterprise"]
        end
        subgraph CoreAI["CORE AI ENGINE — core_ai.py (single gateway)"]
            TA["Tier A: Ollama — local, free, private"]
            TB["Tier B: Gemini — free cloud tier"]
            TC["Tier C: OpenAI / Anthropic — optional"]
            TA -->|fails| TB
            TB -->|fails| TC
        end
        subgraph Intel["Intelligence Layer"]
            RAG["RAG Pipeline — Gemini text-embedding-004 · cosine similarity"]
            AGENT["LangGraph Agent — supervisor routing · guardrails"]
            PROMPTS["Prompt Registry — 6 versioned templates"]
        end
        subgraph MW["8-Layer Middleware Stack"]
            MWL["RequestTracing · Versioning · RateLimit · TrustedHost · CORS · SecurityHeaders · GZip · ExceptionMasking"]
        end
    end

    subgraph Data["DATA LAYER"]
        DB[("SQLite WAL / PostgreSQL")]
        VS[("Vector Store — turbovec SIMD")]
        ML[("5 ML Models + Scalers (.pkl)")]
    end

    Frontend -->|"REST · SSE · WebSocket"| Backend
    Backend --> DB & VS & ML

    style Frontend fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style Backend fill:#1e293b,stroke:#14b8a6,color:#e2e8f0
    style CoreAI fill:#0f172a,stroke:#f59e0b,color:#e2e8f0
    style Intel fill:#0f172a,stroke:#8b5cf6,color:#e2e8f0
    style Data fill:#0f172a,stroke:#22c55e,color:#e2e8f0
    style MW fill:#1e293b,stroke:#ef4444,color:#e2e8f0
```

| Decision | Rationale |
|---|---|
| **All AI through `core_ai.py`** | Single gateway — enforces audit logging; no module may call provider SDKs directly |
| **Prompts in `prompt_registry.py`** | No inline system prompts; versioned, auditable, A/B testable |
| **ML loading via `prediction.py`** | Centralized lifecycle; hot-reload via `POST /v1/admin/reload_models` |
| **`DATABASE_URL` from env** | SQLite (dev) to PostgreSQL (prod) seamlessly |
| **`/v1` prefix on all routes** | Forward-compatible versioning + `X-Request-ID` tracing per request |

---

## 🔬 ML Models — Disease Prediction with Machine Learning

Five models trained on peer-reviewed public clinical datasets:

| # | Disease | Dataset | Algorithm | Features | Accuracy | Endpoint |
|---|---|---|---|---|---|---|
| 1 | **Diabetes Prediction** | BRFSS 2015 — CDC (250k+ records) | XGBoost | 9 | **89%** | `POST /v1/predict/diabetes` |
| 2 | **Heart Disease Detection** | Cleveland Heart Disease — UCI | Voting Ensemble | 13 | **92%** | `POST /v1/predict/heart` |
| 3 | **Liver Disease Screening** | ILPD — Indian Liver Patient Dataset | Ensemble + Scaler | 10 | — | `POST /v1/predict/liver` |
| 4 | **Chronic Kidney Disease** | UCI CKD Dataset | Classifier + Scaler | 24 | — | `POST /v1/predict/kidney` |
| 5 | **Lung Cancer / Respiratory Risk** | Lung Cancer Survey | Classifier + Scaler | 15 | — | `POST /v1/predict/lungs` |

**SHAP Explainability** on 3 models — shows which clinical features drove the result:

```bash
POST /v1/predict/explain/{diabetes|heart|liver}
```

```json
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

Clinicians log override decisions (accepted / overridden / ignored) via `POST /v1/predict/reviews` — written as PHI-safe `REVIEW_AI_PREDICTION` audit entries.

---

## 🤖 3-Tier AI Engine

**File:** `backend/core_ai.py` — the single gateway for ALL AI inference. No other module may import a provider SDK.

```mermaid
graph LR
    REQ["API Request"] --> CHECK{"x-ai-provider\nheader set?"}
    CHECK -->|"Yes"| CLOUD["Cloud Override\nOpenAI / Anthropic"]
    CHECK -->|"No"| OLLAMA["Tier A: Ollama\nLocal · Free · Private"]
    OLLAMA -->|"unavailable"| GEMINI["Tier B: Gemini\nGoogle API · Free tier"]
    GEMINI -->|"unavailable"| FALLBACK["Tier C: OpenAI / Anthropic\nPay-per-use"]

    style OLLAMA fill:#0f172a,stroke:#22c55e,color:#e2e8f0
    style GEMINI fill:#0f172a,stroke:#3b82f6,color:#e2e8f0
    style FALLBACK fill:#0f172a,stroke:#f59e0b,color:#e2e8f0
    style CLOUD fill:#1e293b,stroke:#ef4444,color:#e2e8f0
```

| Tier | Provider | Data stays local? | Cost |
|---|---|---|---|
| **A** | Ollama | ✅ Yes — never leaves your machine | Free |
| **B** | Gemini | ❌ Cloud API | Free tier |
| **C** | OpenAI / Anthropic | ❌ Cloud API | Pay-per-use |

**Features:** fuzzy model name matching · 3-attempt retry with backoff · dual-endpoint fallback · 30s TTL cache · SSE streaming · Ollama model management (list, pull, delete)

**Public API:** `generate()` · `chat()` · `chat_stream()` · `embed_text()` · `generate_vision_content()` · `is_available()`

---

## 📚 RAG Pipeline — AI with Patient Memory

**File:** `backend/rag.py` — semantic search over patient-scoped health records.

```mermaid
graph LR
    Q["User Query"] --> E["core_ai.embed_text()\nGemini text-embedding-004"]
    E --> S["Cosine Similarity\nturbovec SIMD / sklearn fallback"]
    S --> SCOPE{"Scope Check"}
    SCOPE -->|"patient"| P["Own records only"]
    SCOPE -->|"doctor / admin"| G["Global scope\n(facility-aware)"]
    P --> C["Context Assembly\n3,000 tokens · max 10 chunks\nRetrievedChunk · Citation"]
    G --> C
    C --> LLM["LLM via core_ai\n+ Citations + Disclaimer"]

    style Q fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style LLM fill:#0f172a,stroke:#22c55e,color:#e2e8f0
    style SCOPE fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
```

| Component | Implementation |
|---|---|
| **Embedding model** | Gemini `text-embedding-004` (FREE) |
| **Vector backend** | turbovec (Rust SIMD) → scikit-learn cosine fallback |
| **Storage** | Pickle-persisted JSON vector store |
| **Token budget** | 3,000 tokens, max 10 chunks |
| **Scope governance** | Patient-scoped (own records) vs Global-scoped (doctor/admin) |
| **Output types** | `RetrievedChunk` · `Citation` · `RAGResult` dataclasses |

---

## 🕸 LangGraph Medical Agent

**File:** `backend/agent.py` — supervisor-routed multi-node graph.

```mermaid
graph TB
    IN["User Message"] --> SUP["Supervisor Node\nclassifies intent"]
    SUP -->|"medical research"| RES["Researcher Node\nTavily real-time search\nsolves knowledge cutoff"]
    SUP -->|"analyze patient data"| ANA["Analyst Node\nML tool calls\ndeterministic scoring"]
    SUP -->|"off-topic / unsafe"| GUARD["Guardrail Node\nzero-latency rejection"]
    SUP -->|"general chat"| GEN["Generate Node\ncore_ai.chat() + RAG"]
    RES --> GEN
    ANA --> GEN
    GEN --> END1(("END"))
    GUARD --> END2(("END"))

    style SUP fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style GEN fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style GUARD fill:#0f172a,stroke:#ef4444,color:#e2e8f0
    style RES fill:#0f172a,stroke:#22c55e,color:#e2e8f0
    style ANA fill:#0f172a,stroke:#8b5cf6,color:#e2e8f0
```

All nodes use `CoreAIWrapper` — the full fallback chain and audit guarantees apply throughout the graph.

---

## 📝 Prompt Registry

**File:** `backend/prompt_registry.py` — 6 version-controlled, auditable templates. No system prompt is ever inlined in a route handler.

| Template | Purpose |
|---|---|
| `chat_system` | Main chatbot with patient context injection |
| `medical_qa` | RAG-grounded Q&A with citation formatting |
| `symptom_analysis` | Structured symptom assessment with red-flag detection |
| `report_summary` | Health record and lab result summarization |
| `risk_assessment` | ML prediction plain-language explanation |
| `streaming_system` | Token-efficient variant for SSE streaming |

---

## 🏥 Hospital Operations

Eight modules covering the complete clinical workflow — from admission to discharge:

| Module | What It Handles |
|---|---|
| `hospital_operations.py` | Departments · OPD/IPD/emergency encounters · admissions · bed management · clinical orders |
| `monitoring.py` | Vitals capture · deterministic clinician-review signals · batch pattern summaries |
| `diagnostics.py` | Lab/radiology result lifecycle · clinician review · ops metrics |
| `pharmacy.py` | Medication inventory · prescriptions · pharmacist dispensing · stock metrics |
| `billing.py` | Billable service catalog · invoice issuance · payment collection · revenue metrics |
| `discharge.py` | Discharge summaries · admission finalization · bed release |
| `nursing.py` | Task assignment · nurse worklists · care coordination |
| `care_events.py` | Role-scoped care event feeds · shared patient timeline |

Live metrics over `WS /v1/telemetry/stream` — bed census, department loads, ED wait times, surge predictions — pushed every 2 seconds.

---

## 🔗 Interoperability — FHIR · ABDM · DICOM · SMART

| Standard | Module | Status | What's Implemented |
|---|---|---|---|
| **FHIR R4** | `fhir.py` | ✅ | Patient · Encounter · Observation · DiagnosticReport · MedicationRequest · Invoice · Bundle · SHA-256 signed manifests |
| **India ABDM** | `abdm.py` | ✅ | Readiness checks · consent request generation · callback normalization · payload signing · `abdm_consent_events` audit log |
| **DICOMweb / PACS** | `dicomweb.py` | ✅ | QIDO-RS · WADO-RS metadata · STOW-RS endpoint planning (no raw image bytes) |
| **SMART on FHIR** | `smart_fhir.py` | ✅ | Readiness checks · EHR launch authorization URL generation |
| **Terminology** | `terminology.py` | ✅ | LOINC · SNOMED CT · ICD-10-CM seed catalog |

---

## 🖥 Frontend — React 19 Medical Dashboard

**Stack:** Vite 8 · React 19 · TypeScript · Tailwind CSS 4 · React Router DOM v7 · TanStack Query v5 · Zustand v5

| Route | Page |
|---|---|
| `/dashboard` | Patient health summary and recent prediction results |
| `/chat` | AI medical chatbot — SSE streaming, RAG context, suggested questions |
| `/predict` | ML prediction hub |
| `/predict/diabetes` · `/heart` · `/liver` · `/kidney` · `/lungs` | Individual disease screeners with SHAP visualization |
| `/admin` | User management · audit logs · AI governance · model cards · operational health |
| `/capacity` | Live hospital capacity dashboard (WebSocket) |
| `/telemedicine` | Telemedicine appointment booking + Jitsi video |
| `/patients` · `/patients/:id` | Patient management (doctor/admin views) |
| `/profile` · `/pricing` · `/infrastructure` · `/about` | Supporting pages |

**Testing:** Vitest + Testing Library (unit) · Playwright (E2E)

---

## 📡 API Reference

All routes prefixed `/v1`. Interactive docs at **http://127.0.0.1:8000/docs**

<details>
<summary><strong>Auth & Users</strong></summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/signup` | — | Register new user |
| `POST` | `/v1/token` | — | Login · returns JWT |
| `GET` | `/v1/profile` | User | Own profile |
| `PUT` | `/v1/profile` | User | Update profile |
| `GET` | `/v1/users` | Admin | List all users |
| `GET` | `/v1/users/{id}/full` | Admin | Full user dossier |

</details>

<details>
<summary><strong>Disease Predictions & SHAP Explainability</strong></summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/predict/diabetes` | — | Diabetes (9 features · XGBoost · 89%) |
| `POST` | `/v1/predict/heart` | — | Heart disease (13 features · Ensemble · 92%) |
| `POST` | `/v1/predict/liver` | — | Liver disease (10 features) |
| `POST` | `/v1/predict/kidney` | — | Kidney disease (24 features) |
| `POST` | `/v1/predict/lungs` | — | Respiratory (15 features) |
| `POST` | `/v1/predict/explain/{model}` | — | SHAP feature attribution |
| `POST` | `/v1/predict/reviews` | Doctor/Admin | Log clinician override decision |
| `POST` | `/v1/admin/reload_models` | Admin | Hot-reload all ML models |

</details>

<details>
<summary><strong>AI Chatbot & LangGraph Agent</strong></summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/chat` | User | LangGraph + RAG conversation |
| `POST` | `/v1/chat/stream` | User | SSE streaming chat |
| `GET` | `/v1/chat/history` | User | Last 100 messages |
| `DELETE` | `/v1/chat/history` | User | Clear history |
| `GET` | `/v1/chat/context` | User | Debug RAG context assembly |
| `GET` | `/v1/chat/suggestions` | User | Dynamic starter questions |
| `GET` | `/v1/ai/models` | — | List Ollama models |
| `POST` | `/v1/ai/models/pull` | Admin | Pull Ollama model (SSE) |

</details>

<details>
<summary><strong>Health Records · Vision AI · PDF Reports · Appointments</strong></summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/records` | User | Save health record |
| `GET` | `/v1/records` | User | Get all records |
| `DELETE` | `/v1/records/{id}` | User | Delete record |
| `POST` | `/v1/analyze/report` | User | Vision AI — lab report analysis |
| `GET` | `/v1/download/health-report` | User | Download PDF health report |
| `POST` | `/v1/explain/` | User | Plain-language prediction explanation |
| `POST` | `/v1/appointments/` | User | Book telemedicine appointment |
| `GET` | `/v1/appointments/doctors` | — | List available doctors |
| `POST` | `/v1/payments/create-order` | User | Razorpay order |
| `POST` | `/v1/payments/verify` | User | Verify payment signature |

</details>

<details>
<summary><strong>Admin · Governance · Compliance · Telemetry</strong></summary>

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/admin/stats` | Admin | Platform statistics |
| `GET` | `/v1/admin/ai-functions` | Admin | AI governance inventory |
| `GET` | `/v1/admin/model-cards` | Admin | ML model + dataset cards |
| `GET` | `/v1/admin/operational-health` | Admin | Full readiness report |
| `GET` | `/v1/admin/data-quality` | Admin | PHI-safe data quality report |
| `GET` | `/v1/admin/backup-readiness` | Admin | Backup metadata |
| `GET` | `/v1/admin/incident-readiness` | Admin | Incident response metadata |
| `GET` | `/v1/admin/retention-readiness` | Admin | Retention policy metadata |
| `GET` | `/v1/admin/security-assurance` | Admin | Security posture |
| `GET` | `/v1/admin/privacy/deletion-plan/{id}` | Admin | Patient deletion plan |
| `WS` | `/v1/telemetry/stream` | — | Live hospital capacity stream |
| `GET` | `/healthz` | — | Health check |

</details>

---

## 🗄 Database Layer

**File:** `backend/database.py` — SQLAlchemy ORM, auto-migration via Alembic, auto-detects SQLite vs PostgreSQL.

| Table | Key Fields |
|---|---|
| `users` | id, username, role, email, hashed_password, full_name, dob, health fields, plan_tier, allow_data_collection |
| `health_records` | id, user_id, record_type, data (JSON), prediction, timestamp |
| `chat_logs` | id, user_id, role, content, timestamp |
| `audit_logs` | id, admin_id, target_user_id, action, details |
| `appointments` | id, patient_id, doctor_id, date, status |
| `medication_inventory` | id, medication_name, strength, batch_number, quantity_on_hand, reorder_level |
| `prescriptions` | id, encounter_id, patient_id, doctor_id, diagnosis_context, status |
| `invoices` | id, patient_id, status, subtotal, tax_amount, total_amount, paid_amount |
| `discharge_summaries` | id, admission_id, patient_id, doctor_id, diagnosis_summary, follow_up_plan |
| `nursing_tasks` | id, patient_id, assigned_nurse_id, task_type, priority, status, due_at |
| `interoperability_consents` | id, patient_id, scope, purpose, status, abdm_request_id, expires_at |

**Features:** SQLite WAL mode · PostgreSQL connection pooling · `postgres://` URL normalization · Alembic auto-migration on startup

---

## 🔐 Security Posture

**8-layer middleware stack** (execution order):

| # | Middleware | Purpose |
|---|---|---|
| 1 | `RequestTracingMiddleware` | Injects `X-Request-ID` for distributed tracing |
| 2 | `APIVersioningMiddleware` | `/v1` routing and version negotiation |
| 3 | `RateLimitMiddleware` | 60 req/min per IP (configurable) |
| 4 | `TrustedHostMiddleware` | Allowlist via `ALLOWED_HOSTS` |
| 5 | `CORSMiddleware` | Origin-restricted via `CORS_ORIGINS` |
| 6 | `SecurityHeadersMiddleware` | X-Frame-Options · X-Content-Type-Options · nosniff |
| 7 | `GZipMiddleware` | Response compression ≥ 1,000 bytes |
| 8 | `ExceptionMiddleware` | All errors sanitized — **zero PII in any response** |

**Auth:** JWT HS256 (30-min expiry) · bcrypt · RBAC (patient / doctor / admin)

**Privacy:** PII never logged · per-user `allow_data_collection` flag · patient deletion propagation across DB, vector store, ABDM consents, and exports · mandatory medical disclaimers on all AI responses

**Compliance surfaces** at `/v1/admin/*`: backup readiness · incident response · retention policy · security assurance — anchored to WHO AI governance, FDA CDS transparency, and EU AI Act principles

---

## 🔄 CI/CD Pipelines

**8 GitHub Actions workflows:**

| Workflow | Trigger | Purpose |
|---|---|---|
| **CI Tests** | Push / PR | `pytest` full suite + coverage |
| **CodeQL** | Push / PR + weekly | SAST static analysis |
| **Docker** | Push / PR | Build and push to `ghcr.io` |
| **HuggingFace** | Push to `main` | Sync to HF Spaces |
| **Keep-Alive** | Scheduled | Prevent Render cold starts |
| **Labels** | Push to `main` | Sync GitHub label config |
| **Release Drafter** | Push / PR | Auto-generate release notes |
| **Stale Bot** | Scheduled | Close inactive issues/PRs |

Plus: Dependabot (Python · npm · Docker · Actions) · CODEOWNERS · issue/PR templates · FUNDING.yml

---

## 🚀 Deployment

> ⚠️ Before any production rollout, run the readiness gate:
> ```bash
> python scripts/production_readiness_check.py
> ```
> See [`docs/PRODUCTION_READINESS_GATE.md`](docs/PRODUCTION_READINESS_GATE.md) — covers database, security, AI safety, monitoring, and rollback sign-off.

| Option | Command | Best For |
|---|---|---|
| **Docker Compose** | `docker compose up --build` | Local dev and demos |
| **Enterprise Stack** | `docker compose -f docker-compose.enterprise.yml up` | Full local env + PostgreSQL · Redis · Prometheus · Grafana · Jaeger · MLflow |
| **Render** | Auto-deploy via `render.yaml` | Free cloud hosting · Singapore region |
| **Kubernetes** | `kubectl apply -f k8s/` | HA: 3 backend + 2 frontend replicas · PVC · HPA autoscaling |
| **Terraform AWS** | `cd terraform && terraform apply` | Production: VPC · EKS · RDS · ElastiCache · S3 · EFS · ALB · Route53 |

---

## 📁 Project Structure

<details>
<summary><strong>Full directory tree</strong></summary>

```
AI-Healthcare-System/
├── backend/
│   ├── main.py                    # FastAPI app, 8-layer middleware, router mounting
│   ├── core_ai.py                 # 3-tier AI gateway — the ONLY file that calls providers
│   ├── prediction.py              # 5 ML disease prediction + clinician audit
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
│   ├── billing.py                 # Invoicing, payments
│   ├── discharge.py               # Discharge summaries
│   ├── nursing.py                 # Nursing task management
│   ├── care_events.py             # Patient timeline feed
│   ├── interoperability.py        # Unified FHIR/ABDM/DICOM/SMART API
│   ├── fhir.py                    # FHIR R4 serializers
│   ├── abdm.py                    # India ABDM connector
│   ├── dicomweb.py                # DICOMweb/PACS connector
│   ├── smart_fhir.py              # SMART on FHIR helpers
│   ├── terminology.py             # LOINC/SNOMED CT/ICD-10-CM
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
├── frontend/                      # Vite 8 + React 19 + TypeScript
│   ├── src/pages/                 # 17 route pages
│   ├── src/components/            # Shared UI components
│   ├── src/lib/                   # API client, utilities
│   ├── src/__tests__/             # Vitest unit tests
│   └── tests/                     # Playwright E2E
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
├── docs/                          # Architecture docs, runbooks, whitepapers
├── .github/workflows/             # 8 CI/CD pipelines
├── docker-compose.yml
├── docker-compose.enterprise.yml
├── Dockerfile
└── AGENTS.md                      # Canonical AI coding agent instructions
```

</details>

---

## ⚙️ Environment Variables

Minimum required:

```bash
GOOGLE_API_KEY=...    # Free at https://aistudio.google.com (skip if using Ollama)
SECRET_KEY=...        # python -c "import secrets; print(secrets.token_hex(32))"
```

<details>
<summary><strong>Full configuration reference</strong></summary>

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

# Cloud AI fallback (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Interoperability connectors (all disabled by default)
ABDM_ENABLED=false
DICOMWEB_ENABLED=false
SMART_FHIR_ENABLED=false
```

See [`.env.example`](.env.example) for the complete reference.

</details>

---

## ❓ FAQ

**How do I run this without an API key?**
Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, set `OLLAMA_BASE_URL=http://127.0.0.1:11434` in `.env`, and leave `GOOGLE_API_KEY` unset. All inference runs locally — free and private.

**Can I use this as a college final-year project?**
Yes — it's MIT licensed and designed to be studied. See the [Key Files Reference](#-key-files-reference) table for which files cover which concepts.

**How do I deploy to the cloud for free?**
Fork the repo and connect it to [Render](https://render.com). The `render.yaml` handles deployment automatically on the free tier.

**Is this HIPAA compliant?**
This platform implements HIPAA-oriented controls (bcrypt, JWT, RBAC, audit logging, PII-scrubbed errors, per-user consent). Full HIPAA compliance for production requires additional organizational controls, BAAs, and a formal compliance review.

**How do I add a new disease prediction model?**
Add a training script → register in `prediction.py:initialize_models()` → add Pydantic schema → add endpoint → add model card in `model_cards.py` → write unit test.

**How does the chatbot remember my health history?**
RAG — your health records are embedded with Gemini `text-embedding-004`, stored in a vector store, retrieved by cosine similarity when you ask a question, and assembled into context before the LLM responds. Your data is scoped to your account only.

**What is FHIR R4 and why does this implement it?**
FHIR R4 is the international standard for exchanging healthcare data. Implementing it means patient records can be exported to or imported from any FHIR-compatible EHR (Epic, Cerner, etc.) without custom integration. The India ABDM connector extends this for the Indian health stack.

---

## 📂 Key Files Reference

A quick map from system capability to the module that owns it:

| Capability | What it does | Module |
| :--- | :--- | :--- |
| **ML Disease Prediction** | Trains and serves 5 tabular classifiers with SHAP feature attribution. | [backend/ml/train_diabetes.py](backend/ml/train_diabetes.py) · [backend/ml/explainability.py](backend/ml/explainability.py) |
| **Multi-Agent Orchestration** | Supervisor-routed LangGraph graph with researcher, analyst, guardrail, and generate nodes. | [backend/services/agent.py](backend/services/agent.py) |
| **RAG Pipeline** | Patient-scoped semantic retrieval, 3,000-token context assembly, citations. | [backend/services/rag.py](backend/services/rag.py) · [backend/services/chat_context.py](backend/services/chat_context.py) |
| **AI Provider Gateway** | Single-gateway fallback chain: Ollama → Gemini → OpenAI/Anthropic with retry and TTL cache. | [backend/services/core_ai.py](backend/services/core_ai.py) |
| **FHIR R4 & Interoperability** | Patient, Encounter, Observation, and MedicationRequest serializers; ABDM and DICOM connectors. | [backend/fhir.py](backend/fhir.py) · [backend/terminology.py](backend/terminology.py) |
| **Auth & RBAC** | JWT HS256, bcrypt, role enforcement (patient / doctor / admin) across all routes. | [backend/api/auth.py](backend/api/auth.py) |
| **8-Layer Middleware** | Request tracing, rate limiting, PII-safe exception masking, security headers, compression. | [backend/services/middleware.py](backend/services/middleware.py) |
| **AWS Infrastructure (IaC)** | VPC, EKS cluster, RDS, ElastiCache, S3, EFS, ALB, Route53 via Terraform. | [terraform/main.tf](terraform/main.tf) |

---

## 🤝 Contributing

Contributions are welcome — bug fixes, new ML models, docs, tests, or translations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Follow [`AGENTS.md`](AGENTS.md) — the canonical instruction file for all code changes.

```bash
python -m pytest tests/ -v
npm --prefix frontend run test
```

<a href="https://github.com/pavanbadempet/AI-Healthcare-System/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=pavanbadempet/AI-Healthcare-System&max=20" alt="Contributors" />
</a>

<details>
<summary><strong>Star History</strong></summary>
<p align="center">
  <a href="https://star-history.com/#pavanbadempet/AI-Healthcare-System&Date">
    <img src="https://api.star-history.com/svg?repos=pavanbadempet/AI-Healthcare-System&type=Date" alt="Star History" width="600"/>
  </a>
</p>
</details>

---

## 📄 License

MIT License — Copyright © 2025 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE).

---

<div align="center">

<img src="docs/assets/divider.svg" alt="" width="100%"/>

<br/>

**If this project helped you, consider giving it a ⭐**

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=social" alt="Stars" /></a>
  &nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/network/members"><img src="https://img.shields.io/github/forks/pavanbadempet/AI-Healthcare-System?style=social" alt="Forks" /></a>
  &nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/watchers"><img src="https://img.shields.io/github/watchers/pavanbadempet/AI-Healthcare-System?style=social" alt="Watchers" /></a>
</p>

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues/new/choose">🐛 Report Issue</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/discussions">💬 Discuss</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/fork">🍴 Fork</a>
</p>

<sub>
Built with Python, FastAPI, React 19, LangGraph, XGBoost, Ollama, FHIR R4, and a commitment to making healthcare AI accessible to everyone.
</sub>

</div>
