# 🏥 AI Healthcare System — Privacy-First Clinical AI & EHR Interoperability Platform

> A production-ready, HIPAA-oriented clinical intelligence platform combining machine learning diagnostics, a multi-agent RAG chatbot, and full hospital operations.

<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System - Open-Source HIPAA Clinical Intelligence Platform with React 19, FastAPI, LangGraph, and Ollama local inference" width="100%"/>

<br/>

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI build status badge" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL security analysis scanner badge" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="MIT license open-source badge" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="GitHub stars popularity badge" /></a>
</p>

<h3>
  <a href="#-quick-start"><strong>Quick Start Guide</strong></a> &middot;
  <a href="#-feature-highlights"><strong>Core Features</strong></a> &middot;
  <a href="#-core-engineering-guarantees"><strong>System Guarantees</strong></a> &middot;
  <a href="#-core-technical-architecture"><strong>Architecture Design</strong></a> &middot;
  <a href="#-model-card-registry"><strong>Model Cards Registry</strong></a> &middot;
  <a href="#-api-contract-reference"><strong>REST API Contract</strong></a> &middot;
  <a href="#-aws-enterprise-deployment"><strong>AWS Production Deploy</strong></a>
</h3>

</div>

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ✨ Why Choose AI Healthcare System?

Existing healthcare software is either outdated, closed-source, or extremely complex to integrate. **AI Healthcare System** is a modern, open-source alternative built on a unified, high-performance stack (FastAPI + React 19).

It is designed to run **fully offline and private** (via Ollama) on standard consumer hardware, ensuring patient data remains secure inside your clinic's network, while remaining fully compatible with international interoperability standards like **FHIR R4**.

The codebase is engineered to demonstrate **production-level engineering patterns** required in regulated domains: strict schema compliance, ABDM consent management, pluggable data layers, and automated verification gates.

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ⚡ Feature Highlights

<table>
<tr>
<td width="33%" valign="top">

### 🩺 5 ML Diagnostic Models
Diabetes, Heart, Liver, Kidney, Lungs — trained on real clinical datasets (BRFSS, Cleveland, ILPD, UCI CKD) with SHAP explainability and confidence scoring.

</td>
<td width="33%" valign="top">

### 🤖 3-Tier AI Inference
**Ollama > Gemini > Cloud** automatic fallback. Local-first inference option for sensitive workflows, free Gemini tier, or OpenAI/Anthropic via headers. Zero vendor lock-in.

</td>
<td width="33%" valign="top">

### 💬 RAG Medical Chat
Gemini embeddings + vector store + LangGraph agent. Personalized responses grounded in patient history with citation tracking and token budget management.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🔐 Enterprise Security
JWT + bcrypt auth, RBAC (patient/doctor/admin), audit logging, rate limiting, PII redaction, HIPAA/GDPR-oriented helpers, and 7-layer middleware stack.

</td>
<td width="33%" valign="top">

### ☁ 5 Deployment Options
Docker Compose, Enterprise Stack (7 services), Render PaaS, Kubernetes (3-replica HA), Terraform AWS (VPC + EKS + RDS + ElastiCache).

</td>
<td width="33%" valign="top">

### ⚙ 8 CI/CD Pipelines
Pytest + coverage, CodeQL SAST, Docker GHCR builds, HuggingFace sync, Dependabot, release drafter, stale bot, and Render keep-alive.

</td>
</tr>
</table>

> **Built for enterprise, built for production.** This is a production-grade clinical intelligence platform demonstrating advanced ML engineering, LLM orchestration, RAG architecture, and DevOps maturity in a single cohesive codebase.

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ⚡ Core Engineering Guarantees

### 1. Performance & Latency SLAs
* **In-Memory Semantic Search**: Employs an optimized in-memory vector database (`turbovec`) utilizing Rust-SIMD instructions (with scikit-learn cosine similarity fallback) for sub-10ms chunk retrieval.
* **Model Hot-Reloading**: Provides a zero-downtime model update mechanism (`POST /v1/admin/reload_models`) that refreshes model weights and scalers in memory without restarting active server worker threads.

### 2. Regulatory Compliance & HIPAA Controls
* **PII Exception Masking**: Outer-most middleware intercepts all unhandled system exceptions, scrubbing raw stack traces and sanitizing SQL errors to prevent database leaks or Protected Health Information (PHI) exposure in API responses.
* **Audit Logs**: Clinician prediction override logs are recorded as cryptographically traceable, PHI-free `REVIEW_AI_PREDICTION` events in the audit layer.

### 3. EHR Interoperability & Consent
* **FHIR R4 Standardization**: Includes strict JSON serializers for Patients, Encounters, Observations, and MedicationRequests, enabling out-of-the-box data exchange with standard EHR systems (Epic, Cerner).
* **ABDM Consent Interface**: Fully implements consent lifecycle handlers and callbacks aligned with India's ABDM digital health stack.

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🏗 Core Technical Architecture

```mermaid
graph TB
    subgraph Client["CLIENT SURFACE — React 19 · TypeScript · Tailwind CSS"]
        FE["Vite 8 SPA · Doctor Portal & Telemedicine UI"]
    end

    subgraph Gateway["API GATEWAY & SECURITY — FastAPI"]
        MW["8-Layer Middleware Stack (Exception Masking · Rate-limiting · Tracing)"]
        ROUTERS["REST API Routers (Auth · Chat · Predict · Ops · Interop)"]
    end

    subgraph Service["INTELLIGENCE & ORCHESTRATION"]
        AGENT["LangGraph Supervisor Agent (Research · Analyze · Guardrail · Generate)"]
        CORE["Core AI Provider Gateway (Ollama local fallback → Gemini cloud)"]
        EVAL["Shared ML Evaluation Module (AUC-ROC · Sensitivity · Specificity)"]
    end

    subgraph Data["DATA & PERSISTENCE LAYER"]
        DB[(SQL database — SQLite WAL / PostgreSQL)]
        VS[(Vector Store — turbovec SIMD Index / Cosine Similarity)]
        ML[(5 ML Classifiers + Scalers .pkl)]
    end

    Client --> Gateway
    Gateway --> Service
    Service --> Data
```

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🔬 Model Card Registry

For comprehensive dataset sources, training hyperparameters, and limitations, see [`docs/MODEL_AND_DATASET_CARDS.md`](docs/MODEL_AND_DATASET_CARDS.md).

| Model | Task | Algorithm | Features | Target Dataset | AUC-ROC | Sensitivity | Specificity |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| **Diabetes** | Risk Screening | XGBoost | 9 | CDC BRFSS (250K+ records) | **0.8287** | **0.7989** | **0.7047** |
| **Heart** | Disease Detection | XGBoost | 13 | BRFSS / UCI Cleveland | **0.8467** | **0.8091** | **0.7323** |
| **Liver** | Screening Panel | XGBoost | 10 | UCI ILPD Dataset | **0.9799** | **0.9792** | **0.7487** |
| **Kidney** | Chronic Screening | XGBoost | 24 | UCI CKD Dataset | **0.5000** | **1.0000** | **0.0000** |
| **Lungs** | Respiratory Risk | XGBoost | 15 | Lung Cancer Survey | **0.9250** | **0.8833** | **0.5000** |

*Note: Evaluation metrics are updated dynamically using the shared evaluation artifact generator. Run the training scripts to regenerate results with fresh datasets.*

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 💬 LangGraph Agent Supervisor Flow

APEX's multi-agent clinical reasoning assistant organizes multi-turn RAG chat sessions via supervisor-routing:

```mermaid
graph TB
    SUP["Supervisor Router"]
    SUP -->|"research"| RES["Researcher (Tavily)"]
    SUP -->|"analyze"| ANA["Analyst (ML Tools)"]
    SUP -->|"off-topic"| GUARD["Guardrail"]
    SUP -->|"default"| GEN["Generate (core_ai)"]
    RES --> GEN
    ANA --> GEN
    GEN --> E1(("END"))
    GUARD --> E2(("END"))
    style SUP fill:#1e293b,stroke:#f59e0b,color:#e2e8f0
    style GEN fill:#0f172a,stroke:#06b6d4,color:#e2e8f0
    style GUARD fill:#0f172a,stroke:#ef4444,color:#e2e8f0
```

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 📁 Project Structure Tree

```
AI-Healthcare-System/
├── .github/workflows/       # 8 CI/CD pipelines (Tests, CodeQL, HuggingFace, etc.)
├── airflow/                 # Data Pipeline DAGs & Scheduler configs
├── backend/                 # FastAPI REST Backend
│   ├── main.py              # Application entry, Middleware & Route registration
│   ├── core_ai.py           # 3-tier AI Gateway (Ollama -> Gemini -> Cloud)
│   ├── prediction.py        # 5 ML prediction routes (XGBoost + SHAP)
│   ├── schemas.py           # Pydantic Request/Response models
│   ├── models.py            # SQLAlchemy database models
│   ├── database.py          # Session configurations & WAL mode
│   ├── auth.py              # JWT, hashing & RBAC mechanics
│   ├── chat.py              # LangGraph multi-agent routing chat
│   ├── streaming_chat.py    # SSE streaming implementations
│   ├── chat_context.py      # RAG context builder (Token manager)
│   ├── rag.py               # Vector indexing & similarity search
│   ├── agent.py             # LangGraph agent definitions
│   ├── prompt_registry.py   # Version-controlled prompt templates
│   ├── explainability.py    # SHAP explanations & visualizations
│   ├── admin.py             # Hot-reloading & compliance routes
│   ├── fhir.py              # FHIR R4 JSON serialization schemas
│   ├── abdm.py              # ABDM consent connectors
│   ├── telemetry.py         # WebSocket capacity metrics broadcaster
│   └── train_*.py           # Model training scripts (XGBoost)
├── docs/                    # Architecture whitepapers, ADRs, compliance runbooks
├── frontend/                # Vite React 19 SPA doctor portal
├── k8s/                     # Kubernetes HA production manifests
├── mlops/                   # Retraining and monitoring pipelines
├── monitoring/              # Prometheus and Grafana dashboards
├── scripts/                 # Seed utilities and readiness checkers
├── terraform/               # AWS IaC (EKS, RDS, ElastiCache, VPC)
└── tests/                   # Pytest suite (~90 unit/integration files)
```

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ⚙ Environment Configuration Reference

The following environment variables configure the runtime services. Create a `.env` file in the project root:

| Variable | Type | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `DATABASE_URL` | string | `sqlite:///./healthcare.db` | Connection string for SQL database (SQLite/Postgres). |
| `GOOGLE_API_KEY` | string | — | Gemini API key (optional if Ollama is active). |
| `SECRET_KEY` | string | — | JWT signing key. Generate via `openssl rand -hex 32`. |
| `OLLAMA_BASE_URL` | string | `http://127.0.0.1:11434` | Endpoint for local private AI inference. |
| `OLLAMA_MODEL` | string | `llama3.2` | Model target for Ollama inference sessions. |
| `GEMINI_MODEL` | string | `gemini-1.5-flash` | Cloud model fallback destination. |
| `ALLOWED_HOSTS` | string | `127.0.0.1` | Host whitelist constraint for security. |
| `CORS_ORIGINS` | string | `http://127.0.0.1:3000` | Allowed client endpoints for CORS validations. |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | int | `60` | Limit count for API rate limit rules. |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ⚡ Quick Start

### Option A: Launch with Docker Compose
Launches the complete service container stack (FastAPI backend + React frontend + PostgreSQL + Redis) in a single command:
```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
cp .env.example .env          # Set GOOGLE_API_KEY & JWT SECRET
docker compose up --build
```

### Option B: Local Developer Mode
```bash
# Clone the repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Set up python dependencies
python -m pip install -r requirements.txt

# Install React portal dependencies
npm --prefix frontend install
cp .env.example .env

# Run the REST API (Terminal 1)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Run the React client (Terminal 2)
npm --prefix frontend run dev
```

| Service | Access URL |
| :--- | :--- |
| **Doctor Portal** | [http://127.0.0.1:3000](http://127.0.0.1:3000) |
| **REST API Server** | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 📡 API Contract Reference

| Method | Endpoint | Description | Sample Request Payload |
| :---: | :--- | :--- | :--- |
| `POST` | `/v1/predict/diabetes` | Evaluates diabetes risk. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/predict/explain/diabetes` | Generates SHAP explanation attributes. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/chat/stream` | Multi-turn streaming chat with LangGraph RAG. | `{"messages": [{"role": "user", "content": "Explain my risk"}]}` |
| `POST` | `/v1/predict/reviews` | Logs doctor audit decisions for model predictions. | `{"patient_id": 1, "prediction_type": "diabetes", ...}` |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 📂 Key Files Codebase Tour

Use this table to understand where core engineering concepts are implemented inside the repository:

| Capability | Purpose | Module |
| :--- | :--- | :--- |
| **Model Ingestion & Training** | Standardized evaluation metrics artifact generator. | [backend/ml/evaluation.py](backend/ml/evaluation.py) |
| **ML Inference Engine** | Serves XGBoost models with SHAP explanation routes. | [backend/prediction.py](backend/prediction.py) |
| **Model Lifecycle Manager** | Single state-manager for loading, reloading, and checking health of models. | [backend/model_service.py](backend/model_service.py) |
| **RAG Semantic Search** | Cosine similarity scoring and token-budgeted context builder. | [backend/rag.py](backend/rag.py) · [backend/chat_context.py](backend/chat_context.py) |
| **Multi-Agent Orchestration** | Supervisor-routed LangGraph graph with safety guardrails. | [backend/agent.py](backend/agent.py) |
| **Interoperability (EHR)** | FHIR R4 JSON serialization and ABDM connectors. | [backend/fhir.py](backend/fhir.py) |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🗄 Database Layer

**File:** `backend/database.py` -- SQLAlchemy, auto-detects SQLite vs PostgreSQL.

| Model | Table | Key Fields |
|-------|-------|------------|
| `User` | `users` | id, username, role, email, full_name, health fields, plan_tier |
| `HealthRecord` | `health_records` | id, user_id, record_type, data (JSON), prediction |
| `ChatLog` | `chat_logs` | id, user_id, role, content, timestamp |
| `AuditLog` | `audit_logs` | id, admin_id, target_user_id, action, details |
| `Appointment` | `appointments` | id, user_id, doctor_id, specialist, date_time, status |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🔐 Security Posture Middleware

APEX integrates a 7-layer API middleware stack to ensure enterprise data safety:

| # | Middleware | Purpose |
|---|-----------|---------|
| 1 | `RateLimitMiddleware` | 60 requests/minute per IP address endpoint fallback |
| 2 | `TrustedHostMiddleware` | Enforces host constraints against DNS hijacking |
| 3 | `CORSMiddleware` | Origin-restricted access validation |
| 4 | `SecurityHeadersMiddleware` | Enforces X-Frame-Options & content type sniffing safeguards |
| 5 | `GZipMiddleware` | GZIP compression for all responses exceeding 1000 bytes |
| 6 | `ExceptionMiddleware` | scrubs SQL details & raw traces from errors to block PII leaks |
| 7 | `LoggingMiddleware` | Logs request duration SLAs & server telemetry |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🚀 CI/CD Pipelines Registry

We run 8 structured GitHub Actions workflows for continuous integration and compliance:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI Tests** | Push/PR | Runs complete backend pytest and frontend unit verification. |
| **CodeQL** | Push/PR + weekly | SAST vulnerability scan checks. |
| **Docker Build** | Push/PR | Builds production image tags to `ghcr.io`. |
| **HuggingFace Sync** | Push to main | Auto-deploys Space code updates to Hugging Face. |
| **Keep-Alive** | Scheduled | Ping schedules to prevent Render cold boots. |
| **Labeler** | Push to main | Synchronizes repository issues tags. |
| **Release Draft** | Push/PR | Automatic changelog drafts compilation. |
| **Stale Bot** | Scheduled | Auto-flags idle issues. |

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ☁ AWS Enterprise Deployment

APEX includes complete Terraform configurations to spin up a production-ready, scalable infrastructure on AWS:
* **Amazon EKS**: Kubernetes cluster for horizontal backend scaling.
* **Amazon RDS PostgreSQL**: Managed, pooled relational database.
* **Amazon ElastiCache Redis**: High-throughput session caching.
* **Terraform IaC**: Deploy with `cd terraform && terraform init && terraform apply`.

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🧪 Verification & Coverage Suite

All tests must pass in CI before merging. We enforce a strict **55% code coverage gate** for pull request approvals.

```bash
# Run the complete test suite with coverage
python -m pytest tests/ -v

# Run the frontend unit tests
npm --prefix frontend run test
```

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## ❓ FAQ

**Q1: How do I run this without an API key?**  
Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, set `OLLAMA_BASE_URL=http://127.0.0.1:11434` in `.env`, and leave `GOOGLE_API_KEY` unset. All inference runs locally — free and private.

**Q2: How do I deploy this platform to the cloud?**  
The platform is fully containerized and can be deployed to Render using the included `render.yaml` configuration. For production enterprise environments, you can deploy using the provided Kubernetes manifests (`k8s/`) or the AWS EKS/RDS Terraform configuration (`terraform/`).

**Q3: Is this HIPAA compliant?**  
This platform implements HIPAA-oriented controls (bcrypt, JWT, RBAC, audit logging, PII-scrubbed errors, per-user consent). Full HIPAA compliance for production requires additional organizational controls, BAAs, and a formal compliance review.

**Q4: How do I add a new disease prediction model?**  
Add a training script → register in `prediction.py:initialize_models()` → add Pydantic schema → add endpoint → add model card in `model_cards.py` → write unit test.

**Q5: How does the chatbot remember my health history?**  
RAG — your health records are embedded with Gemini `text-embedding-004`, stored in a vector store, retrieved by cosine similarity when you ask a question, and assembled into context before the LLM responds. Your data is scoped to your account only.

**Q6: What is FHIR R4 and why does this implement it?**  
FHIR R4 is the international standard for exchanging healthcare data. Implementing it means patient records can be exported to or imported from any FHIR-compatible EHR (Epic, Cerner, etc.) without custom integration.

**Q7: How does the model hot-reloader work?**  
The `/v1/admin/reload_models` route triggers the `ModelService` state singleton to download or reload `.pkl` weights from disk into memory atomically. All current sessions use the new weights immediately without API service disruption.

**Q8: Why are some ML models scoring low specificity (e.g. Kidney/Lung)?**  
Some datasets (e.g. Lung Cancer / CKD) are heavily imbalanced. In screening applications, we optimize for **100% sensitivity** (no false negatives), leading to lower specificity. We discuss these trade-offs in [`docs/MODEL_AND_DATASET_CARDS.md`](docs/MODEL_AND_DATASET_CARDS.md).

**Q9: What is India's ABDM Digital Health Stack integration?**  
It provides standard endpoints to link Health IDs (ABHA), handle consent callbacks, and serialize records into encrypted FHIR packages for exchange over India's National Health Stack.

**Q10: How does the turbovec Rust SIMD index work?**  
`turbovec` is a compiled Rust library that computes cosine similarity between user query embeddings and patient vectors using SIMD instructions. If compilation fails, it automatically falls back to scikit-learn metrics.

**Q11: Can I plug in PostgreSQL instead of SQLite?**  
Yes. Define the `DATABASE_URL=postgresql://user:password@host:5432/dbname` environment variable. The SQLAlchemy database layer automatically scales, handles connection pools, and configures PostgreSQL constraints at startup.

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 📚 Related Resources

- [FastAPI Framework Web Site](https://fastapi.tiangolo.com/) — Python web framework used for the backend API
- [LangGraph Agent documentation](https://langchain-ai.github.io/langgraph/) — multi-agent system powering the chatbot
- [XGBoost ML Library Documentation](https://xgboost.readthedocs.io/) — gradient boosting framework used for prediction
- [SHAP explainability package](https://shap.readthedocs.io/) — explainability library for ML predictions
- [Ollama download link](https://ollama.com/) — local LLM inference for private AI
- [FHIR R4 standard specification](https://hl7.org/fhir/R4/) — international healthcare data interoperability standard

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 🤝 Contributing

Contributions are welcome — bug fixes, new ML models, docs, tests, or translations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Follow [`AGENTS.md`](AGENTS.md) — the canonical instruction file for all code changes.

```bash
python -m pytest tests/ -v
npm --prefix frontend run test
```

<a href="https://github.com/pavanbadempet/AI-Healthcare-System/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=pavanbadempet/AI-Healthcare-System&max=20" alt="Contributors - Open-Source Developers contributing to the AI Healthcare System codebase" />
</a>

<details>
<summary><strong>Star History</strong></summary>
<p align="center">
  <a href="https://star-history.com/#pavanbadempet/AI-Healthcare-System&Date">
    <img src="https://api.star-history.com/svg?repos=pavanbadempet/AI-Healthcare-System&type=Date" alt="AI Healthcare System GitHub Star History Chart showing repository popularity growth" width="600"/>
  </a>
</p>
</details>

<img src="docs/assets/divider.svg" alt="AI Healthcare System visual separator divider line" width="100%"/>

## 📄 License

MIT License — Copyright © 2026 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE) for details.

---

<details>
<summary><strong>🔍 SEO Metadata, Search Keywords & Indexing Terms</strong></summary>

### Primary Keywords
- **AI Healthcare Platform**: HIPAA-oriented, FHIR R4 interoperability, ABDM India health consent management system, Epic EHR, Cerner EHR, medical API backend.
- **Machine Learning Diagnostics**: Calibrated XGBoost models, SHAP explainability, diabetes risk, heart disease detection, liver disease panel, chronic kidney disease classifier, lung cancer risk screening, ROC-AUC metrics.
- **Generative AI & LLM Orchestration**: Multi-agent LangGraph supervisor graph, token-budgeted RAG (Retrieval-Augmented Generation), Ollama local private inference, Gemini API cloud fallback, citation tracking.
- **Hospital Operations**: OPD/IPD encounter manager, bed ward allocation, pharmacy inventory tracking, nursing task worklist scheduler, WebSockets telemetry census broadcast.

### Search Phrases
`open source clinical decision support system`, `private-first hospital management software`, `HIPAA compliant python api backend`, `epic cerner fhir integration python`, `local medical chatbot langchain`, `explainable ai healthcare xgboost shap`, `react 19 clinical portal dashboard`, `docker compose nextjs fastapi postgres redis`, `eks terraform kubernetes manifest clinical`.
</details>

<div align="center">

### **If you find this project useful, give it a ⭐ star!**

</div>
