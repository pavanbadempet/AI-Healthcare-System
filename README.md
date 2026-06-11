# 🏥 AI Healthcare System — Privacy-First Clinical AI & EHR Interoperability Platform

> A production-ready, HIPAA-oriented clinical intelligence platform combining machine learning diagnostics, a multi-agent RAG chatbot, and full hospital operations.

<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System Banner" width="100%"/>

<br/>

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI build status" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL security analysis" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/pavanbadempet/AI-Healthcare-System?color=22c55e&style=flat-square" alt="MIT license" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="GitHub stars" /></a>
</p>

<h3>
  <a href="#-quick-start"><strong>Quick Start</strong></a> &middot;
  <a href="#-core-pillars"><strong>Features</strong></a> &middot;
  <a href="#-core-engineering-guarantees"><strong>Guarantees</strong></a> &middot;
  <a href="#-core-technical-architecture"><strong>Architecture</strong></a> &middot;
  <a href="#-model-card-registry"><strong>Model Cards</strong></a> &middot;
  <a href="#-api-contract-reference"><strong>API Contract</strong></a> &middot;
  <a href="#-aws-enterprise-deployment"><strong>AWS Deploy</strong></a>
</h3>

</div>

---

## ✨ Why Choose AI Healthcare System?

Existing healthcare software is either outdated, closed-source, or extremely complex to integrate. **AI Healthcare System** is a modern, open-source alternative built on a unified, high-performance stack (FastAPI + React 19).

It is designed to run **fully offline and private** (via Ollama) on standard consumer hardware, ensuring patient data remains secure inside your clinic's network, while remaining fully compatible with international interoperability standards like **FHIR R4**.

The codebase is engineered to demonstrate **production-level engineering patterns** required in regulated domains: strict schema compliance, ABDM consent management, pluggable data layers, and automated verification gates.

---

## ⚡ Core Pillars

<table>
<tr>
<td width="33%" valign="top">

### 🩺 5 ML Diagnostics
Instant screening for **Diabetes, Heart, Liver, Kidney, and Lung health** using calibrated XGBoost models. Every prediction includes gain-based SHAP explainability so clinicians know *why* a risk was flagged.

</td>
<td width="33%" valign="top">

### 💬 Multi-Agent RAG Chat
A supervisor-routed LangGraph reasoning graph that retrieves patient records with citation tracking. Safety guardrails gate and review all answers to prevent medical hallucinations.

</td>
<td width="33%" valign="top">

### 🏥 Hospital Operations
A complete system to run your facility: OPD/IPD encounters, ward bed allocations, pharmacy inventory, nursing task worklists, billing, and real-time WebSocket capacity telemetry.

</td>
</tr>
</table>

---

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

---

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

---

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

---

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

---

## 📡 API Contract Reference

| Method | Endpoint | Description | Sample Request Payload |
| :---: | :--- | :--- | :--- |
| `POST` | `/v1/predict/diabetes` | Evaluates diabetes risk. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/predict/explain/diabetes` | Generates SHAP explanation attributes. | `{"hypertension": 1, "high_chol": 1, "bmi": 28.5, ...}` |
| `POST` | `/v1/chat/stream` | Multi-turn streaming chat with LangGraph RAG. | `{"messages": [{"role": "user", "content": "Explain my risk"}]}` |
| `POST` | `/v1/predict/reviews` | Logs doctor audit decisions for model predictions. | `{"patient_id": 1, "prediction_type": "diabetes", ...}` |

---

## 📂 Key Modules Directory

| Capability | Purpose | Module |
| :--- | :--- | :--- |
| **Model Ingestion & Training** | Standardized evaluation metrics artifact generator. | [backend/ml/evaluation.py](backend/ml/evaluation.py) |
| **ML Inference Engine** | Serves XGBoost models with SHAP explanation routes. | [backend/prediction.py](backend/prediction.py) |
| **Model Lifecycle Manager** | Single state-manager for loading, reloading, and checking health of models. | [backend/model_service.py](backend/model_service.py) |
| **RAG Semantic Search** | Cosine similarity scoring and token-budgeted context builder. | [backend/rag.py](backend/rag.py) · [backend/chat_context.py](backend/chat_context.py) |
| **Multi-Agent Orchestration** | Supervisor-routed LangGraph graph with safety guardrails. | [backend/agent.py](backend/agent.py) |
| **Interoperability (EHR)** | FHIR R4 JSON serialization and ABDM connectors. | [backend/fhir.py](backend/fhir.py) |

---

## ☁ AWS Enterprise Deployment

APEX includes complete Terraform configurations to spin up a production-ready, scalable infrastructure on AWS:
* **Amazon EKS**: Kubernetes cluster for horizontal backend scaling.
* **Amazon RDS PostgreSQL**: Managed, pooled relational database.
* **Amazon ElastiCache Redis**: High-throughput session caching.
* **Terraform IaC**: Deploy with `cd terraform && terraform init && terraform apply`.

---

## 🧪 Verification & Coverage Suite

All tests must pass in CI before merging. We enforce a strict **55% code coverage gate** for pull request approvals.

```bash
# Run the complete test suite with coverage
python -m pytest tests/ -v

# Run the frontend unit tests
npm --prefix frontend run test
```

---

## 📄 License

MIT License — Copyright © 2026 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE) for details.

---

<div align="center">

### **If you find this project useful, give it a ⭐ star!**

</div>
