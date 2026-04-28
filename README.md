<!-- 
  SEO: AI Healthcare System, Medical AI, Healthcare ML, Disease Prediction, 
  Health Risk Assessment, Clinical Decision Support, Medical AI Platform,
  FastAPI Healthcare, Next.js Medical Dashboard, RAG Healthcare, 
  Gemini Medical AI, XGBoost Disease Classification, HIPAA Compliant AI,
  Open Source Healthcare, Patient Portal AI, Diagnostic AI System
-->

<p align="center">
  <img src="https://img.shields.io/badge/🏥-AI_Healthcare_System-00D4AA?style=for-the-badge&labelColor=0a0a0a" alt="AI Healthcare System" height="40"/>
</p>

<h1 align="center">AI Healthcare System</h1>

<p align="center">
  <strong>Production-Grade Clinical Decision Support Platform</strong><br/>
  <em>Bridging Lab Results to Patient Understanding with AI · ML-Powered Diagnostics · RAG-Enhanced Medical Chat</em>
</p>

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml">
    <img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI Status"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml">
    <img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=blue" alt="License"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/pulls">
    <img src="https://img.shields.io/github/issues-pr/pavanbadempet/AI-Healthcare-System?color=purple" alt="PRs"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues">
    <img src="https://img.shields.io/github/issues/pavanbadempet/AI-Healthcare-System?color=orange" alt="Issues"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers">
    <img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=social" alt="Stars"/>
  </a>
</p>

<p align="center">
  <a href="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python"/>
  </a>
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js_15-000000?logo=nextdotjs&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Gemini_AI-4285F4?logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/XGBoost-FF6600?logo=xgboost&logoColor=white" alt="XGBoost"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white" alt="Terraform"/>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-ml-models">ML Models</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 What Is This?

**AI Healthcare System** is a full-stack clinical decision support platform that transforms raw lab reports into actionable patient insights. It combines **ML-powered disease screening**, **RAG-enhanced medical chat**, and **automated PDF report generation** into a single, production-ready system.

### The Problem
> Patients receive lab reports full of numbers they don't understand. Doctors spend time explaining basics instead of treating.

### The Solution
A platform where patients get **instant risk assessments** with **plain-English explanations**, and clinicians get a **unified dashboard** to monitor patient health — all powered by AI with built-in medical safety guardrails.

<table>
<tr>
<td width="50%">

**🧑‍⚕️ For Clinicians**
- Patient management dashboard
- Health trend visualization over time
- Automated PDF medical reports
- Role-based access control (RBAC)
- Telemedicine scheduling

</td>
<td width="50%">

**🧑‍💻 For Patients**
- Upload lab PDF → instant AI summary
- 5-disease ML risk screening
- Chat with AI that knows your history
- Download professional PDF reports
- Secure, isolated health records

</td>
</tr>
</table>

---

## ✨ Features

### 🔬 ML-Powered Disease Screening
Real-time risk prediction using validated clinical ML models:

| Disease | Algorithm | Key Features | Clinical Markers |
|---------|-----------|--------------|------------------|
| **Diabetes** | XGBoost | Glucose, BMI, Insulin, Age | HbA1c correlation |
| **Heart Disease** | Random Forest | Cholesterol, BP, ECG, Chest Pain | Framingham-aligned |
| **Liver Disease** | XGBoost | Bilirubin, Albumin, ALT/AST | Enzyme ratio analysis |
| **Kidney Disease** | Random Forest | Creatinine, Blood Urea, Albumin | GFR estimation support |
| **Lung Cancer** | XGBoost | Smoking history, Chronic Disease, Allergy | Multi-factor risk scoring |

### 🤖 AI-Powered Medical Assistant
- **RAG Architecture** — Per-user vector stores (FAISS) prevent cross-patient data leakage
- **Vision AI** — Gemini Pro Vision reads raw PDF lab reports automatically
- **Streaming Chat** — Real-time AI responses with medical context awareness
- **Prompt Registry** — All system prompts managed centrally for auditability
- **Medical Safety** — Built-in disclaimers and guardrails on all AI-generated advice

### 🔒 Enterprise Security
- JWT authentication with configurable token expiry
- Role-based access control (Patient / Doctor / Admin)
- CORS and trusted host middleware
- PII never logged or exposed in error messages
- CodeQL + Dependabot automated security scanning

### 📊 Clinical Intelligence
- **SHAP Explainability** — Model predictions are interpretable and auditable
- **PDF Report Generation** — Professional medical reports with risk indicators
- **Health Trend Tracking** — Longitudinal patient metric visualization
- **Automated Screening Pipelines** — End-to-end from lab upload to risk assessment

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Next.js 15  │  │  Streamlit   │  │   REST API Consumers    │  │
│  │  (Primary UI) │  │  (Legacy UI) │  │   (Mobile / 3rd Party)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                          │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────┐ ┌───────────────┐  │
│  │  Auth   │ │ Predict  │ │  Chat  │ │  RAG  │ │  PDF Reports  │  │
│  │ (JWT)   │ │ (5 Models)│ │(Stream)│ │(FAISS)│ │  (fpdf2)      │  │
│  └─────────┘ └──────────┘ └────────┘ └───────┘ └───────────────┘  │
│  ┌─────────┐ ┌──────────┐ ┌────────────────────────────────────┐  │
│  │ Vision  │ │  SHAP    │ │         Prompt Registry            │  │
│  │ Service │ │ Explain  │ │    (Centralized System Prompts)    │  │
│  └─────────┘ └──────────┘ └────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐  ┌─────────────┐  ┌─────────────┐
   │  SQLite    │  │    FAISS    │  │  Gemini AI  │
   │ (Users,    │  │  (Per-User  │  │  (Chat,     │
   │  Records)  │  │  Vectors)   │  │   Vision)   │
   └────────────┘  └─────────────┘  └─────────────┘
```

### Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **AI Safety** | All inference through `core_ai.py` — never direct API calls |
| **Prompt Governance** | System prompts in `prompt_registry.py` — never inlined |
| **Data Isolation** | Per-user FAISS vector stores prevent cross-patient leakage |
| **Medical Disclaimers** | Enforced on every AI-generated response |
| **Model Integrity** | Training scripts prevent data leakage; honest accuracy metrics |
| **Zero-PII Logging** | Patient data never appears in logs or error messages |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15, React 19, Framer Motion | Modern clinical dashboard UI |
| **State** | Zustand, SWR | Client-side state management |
| **Backend** | FastAPI, Pydantic v2 | REST API with auto-validation |
| **ML/AI** | XGBoost, Scikit-Learn, SHAP | Disease classification + explainability |
| **GenAI** | Gemini Pro, LangChain | Medical chat assistant + Vision |
| **Vector DB** | FAISS | Per-user semantic search |
| **Database** | SQLite (dev) / PostgreSQL (prod) | User data, chat history, records |
| **PDF** | fpdf2 | Professional medical report generation |
| **DevOps** | Docker, Docker Compose | Multi-container orchestration |
| **CI/CD** | GitHub Actions (8 workflows) | Testing, security, deployment |
| **Security** | CodeQL, Dependabot | Automated vulnerability scanning |
| **IaC** | Terraform, Kubernetes (k8s) | Cloud infrastructure definitions |
| **Hosting** | Render, HF Spaces, Streamlit Cloud | Production deployment |

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Configure
cp .env.example .env
# Edit .env → add your GOOGLE_API_KEY

# Launch
docker-compose up --build
```

| Service | URL |
|---------|-----|
| **Frontend (Next.js)** | `http://127.0.0.1:3000` |
| **Backend API** | `http://127.0.0.1:8000` |
| **API Docs (Swagger)** | `http://127.0.0.1:8000/docs` |

### Option 2: Local Development

```bash
# Prerequisites: Python 3.10+, Node.js 18+

# Backend (Terminal 1)
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend && npm install && npm run dev -- -p 3000
```

### Option 3: Quick Scripts (Windows)

```powershell
.\scripts\runners\run_app.bat          # Run everything
.\scripts\runners\run_e2e_tests.ps1    # Run E2E tests
.\scripts\runners\run_test_suite.ps1   # Run full test suite
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Gemini API key for AI features |
| `SECRET_KEY` | ✅ | JWT signing key |
| `DATABASE_URL` | ❌ | Database URL (defaults to SQLite) |
| `TESTING` | ❌ | Set to `true` for test mode |

---

## 🧠 ML Models

### Training Pipeline

All models follow a validated training pipeline with **data leakage prevention**:

```bash
# Train individual models
python backend/train_diabetes.py
python backend/train_heart.py
python backend/train_liver.py
python backend/train_kidney.py
python backend/train_lungs.py

# Generate placeholder models for CI
python scripts/generate_placeholder_models.py
```

### Model Architecture

```
Data → Feature Engineering → Train/Test Split → Model Training → SHAP Validation → .pkl Export
                                    │
                                    ▼
                        ┌──── Leakage Guard ────┐
                        │  No test data in train │
                        │  No target in features │
                        └────────────────────────┘
```

### Explainability
Every prediction includes **SHAP-based feature importance** so clinicians understand *why* the model made its prediction — not just *what* it predicted.

---

## 📡 API Reference

The backend exposes a RESTful API with full Swagger documentation at `/docs`.

### Key Endpoints

```
POST   /auth/register          # User registration
POST   /auth/login             # JWT authentication
GET    /auth/me                # Current user profile

POST   /predict/{disease}      # ML disease prediction
POST   /predict/explain        # SHAP explainability

POST   /chat                   # AI medical chat
POST   /chat/stream            # Streaming chat (SSE)
POST   /vision/analyze         # PDF lab report analysis

GET    /report/generate        # PDF medical report
GET    /patients               # Patient listing (doctor)
GET    /healthz                # Health check
```

### Example: Disease Prediction

```bash
curl -X POST http://127.0.0.1:8000/predict/diabetes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "glucose": 120,
    "bmi": 28.5,
    "insulin": 80,
    "age": 45,
    "blood_pressure": 130
  }'
```

```json
{
  "prediction": "High Risk",
  "confidence": 0.87,
  "risk_factors": ["glucose", "bmi"],
  "disclaimer": "This is not a medical diagnosis. Please consult a healthcare professional."
}
```

---

## 🧪 Testing

```bash
# Full test suite with coverage
pytest tests/ --cov=backend --cov-report=term-missing

# By category
pytest tests/unit/              # Unit tests
pytest tests/integration/       # API integration tests
pytest tests/e2e/               # End-to-end (requires running app)

# Specific test files
pytest tests/unit/test_prediction_shap.py -v    # ML model tests
pytest tests/unit/test_pdf_service.py -v        # PDF generation tests
pytest tests/unit/test_rag.py -v                # RAG pipeline tests
```

### CI/CD Pipeline (8 Workflows)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | Push / PR | Tests + coverage |
| **CodeQL** | Push / PR / Weekly | Security vulnerability scanning |
| **Docker** | Push / PR | Build + push to GHCR |
| **HF Sync** | Push | Deploy to Hugging Face Space |
| **Keep-Alive** | Cron (14min) | Prevent free-tier spin-down |
| **Stale Bot** | Daily | Auto-close inactive issues |
| **Release Drafter** | PR merge | Auto-generate release notes |
| **Label Sync** | Manual | Sync label taxonomy |

---

## 📁 Project Structure

```
AI-Healthcare-System/
├── 🔧 backend/                  # FastAPI Backend
│   ├── main.py                  #   App entrypoint + route mounting
│   ├── core_ai.py               #   Central AI inference gateway
│   ├── prediction.py            #   ML model loading + prediction
│   ├── agent.py                 #   AI chat agent orchestration
│   ├── rag.py                   #   RAG pipeline (per-user FAISS)
│   ├── vision_service.py        #   PDF lab report vision analysis
│   ├── prompt_registry.py       #   Centralized system prompts
│   ├── explainability.py        #   SHAP model explanations
│   ├── pdf_service.py           #   Medical PDF report generation
│   ├── streaming_chat.py        #   SSE streaming chat
│   ├── security.py              #   Auth + RBAC middleware
│   ├── schemas.py               #   Pydantic request/response models
│   ├── models.py                #   SQLAlchemy ORM models
│   ├── database.py              #   Database session management
│   └── train_*.py               #   ML model training scripts
│
├── 🎨 frontend/                 # Next.js 15 Frontend
│   └── src/app/
│       ├── (protected)/         #   Authenticated routes
│       │   ├── dashboard/       #     Main clinical dashboard
│       │   ├── predict/         #     Disease screening UI
│       │   ├── chat/            #     AI medical assistant
│       │   ├── patients/        #     Patient management
│       │   ├── telemedicine/    #     Telemedicine scheduling
│       │   └── profile/         #     User settings
│       ├── login/               #   Login page
│       └── signup/              #   Registration page
│
├── 🧪 tests/                   # Test Suite
│   ├── unit/                    #   20+ unit test files
│   ├── integration/             #   API integration tests
│   └── e2e/                     #   Playwright E2E tests
│
├── 📊 mlops/                   # MLOps Pipeline
│   ├── data_ingestion.py        #   Data loading
│   ├── data_processing.py       #   Feature engineering
│   └── model_training.py        #   Training orchestration
│
├── ☁️ Infrastructure
│   ├── terraform/               #   Terraform IaC configs
│   ├── k8s/                     #   Kubernetes manifests
│   ├── airflow/                 #   Airflow DAG definitions
│   ├── monitoring/              #   Observability configs
│   ├── docker-compose.yml       #   Multi-container setup
│   ├── Dockerfile               #   Production container
│   └── render.yaml              #   Render deployment config
│
├── 📚 docs/                    # Documentation
│   ├── AI_AGENT_ARCHITECTURE.md #   AI module deep-dive
│   ├── TECHNICAL_WHITEPAPER.md  #   System design whitepaper
│   ├── MASTER_PROJECT_REPORT.md #   Full project report
│   └── ZERO_CAPITAL_GUIDE.md    #   Free-tier deployment guide
│
└── ⚙️ .github/                 # GitHub Configuration
    ├── workflows/               #   8 CI/CD workflows
    ├── ISSUE_TEMPLATE/          #   Bug, feature, docs templates
    ├── PULL_REQUEST_TEMPLATE.md #   PR checklist (medical safety)
    ├── dependabot.yml           #   Dependency auto-updates
    ├── CODEOWNERS               #   Auto-assign reviewers
    └── FUNDING.yml              #   Sponsor configuration
```

---

## 🌐 Deployment

### Production (Render + HF Spaces)

| Component | Platform | URL |
|-----------|----------|-----|
| Backend API | Render | Auto-deployed via `render.yaml` |
| Frontend | Vercel / Streamlit Cloud | Connect repo + set `BACKEND_URL` |
| HF Space | Hugging Face | Auto-synced via GitHub Actions |

### Self-Hosted (Docker)

```bash
docker-compose up -d --build
```

### Cloud (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Required Secrets for CI/CD

| Secret | Used By |
|--------|---------|
| `GOOGLE_API_KEY` | Backend AI features |
| `SECRET_KEY` | JWT auth |
| `HF_TOKEN` | Hugging Face sync |
| `HF_USERNAME` | Hugging Face sync |
| `HF_SPACE_NAME` | Hugging Face sync |

---

## 🔒 Security

This project takes security seriously, especially given the sensitivity of medical data.

- 🛡️ **CodeQL** — Automated static analysis on every push (Python + JavaScript)
- 📦 **Dependabot** — Auto-PRs for vulnerable dependencies (pip, npm, Actions, Docker)
- 🔐 **JWT Auth** — Configurable token expiry with role-based access
- 🚫 **Zero-PII Logging** — Patient data never exposed in logs or errors
- ⚕️ **Medical Disclaimers** — Enforced on all AI-generated health advice
- 📋 **SECURITY.md** — [Vulnerability reporting policy](SECURITY.md)

Found a vulnerability? Please report it privately via our [Security Policy](SECURITY.md).

---

## 📈 Project Status

| Metric | Status |
|--------|--------|
| **CI/CD** | [![CI](https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg)](https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml) |
| **Security** | [![CodeQL](https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg)](https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml) |
| **Test Coverage** | 134+ passing tests |
| **Commits** | 330+ commits |
| **License** | MIT |

---

## 🤝 Contributing

Contributions are welcome! We have structured templates to make it easy:

1. **🐛 [Report a Bug](https://github.com/pavanbadempet/AI-Healthcare-System/issues/new?template=bug_report.yml)** — Structured bug report form
2. **✨ [Request a Feature](https://github.com/pavanbadempet/AI-Healthcare-System/issues/new?template=feature_request.yml)** — Feature proposal with priority
3. **📚 [Improve Docs](https://github.com/pavanbadempet/AI-Healthcare-System/issues/new?template=docs.yml)** — Documentation gaps

### Development Workflow

```bash
# Fork → Clone → Branch → Code → Test → PR
git checkout -b feature/amazing-feature
pytest tests/ --cov=backend            # Ensure tests pass
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
# Open PR → Auto-assigned reviewer → CI runs → Merge
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [AI Agent Architecture](docs/AI_AGENT_ARCHITECTURE.md) | Deep-dive into AI module design |
| [Technical Whitepaper](docs/TECHNICAL_WHITEPAPER.md) | Full system design document |
| [Model Integrity Report](docs/MODEL_INTEGRITY_REPORT.md) | ML model validation & metrics |
| [Master Project Report](docs/MASTER_PROJECT_REPORT.md) | Comprehensive project analysis |
| [Zero Capital Guide](docs/ZERO_CAPITAL_GUIDE.md) | Deploy entirely on free tiers |
| [Security Policy](SECURITY.md) | Vulnerability reporting process |
| [Contributing Guide](CONTRIBUTING.md) | How to contribute |

---

## ⭐ Star History

If this project helped you, consider giving it a ⭐ — it helps others discover it!

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers">
    <img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=for-the-badge&color=yellow&logo=github" alt="Star this repo"/>
  </a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/fork">
    <img src="https://img.shields.io/github/forks/pavanbadempet/AI-Healthcare-System?style=for-the-badge&color=blue&logo=github" alt="Fork this repo"/>
  </a>
</p>

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/pavanbadempet">Pavan Badempet</a></strong>
  <br/>
  <sub>© 2025 Pavan Badempet, Shiva Prasad Anagondi, Prashanth Cheerala</sub>
</p>

---

<p align="center">
  <sub>
    <strong>Keywords:</strong> AI Healthcare · Medical AI Platform · Disease Prediction · Clinical Decision Support · 
    Health Risk Assessment · ML Diagnostics · RAG Medical Chat · FastAPI Healthcare API · Next.js Medical Dashboard · 
    XGBoost Disease Classification · SHAP Explainability · Open Source Healthcare · Patient Portal · 
    Gemini Medical AI · HIPAA-Aware · Telemedicine · Medical Report Generator
  </sub>
</p>
