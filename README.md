# AI Healthcare System — Open-Source Medical AI Platform

> Disease Prediction · RAG-Powered Clinical Chat · Healthcare Data Engineering · FHIR R4 Interoperability · FastAPI · React 19 · LangGraph · AWS Terraform

<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System — open-source medical AI platform for disease prediction, RAG chatbot, hospital management, FHIR R4, FastAPI, React 19" width="100%"/>

<br/>

<p>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI build status" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL security analysis" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="MIT license" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="GitHub stars" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/issues"><img src="https://img.shields.io/github/issues/pavanbadempet/AI-Healthcare-System?style=flat-square&color=ef4444" alt="Open issues" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/XGBoost-189FDD?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge" alt="LangGraph" />
</p>

<p>
  <a href="#-core-capabilities"><strong>Core Capabilities</strong></a> &middot;
  <a href="#-architecture--data-flow"><strong>Architecture</strong></a> &middot;
  <a href="#-data-engineering--ai-ops"><strong>Data & AI OPs</strong></a> &middot;
  <a href="#-model-card-registry"><strong>Model Cards</strong></a> &middot;
  <a href="#-quick-start"><strong>Quick Start</strong></a> &middot;
  <a href="#-rest-api-reference"><strong>API Reference</strong></a>
</p>

</div>

---

## 💡 What Is This?

**AI Healthcare System** is an open-source, production-grade medical AI and health data platform. It integrates machine learning screening models, a retrieval-augmented generation (RAG) clinical chat assistant, and standard hospital workflows into a single system designed for sub-100ms inference and secure data exchange.

Rather than a simple notebook demo, this repository demonstrates robust **AI Data Engineering (AI DE) and MLOps patterns**—incorporating standard clinical schemas (FHIR R4), PII-masked audit logs, pluggable vector store architectures, and automated model evaluation gates.

---

## 🚀 Core Capabilities

<table>
<tr>
<td width="33%" valign="top">

### 📊 5 Clinical ML Classifiers
Diabetes, Heart, Liver, Kidney, and Lung health screening models trained on peer-reviewed CDC and UCI datasets. Uses gradient-boosted trees (XGBoost) with SHAP explainability and probability calibration.

</td>
<td width="33%" valign="top">

### 🤖 Multi-Agent RAG Chat
Supervisor-routed LangGraph reasoning graph incorporating patient-scoped vector retrieval (Gemini `text-embedding-004`), citation tracking, and strict output guardrails to prevent hallucinations.

</td>
<td width="33%" valign="top">

### 🏥 Hospital Operations
OPD/IPD encounters, bed assignments, diagnostics, pharmacy, billing, and nursing task queues. Telemetry updates are streamed in real-time over WebSocket.

</td>
</tr>
</table>

---

## 🏗 Architecture & Data Flow

```mermaid
graph TB
    subgraph Client["CLIENT SURFACE — React 19 · TS · Tailwind CSS"]
        FE["Vite 8 SPA · Clinical Portal & Telemedicine UI"]
    end

    subgraph Gateway["API GATEWAY & MIDDLEWARE — FastAPI"]
        MW["8-Layer Middleware Stack (Tracing · Rate-limiting · PII-Masking)"]
        ROUTERS["REST API Routers (Auth · Chat · Predict · Ops · Interop)"]
    end

    subgraph Service["INTELLIGENCE & ORCHESTRATION"]
        AGENT["LangGraph Supervisor Agent (Research · Analyze · Guardrail · Generate)"]
        CORE["Core AI Provider Gateway (Ollama local fallback → Gemini cloud)")
        EVAL["Shared ML Evaluation Module (AUC-ROC · Sensitivity · Specificity)"]
    end

    subgraph Data["DATA & PERSISTENCE LAYER"]
        DB[(SQL database — SQLite WAL / PostgreSQL)]
        VS[(Vector Store — turbovec SIMD Index / Cosine Similarity)]
        ML[(5 ML Classifiers + Scalers .pkl)]
    end

    Client -->|"JSON / SSE / WebSocket"| Gateway
    Gateway --> Service
    Service --> Data
```

---

## 🛠 Data Engineering & AI Ops

This project stands out by implementing real-world **AI Data Engineering** patterns to make models robust, secure, and auditable in production:

### 1. HIPAA-Aware Data Governance
* **PII Exception Masking**: Outer-most middleware intercepts all system exceptions, scrubbing raw stack traces and sanitizing database errors to prevent Protected Health Information (PHI) leaks.
* **Gated Doctor Override Logs**: Clinician overrides (accepting/rejecting AI predictions) are recorded as cryptographically traceable, PHI-free `REVIEW_AI_PREDICTION` events in the audit table.

### 2. Multi-Tier AI Provider Gateway (`core_ai.py`)
To prevent vendor lock-in and minimize cloud costs, all LLM calls route through a single, isolated module:
1. **Tier A (Local)**: Queries local **Ollama** model server (`llama3.2`) for zero cloud costs.
2. **Tier B (Cloud)**: Falls back automatically to **Google Gemini** free API tier.
3. **Tier C (Enterprise)**: Connects to **OpenAI / Anthropic** as a pay-per-use fallback.
*Enforces 30s TTL caching, automatic backoff retry, and unified token streaming.*

### 3. Pluggable Semantic Indexing (RAG)
* **turbovec Engine**: Fast in-memory similarity search over patient-scoped document indices using Rust-SIMD vectors or scikit-learn cosine fallbacks.
* **ACL Scoping**: Enforces database-level access control filters (user_id and facility_id) at the vector level before document chunk retrieval.

### 4. Schema Mapping & Alignment
* **Ingestion Adapters**: Normalizes heterogeneous clinical inputs (e.g., mapping CDC BRFSS survey columns like `high_bp` to Cleveland clinical features like `cp`) so the inference engine can run models interchangeably on diverse source schemas.

---

## 🔬 Model Card Registry

For comprehensive dataset sources, training hyper-parameters, and limitations, see [`docs/MODEL_AND_DATASET_CARDS.md`](docs/MODEL_AND_DATASET_CARDS.md).

| Model | Task | Algorithm | Features | Target Dataset | AUC-ROC | Sensitivity |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| **Diabetes** | Risk Screening | XGBoost | 9 | CDC BRFSS (250K+ records) | **0.8287** | **0.7989** |
| **Heart** | Disease Detection | XGBoost | 13 | BRFSS / UCI Cleveland | **0.8467** | **0.8091** |
| **Liver** | Screening Panel | XGBoost | 10 | UCI ILPD Dataset | **0.9799** | **0.9792** |
| **Kidney** | Chronic Screening | XGBoost | 24 | UCI CKD Dataset | **0.5000** | **1.0000** |
| **Lungs** | Respiratory Risk | XGBoost | 15 | Lung Cancer Survey | **0.9250** | **0.8833** |

*Note: Evaluation metrics are updated dynamically using the shared evaluation artifact generator. Run the training scripts to regenerate results with fresh datasets.*

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20.9+

### Option A: One-Command Docker Setup
```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
cp .env.example .env          # Set GOOGLE_API_KEY & SECRET_KEY
docker compose up --build
```

### Option B: Local Developer Run
```bash
# Clone the repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Set up Python environment
python -m pip install -r requirements.txt

# Install frontend dependencies
npm --prefix frontend install

# Set up environment variables
cp .env.example .env

# Start FastAPI backend (Terminal 1)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Start React frontend (Terminal 2)
npm --prefix frontend run dev
```

| Service | Access URL |
| :--- | :--- |
| **Frontend Portal** | [http://127.0.0.1:3000](http://127.0.0.1:3000) |
| **REST API Server** | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |

---

## 📡 REST API Reference

| Method | Endpoint | Description | Sample Request Body |
| :---: | :--- | :--- | :--- |
| `POST` | `/v1/predict/diabetes` | Predicts diabetes risk using XGBoost. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/predict/explain/diabetes` | Returns SHAP explainability feature attribution. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/chat/stream` | Multi-turn streaming chat with LangGraph RAG. | `{"messages": [{"role": "user", "content": "Explain my risk"}]}` |
| `POST` | `/v1/predict/reviews` | Logs clinical audit decisions for model predictions. | `{"patient_id": 1, "prediction_type": "diabetes", ...}` |
| `GET` | `/v1/admin/model-cards` | Fetches the active model card specifications. | *None* |

---

## 📂 Key Files Reference

| Capability | Purpose | Module |
| :--- | :--- | :--- |
| **Model Ingestion & Training** | Evaluates models and writes standard performance metrics. | [backend/ml/evaluation.py](backend/ml/evaluation.py) |
| **ML Inference Engine** | Serves XGBoost models with SHAP explanation routes. | [backend/prediction.py](backend/prediction.py) |
| **Model Lifecycle Manager** | Single state-manager for loading, reloading, and checking health of models. | [backend/model_service.py](backend/model_service.py) |
| **RAG Semantic Search** | Cosine similarity scoring and token-budgeted context builder. | [backend/rag.py](backend/rag.py) · [backend/chat_context.py](backend/chat_context.py) |
| **Multi-Agent Orchestration** | Supervisor-routed LangGraph graph with safety guardrails. | [backend/agent.py](backend/agent.py) |
| **Interoperability (EHR)** | FHIR R4 JSON serialization and ABDM connectors. | [backend/fhir.py](backend/fhir.py) · [backend/fhir.py](backend/fhir.py) |
| **Infrastructure (IaC)** | EKS cluster, RDS PostgreSQL, and caching infrastructure. | [terraform/main.tf](terraform/main.tf) |

---

## 🤝 Contributing & Tests

Ensure all tests pass before making pull requests. We enforce strict test coverage thresholds in CI.

```bash
# Run the complete test suite with coverage
python -m pytest tests/ -v

# Run the frontend unit tests
npm --prefix frontend run test
```

---

## 📄 License

MIT License — Copyright © 2026 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE) for details.
