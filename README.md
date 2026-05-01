<div align="center">

<!-- HERO BANNER -->
<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System â€” Clinical Decision Support Platform" width="100%"/>

<br/>

<!-- DYNAMIC GITHUB BADGES -->
<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="License" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="Stars" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues"><img src="https://img.shields.io/github/issues/pavanbadempet/AI-Healthcare-System?style=flat-square&color=ef4444" alt="Issues" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/pulls"><img src="https://img.shields.io/github/issues-pr/pavanbadempet/AI-Healthcare-System?style=flat-square&color=8b5cf6" alt="PRs" /></a>
</p>

<!-- TECH STACK BADGES -->
<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge&logo=chainlink&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />
  <img src="https://img.shields.io/badge/XGBoost-189FDD?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost" />
</p>
<p>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="K8s" />
  <img src="https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white" alt="Terraform" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus" />
</p>

<!-- NAVIGATION -->
<p>
  <a href="#-quick-start"><strong>Quick Start</strong></a> Â· 
  <a href="#-architecture"><strong>Architecture</strong></a> Â· 
  <a href="#-ml-models"><strong>ML Models</strong></a> Â· 
  <a href="#-3-tier-ai-engine"><strong>AI Engine</strong></a> Â· 
  <a href="#-rag-pipeline"><strong>RAG Pipeline</strong></a> Â· 
  <a href="#-api-reference"><strong>API Docs</strong></a> Â· 
  <a href="#-deployment"><strong>Deploy</strong></a>
</p>

</div>

<img src="docs/assets/divider.svg" alt="" width="100%"/>

## âš¡ Feature Highlights

<table>
<tr>
<td width="33%" valign="top">

### ðŸ”¬ 5 ML Diagnostic Models
Diabetes Â· Heart Â· Liver Â· Kidney Â· Lungs â€” trained on real clinical datasets (BRFSS, Cleveland, ILPD, UCI CKD) with SHAP explainability and confidence scoring.

</td>
<td width="33%" valign="top">

### ðŸ§  3-Tier AI Inference
**Ollama â†’ Gemini â†’ Cloud** automatic fallback. HIPAA-friendly local inference, free Gemini tier, or OpenAI/Anthropic via headers. Zero vendor lock-in.

</td>
<td width="33%" valign="top">

### ðŸ“š RAG Medical Chat
Gemini embeddings + vector store + LangGraph agent. Personalized responses grounded in patient history with citation tracking and token budget management.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### ðŸ”’ Enterprise Security
JWT + bcrypt auth, RBAC (patient/doctor/admin), audit logging, rate limiting, PII redaction, HIPAA/GDPR compliance modules, and 7-layer middleware stack.

</td>
<td width="33%" valign="top">

### ðŸš€ 5 Deployment Options
Docker Compose Â· Enterprise Stack (7 services) Â· Render PaaS Â· Kubernetes (3-replica HA) Â· Terraform AWS (VPC + EKS + RDS + ElastiCache).

</td>
<td width="33%" valign="top">

### âš™ï¸ 8 CI/CD Pipelines
Pytest + coverage, CodeQL SAST, Docker GHCR builds, HuggingFace sync, Dependabot, release drafter, stale bot, and Render keep-alive.

</td>
</tr>
</table>

> **Built for portfolios, built for production.** This isn't a tutorial project â€” it's a full-stack healthcare platform demonstrating ML engineering, LLM orchestration, RAG architecture, and DevOps maturity in a single cohesive codebase.

<img src="docs/assets/divider.svg" alt="" width="100%"/>
## ðŸ“‹ Table of Contents

<details>
<summary><strong>Click to expand full table of contents</strong></summary>

- [Quick Start](#-quick-start)
- [Architecture Overview](#-architecture)
- [ML Diagnostic Models (5)](#-ml-models)
- [3-Tier AI Inference Engine](#-3-tier-ai-engine)
- [RAG Pipeline & Semantic Memory](#-rag-pipeline)
- [LangGraph Agent](#-langgraph-medical-agent)
- [Prompt Registry](#-prompt-registry)
- [API Reference (All Endpoints)](#-api-reference)
- [Pydantic Schemas](#-pydantic-schemas)
- [Frontend (Next.js)](#-frontend)
- [Database Layer](#-database-layer)
- [Security Posture](#-security-posture)
- [CI/CD Pipelines (8 Workflows)](#-cicd-pipelines)
- [Telemetry WebSocket](#-telemetry-websocket)
- [Deployment Options](#-deployment)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)

</details>

---

## ðŸš€ Quick Start

### Prerequisites

- Python 3.10+ &nbsp;|&nbsp; Node.js 18+ &nbsp;|&nbsp; (Optional) [Ollama](https://ollama.com) for local AI

### 1. Clone & Install

```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env â†’ set GOOGLE_API_KEY (free Gemini key) and SECRET_KEY
```

### 3. Run

```bash
# Terminal 1: Backend (FastAPI on port 8000)
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend (Next.js on port 3000)
cd frontend && npm run dev -- -p 3000
```

### 4. (Optional) Local AI with Ollama

```bash
# Install Ollama â†’ https://ollama.com
ollama pull llama3.2
# The system auto-detects Ollama on 127.0.0.1:11434
```

---

## ðŸ— Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    FRONTEND (Next.js 15)                        â”‚
â”‚   App Router â€¢ Auth Pages â€¢ Dashboard â€¢ Chat â€¢ Predict â€¢ Admin  â”‚
â”‚   Capacity Board â€¢ Telemedicine â€¢ Profile â€¢ Pricing             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚ REST / SSE / WebSocket
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    FASTAPI BACKEND                              â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚   Auth   â”‚ â”‚   Chat   â”‚ â”‚ Predict  â”‚ â”‚  Streaming Chat   â”‚  â”‚
â”‚  â”‚  (JWT)   â”‚ â”‚(LangGraphâ”‚ â”‚ (5 ML    â”‚ â”‚  (SSE + Heartbeat)â”‚  â”‚
â”‚  â”‚  bcrypt  â”‚ â”‚  Agent)  â”‚ â”‚  Models) â”‚ â”‚                   â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚  Admin   â”‚ â”‚ Reports  â”‚ â”‚Payments  â”‚ â”‚   Appointments    â”‚  â”‚
â”‚  â”‚Dashboard â”‚ â”‚PDF+Visionâ”‚ â”‚(Razorpay)â”‚ â”‚  + Email + Jitsi  â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚Telemetry â”‚ â”‚Explain AIâ”‚ â”‚ Ollama   â”‚ â”‚   Enterprise      â”‚  â”‚
â”‚  â”‚WebSocket â”‚ â”‚(core_ai) â”‚ â”‚ Routes   â”‚ â”‚   Features        â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                                                                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚              CORE AI ENGINE (core_ai.py)                â”‚    â”‚
â”‚  â”‚   Tier A: Ollama (Local, HIPAA-friendly)                â”‚    â”‚
â”‚  â”‚   Tier B: Gemini (Google API, free tier)                â”‚    â”‚
â”‚  â”‚   Tier C: OpenAI / Anthropic / OpenRouter (Cloud)       â”‚    â”‚
â”‚  â”‚   Auto-fallback: A â†’ B â†’ C                             â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â”‚                                                                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”‚
â”‚  â”‚   RAG Pipeline     â”‚  â”‚     Prompt Registry             â”‚    â”‚
â”‚  â”‚ Gemini Embeddings  â”‚  â”‚  Version-controlled prompts     â”‚    â”‚
â”‚  â”‚ Cosine Similarity  â”‚  â”‚  6 registered templates         â”‚    â”‚
â”‚  â”‚ Citation Tracking  â”‚  â”‚  A/B testing support            â”‚    â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â–¼                  â–¼                  â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   SQLite /   â”‚  â”‚ Vector Store â”‚  â”‚  ML Model Files  â”‚
â”‚  PostgreSQL  â”‚  â”‚  (Pickle +   â”‚  â”‚  (.pkl artifacts)â”‚
â”‚  (DATABASE_  â”‚  â”‚   Cosine)    â”‚  â”‚  5 models +      â”‚
â”‚   URL env)   â”‚  â”‚              â”‚  â”‚  3 scalers       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **All AI through `core_ai.py`** | Single gateway prevents provider lock-in; enforces audit logging |
| **Prompts in `prompt_registry.py`** | No inline prompts in handlers; versioned, auditable, A/B testable |
| **ML loading via `prediction.py â†’ initialize_models()`** | Centralized model lifecycle; supports hot-reload via `/admin/reload_models` |
| **`DATABASE_URL` from env** | Never hardcoded; supports SQLite (dev) â†’ PostgreSQL (prod) seamlessly |
| **Gemini embeddings for RAG** | Free API, saves ~200MB vs local sentence-transformers |

---

## ðŸ¤– ML Models

Five scikit-learn/XGBoost diagnostic models trained on public clinical datasets:

### 1. Diabetes Prediction (`diabetes_model.pkl`)

| Property | Value |
|----------|-------|
| **Dataset** | BRFSS 2015 (CDC Big Data) |
| **Algorithm** | XGBoost Classifier |
| **Features (9)** | `hypertension`, `high_chol`, `bmi`, `smoking_history`, `heart_disease`, `physical_activity`, `general_health`, `gender`, `age_bucket` |
| **Preprocessing** | Age mapped to BRFSS buckets (1â€“13) via `get_age_bucket()` |
| **Endpoint** | `POST /predict/diabetes` |
| **Training Script** | `backend/train_diabetes.py` |

### 2. Heart Disease Prediction (`heart_disease_model.pkl`)

| Property | Value |
|----------|-------|
| **Dataset** | Cleveland Heart Disease (UCI) |
| **Algorithm** | Ensemble Classifier |
| **Features (13)** | `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal` |
| **Endpoint** | `POST /predict/heart` |
| **Training Script** | `backend/train_heart.py` |

### 3. Liver Disease Prediction (`liver_disease_model.pkl`)

| Property | Value |
|----------|-------|
| **Dataset** | Indian Liver Patient Dataset (ILPD) |
| **Algorithm** | Ensemble with StandardScaler |
| **Features (10)** | `Age`, `Gender`, `Total_Bilirubin`, `Direct_Bilirubin`, `Alkaline_Phosphotase`, `Alamine_Aminotransferase`, `Aspartate_Aminotransferase`, `Total_Proteins`, `Albumin`, `Albumin_and_Globulin_Ratio` |
| **Preprocessing** | Log1p transform on skewed features + StandardScaler (`liver_scaler.pkl`) |
| **Endpoint** | `POST /predict/liver` |
| **Training Script** | `backend/train_liver.py` |

### 4. Kidney Disease Prediction (`kidney_model.pkl`)

| Property | Value |
|----------|-------|
| **Dataset** | Chronic Kidney Disease (UCI) |
| **Algorithm** | Classifier with StandardScaler |
| **Features (24)** | `age`, `bp`, `sg`, `al`, `su`, `rbc`, `pc`, `pcc`, `ba`, `bgr`, `bu`, `sc`, `sod`, `pot`, `hemo`, `pcv`, `wc`, `rc`, `htn`, `dm`, `cad`, `appet`, `pe`, `ane` |
| **Preprocessing** | StandardScaler (`kidney_scaler.pkl`) |
| **Endpoint** | `POST /predict/kidney` |
| **Training Script** | `backend/train_kidney.py` |

### 5. Lung/Respiratory Prediction (`lungs_model.pkl`)

| Property | Value |
|----------|-------|
| **Dataset** | Lung Cancer Survey Dataset |
| **Algorithm** | Classifier with StandardScaler |
| **Features (15)** | `GENDER`, `AGE`, `SMOKING`, `YELLOW_FINGERS`, `ANXIETY`, `PEER_PRESSURE`, `CHRONIC_DISEASE`, `FATIGUE`, `ALLERGY`, `WHEEZING`, `ALCOHOL_CONSUMING`, `COUGHING`, `SHORTNESS_OF_BREATH`, `SWALLOWING_DIFFICULTY`, `CHEST_PAIN` |
| **Preprocessing** | StandardScaler (`lungs_scaler.pkl`) |
| **Endpoint** | `POST /predict/lungs` |
| **Training Script** | `backend/train_lungs.py` |

### Prediction Response Format (All Models)

```json
{
  "prediction": "High Risk | Low Risk | Disease Detected | Healthy",
  "raw": 0,
  "confidence": 78.5,
  "risk_level": "High | Moderate | Low",
  "disclaimer": "This is an AI-assisted screening tool, not a medical diagnosis..."
}
```

### SHAP Explainability

Three models support SHAP-based explanation endpoints that return interactive force plots:
- `POST /predict/explain/diabetes`
- `POST /predict/explain/heart`
- `POST /predict/explain/liver`

Uses `TreeExplainer` with VotingClassifier unwrapping for real-time proxy explanations.

---

## ðŸ§  3-Tier AI Engine

**File:** `backend/core_ai.py` â€” **The single gateway for ALL AI inference.** No module may call provider APIs directly.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 PUBLIC API (3 functions)                 â”‚
â”‚  generate(prompt, system, model, api_provider, api_key) â”‚
â”‚  chat(messages, system, model, api_provider, api_key)   â”‚
â”‚  chat_stream(messages, system, ...)  â†’ async generator  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â”‚ Automatic Fallback Chain
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â–¼              â–¼                  â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚  TIER A     â”‚ â”‚ TIER B   â”‚  â”‚    TIER C         â”‚
   â”‚  Ollama     â”‚ â”‚ Gemini   â”‚  â”‚ OpenAI/Anthropic  â”‚
   â”‚  (Local)    â”‚ â”‚ (Google) â”‚  â”‚ /OpenRouter       â”‚
   â”‚             â”‚ â”‚          â”‚  â”‚                   â”‚
   â”‚ llama3.2    â”‚ â”‚ gemini-  â”‚  â”‚ gpt-4o-mini       â”‚
   â”‚ Zero-cost   â”‚ â”‚ 1.5-flashâ”‚  â”‚ claude-3-haiku    â”‚
   â”‚ HIPAA-safe  â”‚ â”‚ Free tierâ”‚  â”‚ Via headers       â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

| Tier | Provider | Config | Privacy | Cost |
|------|----------|--------|---------|------|
| **A** | Ollama | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | âœ… Data never leaves machine | Free |
| **B** | Gemini | `GOOGLE_API_KEY`, `GEMINI_MODEL` | Cloud API | Free tier available |
| **C** | OpenAI/Anthropic/OpenRouter | `x-ai-provider` + `x-ai-api-key` headers | Cloud API | Pay-per-use |

**Key features:**
- **Fuzzy model matching** â€” `llama3.2` auto-resolves to `llama3.2:3b` if exact name unavailable
- **3-attempt retry** with warmup detection for Ollama cold starts
- **Dual-endpoint fallback** â€” tries `/api/generate` then `/api/chat` on Ollama
- **Model list TTL cache** (30s) to avoid redundant `/api/tags` calls
- **Streaming support** â€” true SSE streaming for Ollama, pseudo-stream for Gemini/Cloud

---

## ðŸ“š RAG Pipeline

**File:** `backend/rag.py` â€” Retrieval-Augmented Generation with semantic memory.

### Architecture

```
User Query â†’ Gemini Embedding API â†’ Cosine Similarity Search â†’ Context Assembly â†’ LLM
                (text-embedding-004)     (scikit-learn)         (Token Budget)
```

### Components

| Component | Implementation |
|-----------|---------------|
| **Embedding Model** | `models/text-embedding-004` (FREE Gemini API) |
| **Vector Store** | `SimpleVectorStore` â€” Pickle-persisted, cosine similarity via scikit-learn |
| **Storage** | `models/vector_store.pkl` |
| **Token Budget** | 3,000 tokens default, max 10 chunks |
| **Dual task types** | `retrieval_document` for indexing, `retrieval_query` for search |

### Data Classes

```python
RetrievedChunk    # record_type, record_id, text, similarity, metadata
Citation          # record_type, record_id, record_name, relevance, excerpt
RAGResult         # answer, citations[], context_chunks_used, total_context_tokens, grounded
```

### Context Builder (`chat_context.py`)

The `build_chat_context()` function assembles structured RAG context with **role-based governance**:

| Scope | Access | Description |
|-------|--------|-------------|
| `patient` | All users | Patient's own profile, records, chat history |
| `global` | Doctors/Admins only | Anonymized hospital-wide historical cases |

Context sections assembled in order:
1. **Patient Profile** â€” demographics, lifestyle (diet, activity, sleep, stress)
2. **Condition-Specific Records** â€” keyword-matched health records (diabetes, heart, liver, kidney, lungs)
3. **General Health Records** â€” fallback if no condition keyword matched
4. **General Stats** â€” trend/summary if user asks about progress
5. **Chat History** â€” last 3 conversation pairs for continuity

Max context: 6,000 characters, truncated with `...(truncated)` marker.

---

## ðŸ•¸ LangGraph Medical Agent

**File:** `backend/agent.py` â€” A stateful multi-node agent graph built with LangGraph.

```
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”‚ Supervisor  â”‚â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚         â”‚ (Router)    â”‚         â”‚
         â”‚         â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜         â”‚
         â”‚                â”‚                â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”
    â”‚Researcherâ”‚    â”‚  Analyst   â”‚   â”‚ Guardrail  â”‚
    â”‚(Tavily)  â”‚    â”‚ (ML Tools) â”‚   â”‚(Off-topic) â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
         â”‚                â”‚                â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜                â”‚
           â”Œâ”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”                 â”‚
           â”‚  Generate   â”‚                 â”‚
           â”‚  (core_ai)  â”‚                 â”‚
           â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜                 â”‚
                  â”‚                        â”‚
                  â–¼                        â–¼
                 END                      END
```

### Agent State (`AgentState`)

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | `List[BaseMessage]` | Conversation history |
| `user_id` | `int` | Current user ID |
| `user_profile` | `str` | Demographics from DB |
| `psych_profile` | `str` | Long-term AI memory |
| `available_reports` | `str` | Medical history context |
| `rag_memories` | `str` | Semantic memory from vector store |
| `conversation_count` | `int` | Message count for engagement style |
| `tavily_results` | `str` | Web search results |
| `next_step` | `str` | Router decision: `research`, `analyze`, `respond`, `off_topic` |

### Routing Logic

- **Research** â†’ keywords: `latest`, `news`, `treatment`, `research`, `study`, `2024`, `2025`
- **Analyze** â†’ keywords: `predict`, `risk`, `chance`, `probability`, `analyze`
- **Off-topic** â†’ guardrail keywords: `president`, `politics`, `movie`, `song`, `joke`, `code`, `finance`
- **Respond** â†’ default path

### `CoreAIWrapper`

LangChain-compatible `.invoke()` wrapper around `core_ai.generate()` â€” bridges the LangGraph agent to the multi-tier inference engine.

---

## ðŸ“ Prompt Registry

**File:** `backend/prompt_registry.py` â€” Version-controlled, auditable prompt management.

### Registered Prompts (6)

| Name | Version | Description |
|------|---------|-------------|
| `chat_system` | 1.0 | Main chatbot system prompt with full context injection (profile, history, RAG, web) |
| `medical_qa` | 1.0 | RAG-grounded Q&A with citation requirements |
| `symptom_analysis` | 1.0 | Structured symptom analysis with red-flag detection |
| `report_summary` | 1.0 | Health record summarization in plain language |
| `risk_assessment` | 1.0 | Disease prediction explanation and recommendations |
| `streaming_system` | 1.0 | Compact system prompt for SSE streaming (token-efficient) |

### API

```python
from backend.prompt_registry import get_prompt, register_prompt

template = get_prompt("medical_qa")                    # Get active version
template = get_prompt("chat_system", version="1.0")    # Get specific version
register_prompt("medical_qa", version="2.0", template="...")  # Register new
```

### Features
- **Versioning** â€” Multiple versions per prompt, activate/deactivate
- **A/B Testing** â€” Switch active versions at runtime
- **Audit Trail** â€” Each version has `created_at` timestamp and metadata
- **No Inline Prompts** â€” All handlers use `get_prompt()`, never raw strings

---
## ðŸ“¡ API Reference

<details>
<summary><strong>Authentication</strong> â€” <code>backend/auth.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/signup` | âŒ | Register new user (password complexity enforced) |
| `POST` | `/token` | âŒ | Login â†’ returns JWT `access_token` |
| `GET` | `/profile` | ðŸ”’ | Get current user profile |
| `PUT` | `/profile` | ðŸ”’ | Update profile fields |
| `GET` | `/users` | ðŸ”’ Admin | List all users |
| `GET` | `/users/{id}/full` | ðŸ”’ Admin | Full user dossier (audit logged, privacy-gated) |

</details>

<details>
<summary><strong>Prediction</strong> â€” <code>backend/prediction.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/predict/diabetes` | âŒ | Diabetes risk screening (9 features) |
| `POST` | `/predict/heart` | âŒ | Heart disease detection (13 features) |
| `POST` | `/predict/liver` | âŒ | Liver disease detection (10 features) |
| `POST` | `/predict/kidney` | âŒ | Chronic kidney disease (24 features) |
| `POST` | `/predict/lungs` | âŒ | Respiratory issue detection (15 features) |
| `POST` | `/predict/explain/diabetes` | âŒ | SHAP explanation for diabetes |
| `POST` | `/predict/explain/heart` | âŒ | SHAP explanation for heart |
| `POST` | `/predict/explain/liver` | âŒ | SHAP explanation for liver |
| `POST` | `/admin/reload_models` | ðŸ”’ Admin | Hot-reload ML models from disk |

</details>

<details>
<summary><strong>Chat & Streaming</strong> â€” <code>backend/chat.py</code>, <code>backend/streaming_chat.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/chat` | ðŸ”’ | AI chat with LangGraph agent + RAG context |
| `GET` | `/chat/history` | ðŸ”’ | Retrieve chat history (last 100) |
| `DELETE` | `/chat/history` | ðŸ”’ | Clear chat history |
| `POST` | `/chat/stream` | ðŸ”’ | SSE streaming chat with heartbeat keepalive |
| `GET` | `/chat/context` | ðŸ”’ | Debug: view assembled RAG context for a query |
| `GET` | `/chat/suggestions` | ðŸ”’ | Dynamic starter questions based on patient data |

</details>

<details>
<summary><strong>Health Records</strong> â€” <code>backend/chat.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/records` | ðŸ”’ | Save health record (auto-indexed to RAG) |
| `GET` | `/records` | ðŸ”’ | Get records (optional `?record_type=` filter) |
| `DELETE` | `/records/{id}` | ðŸ”’ | Delete record (removes from RAG index too) |

</details>

<details>
<summary><strong>Reports & Vision</strong> â€” <code>backend/report.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/analyze/report` | âŒ | Vision AI analysis of uploaded lab report image |
| `GET` | `/download/health-report` | ðŸ”’ | Generate & download PDF health report |
| `POST` | `/generate_report` | âŒ | Generate PDF from provided data |

</details>

<details>
<summary><strong>Explanation</strong> â€” <code>backend/explanation.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/explain/` | âŒ | AI-generated plain-English explanation of any prediction |

</details>

<details>
<summary><strong>Appointments</strong> â€” <code>backend/appointments.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/appointments/` | ðŸ”’ | Book appointment (sends email + Jitsi link) |
| `GET` | `/appointments/` | ðŸ”’ | List appointments (admin/doctor see all) |
| `GET` | `/appointments/doctors` | âŒ | List available doctors |
| `PUT` | `/appointments/{id}/cancel` | ðŸ”’ | Cancel appointment |
| `PUT` | `/appointments/{id}/reschedule` | ðŸ”’ | Reschedule appointment |
| `DELETE` | `/appointments/{id}` | ðŸ”’ | Delete appointment |

</details>

<details>
<summary><strong>Payments</strong> â€” <code>backend/payments.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/payments/create-order` | ðŸ”’ | Create Razorpay order |
| `POST` | `/payments/verify` | ðŸ”’ | Verify payment signature â†’ activate subscription |

</details>

<details>
<summary><strong>Admin</strong> â€” <code>backend/admin.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/admin/stats` | ðŸ”’ Admin | System statistics (users, predictions, messages) |
| `GET` | `/admin/users` | ðŸ”’ Admin | Paginated user list |
| `PUT` | `/admin/users/{id}/role` | ðŸ”’ Admin | Change user role (patient/doctor/admin) |
| `DELETE` | `/admin/users/{id}` | ðŸ”’ Admin | Delete user |

</details>

<details>
<summary><strong>Ollama Model Management</strong> â€” <code>backend/ollama_routes.py</code></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/ai/models` | âŒ | List downloaded Ollama models |
| `POST` | `/ai/models/pull` | âŒ | Pull model with SSE streaming progress |
| `DELETE` | `/ai/models` | âŒ | Delete an Ollama model |
| `GET` | `/ai/models/library` | âŒ | Catalog of recommended models |

</details>

<details>
<summary><strong>Telemetry & System</strong></summary>

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `WS` | `/telemetry/stream` | âŒ | WebSocket stream of live hospital telemetry |
| `GET` | `/` | âŒ | API root |
| `GET` | `/healthz` | âŒ | Health check |

</details>

---

## ðŸ“ Pydantic Schemas

**File:** `backend/schemas.py`

<details>
<summary><strong>Authentication & User Schemas</strong></summary>

| Schema | Fields | Usage |
|--------|--------|-------|
| `Token` | `access_token`, `token_type` | JWT response |
| `UserCreate` | `username`, `password`, `email`, `full_name`, `dob` | Registration |
| `UserResponse` | `id`, `username`, `role`, `full_name`, `email` | Public profile |
| `UserProfileUpdate` | 15 fields including demographics, lifestyle, privacy | Profile update |
| `UserFullResponse` | Extends `UserResponse` + `health_records[]`, `chat_logs[]` | Admin dossier |
| `HealthRecordResponse` | `id`, `record_type`, `prediction`, `timestamp`, `data` | Health record |
| `ChatLogResponse` | `id`, `role`, `content`, `timestamp` | Chat log entry |

</details>

<details>
<summary><strong>Prediction Input Schemas (5)</strong></summary>

| Schema | Features | Dataset |
|--------|----------|---------|
| `DiabetesInput` | 9 fields | BRFSS 2015 |
| `HeartInput` | 13 fields | Cleveland UCI |
| `LiverInput` | 10 fields | ILPD |
| `KidneyInput` | 24 fields | UCI CKD |
| `LungInput` | 15 fields | Lung Survey |

</details>

<details>
<summary><strong>Appointment & Payment Schemas</strong></summary>

| Schema | Fields |
|--------|--------|
| `AppointmentCreate` | `doctor_id`, `specialist`, `date`, `time`, `reason` |
| `AppointmentResponse` | `id`, `user_id`, `doctor_id`, `specialist`, `date_time`, `reason`, `status` |
| `DoctorResponse` | `id`, `full_name`, `specialization`, `consultation_fee`, `profile_picture` |

</details>

---

## ðŸ–¥ Frontend

**Stack:** Next.js 15 (App Router) + TypeScript + Tailwind CSS

### Pages (Protected Routes)

| Route | Page | Description |
|-------|------|-------------|
| `/dashboard` | Patient Dashboard | Health overview, recent records, quick actions |
| `/chat` | AI Chat | Medical chatbot with SSE streaming |
| `/predict` | Predictions | ML diagnostic forms for 5 conditions |
| `/profile` | Profile | User profile management |
| `/admin` | Admin Panel | System stats, user management |
| `/capacity` | Capacity Board | Real-time hospital telemetry (WebSocket) |
| `/infrastructure` | Infrastructure | System monitoring |
| `/telemedicine` | Telemedicine | Jitsi video consultations |
| `/patients` | Patient Management | Doctor/admin patient view |
| `/pricing` | Pricing | Subscription tiers |
| `/about` | About | Platform information |
| `/login` | Login | Authentication |
| `/signup` | Registration | New user signup |

---

## ðŸ—„ Database Layer

**File:** `backend/database.py` â€” SQLAlchemy with auto-detection of SQLite vs PostgreSQL.

### ORM Models (`backend/models.py`)

| Model | Table | Key Fields |
|-------|-------|------------|
| `User` | `users` | id, username, role (patient/doctor/admin), email, full_name, gender, dob, height, weight, blood_type, diet, activity_level, sleep_hours, stress_level, psych_profile, plan_tier, subscription_expiry |
| `HealthRecord` | `health_records` | id, user_id (FK), record_type, data (JSON), prediction, timestamp |
| `ChatLog` | `chat_logs` | id, user_id (FK), role, content, timestamp |
| `AuditLog` | `audit_logs` | id, admin_id (FK), target_user_id, action, timestamp, details |
| `Appointment` | `appointments` | id, user_id (FK), doctor_id (FK), specialist, date_time, reason, status |

### Database Features

- **SQLite WAL mode** enabled for dev performance (`PRAGMA journal_mode=WAL`)
- **Connection pooling** for PostgreSQL (`pool_size=5`, `pool_pre_ping=True`)
- **Auto-migration** â€” `run_migrations()` adds missing columns at startup
- **`postgres://` fix** â€” auto-converts to `postgresql://` for Render/Heroku

---

## ðŸ”’ Security Posture

### Authentication & Authorization
- **JWT tokens** (HS256) with 30-minute expiry via `python-jose`
- **bcrypt** password hashing with 72-byte truncation safety
- **Password complexity** â€” regex: 8+ chars, letters + numbers required
- **Role-Based Access Control** â€” `patient`, `doctor`, `admin` roles
- **OAuth2PasswordBearer** token flow

### Middleware Stack (applied in order)

| # | Middleware | Purpose |
|---|-----------|---------|
| 1 | `RateLimitMiddleware` | Sliding window rate limiter (60 req/min per IP) |
| 2 | `TrustedHostMiddleware` | Allows only `127.0.0.1` and `aio-health-backend.onrender.com` |
| 3 | `CORSMiddleware` | Origin: `http://127.0.0.1:3000`, credentials allowed |
| 4 | `SecurityHeadersMiddleware` | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` |
| 5 | `GZipMiddleware` | Response compression (min 1000 bytes) |
| 6 | `ExceptionMiddleware` | Error ID generation, no PII in error responses |
| 7 | `LoggingMiddleware` | Request timing and status logging |

### Data Privacy
- **PII Redaction** â€” Privacy-opted-out users get `[REDACTED]` in admin views
- **Audit Logging** â€” All admin data access logged to `AuditLog` table
- **Medical Disclaimers** â€” Every AI response includes mandatory disclaimer
- **`allow_data_collection`** flag â€” per-user privacy control
- **RAG Governance** â€” Global hospital search restricted to doctor/admin roles

### Enterprise Security (`backend/enterprise_features.py`)
- Prometheus metrics (request count, duration, prediction metrics)
- HIPAA/GDPR compliance audit logging
- Anomaly detection heuristics
- Redis-backed rate limiting for enterprise deployments

---

## âš™ CI/CD Pipelines

**8 GitHub Actions workflows** in `.github/workflows/`:

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI Tests** | `ci.yml` | Push/PR to `main` | Python 3.10, pytest with coverage, placeholder model generation |
| **CodeQL Security** | `codeql.yml` | Push/PR + weekly cron | SAST scanning for Python & JS/TS (security-extended queries) |
| **Docker Image** | `docker-image.yml` | Push/PR to `main` | Build & push to `ghcr.io`, Buildx layer caching |
| **HuggingFace Sync** | `huggingface.yml` | Push to `main` | Deploy to HF Spaces (scrubs binaries, adds HF frontmatter) |
| **Keep-Alive** | `keep-alive.yml` | Scheduled | Prevents Render free-tier cold starts |
| **Label Sync** | `labels.yml` | Push to `main` | Syncs GitHub labels from `.github/labels.yml` |
| **Release Drafter** | `release-drafter.yml` | Push/PR to `main` | Auto-drafts release notes |
| **Stale Bot** | `stale.yml` | Scheduled | Marks/closes stale issues and PRs |

### Additional GitHub Features
- **Dependabot** â€” Auto-updates for pip, npm, GitHub Actions, Docker
- **CODEOWNERS** â€” Automated review assignment
- **Issue/PR Templates** â€” Standardized contribution flow
- **FUNDING.yml** â€” Sponsor configuration

---

## ðŸ“Š Telemetry WebSocket

**File:** `backend/telemetry.py` â€” Real-time hospital operations dashboard.

**Endpoint:** `WS /telemetry/stream` â€” pushes JSON snapshots every 2 seconds.

<details>
<summary><strong>Telemetry Payload Example</strong></summary>

```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "active_census": 77,
  "total_capacity": 100,
  "system_latency_ms": 14,
  "ai_nodes_active": 14,
  "ed_boarding": 18,
  "ed_avg_wait_min": 135,
  "pending_discharges": 34,
  "confirmed_discharges": 12,
  "surge_prediction_pct": 12,
  "department_loads": [
    {"dept": "Cardiology", "load": 82, "status": "Elevated"},
    {"dept": "Pulmonology", "load": 65, "status": "Stable"},
    {"dept": "Nephrology", "load": 45, "status": "Stable"},
    {"dept": "Endocrinology", "load": 72, "status": "Elevated"}
  ],
  "bed_units": [
    {"unit": "ICU-A", "total": 20, "occupied": 17, "cleaning": 1, "available": 2},
    {"unit": "MED-SURG 4B", "total": 40, "occupied": 34, "cleaning": 2, "available": 4}
  ]
}
```

</details>

---

## ðŸš¢ Deployment

### Option 1: Docker Compose (Recommended)

```bash
docker compose up --build
# Backend: http://127.0.0.1:8000
# Frontend: http://127.0.0.1:3000
```

### Option 2: Enterprise Docker Compose

Full stack with PostgreSQL, Redis, Prometheus, Grafana, Jaeger, and MLflow:

```bash
docker compose -f docker-compose.enterprise.yml up --build
```

| Service | Port | Purpose |
|---------|------|---------|
| Backend | 8000 | FastAPI application |
| PostgreSQL 15 | 5432 | Production database |
| Redis 7 | 6379 | Caching & sessions |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Dashboards |
| Jaeger | 16686 | Distributed tracing |
| MLflow | 5000 | ML experiment tracking |

### Option 3: Render (Free Tier)

Pre-configured via `render.yaml` â€” auto-deploys from `main`, health check at `/healthz`, Singapore region.

### Option 4: Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/autoscaling.yaml
```

K8s manifests provision: Backend (3 replicas) Â· Frontend (2 replicas) Â· PostgreSQL Â· Redis â€” all with PVC storage, liveness/readiness probes, and resource limits.

### Option 5: Terraform (AWS)

```bash
cd terraform && terraform init && terraform plan && terraform apply
```

Provisions: VPC (3 AZs) Â· EKS (2â€“10 nodes) Â· RDS PostgreSQL 15 (encrypted, 7-day backups) Â· ElastiCache Redis Â· S3 (versioned, SSE) Â· EFS Â· ALB + Route53 DNS Â· Secrets Manager Â· CloudWatch.

---

## ðŸ“ Project Structure

<details>
<summary><strong>Click to expand full project tree</strong></summary>

```
AI-Healthcare-System/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ main.py                 # FastAPI entry point, middleware, routers
â”‚   â”œâ”€â”€ core_ai.py              # 3-tier AI engine (Ollamaâ†’Geminiâ†’Cloud)
â”‚   â”œâ”€â”€ prediction.py           # ML model loading & 5 prediction endpoints
â”‚   â”œâ”€â”€ schemas.py              # All Pydantic schemas
â”‚   â”œâ”€â”€ models.py               # SQLAlchemy ORM models
â”‚   â”œâ”€â”€ database.py             # DB engine (SQLite/PostgreSQL auto-detect)
â”‚   â”œâ”€â”€ auth.py                 # JWT auth, signup, login, RBAC
â”‚   â”œâ”€â”€ chat.py                 # LangGraph agent chat + health records
â”‚   â”œâ”€â”€ streaming_chat.py       # SSE streaming chat with heartbeat
â”‚   â”œâ”€â”€ chat_context.py         # RAG context builder with governance
â”‚   â”œâ”€â”€ rag.py                  # Vector store, embeddings, semantic search
â”‚   â”œâ”€â”€ agent.py                # LangGraph medical agent
â”‚   â”œâ”€â”€ prompt_registry.py      # Version-controlled prompts (6 templates)
â”‚   â”œâ”€â”€ explainability.py       # SHAP TreeExplainer
â”‚   â”œâ”€â”€ explanation.py          # AI plain-English explanations
â”‚   â”œâ”€â”€ features.py             # Canonical feature schemas (5 models)
â”‚   â”œâ”€â”€ admin.py                # Admin dashboard routes
â”‚   â”œâ”€â”€ appointments.py         # Booking, Jitsi links, email
â”‚   â”œâ”€â”€ payments.py             # Razorpay integration
â”‚   â”œâ”€â”€ report.py               # Lab report vision + PDF download
â”‚   â”œâ”€â”€ pdf_service.py          # PDF generation (fpdf2)
â”‚   â”œâ”€â”€ vision_service.py       # Gemini Vision for medical OCR
â”‚   â”œâ”€â”€ security.py             # Audit logging + rate limiter
â”‚   â”œâ”€â”€ telemetry.py            # WebSocket hospital telemetry
â”‚   â”œâ”€â”€ enterprise_features.py  # Prometheus, HIPAA, Redis
â”‚   â”œâ”€â”€ ollama_routes.py        # Ollama model management
â”‚   â”œâ”€â”€ email_service.py        # Appointment emails
â”‚   â”œâ”€â”€ train_*.py              # Training scripts (5 models)
â”‚   â””â”€â”€ *.pkl                   # Trained model artifacts
â”‚
â”œâ”€â”€ frontend/                   # Next.js 15 App Router
â”‚   â”œâ”€â”€ src/app/(protected)/    # Auth-gated routes (11 pages)
â”‚   â”œâ”€â”€ src/components/         # Chat, layout, predict components
â”‚   â””â”€â”€ src/lib/                # Auth utilities, API client
â”‚
â”œâ”€â”€ tests/                      # Pytest suite
â”‚   â”œâ”€â”€ unit/                   # Unit tests
â”‚   â”œâ”€â”€ integration/            # Integration tests
â”‚   â””â”€â”€ e2e/                    # Playwright E2E tests
â”‚
â”œâ”€â”€ k8s/                        # Kubernetes manifests
â”œâ”€â”€ terraform/                  # AWS IaC (VPC, EKS, RDS, etc.)
â”œâ”€â”€ monitoring/                 # Prometheus config
â”œâ”€â”€ .github/workflows/          # 8 CI/CD pipelines
â”œâ”€â”€ docker-compose.yml          # Standard 2-service stack
â”œâ”€â”€ docker-compose.enterprise.yml  # 7-service enterprise stack
â”œâ”€â”€ Dockerfile                  # Backend (Python 3.12-slim)
â”œâ”€â”€ render.yaml                 # Render PaaS config
â””â”€â”€ .env.example                # Environment template
```

</details>

---

## ðŸ”§ Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key     # Gemini AI + Embeddings (free tier)
SECRET_KEY=random_secret_string        # JWT signing key

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./healthcare.db # or postgresql://user:pass@host/db

# Local AI (Optional â€” zero-cost, HIPAA-friendly)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120

# Gemini Model Selection
GEMINI_MODEL=gemini-1.5-flash

# Payments (Optional)
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Cloud AI Fallback (Optional â€” via request headers)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

---

## ðŸ¤ Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Run tests (`pytest tests/ -v`)
4. Submit a Pull Request

---

## ðŸ“„ License

MIT License â€” Copyright (c) 2025 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala.

See [LICENSE](LICENSE) for full text.

---

<div align="center">

**If this project helped you, consider giving it a â­**

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=social" alt="Stars" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/network/members"><img src="https://img.shields.io/github/forks/pavanbadempet/AI-Healthcare-System?style=social" alt="Forks" /></a>
</p>

<sub>
<strong>Keywords:</strong> AI healthcare, machine learning diagnosis, medical chatbot, diabetes prediction, heart disease prediction, liver disease prediction, kidney disease prediction, lung cancer prediction, FastAPI healthcare API, LangGraph medical agent, RAG healthcare, SHAP explainability, Ollama local inference, Gemini healthcare, HIPAA-friendly AI, healthcare ML models, clinical decision support, medical AI system, health prediction API, telemedicine platform, hospital capacity management, real-time telemetry, enterprise healthcare, Docker healthcare deployment, Kubernetes healthcare, Terraform AWS healthcare, prompt engineering healthcare, vector store medical records, patient data privacy, audit logging healthcare
</sub>

</div>
