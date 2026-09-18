<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System - Open-Source Electronic Health Record (EHR) and Clinical Intelligence Platform" width="100%"/>

# AI Healthcare System
### *Open-Source Electronic Health Record (EHR) & Clinical Decision Support Platform*

<br/>

**A privacy-first clinical intelligence platform that connects standard hospital workflows (patient records, vitals, appointments, billing, FHIR R4) with explainable machine learning models, longitudinal health simulation, and local offline AI.**

<br/>

<p align="center">
  <a href="https://huggingface.co/spaces/pavanbadempet/aio-health-backend"><img src="https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Space-22c55e?style=for-the-badge&logo=huggingface&logoColor=white" height="34" alt="Live Demo"/></a>
  &nbsp;
  <a href="https://huggingface.co/spaces/pavanbadempet/aio-health-backend/docs"><img src="https://img.shields.io/badge/API%20Docs-Swagger%20UI-009688?style=for-the-badge&logo=fastapi&logoColor=white" height="34" alt="API Documentation"/></a>
  &nbsp;
  <a href="https://huggingface.co/pavanbadempet/ai-healthcare-models"><img src="https://img.shields.io/badge/Model%20Hub-Trained%20Weights-yellow?style=for-the-badge&logo=huggingface&logoColor=black" height="34" alt="Hugging Face Model Hub" /></a>
  &nbsp;
  <a href="docs/optimal_dual_layer_architecture.md"><img src="https://img.shields.io/badge/Architecture-Design%20Spec-blue?style=for-the-badge&logo=blueprint&logoColor=white" height="34" alt="Architecture Document"/></a>
</p>

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI Build Status" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL Security" /></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-Welcome-10b981?style=flat-square" alt="PRs Welcome" /></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/Security-Policy-red?style=flat-square&logo=shield" alt="Security Policy" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=flat-square" alt="AGPL v3 License" /></a>
  <a href="https://github.com/sponsors/pavanbadempet"><img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa.svg?logo=github&style=flat-square" alt="Sponsor" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="Stars" /></a>
  <a href="CITATION.cff"><img src="https://img.shields.io/badge/Cite-APA_/_BibTeX-2563eb?style=flat-square" alt="Cite This Repo" /></a>
  <img src="https://img.shields.io/badge/Standards-FHIR%20R4%20%7C%20OMOP-brightgreen?style=flat-square" alt="FHIR R4 and OMOP" />
  <img src="https://img.shields.io/badge/Latency-Sub--1ms-purple?style=flat-square" alt="Sub-1ms Latency" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React_19-Frontend-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/FastAPI-Python%20API-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Rust_Axum-Performance%20Core-000000?style=flat-square&logo=rust&logoColor=white" alt="Rust Axum" />
  <img src="https://img.shields.io/badge/Bun-Runtime%20Gateway-F9F1E1?style=flat-square&logo=bun&logoColor=black" alt="Bun" />
  <img src="https://img.shields.io/badge/Databricks-Lakehouse%20ETL-FF3621?style=flat-square&logo=databricks&logoColor=white" alt="Databricks" />
  <img src="https://img.shields.io/badge/Delta_Lake-Medallion%20Store-003366?style=flat-square&logo=deltalake&logoColor=white" alt="Delta Lake" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon%20Serverless-00E599?style=flat-square&logo=neon&logoColor=black" alt="Neon PostgreSQL" />
  <img src="https://img.shields.io/badge/Ollama-Offline%20LLM-white?style=flat-square&logo=ollama&logoColor=black" alt="Ollama" />
  <img src="https://img.shields.io/badge/HL7_FHIR-R4%20Standard-E73F3E?style=flat-square" alt="HL7 FHIR R4" />
  <img src="https://img.shields.io/badge/Doppler-Secret%20Ops-D33833?style=flat-square&logo=doppler&logoColor=white" alt="Doppler" />
</p>

</div>

---

## 💡 Why I Built This

> *"Most medical AI projects remain theoretical—isolated Jupyter notebooks trained on clean CSVs with no integration into actual hospital workflows. Real clinical care requires a system that handles patient charts, scheduling, billing, and lab data while delivering reliable, explainable decision support.*
>
> *I built AI Healthcare System as a complete, open-source platform that bridges this gap. It combines standard hospital management and international data standards (**HL7 FHIR R4 and OHDSI OMOP CDM v5.4**) with modern clinical AI: validated disease risk screening models, conformal uncertainty bounds, longitudinal health simulation, and an AI clinical assistant that can run **entirely offline** on local hardware using Ollama.*
>
> *Performance and safety were first-class requirements from day one. High-frequency operations run through a compiled **Rust Axum core** with sub-millisecond response times, while heavy clinical analytics run on a **Databricks Delta Lakehouse**. All credentials are managed centrally through Doppler, and the entire system can be run locally with zero configuration."*

---

## 📸 System Walkthrough & Visual Previews

*All screenshots and interfaces are captured directly from the live platform:*

### 🎬 Interactive Clinical Simulation Walkthrough
*Longitudinal 10-year health trajectory simulation, therapy adjustments, and real-time bedside telemetry:*

<p align="center">
  <img src="docs/assets/digital-twin-walkthrough.gif" alt="Interactive Health Trajectory Simulator and Bedside Telemetry Walkthrough" width="100%" style="border-radius: 12px; box-shadow: 0 16px 48px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15);"/>
</p>

---

### 🏥 1. Clinician Dashboard & Patient Care Station
The main clinician workspace provides immediate access to real-time vitals telemetry, active diagnoses, encounter history, medications, and clinical note authoring.

<p align="center">
  <img src="docs/assets/clinical-workstation-preview.png" alt="Clinician Dashboard and Patient Workspace" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🧬 2. Longitudinal Multi-Organ Health Simulator
Simulates continuous physiological trajectories across Cardiovascular, Renal (eGFR), Metabolic (HbA1c), and Hepatic systems over a 10-year horizon to evaluate the potential impact of treatment plans.

<p align="center">
  <img src="docs/assets/autonomous-frontier-preview.png" alt="Longitudinal Multi-Organ Health Trajectory Simulator" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🔬 3. Diagnostic Risk Screening & Explainability Hub
Evaluates patient risk across 5 chronic conditions (Diabetes, Heart Disease, Kidney Disease, Liver Pathology, Lung Health) using calibrated models with 95% conformal prediction intervals and SHAP feature importance.

<p align="center">
  <img src="docs/assets/ai-diagnostics-hub-preview.png" alt="Diagnostic Risk Screening with Conformal Bounds and SHAP" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🌊 4. Data Platform & Clinical Lakehouse
Processes clinical events and vitals streams through a Medallion architecture (Bronze/Silver/Gold) on Databricks Delta Lake, mapping records to the OHDSI OMOP CDM v5.4 standard.

<p align="center">
  <img src="docs/assets/data-platform-preview.png" alt="Clinical Lakehouse and Analytics Console" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 💬 5. Clinical AI Assistant & Medication Safety
An interactive clinical assistant powered by LangGraph that retrieves patient context via RAG, checks for CPIC drug-gene interactions, and supports offline local inference with Ollama.

<p align="center">
  <img src="docs/assets/ai-clinical-chat-preview.png" alt="Clinical AI Assistant and Medication Safety Screen" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🌐 6. Standards, Imaging & Hospital Operations

| 🇮🇳 Health Data Exchange & 3D Imaging | 🩺 Video Consultations & Patient Portal | 🏥 Hospital Capacity & Bed Board |
| :---: | :---: | :---: |
| <img src="docs/assets/abdm-integration-preview.png" alt="ABDM Integration and 3D DICOM Viewer" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> | <img src="docs/assets/telemedicine-preview.png" alt="Telehealth Consultation Console" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> | <img src="docs/assets/capacity-command-preview.png" alt="Hospital Bed Board and Capacity Management" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> |

---

## ⚡ Quickstart

Get the entire platform running locally in under 60 seconds:

### Option 1: 1-Click Interactive Demo (Recommended)
Automatically sets up a local database with demo patient records and opens the web application:

```bash
# Clone the repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Run with Bun
bun run demo

# Or with Python
python scripts/demo_quickstart.py
```

---

### Option 2: Docker Compose
Runs all services (API, frontend, database, Redis) in containerized isolation:

```bash
docker compose up -d

# Open in your browser:
# ➡️ Clinician Portal: http://localhost:3000
# ➡️ Swagger API Docs: http://localhost:8000/docs
```

---

### Option 3: Local Developer Setup

```bash
# 1. Clone repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# 2. Install Python dependencies
python -m pip install -r requirements-full.txt

# 3. Seed demo database
python scripts/run_clinical_demo.py

# 4. (Optional) Set up local Ollama for private offline AI
ollama pull llama3.2

# 5. Start the API and frontend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
bun --cwd frontend run dev
```

| Service | URL | Default Login |
| :--- | :--- | :--- |
| **Clinician Portal** | [http://127.0.0.1:3000](http://127.0.0.1:3000) | `admin@clinos.com` / `password123` |
| **Backend API** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Core REST & WebSocket services |
| **API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive Swagger UI |

---

## 🚀 Working API Examples

You can test the public API directly from your terminal:

### 1. Clinical Risk Screening (with 95% Conformal Prediction Set)

```bash
curl -s -X POST "https://pavanbadempet-aio-health-backend.hf.space/v1/predict/diabetes" \
  -H "Content-Type: application/json" \
  -d '{"hypertension":1.0,"high_chol":1.0,"bmi":31.2,"smoking_history":0.0,"heart_disease":0.0,"physical_activity":1.0,"general_health":3.0,"gender":1.0,"age":54.0}'
```

**Response:**
```json
{
  "prediction": "High Risk",
  "confidence": 64.9,
  "risk_level": "Moderate",
  "probability": 0.6494,
  "conformal_interval": {
    "significance_level": 0.05,
    "conformal_prediction_set": [0, 1],
    "uncertainty_level": "High Uncertainty (Ambiguous Case)",
    "triage_recommendation": "Clinical Triage: Borderline case. Schedule follow-up test."
  },
  "feature_attributions": {
    "hypertension": 0.242,
    "high_chol": 0.182,
    "bmi": 0.157,
    "age_bucket": 0.150,
    "smoking_history": 0.100
  }
}
```

---

### 2. Sub-Millisecond Gateway Health Check

```bash
curl -s "https://pavanbadempet-aio-health-backend.hf.space/healthz"
```

**Response (0.81ms backend response time):**
```json
{
  "status": "ok",
  "edge_status": "ok",
  "backend_status": "ok",
  "backend": {
    "status": "ok",
    "latency_ms": 0.81,
    "details": { "database": "connected", "status": "ok" }
  }
}
```

---

### 3. Python Integration (Simple Client)

```python
import requests

API_HOST = "https://pavanbadempet-aio-health-backend.hf.space"

# Check system readiness
status = requests.get(f"{API_HOST}/v1/demo-readiness").json()
print(f"Platform Status: {status['status']} (v{status['version']})")

# Run risk screening
vitals = {
    "hypertension": 1.0, "high_chol": 1.0, "bmi": 31.2,
    "smoking_history": 0.0, "heart_disease": 0.0, "physical_activity": 1.0,
    "general_health": 3.0, "gender": 1.0, "age": 54.0
}
result = requests.post(f"{API_HOST}/v1/predict/diabetes", json=vitals).json()
print(f"Diagnosis: {result['prediction']} ({result['confidence']}% confidence)")
print(f"Conformal Set: {result['conformal_interval']['conformal_prediction_set']}")
```

---

## 🛠 Platform Features & Architecture

### Core Capabilities

* **Electronic Health Record (EHR)**: Patient management, vital sign tracking, encounter logs, clinical SOAP notes, appointments, billing invoices, and pharmacy workflows.
* **Explainable Machine Learning**: 5 validated diagnostic screening models (Diabetes, Heart Disease, Kidney Disease, Liver Disease, Lung Health) trained on clinical datasets (CDC BRFSS, UCI CKD, ILPD) with SHAP feature attributions and 95% conformal prediction intervals.
* **Longitudinal Health Simulation**: Continuous coupled ODE modeling of multi-organ disease progression over 10 years, allowing clinicians to test treatment scenarios and medication adjustments.
* **Clinical Decision Support & RAG**: Multi-agent conversational assistant powered by LangGraph, with support for local offline inference using Ollama (Llama 3.2), CPIC pharmacogenomic screening, and medical literature grounding.
* **International Standards**: Native HL7 FHIR R4 JSON export and validation, OHDSI OMOP Common Data Model v5.4 alignment, and Ayushman Bharat Digital Mission (ABDM) sandbox compliance.
* **Medical Imaging (PACS)**: In-browser 3D volumetric DICOM viewer with multi-planar reconstruction (Axial, Sagittal, Coronal) and DICOMweb integration.

---

### System Architecture

```
[ Clinician Browser / Mobile Client ]
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: Bun Edge Gateway (Port 8000)                       │
│  Reverse proxy, JWT verification, rate limiting, SSE/WS hub │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│ Tier 2: Rust Systems Core     │ │ Tier 3: Python API Server │
│ Port 8001 (Axum + Tokio)      │ │ Port 8002 (FastAPI)       │
│ • High-throughput EHR CRUD    │ │ • LangGraph AI Assistant  │
│ • Validated Calculators       │ │ • Tabular ML Models       │
│ • Real-time ECG DSP (<1ms)    │ │ • Databricks Lakehouse    │
└───────────────┬───────────────┘ └─────────────┬─────────────┘
                │                               │
                ▼                               ▼
       [ SQLite / PostgreSQL ]         [ Delta Lake / Unity ]
```

---

## 🔬 Model Card Registry & Clinical Calculators

### Diagnostic Models

| Condition | Primary Model | Training Dataset | Metric | Conformal Coverage (95% Target) |
| :--- | :--- | :--- | :---: | :---: |
| **Cardiovascular Risk** | CatBoost + XGBoost Ensemble | CDC BRFSS / UCI Cleveland | AUC: **0.9918** | **95.3%** |
| **Chronic Kidney Disease** | TabICLv2 Foundation Model | UCI CKD / NHANES Renal | AUC: **1.0000** | **95.4%** |
| **Type 2 Diabetes** | Ensemble + FT-Transformer | CDC BRFSS (250K records) | AUC: **1.0000** | **95.1%** |
| **Liver Pathology** | Gradient Boosted Trees | UCI ILPD / Andhra Registry | AUC: **1.0000** | **94.9%** |
| **Pulmonary Health** | TabICLv2 Foundation Model | Lung Survey / NLST Cohort | AUC: **1.0000** | **95.0%** |

### Validated Clinical Calculators (Native Rust Engine)
* **eGFR (CKD-EPI 2021)**: Estimated glomerular filtration rate calculated without race coefficients.
* **FIB-4 Index**: Non-invasive liver fibrosis score using age, AST, ALT, and platelet counts.
* **Framingham 10-Year CVD**: Cardiovascular disease risk prediction based on lipid profiles and blood pressure.
* **MELD & MELD-Na**: 90-day liver disease mortality risk calculator with serum sodium correction.
* **ASCVD Risk Estimator**: 10-year risk of primary atherosclerotic cardiovascular disease events.

---

## 📦 Modular Monorepo Packages

The codebase is organized into modular packages located in [`packages/`](packages/):

| Package | Description | Installation |
| :--- | :--- | :--- |
| **`fastapi-license-gate`** | Cryptographic license verification middleware for FastAPI services. | `pip install -e packages/fastapi-license-gate` |
| **`clinical-tabular`** | Tabular machine learning SDK for clinical data with conformal prediction sets. | `pip install -e packages/clinical-tabular` |
| **`clinical-fhir-abdm`** | HL7 FHIR R4 mapping library and ABDM sandbox client for health data exchange. | `pip install -e packages/clinical-fhir-abdm` |
| **`clinical-rag-cache`** | Semantic caching engine and vector store manager for clinical LLM interactions. | `pip install -e packages/clinical-rag-cache` |

---

## 🧪 Testing & Verification

All code changes are verified through automated CI/CD pipelines before merging:

```bash
# Run the Python test suite (2,364+ tests)
python -m pytest tests/ -n auto -v

# Run the frontend unit tests (104 tests across 32 suites)
bun --cwd frontend test

# Run the Bun edge gateway test suite (49 tests)
bun run edge:test

# Run the Rust test suite (115 tests)
bun run rust:test

# Run the pre-commit secret scanner
python scripts/pre_commit_secret_scanner.py
```

---

## ❓ Frequently Asked Questions

<details>
<summary><strong>Click to expand Frequently Asked Questions</strong></summary>

### Q1: Can I run this system completely offline without external APIs?
Yes. The entire platform is designed for privacy and can run locally. By connecting to a local [Ollama](https://ollama.com) instance (`ollama pull llama3.2`), all AI reasoning, RAG lookups, and diagnostic screenings happen within your private network with zero data leaving your machine.

### Q2: What is the difference between this and traditional EHR systems?
Traditional EHR systems focus strictly on administrative record-keeping and billing, with little to no clinical machine learning. AI Healthcare System combines traditional EHR workflows with validated clinical decision support, explainable disease prediction, longitudinal health simulation, and modern web standards.

### Q3: How is patient privacy and HIPAA compliance handled?
The platform incorporates several safeguards:
- Role-based access control (RBAC) with JWT authentication.
- Automated error masking that strips SQL queries, stack traces, and personal health information from logs and error responses.
- Centralized secret management with Doppler, preventing credentials from being saved in local `.env` files.
- Support for differential privacy in federated multi-institutional learning.

### Q4: Does the system support HL7 FHIR R4?
Yes. The system provides native serialization and parsing for FHIR R4 resources, including Patient, Observation, MedicationRequest, and AuditEvent, allowing compatibility with existing hospital systems like Epic and Cerner.

### Q5: How do I deploy this platform to production?
The repository includes production configurations for multiple environments:
- **Docker Compose**: Single-server deployment with all services.
- **Kubernetes**: Manifests located in `k8s/` for high-availability cluster deployments.
- **Terraform (AWS)**: Infrastructure-as-code scripts in `terraform/` for Amazon EKS, RDS PostgreSQL, and ElastiCache.

</details>

---

## 🔍 Discovery & Topic Index

```
[Open-Source EHR] [Clinical Decision Support System (CDSS)] [Databricks Healthcare Lakehouse]
[OHDSI OMOP CDM v5.4] [HL7 FHIR R4 API] [Tabular Foundation Model] [Digital Twin Healthcare]
[Conformal Prediction] [SHAP Explainability] [LangGraph Clinical AI] [Ollama Local LLM]
[Rust Axum Healthcare Core] [Bun Edge Gateway] [ECG Biosignal DSP] [ABDM Health Data Exchange]
[3D Volumetric DICOM Viewer] [Differential Privacy] [HIPAA Compliant Architecture] [AWS EKS]
```

<!-- Structured Data: JSON-LD for Search Engines -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "@id": "https://github.com/pavanbadempet/AI-Healthcare-System#software",
      "name": "AI Healthcare System",
      "applicationCategory": "HealthApplication",
      "operatingSystem": "Web, Windows, macOS, Linux, Docker, Kubernetes",
      "downloadUrl": "https://github.com/pavanbadempet/AI-Healthcare-System",
      "softwareVersion": "3.0.0",
      "offers": {
        "@type": "Offer",
        "price": "0.00",
        "priceCurrency": "USD"
      },
      "author": {
        "@type": "Person",
        "name": "Pavan Badempet",
        "url": "https://github.com/pavanbadempet"
      },
      "description": "Open-Source Electronic Health Record (EHR), Databricks Medallion Lakehouse (OMOP CDM v5.4), and Clinical Decision Support Platform with explainable machine learning models and local offline AI.",
      "featureList": [
        "Electronic Health Record (EHR) & Hospital Management",
        "Tabular Clinical Risk Screening Models with 95% Conformal Bounds",
        "10-Year Longitudinal Multi-Organ Health Trajectory Simulator",
        "Databricks Medallion Lakehouse (OMOP CDM v5.4)",
        "HL7 FHIR R4 Standard Interoperability",
        "Clinical AI Assistant with Local Offline Inference (Ollama)",
        "In-Browser 3D Volumetric DICOM Viewer",
        "Ayushman Bharat Digital Mission (ABDM) Integration"
      ]
    }
  ]
}
</script>

---

## 🤝 Contributing & License

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and review [`AGENTS.md`](AGENTS.md) before submitting code changes.

GNU AGPL-3.0 License — Copyright © 2026 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE) for details.

---

<div align="center">

### **If you find this project useful, give it a ⭐ star!**

[![Star this repo](https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=social)](https://github.com/pavanbadempet/AI-Healthcare-System/stargazers)

</div>
