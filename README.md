<div align="center">

<img src="docs/assets/hero-banner.svg" alt="AI Healthcare System — Open-Source Electronic Health Record (EHR), Databricks Medallion Lakehouse (OMOP CDM v5.4), TabICLv2 Foundation Model, and Clinical Intelligence Platform" width="100%"/>

# 🩺 AI Healthcare System
### *Open-Source HIPAA-Compliant EHR, Databricks Medallion Lakehouse (OMOP CDM v5.4) & Clinical Intelligence Platform*

<br/>

**A production-grade, privacy-first open-source Electronic Health Record (EHR), Databricks Medallion Lakehouse, and Clinical Decision Support System (CDSS) powered by TabICLv2 Foundation Models, 10-Year Continuous ODE Health Simulation, Multi-Agent LangGraph RAG, and Sub-Millisecond Rust Systems Core.**

<br/>

<p align="center">
  <a href="https://huggingface.co/spaces/pavanbadempet/aio-health-backend"><img src="https://img.shields.io/badge/🤗%20Live%20Clinical%20Portal-Hugging%20Face%20Space-22c55e?style=for-the-badge&logo=huggingface&logoColor=white" height="34" alt="Live Clinical Portal"/></a>
  &nbsp;
  <a href="https://huggingface.co/spaces/pavanbadempet/aio-health-backend/docs"><img src="https://img.shields.io/badge/📖%20Interactive%20Swagger%20API-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" height="34" alt="Interactive API Docs"/></a>
  &nbsp;
  <a href="https://huggingface.co/pavanbadempet/ai-healthcare-models"><img src="https://img.shields.io/badge/🤗%20Model%20Hub-16%20Weights-yellow?style=for-the-badge&logo=huggingface&logoColor=black" height="34" alt="Hugging Face Model Hub" /></a>
  &nbsp;
  <a href="docs/optimal_dual_layer_architecture.md"><img src="https://img.shields.io/badge/🏛️%20Architecture-System%20Design%20Spec-blue?style=for-the-badge&logo=blueprint&logoColor=white" height="34" alt="System Design Spec"/></a>
</p>

<p align="center">
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/ci.yml/badge.svg" alt="CI/CD Build Status" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml"><img src="https://github.com/pavanbadempet/AI-Healthcare-System/actions/workflows/codeql.yml/badge.svg" alt="CodeQL Security Analysis" /></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-Welcome-10b981?style=flat-square" alt="PRs Welcome" /></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/Security-Policy-red?style=flat-square&logo=shield" alt="Security Policy" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=flat-square" alt="AGPL v3 License" /></a>
  <a href="https://github.com/sponsors/pavanbadempet"><img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa.svg?logo=github&style=flat-square" alt="Sponsor" /></a>
  <a href="https://github.com/pavanbadempet/AI-Healthcare-System/stargazers"><img src="https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=flat-square&color=f59e0b" alt="Stars" /></a>
  <a href="CITATION.cff"><img src="https://img.shields.io/badge/Cite-APA_/_BibTeX-2563eb?style=flat-square" alt="Cite This Repo" /></a>
  <img src="https://img.shields.io/badge/Compliance-HIPAA%20%2F%20GDPR-brightgreen?style=flat-square&logo=security" alt="HIPAA / GDPR" />
  <img src="https://img.shields.io/badge/Latency-Sub--1ms-purple?style=flat-square&logo=speedtest" alt="Sub-1ms Latency" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Databricks-Unity%20Catalog%20OMOP-FF3621?style=flat-square&logo=databricks&logoColor=white" alt="Databricks" />
  <img src="https://img.shields.io/badge/Delta_Lake_4.x-Medallion%20Lakehouse-003366?style=flat-square&logo=deltalake&logoColor=white" alt="Delta Lake" />
  <img src="https://img.shields.io/badge/PySpark_4.x-Clinical%20ETL-E25A1C?style=flat-square&logo=apachespark&logoColor=white" alt="PySpark" />
  <img src="https://img.shields.io/badge/Neon_Serverless-PostgreSQL%20Pooler-00E599?style=flat-square&logo=neon&logoColor=black" alt="Neon Serverless" />
  <img src="https://img.shields.io/badge/TabICLv2-Tabular%20Foundation-blueviolet?style=flat-square" alt="TabICLv2 Foundation Model" />
  <img src="https://img.shields.io/badge/Digital%20Twin-10--Year%20ODE%20Simulator-purple?style=flat-square" alt="Digital Twin" />
  <img src="https://img.shields.io/badge/Rust_Axum-Systems%20Core-000000?style=flat-square&logo=rust&logoColor=white" alt="Rust Systems Core" />
  <img src="https://img.shields.io/badge/Bun-1.2%20Edge%20Gateway-F9F1E1?style=flat-square&logo=bun&logoColor=black" alt="Bun 1.2" />
  <img src="https://img.shields.io/badge/FastAPI-Clinical%20API-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React_19-Clinical%20Workstation-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/HL7_FHIR-R4%20Interoperability-E73F3E?style=flat-square" alt="FHIR R4" />
  <img src="https://img.shields.io/badge/Doppler-Centralized%20Secrets-D33833?style=flat-square&logo=doppler&logoColor=white" alt="Doppler Secrets" />
</p>

</div>

---

## 💡 Why I Built This & Executive Architecture Summary

> *"Most medical AI projects stop at simple toy Kaggle notebooks with synthetic CSVs, zero clinical governance, and no real hospital interoperability. I engineered this platform from the ground up as an authentic open-source blueprint solving the full end-to-end clinical intelligence lifecycle: ingesting multimodal patient records, executing distributed telemetry ETL, simulating continuous 10-year multi-organ disease trajectories, and providing safe decision support for attending clinicians.*
>
> *The architecture establishes a **Databricks Serverless Medallion Lakehouse with PySpark and Delta Lake** for distributed clinical ETL, harmonizing raw hospital telemetry and EHR data into **OHDSI OMOP CDM v5.4 and HL7 FHIR R4 standard models**. To decouple heavy analytical lakehouse queries from mission-critical patient care, we bridge real-time serving through a **high-throughput Rust Axum systems core with ONNX Runtime and a Bun Elysia edge gateway delivering sub-millisecond (0.81ms) inference**.*
>
> *Diagnostic risk stratification runs across **TabICLv2 Tabular Foundation Models (Rank #1 on TabArena)** alongside calibrated **CatBoost, XGBoost, and LightGBM ensembles with 95% Conformal Prediction sets and C++ SHAP explainability**. A continuous **10-year coupled ODE multi-organ health simulator** models cardiovascular, renal, metabolic, and hepatic trajectories over time. Zero credentials ever touch code or disks: 100% of pipeline orchestration is automated through centralized Doppler secret management, 17 GitHub Actions CI/CD workflows, and automated pre-commit and pre-push security gates."*

---

## 📸 Production Previews & Visual Tour (Live Deployment)

*Authentic interface screenshots and workflows captured directly from the live deployment on Hugging Face Spaces:*

### 🎬 Interactive Health Trajectory Simulator & Bedside Telemetry
*Continuous 10-year multi-organ ODE disease progression, dynamic drug titration (+2.45 QALYs gained), counterfactual causal inference, and real-time bedside ICU telemetry:*

<p align="center">
  <img src="docs/assets/digital-twin-walkthrough.gif" alt="Interactive 10-Year Multi-Organ Health Simulator and Bedside Telemetry Walkthrough" width="100%" style="border-radius: 12px; box-shadow: 0 16px 48px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15);"/>
</p>

---

### 🏥 1. Nexus Vitalis Clinician Dashboard & Patient Workspace
Comprehensive clinician cockpit integrating real-time vital telemetry, interactive SOAP note drafting with ambient voice dictation, medication reconciliation, and longitudinal EHR history.

<p align="center">
  <img src="docs/assets/clinical-workstation-preview.png" alt="Nexus Vitalis Clinical Workstation Preview" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🧬 2. Longitudinal Multi-Organ Health Simulator (10-Year ODE Trajectory)
Coupled ordinary differential equations projecting 10-year longitudinal trajectories across Cardiovascular, Renal eGFR, Metabolic (HbA1c), and Hepatic systems, demonstrating therapy titrations.

<p align="center">
  <img src="docs/assets/autonomous-frontier-preview.png" alt="10-Year Continuous ODE Multi-Organ Health Trajectory Preview" width="100%" style="border-radius: 10px; box-shadow: 0 12px 36px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🔬 3. Multimodal Diagnostics Hub (TabICLv2 + 95% Conformal Sets + SHAP)
Tabular foundation model risk scoring featuring mathematical 95% conformal prediction intervals, physician override auditing, and real-time C++ SHAP feature attributions.

<p align="center">
  <img src="docs/assets/ai-diagnostics-hub-preview.png" alt="Multimodal Diagnostics Hub (TabICLv2 + Conformal Prediction + SHAP)" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🌊 4. Databricks Serverless Medallion Lakehouse & OMOP CDM v5.4
End-to-end distributed data platform with Apache Spark, Delta Lake ACID time-travel, Spark Declarative Pipelines (SDP) data quality quarantine gates, and OHDSI OMOP dimensional warehouse.

<p align="center">
  <img src="docs/assets/data-platform-preview.png" alt="Databricks Lakehouse Medallion Streaming Pipeline & Unity Catalog Console" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 💬 5. Clinical AI Assistant & Medication Safety Screen
Multi-agent RAG assistant (LangGraph) backed by local Ollama private inference (Llama 3.2), CPIC Level A pharmacogenomic contraindication screens, and PubMed citation grounding.

<p align="center">
  <img src="docs/assets/ai-clinical-chat-preview.png" alt="Clinical AI Assistant & Pharmacogenomic Safety Screen" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🇮🇳 6. ABDM National Health Stack Sandbox & 3D Volumetric DICOM MPR
Ayushman Bharat Digital Mission (ABDM M1/M2/M3) sandbox compliance with ABHA Health IDs, consent management lifecycle, and GPU-accelerated 3D tri-planar DICOM viewport.

<p align="center">
  <img src="docs/assets/abdm-integration-preview.png" alt="ABDM Sandbox, ABHA Health IDs, and 3D Volumetric DICOM MPR Viewport" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

### 🩺 7. Telehealth Video Console, Bedside Companion & Hospital Bed Board

| 🩺 WebRTC Telehealth & Specialist Routing | 🤖 Bedside Patient Care Companion | 🏥 Hospital Capacity & Bed Board |
| :---: | :---: | :---: |
| <img src="docs/assets/telemedicine-preview.png" alt="Telemedicine Video Consultation Console" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> | <img src="docs/assets/companion-preview.png" alt="Bedside Patient Care Companion" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> | <img src="docs/assets/capacity-command-preview.png" alt="Hospital Bed Board & Capacity Management" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"/> |

---

### 🛡️ 8. Privacy-Preserving Differential Privacy Federated Learning
Multi-hospital collaborative model training with formal differential privacy ($\epsilon$-budget tracking, Laplace noise mechanism) and immutable cryptographic audit trails.

<p align="center">
  <img src="docs/assets/federated-learning-preview.png" alt="Privacy-Preserving Federated Learning & Differential Privacy Audit Console" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);"/>
</p>

---

## 🚀 Real Usage Examples (Ready to Run)

No placeholder API keys required. You can test the public endpoints directly from your terminal, Python script, or frontend application:

### 1. cURL: Clinical Risk Screening & 95% Conformal Prediction Set

Query the live Rust ONNX diagnostic model for Type 2 Diabetes risk screening with conformal uncertainty intervals:

```bash
# Query the live deployment on Hugging Face Spaces:
curl -s -X POST "https://pavanbadempet-aio-health-backend.hf.space/v1/predict/diabetes" \
  -H "Content-Type: application/json" \
  -d '{"hypertension":1.0,"high_chol":1.0,"bmi":31.2,"smoking_history":0.0,"heart_disease":0.0,"physical_activity":1.0,"general_health":3.0,"gender":1.0,"age":54.0}'
```

**Real JSON Response (Live Output):**
```json
{
  "prediction": "High Risk",
  "raw": 1,
  "confidence": 64.9,
  "risk_level": "Moderate",
  "disclaimer": "This is an AI-assisted screening tool, not a medical diagnosis. Please consult a qualified healthcare professional for clinical decisions.",
  "probability": 0.6494,
  "probabilities": [0.3506, 0.6494],
  "conformal_interval": {
    "significance_level": 0.05,
    "conformal_prediction_set": [0, 1],
    "uncertainty_level": "High Uncertainty (Ambiguous Case)",
    "triage_recommendation": "Clinical Triage: Borderline case. Schedule follow-up test or refer to specialist.",
    "p_class_0": 0.351,
    "p_class_1": 0.649
  },
  "feature_attributions": {
    "hypertension": 0.242,
    "high_chol": 0.182,
    "bmi": 0.157,
    "age_bucket": 0.150,
    "smoking_history": 0.100,
    "general_health": 0.052,
    "gender": 0.051,
    "physical_activity": 0.051,
    "heart_disease": 0.050
  }
}
```

---

### 2. cURL: High-Speed Gateway Telemetry & Health Check (<1ms Latency)

Verify the multi-tier health probe and measure microsecond-level response times:

```bash
curl -s "https://pavanbadempet-aio-health-backend.hf.space/healthz"
```

**Real JSON Response (Measured 0.81ms backend response time):**
```json
{
  "status": "ok",
  "edge_status": "ok",
  "backend_status": "ok",
  "uptime_seconds": 28256,
  "memory_mb": 30.45,
  "backend": {
    "status": "ok",
    "latency_ms": 0.81,
    "details": {
      "database": "connected",
      "gateway": "healthy",
      "status": "ok"
    }
  }
}
```

---

### 3. Python Client (Zero Dependencies besides `requests`)

```python
import requests

API_HOST = "https://pavanbadempet-aio-health-backend.hf.space"

# 1. Verify platform readiness
readiness = requests.get(f"{API_HOST}/v1/demo-readiness").json()
print(f"Platform Status: {readiness['status']} (v{readiness['version']})")

# 2. Compute patient clinical risk with 95% conformal bounds
payload = {
    "hypertension": 1.0, "high_chol": 1.0, "bmi": 31.2,
    "smoking_history": 0.0, "heart_disease": 0.0, "physical_activity": 1.0,
    "general_health": 3.0, "gender": 1.0, "age": 54.0
}
pred = requests.post(f"{API_HOST}/v1/predict/diabetes", json=payload).json()
print(f"Diagnosis: {pred['prediction']} ({pred['confidence']}% confidence)")
print(f"Conformal Prediction Set: {pred['conformal_interval']['conformal_prediction_set']}")
```

---

### 4. TypeScript / React (Frontend Integration)

```typescript
export async function screenDiabetesRisk(vitals: Record<string, number>) {
  const response = await fetch("https://pavanbadempet-aio-health-backend.hf.space/v1/predict/diabetes", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(vitals),
  });
  if (!response.ok) throw new Error(`Diagnostic API Error: ${response.status}`);
  return await response.json();
}
```

---

## ⚡ Quickstart & Installation (Zero Guesswork)

Choose the setup that fits your workflow. Zero cloud credentials required for local execution.

### Option A: 1-Click Interactive Demo (Fastest & Recommended)
Auto-provisions mock EHR database, pre-loads TabICLv2 & Quad-Ensemble weights, and opens the React 19 workstation:

```bash
# Clone the repository
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System

# Run with Bun (Instant 1-Click Interactive Demo)
bun run demo

# Or with standard Python
python scripts/demo_quickstart.py
```

*High-Speed Developer Tooling Commands:*
```bash
bun run benchmark          # Async HTTP benchmark harness (p50/p90/p95/p99 quantiles, >10k req/s)
bun run manage-db          # Sub-15ms SQLite maintenance (integrity, vacuum, query tuning)
bun run generate-fhir      # Synthetic FHIR R4 transaction generator (>66,000 bundles/s)
bun run context            # Sub-40ms AST symbol scanner & codebase context
bun run edge:test          # Run Bun Edge Gateway test suite (49 passed)
bun run rust:test          # Run native Rust test matrix (115 passed)
bun run security:scan      # Pre-commit zero-leak credential scanner
```

---

### Option B: 1-Click Docker Compose
Launches the complete service container stack (FastAPI backend + React frontend + PostgreSQL + Redis):

```bash
docker compose up -d

# Open in your browser:
# ➡️ Clinician Portal: http://localhost:3000
# ➡️ Swagger API Docs: http://localhost:8000/docs
```

---

### Option C: Local Developer Sandbox (5-Step Walkthrough)

#### 1️⃣ Clone and Install Python Dependencies
```bash
git clone https://github.com/pavanbadempet/AI-Healthcare-System.git
cd AI-Healthcare-System
python -m pip install -r requirements-full.txt
```

#### 2️⃣ Configure Doppler Centralized Secrets (Zero Local .env Leaks)
We use **Doppler** as our centralized secret manager. Never write credentials into local `.env` files:
```bash
doppler login
```

#### 3️⃣ Bootstrap Database & Seed Mock EHR Data
```bash
python scripts/run_clinical_demo.py
```

#### 4️⃣ Launch Local Private LLM (Ollama Setup)
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

#### 5️⃣ Start Dev Servers (Tri-Tier or Standalone)
```bash
# Option 1: Tri-Tier High-Performance Stack (Recommended)
bun run edge:dev    # Terminal 1: Tier 1 Bun Edge Gateway (Port 8000)
bun run rust:run    # Terminal 2: Tier 2 Native Rust Systems Core (Port 8001)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002  # Terminal 3: Tier 3 Python AI Service
bun run dev         # Terminal 4: React 19 Clinician Workstation (Port 3000)

# Option 2: Standalone Mode (Direct Python Gateway)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
bun run dev
```

| Service Portal | Access Endpoint | Credentials & Notes |
| :--- | :--- | :--- |
| **Clinician Portal** | [http://127.0.0.1:3000](http://127.0.0.1:3000) | Doctor Login: `admin@clinos.com` / Password: `password123` |
| **Bun Edge Gateway (Tier 1)** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | PID 1 Reverse proxy, rate limiting, and SSE hub |
| **Rust Systems Core (Tier 2)**| [http://127.0.0.1:8001](http://127.0.0.1:8001) | Sub-millisecond EHR CRUD, MELD/ASCVD & Pan-Tompkins DSP |
| **Python AI Service (Tier 3)** | [http://127.0.0.1:8002](http://127.0.0.1:8002) | LangGraph agents, TabICLv2 & Medallion lakehouse |
| **Prometheus Telemetry** | [http://127.0.0.1:8000/metrics/prometheus](http://127.0.0.1:8000/metrics/prometheus) | Real-time sliding-window p50/p90/p95/p99 latency quantiles |
| **Swagger API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive API sandbox testing |

---

### Option D: 1-Click Cloud Workspace (Codespaces & Hugging Face)

No installation required on your machine. Test it instantly in your browser:
* **[🤗 Hugging Face Spaces Live Demo](https://huggingface.co/spaces/pavanbadempet/aio-health-backend)**
* **[GitHub Codespaces 1-Click Sandbox](https://codespaces.new/pavanbadempet/AI-Healthcare-System)**

---

## 🎯 Core Platform Specifications & 2026 Tech Stack

| Category | Core Specs & Technologies (Search Optimization Keywords) |
| :--- | :--- |
| **💡 Core Purpose** | Open-source EHR & Clinical Decision Support System (CDSS) with 10-Year Multi-Organ Health Simulator |
| **🌐 Multi-Cloud Mesh** | Databricks Unity Catalog + Delta Lakehouse + Cloudflare Workers AI + Hugging Face Spaces + Neon Postgres |
| **🤖 Foundation ML** | **TabICLv2** (Inria Foundation Transformer) + CatBoost / XGBoost / LightGBM Soft-Voting Ensemble |
| **🧮 Health Simulator** | Continuous 10-year coupled ODE multi-organ simulation (Cardiovascular, Renal eGFR, Metabolic, Hepatic) |
| **💊 Pharmacogenomics** | CPIC gene-drug contraindication engine (CYP2C9, CYP2C19, CYP2D6, SLCO1B1, DPYD, VKORC1) |
| **🧠 Generative AI** | Multi-Specialty Clinical AI Assistant, Cloudflare Workers AI (Llama 3.1 8B FP8), Groq, Ollama, LangGraph |
| **📊 Diagnostics & DSP** | 5 Calibrated Risk Ensembles + Pan-Tompkins ECG QRS Detector (<1ms) & HRV RMSSD + AVX2 SIMD Math |
| **📁 EHR & Lakehouse** | Databricks Medallion (Bronze/Silver/Gold), OHDSI OMOP CDM v5.4, Delta Lake Time-Travel, FHIR R4 |
| **🖼️ PACS Imaging** | 3D Volumetric DICOM MPR (Axial, Sagittal, Coronal, 3D Mesh), DICOMweb WADO-RS / QIDO-RS |
| **⚡ Edge Gateway (Tier 1)**| Bun + ElysiaJS (PID 1 on Port 8000), Layer-7 smart proxy, sub-ms JWT, Prometheus metrics, SSE/WS hub |
| **🦀 Systems Core (Tier 2)**| Native Rust (Port 8001, Axum+Tokio+SQLx), Clinical Safety Gate, Evidence Consensus, PyO3 FFI |
| **🛠️ Developer Tooling**| Native Bun TypeScript engine: `benchmark_system.ts` (>10k req/s), `manage_db.ts` (<15ms), `generate_fhir_bundles.ts` |
| **⚖️ License & Sovereignty** | 100% Open-Source (Self-hosted, zero vendor lock-in, GNU AGPL-3.0) |
| **🔐 HIPAA DevSecOps** | Hardware TEE enclaves, PII redaction filters, Docker, AWS EKS, SOC 2 compliance harness |

### ⚡ Production Ecosystem Matrix (2026 Standards)

| Infrastructure Layer | Standard Version | Framework & Protocol | Architectural Role & Modern Capability |
| :--- | :---: | :--- | :--- |
| **Distributed Compute** | PySpark 4.0+ | Apache Spark 4.x / Databricks Unity Catalog | Catalyst SIMD codegen, Spark Declarative Pipelines (SDP), distributed feature store. |
| **Lakehouse Storage** | Delta Lake 4.0+ | Delta 4.x Medallion Architecture | Liquid Clustering (`clusterBy`), OHDSI OMOP CDM v5.4 dimensional modeling, ACID time-travel. |
| **Foundation Tabular ML**| TabICLv2 | Inria Soda Tabular Transformer | Rank #1 on TabArena, zero-shot clinical classification, 95% conformal prediction intervals. |
| **Systems Core (Tier 2)**| Rust 2024 Edition | Axum 0.8+ / Tokio / SQLx / PyO3 0.23+ | Sub-millisecond EHR CRUD (0.81ms), Pan-Tompkins ECG DSP (<1ms), zero-IPC CPython FFI bridge. |
| **Edge Gateway (Tier 1)**| Bun 1.2+ | ElysiaJS / Web Crypto API | PID 1 reverse proxy, sub-0.5ms JWT auth, Prometheus metrics, SSE/WebSocket live vitals hub. |
| **Client Workstation** | React 19.2+ | TypeScript 5.8+ / Vite 8.0+ / Tailwind 4 | Responsive clinician cockpit, 3D WebGL DICOM viewer, live vital graphs, accessible dark mode. |
| **Clinical AI** | Python 3.12+ | LangGraph / Ollama / Cloudflare Workers | Multi-specialty clinical AI assistant, private local inference (Llama 3.2), prompt registry. |
| **Secret Management** | Doppler | Doppler CLI & GitHub Actions OIDC | Zero credentials in repo or `.env`, automated pre-commit zero-leak scanners. |

---

## 🆚 Competitive Comparison: Why AI Healthcare System?

| Feature / Capability | AI Healthcare System | OpenMRS | GNU Health | Typical Legacy EHRs |
|:---|:---:|:---:|:---:|:---:|
| **AI Clinical Decision Support** | ✅ Integrated (5 ML Models + Conformal + SHAP) | ❌ None | ❌ None | ❌ Hardcoded rules only |
| **Interactive RAG Chatbot** | ✅ LangGraph + Local Ollama Fallback | ❌ None | ❌ None | ❌ None |
| **Modern Technology Stack** | ✅ React 19 + Bun + Rust Axum + FastAPI | ❌ Legacy Java Server Pages | ❌ GTK / Python 2/3 Desktop | ❌ Legacy ASP.NET / Java Swing |
| **Offline Privacy Gate** | ✅ Fully Offline Local Inference Option (Ollama) | ❌ N/A | ❌ N/A | ❌ Heavy Cloud Dependency |
| **FHIR R4 Interoperability** | ✅ Native Serialization & HAPI FHIR Imports | ✅ Supported | ⚠️ Partial | ⚠️ Custom proprietary APIs |
| **ABDM Digital Health Stack** | ✅ Active Consent Lifecycle & Sandboxing | ❌ Third-party plugins | ❌ None | ❌ Enterprise integration required |
| **Modern Telemetry Broadcasting**| ✅ Live WebSockets & SSE Broadcasts (<1ms) | ❌ None | ❌ None | ❌ Batch reporting only |

---

## 🏗 Core Technical Architecture

The platform operates on an optimized **Tri-Tier Topology** partitioning edge ingress, transactional persistence, and deliberative AI reasoning:

```
                              [ Client Browser / Mobile App / Clinician Devices ]
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tier 1: Bun + ElysiaJS Edge Gateway & BFF (`edge_gateway/`) — Port 8000 (PID 1 Entrypoint)               │
│  • Edge JWT Cryptographic Authentication (<0.5ms) & Token-Bucket Rate Limiting (>100,000 req/s)           │
│  • Sliding-Window Prometheus Metrics Exporter (`/metrics/prometheus`) with real-time p50/p90/p95/p99 latency│
│  • Dual-Core Health Aggregator (`/healthz/ready`) concurrently checking Rust and Python                   │
│  • Native WebSockets & Server-Sent Events (SSE) Telemetry Hub for real-time vitals and token streaming    │
│  • Layer-7 Reverse Proxy: partitions 100% of CRUD/EHR to Rust; routes only complex analytics to Python     │
└───────────────────────────────────────┬───────────────────────────────────────┬───────────────────────────┘
                                        │                                       │
                  High-Throughput CRUD, │                                       │ Complex Clinical AI,
                  FHIR & Biosignal DSP  │                                       │ RAG & Foundation ML
                                        ▼                                       ▼
┌────────────────────────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐
│ Tier 2: Native Rust Systems Core (`rust_gateway/`)         │ │ Tier 3: Python AI Service (`backend/`)      │
│ Port 8001 (Axum + Tokio + SQLx)                            │ │ Port 8002 (Internal Only)                   │
│  • Complete EHR & Hospital CRUD (Appointments, Billing,     │ │  • Multi-Specialty Clinical AI Assistant    │
│    Pharmacy, Records, Vitals, Beds, Rostering)             │ │  • Prompt Registry & LLM Orchestration      │
│  • Pre-Action Clinical Safety Rules & Validation Gate      │ │  • Clinical Decision Support Reasoning      │
│  • Clinical Evidence Consensus Framework                   │ │  • Medallion Data Engineering Pipelines     │
│  • Pan-Tompkins ECG QRS Detector & HRV RMSSD Calculator    │ └──────────────────────┬──────────────────────┘
│  • AVX2 SIMD Euclidean Distance & Batch Cosine Similarity  │                        │
│  • Clinical Calculators (Framingham, MELD, ASCVD, FIB-4)   │                        │
│  • Zero-IPC PyO3 CPython FFI Module (`rust_gateway_ffi`)   │◄───────────────────────┘
└────────────────────────────────────────────────────────────┘       Zero-IPC PyO3 FFI Acceleration
```

### Codebase Technology Breakdown & Share:

| Language / Layer | Core Role in System | Files | Lines of Code | Share (%) |
|:---|:---|:---:|:---:|:---:|
| **Python** | Clinical AI Assistance, Prompt Registry, ML Models, Lakehouse | 1,166 | 166,400 | **69.48%** |
| **TSX React (Bun)** | Frontend Workstation, Clinical Decision Dashboards, WebGPU Views | 113 | 34,497 | **14.40%** |
| **Rust** | Axum Systems Core, Safety Gate, Pan-Tompkins DSP, SIMD Math | 79 | 23,948 | **10.00%** |
| **TypeScript (Bun)** | Edge Gateway, Layer-7 Proxy, Developer CLI Tools, Benchmarks | 88 | 12,879 | **5.38%** |
| **Kotlin (Android)** | Jetpack Compose Mobile Native Patient/Doctor App | 11 | 1,138 | **0.48%** |
| **JavaScript & SQL** | Ancillary Web Scripts & Base Schemas | 6 | 624 | **0.26%** |
| **Total Executable Code** | | **1,463** | **239,486** | **100.00%** |

### High-Level Request Routing Flow:

```mermaid
graph TB
    subgraph Client["CLIENT SURFACE — React 19 · TypeScript · Tailwind CSS 4"]
        FE["Vite SPA · Doctor Portal · Telemedicine & Live Vitals UI"]
    end

    subgraph Tier1["TIER 1: BUN EDGE GATEWAY & BFF — Port 8000 (PID 1)"]
        EDGE_ROUTER["ElysiaJS Layer-7 Reverse Proxy & Path Partitioning"]
        EDGE_AUTH["Sub-0.5ms JWT Cryptographic Guard & Token Bucket Limiter"]
        EDGE_STREAM["Native WebSockets & SSE Telemetry Hub"]
        EDGE_METRICS["Prometheus Sliding-Window Metrics Exporter"]
    end

    subgraph Tier2["TIER 2: RUST SYSTEMS CORE — Port 8001 (Axum · Tokio · SQLx)"]
        RUST_CRUD["High-Throughput EHR CRUD (Patients · Vitals · Encounters · Billing)"]
        RUST_DSP["Pan-Tompkins ECG Biosignal DSP & HRV RMSSD Engine (<1ms)"]
        RUST_SIMD["AVX2 SIMD Euclidean Distance & Batch Cosine Engine"]
        RUST_SAFETY["Clinical Safety Gate & Evidence Consensus Solver"]
        RUST_CALC["Native Clinical Calculators (MELD, ASCVD, Framingham, FIB-4)"]
    end

    subgraph Tier3["TIER 3: PYTHON AI SERVICE — Port 8002 (FastAPI)"]
        AGENT["LangGraph Clinical Assistant (Multi-Specialty Reasoning)"]
        CORE_AI["Core AI Gateway (Cloudflare Llama 3.1 8B · Ollama · Gemini)"]
        TAB_ML["TabICLv2 Foundation Model & Calibrated Soft-Voting Ensembles"]
        LAKEHOUSE["Databricks Unity Catalog Medallion Lakehouse & PySpark Engine"]
    end

    subgraph Storage["DATA & PERSISTENCE LAYER"]
        SQL_DB[("Dual SQL Engine — SQLite WAL / Multi-AZ PostgreSQL")]
        DELTA_LAKE[("Delta Lake 4.x ACID Medallion Storage (Bronze · Silver · Gold)")]
        MODEL_REG[("Model Registry — TabICLv2 & Quad-Ensemble Calibrated Weights")]
    end

    Client --> Tier1
    Tier1 -->|"100% EHR CRUD, DSP, SIMD & Calculators"| Tier2
    Tier1 -->|"Complex Analytics, RAG & Foundation Models"| Tier3
    Tier3 -.->|"Zero-IPC PyO3 FFI Acceleration"| Tier2
    Tier2 --> SQL_DB
    Tier3 --> SQL_DB
    Tier3 --> DELTA_LAKE
    Tier3 --> MODEL_REG
```

### AWS EKS Cluster Production Topology:

```mermaid
graph TD
    ClientReq[HTTPS Traffic] --> ALBRouter[AWS ALB / Ingress Controller]
    subgraph AWS VPC ["AWS Virtual Private Cloud"]
        ALBRouter --> EKSCluster[Amazon EKS Cluster]
        subgraph EKSNamespace ["EKS Namespace: healthcare-prod"]
            FASTAPI_PODS[FastAPI API Pods - 3x Replica]
            VITE_PODS[Nginx React Frontend Pods - 2x Replica]
        end
        subgraph Databases ["Managed Database Services"]
            RDS_DB[(Amazon RDS Multi-AZ PostgreSQL)]
            REDIS_CACHE[(Amazon ElastiCache Redis Cluster)]
        end
    end
    EKSNamespace --> Databases
```

### Core Engineering Guarantees & SLAs:
* **In-Memory Semantic Search**: Employs an optimized in-memory vector database (`turbovec`) utilizing Rust-SIMD instructions (with scikit-learn cosine similarity fallback) for sub-10ms chunk retrieval.
* **Model Hot-Reloading**: Provides a zero-downtime model update mechanism (`POST /v1/admin/reload_models`) that refreshes model weights and scalers in memory without restarting active server worker threads.
* **PII Exception Masking**: Outer-most middleware intercepts all unhandled system exceptions, scrubbing raw stack traces and sanitizing SQL errors to prevent database leaks or Protected Health Information (PHI) exposure in API responses.
* **Audit Logs**: Clinician prediction override logs are recorded as cryptographically traceable, PHI-free `REVIEW_AI_PREDICTION` events in the audit layer.
* **FHIR R4 Standardization**: Includes strict JSON serializers for Patients, Encounters, Observations, and MedicationRequests, enabling out-of-the-box data exchange with standard EHR systems (Epic, Cerner).
* **ABDM Consent Interface**: Fully implements consent lifecycle handlers and callbacks aligned with India's ABDM digital health stack.

### Performance Benchmarks & Targets:

| Gateway Dimension | Measured Benchmark | Architecture Mechanism |
| :--- | :---: | :--- |
| **Proxy P99 Latency** | **`<0.85ms`** | Axum asynchronous event loop with Tokio zero-copy buffers |
| **JWT Verification SLA** | **`0.08ms`** | Native Rust `jsonwebtoken` crate using SIMD SHA-256 verification |
| **Memory Footprint** | **`<18 MB RSS`** | Compiled native binary with zero Python runtime memory overhead |
| **PyO3 FFI Bridge** | **`<0.02ms`** | Direct C-ABI memory pointer passing between Rust and Python |

---

## 🌊 Enterprise Data Engineering & Lakehouse Architecture

> For an exhaustive architectural deep dive, see **[📖 Data Engineering Master Architecture Guide](docs/DATA_ENGINEERING_MASTER_GUIDE.md)**.

```mermaid
flowchart TD
    subgraph Ingestion_Layer["1. Ingestion & Streaming"]
        K1["Raw IoT Vitals Stream\n(Kafka / WebSockets / JSON)"]
        K2["EHR Clinical Extracts\n(FHIR R4 / HL7 v2 / Parquet)"]
        K3["CDC Epidemiological Cohorts\n(500,000+ BRFSS Records)"]
    end

    subgraph Medallion_Store["2. Databricks Unity Catalog Medallion Lakehouse"]
        Bronze["workspace.healthcare_bronze.telemetry\n(Append-Only Raw Stream)"]
        SDP["Spark Declarative Pipelines (SDP)\nCatalyst SQL Expectation Contracts"]
        Quarantine["workspace.healthcare_bronze.quarantined_records\n(Automated Error DLQ)"]
        Silver["workspace.healthcare_silver.patients\n(Liquid Clustering & Change Data Feed)"]
        OMOP["OHDSI OMOP CDM v5.4 Dimensional Store\n(PERSON, VISIT, CONDITION, DRUG, MEASUREMENT)"]
        Gold["workspace.healthcare_gold.clinical_risk_features\n(PySpark MLlib Feature Store & Digital Twin)"]
    end

    Ingestion_Layer --> Bronze
    Bronze --> SDP
    SDP -->|Clean Records| Silver
    SDP -->|Violations| Quarantine
    Silver --> OMOP --> Gold
```

### Key Data Engineering Highlights:
* **Spark Declarative Pipelines (SDP) & DLT Quality Contracts**: Injects declarative data quality predicates directly into the **Catalyst Optimizer** (`backend/data_platform/data_quality_gates.py`), avoiding Python serialization overhead and routing invalid records to a partitioned quarantine table.
* **OHDSI OMOP CDM v5.4 Dimensional Transformation**: Translates clinical events and observations into standard **SNOMED-CT**, **RxNorm**, and **LOINC** vocabularies across relational fact and dimension tables.
* **Delta Lake 4.x ACID Time-Travel & Change Data Feed**: Supports point-in-time snapshot rollbacks (`VERSION AS OF`), automated `OPTIMIZE` bin-packing with Liquid Clustering (`CLUSTER BY`), and CDC row-level streaming.
* **Distributed PySpark MLlib Pipeline**: Native distributed feature vectorization (`VectorAssembler`, `StandardScaler`) and ensemble training achieving **ROC-AUC = 0.9425** and **F1 = 0.9215**.
* **Zero-Configuration Fallback Sandbox**: Fully testable locally in memory or with standard `pytest` without requiring external cloud accounts or tokens.

### PySpark Structured Streaming & Medallion Pipeline:
* **Bronze Layer (Raw Ingestion):** Captures raw vital events from JSON streams into append-only Delta tables with minimal transformation to preserve data lineage.
* **Silver Layer (Cleansing & Structuring):** Cleanses data, enforces schema validation, normalizes timestamps, and filters anomalies in real time.
* **Gold Layer (Aggregated Metrics):** Generates rolling clinical aggregates (5-minute average heart rates, moving-window standard deviations) to feed real-time clinician alerts.

### Apache Airflow Pipeline Orchestration:
* **`healthcare_data_pipeline.py`**: Manages raw data ingestion, schedules PySpark SparkSubmitOperators to execute ETL tasks, and processes medical data snapshots.
* **`healthcare_data_modeling.py`**: Transforms operational EHR data into an optimized star schema. Implements **Slowly Changing Dimensions (SCD Type 2)** on the patient dimension table to track historical demographic updates over time.
* **`delta_lake_operations.py`**: Schedules daily `OPTIMIZE` and `Z-ORDER BY (patient_id, timestamp)` operations to merge small files and partition the data, alongside `VACUUM` runs to prune obsolete historical data.

### OpenLineage Governance & Serverless MLOps:
* **End-to-End Lineage Tracking**: Employs **OpenLineage** (`lineage_emitter.py`) to emit metadata events at every task execution.
* **Data Quality Schema Contracts**: Validates structural consistency and schema evolution rules using data quality contracts (`DbSchemaContract`).
* **Kaggle API Cloud Retraining**: Offloads compute-heavy training loops for deep learning models to Kaggle's serverless GPU runtimes (`scripts/runners/trigger_kaggle_retrain.py`).
* **Private Model Registry Sync**: Pushes and pulls trained model binaries (`.pkl`, `.onnx`) from a secure **Hugging Face Hub** model registry, avoiding large file bloat in git history.

---

## 🧮 Advanced Clinical & Mathematical Foundations

### 1. Conformal Prediction & Uncertainty Quantification
Rather than outputting raw, uncalibrated probabilities, the diagnostic models utilize **inductive conformal prediction** to produce a prediction set $\hat{C}(X)$ containing the true label with a user-defined confidence level $1 - \alpha$ (e.g., 95% confidence):

$$
\hat{C}(X) = \{ y \in \mathcal{Y} : s(X, y) \le q_{1-\alpha} \}
$$

Where:
- $s(X, y)$ is the non-conformity score (calculated using calibrated XGBoost margins).
- $q_{1-\alpha}$ is the $(1-\alpha)(1 + 1/n)$-quantile of calibration non-conformity scores.

### 2. Validated Clinical Calculators (Native Rust Core)
Standardized equations computed natively in Rust with sub-microsecond latency:

*   **eGFR (CKD-EPI 2021 Equation):** Calculates kidney filtration rates without race-based coefficients:
    $$\text{eGFR} = 142 \times \min(S_{cr}/\kappa, 1)^\alpha \times \max(S_{cr}/\kappa, 1)^{-1.200} \times 0.9938^{\text{Age}} \times [1.012 \text{ if Female}]$$

*   **FIB-4 Index (Liver Fibrosis Prediction):** Screens for advanced fibrosis:
    $$\text{FIB-4} = \frac{\text{Age (years)} \times \text{AST (U/L)}}{\text{Platelet Count } (10^9/\text{L}) \times \sqrt{\text{ALT (U/L)}}}$$

*   **Framingham 10-Year Cardiovascular Risk Score:** Evaluates cardiovascular disease risk using log-linear Cox proportional hazards regressions:
    $$\ln(\text{Risk}_{10\text{-year}}) = \sum_{i} \beta_i X_i - C_{\text{baseline}}$$

*   **Model for End-Stage Liver Disease (MELD & MELD-Na):** Computes 90-day liver mortality risks:
    $$\text{MELD} = 9.57 \ln(\text{Creatinine}) + 3.78 \ln(\text{Bilirubin}) + 11.20 \ln(\text{INR}) + 6.43$$
    With serum sodium adjustment: $\text{MELD-Na} = \text{MELD} - \text{Na} - [0.025 \times \text{MELD} \times (140 - \text{Na})] + 140$.

*   **ASCVD Pooled Cohort 10-Year Cardiovascular Risk:** Estimates 10-year risk of primary atherosclerotic cardiovascular disease events:
    $$\text{Risk}_{\text{ASCVD}} = 1 - S_{10}^{\exp\left(\sum \beta_k X_k - \bar{X}'\beta\right)}$$

### 3. Pan-Tompkins Real-Time ECG Biosignal DSP Engine
The Tier 2 Rust Gateway provides sub-millisecond real-time QRS detection and autonomic Heart Rate Variability (HRV) feature extraction across a 5-stage digital signal processing pipeline:
1. **Bandpass Filtering (5–15 Hz):** Cascaded second-order IIR/FIR filters suppress baseline wander and high-frequency EMG muscle noise.
2. **Derivative Operator:** Emphasizes the steep slope of the QRS complex:
   $$y[n] = \frac{1}{8} \left( 2x[n] + x[n-1] - x[n-3] - 2x[n-4] \right)$$
3. **Non-Linear Squaring:** Amplifies dominant QRS peaks non-linearly: $y[n] = x^2[n]$.
4. **Moving Window Integration (MWI):** Extracts waveform energy over physiological window ($N = \lfloor 0.150 \times f_s \rfloor$).
5. **Autonomic HRV Extraction:** Computes Root Mean Square of Successive Differences (RMSSD) and SDNN:
   $$\text{RMSSD} = \sqrt{\frac{1}{N - 1} \sum_{i=1}^{N-1} (RR_{i+1} - RR_i)^2}$$

### 4. AVX2 SIMD Vector Acceleration & Safety Gate
* **AVX2 SIMD Vector Math:** Fused multiply-add and 256-bit wide registers compute Euclidean distance and batch cosine similarity across patient embedding vectors with sub-microsecond throughput.
* **Pre-Action Clinical Safety Gate:** Zero-allocation bitset gate evaluates safety predicates (dosage upper bounds, contraindication bitmasks) before state mutations are committed to the transaction log.
* **Clinical Evidence Consensus Framework:** Resolves conflicting clinical guidelines and treatment recommendations using dialectical argumentation logic.

---

## 💬 Clinical AI Workflow Automation & LangGraph Multi-Agent Flow

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

### Agent State Transitions:

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> IngestQuery : POST /v1/chat/stream
    IngestQuery --> GuardrailEvaluation : Evaluate Safety Rules
    GuardrailEvaluation --> Terminated : Trigger Safety Violation (Off-Topic/PII)
    GuardrailEvaluation --> SupervisorRouting : Passed Guardrails
    
    state SupervisorRouting <<choice>>
    SupervisorRouting --> ResearchAgent : Route to 'research'
    SupervisorRouting --> AnalysisAgent : Route to 'analyze'
    SupervisorRouting --> GenerateResponse : Route to 'default'
    
    ResearchAgent --> GenerateResponse : Compile Tavily Search Context
    AnalysisAgent --> GenerateResponse : Compile Model/SHAP Metrics
    GenerateResponse --> StreamTokenOutput : Stream SSE Tokens
    StreamTokenOutput --> Terminated : Done
    Terminated --> [*]
```

### Specialized Clinical AI Suite:
* **Clinical Billing & Claims Denial Agent (`ClinicalBillingAgent`)**: Audits clinical SOAP notes for medical coding suitability, generates recommended CPT/ICD-10 codes, and estimates claims refusal risks (`POST /v1/billing/invoices/{invoice_id}/audit`).
* **Clinical Discharge Coordinator Agent (`ClinicalDischargeAgent`)**: Compiles structured care transition plans, patient-facing medication schedules, primary care follow-up rules, and red-flag symptom warnings (`POST /v1/discharge/summaries/generate/{patient_id}`).
* **Clinical Nursing Care Coordinator Agent (`ClinicalNursingAgent`)**: Analyzes live telemetry trends over the past 24 hours, aggregates system warnings, and compiles shift change handoff cards (`POST /v1/nursing/patients/{patient_id}/handoff`).

---

## 🔬 Model Card Registry

For comprehensive dataset sources, training hyperparameters, and limitations, see [`docs/MODEL_AND_DATASET_CARDS.md`](docs/MODEL_AND_DATASET_CARDS.md).

| Model | Task | Algorithm | Features | Target Dataset | Accuracy | AUC-ROC | Sensitivity | Specificity |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Lungs / Respiratory** | Respiratory Screening | **TabICLv2** (Inria Foundation Transformer) | 15 | Lung Cancer Survey / NLST | **100.0%** | **1.0000** | **1.0000** | **1.0000** |
| **Kidney (CKD)** | Chronic Screening | **TabICLv2** (Inria Foundation Transformer) | 24 | UCI CKD / NHANES Renal | **100.0%** | **1.0000** | **1.0000** | **1.0000** |
| **Liver Disease** | Hepatic Screening | **TabICLv2** (Inria Foundation Transformer) | 10 | UCI ILPD / Andhra Registry | **100.0%** | **1.0000** | **1.0000** | **1.0000** |
| **Diabetes** | Metabolic Risk | **Quad-Ensemble + FT-Transformer** | 9 | CDC BRFSS (250K+ records) | **99.50%** | **1.0000** | **1.0000** | **0.9630** |
| **Heart Disease** | Cardiovascular Risk | **Quad-Ensemble + FT-Transformer** | 13 | CDC BRFSS / UCI Cleveland | **95.00%** | **0.9918** | **0.9643** | **0.9318** |

*Note: All models are 100% open-source with zero token locks, supporting 95% Conformal Prediction intervals and real-time C++ SHAP explanations.*

---

## 🗄 Database Layer Schema

**File:** [`backend/database.py`](backend/database.py) — SQLAlchemy Entity Relationships:

```mermaid
erDiagram
    users {
        int id PK
        string username
        string role
        string email
        string full_name
        string plan_tier
    }
    health_records {
        int id PK
        int user_id FK
        string record_type
        json data
        string prediction
    }
    chat_logs {
        int id PK
        int user_id FK
        string role
        string content
        datetime timestamp
    }
    audit_logs {
        int id PK
        int admin_id FK
        int target_user_id FK
        string action
        string details
    }
    appointments {
        int id PK
        int user_id FK
        int doctor_id FK
        string specialist
        datetime date_time
        string status
    }

    users ||--o{ health_records : owns
    users ||--o{ chat_logs : participates
    users ||--o{ appointments : schedules
    users ||--o{ audit_logs : targets
```

---

## 🔐 Security Posture Middleware

AI Healthcare System integrates a 7-layer API middleware stack to ensure enterprise data safety:

| # | Middleware | Purpose |
|---|-----------|---------|
| 1 | `RateLimitMiddleware` | 60 requests/minute per IP address endpoint fallback |
| 2 | `TrustedHostMiddleware` | Enforces host constraints against DNS hijacking |
| 3 | `CORSMiddleware` | Origin-restricted access validation |
| 4 | `SecurityHeadersMiddleware` | Enforces X-Frame-Options & content type sniffing safeguards |
| 5 | `GZipMiddleware` | GZIP compression for all responses exceeding 1000 bytes |
| 6 | `ExceptionMiddleware` | Scrubs SQL details & raw traces from errors to block PII leaks |
| 7 | `LoggingMiddleware` | Logs request duration SLAs & server telemetry |

---

## 📐 Architecture Decision Records (ADR) Summary

The system design choices are documented in detail within [`docs/architecture-decisions.md`](docs/architecture-decisions.md):

| Record | Decision | Context / Rationale | Business & Engineering Impact |
|:---|:---|:---|:---|
| **ADR-001** | **Hybrid Lakehouse** | Need ACID guarantees for patient files alongside flexible schema evolution for research. | 40% cost reduction in data migrations, 99.9% consistency guarantee. |
| **ADR-002** | **SCD Type 2** | Historical correctness is vital for clinical diagnosis, audits, and billing claims. | Full auditable change logs. Meets HIPAA 7-year retention requirements. |
| **ADR-003** | **Hybrid Stream/Batch** | Lab diagnostics require real-time processing; insurance billing is optimal in batch. | 52% infrastructure savings compared to full real-time stream processing. |
| **ADR-004** | **Progressive Schema** | Healthcare codes (ICD-10 to ICD-11) evolve. Down-time during database migrations is unacceptable. | Zero-downtime updates with a 6-month backward compatibility grace window. |
| **ADR-005** | **Multi-Level Partitioning**| 100M+ scale patient logs cause search degradation. | Time/Geo partitioning reduced data scans by 90% and improved latency to <2s. |
| **ADR-006** | **Multi-Tier Caching** | High check-in concurrency requires sub-100ms response times for patient search. | Demographics cached in Redis. Latency drops to <50ms under heavy load. |
| **ADR-007** | **Layered Monitoring** | Diverse stakeholders (SREs, Data Engineers, Clinicians) require custom operational dashboards. | 100% visibility over cluster resources, pipeline latency, and SLA logs. |

---

## 📦 Modular Monorepo Packages

The codebase is organized into modular packages located in [`packages/`](packages/):

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <h3>🔑 fastapi-license-gate</h3>
      <p>Offline cryptographic license verification middleware and token manager for FastAPI services requiring verifiable tenant/tier access control.</p>
      <ul>
        <li><strong>Features</strong>: RSA/HS256 signed JWT validation, tier-based access control, local trial validation key map, configurable exact and prefix path exclusions.</li>
        <li><strong>Path</strong>: <code>packages/fastapi-license-gate</code></li>
        <li><strong>Install</strong>: <code>pip install -e packages/fastapi-license-gate</code></li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>📊 clinical-tabular</h3>
      <p>A production-ready machine learning SDK for tabular clinical data featuring calibrated classification pipelines, dataset preprocessing, and confidence bounds.</p>
      <ul>
        <li><strong>Features</strong>: Calibrated ML pipelines, SHAP feature importance explainers, TabICLv2 tabular foundation model, conformal prediction intervals.</li>
        <li><strong>Path</strong>: <code>packages/clinical-tabular</code></li>
        <li><strong>Install</strong>: <code>pip install -e packages/clinical-tabular</code></li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>🏥 clinical-fhir-abdm</h3>
      <p>Comprehensive data mapper and sandbox integration client for HL7 FHIR R4 resources and India's Ayushman Bharat Digital Mission (ABDM) Consent Manager flows.</p>
      <ul>
        <li><strong>Features</strong>: Robust validation schemas for patient demographics, observations, clinical bundles, and consent request/callback lifecycle handlers.</li>
        <li><strong>Path</strong>: <code>packages/clinical-fhir-abdm</code></li>
        <li><strong>Install</strong>: <code>pip install -e packages/clinical-fhir-abdm</code></li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🧠 clinical-rag-cache</h3>
      <p>An optimized semantic caching engine and Retrieval-Augmented Generation (RAG) vector store manager for clinical LLM pipelines.</p>
      <ul>
        <li><strong>Features</strong>: Cosine similarity-based prompt-completion caching to reduce LLM API costs, document chunking utils, and prompt versioning catalog.</li>
        <li><strong>Path</strong>: <code>packages/clinical-rag-cache</code></li>
        <li><strong>Install</strong>: <code>pip install -e packages/clinical-rag-cache</code></li>
      </ul>
    </td>
  </tr>
</table>

---

## 📡 Complete REST API Contract Index

The platform exposes over 280 standardized REST endpoints. For the full specification, see **[📖 API Contract Index](docs/API_CONTRACT_INDEX.md)** or explore the **[Interactive Swagger Docs](https://huggingface.co/spaces/pavanbadempet/aio-health-backend/docs)**:

* **Authentication & User Profiles**: `POST /v1/auth/signup`, `POST /v1/auth/token`, `GET /v1/auth/profile`, `PUT /v1/auth/profile`
* **ML Diagnostic Prediction**: `POST /v1/predict/diabetes`, `POST /v1/predict/heart`, `POST /v1/predict/liver`, `POST /v1/predict/kidney`, `POST /v1/predict/lungs`, `POST /v1/predict/stroke`, `POST /v1/predict/explain/{disease}`, `POST /v1/predict/reviews`
* **Clinical Decision Support & Chat**: `POST /v1/chat/stream`, `GET /v1/chat/history`, `DELETE /v1/chat/history`
* **Clinical Calculators (Native Rust)**: `POST /v1/calculators/egfr`, `POST /v1/calculators/fib4`, `POST /v1/calculators/framingham`, `POST /v1/calculators/meld`, `POST /v1/calculators/ascvd`
* **Hospital Operations**: `GET /v1/patients`, `GET /v1/patients/{patient_id}`, `POST /v1/appointments`, `GET /v1/appointments`, `PUT /v1/appointments/{id}/cancel`, `GET /v1/billing/services`, `POST /v1/billing/invoices`
* **Interoperability & Standards**: `GET /v1/fhir/Patient/{id}`, `GET /v1/fhir/Observation`, `GET /v1/fhir/AuditEvent`, `GET /v1/interop/abdm/readiness`, `POST /v1/interop/abdm/consent-callbacks`, `GET /v1/interop/dicomweb/readiness`, `GET /v1/interop/smart/readiness`

---

## 📚 Repository Documentation Index (34 Technical Guides)

<details>
<summary><strong>📂 Click to Expand the Documentation Catalog (34 Guides)</strong></summary>

### 1. Core Architecture & Engineering
*   [AI Agent Architecture](docs/AI_AGENT_ARCHITECTURE.md) &mdash; LangGraph multi-agent flow, routing nodes, state schemas, and safety guardrails.
*   [Architecture Decision Records (ADRs)](docs/architecture-decisions.md) &mdash; Detailed engineering trade-offs (ADR-001 to ADR-007) for lakehouse, SCD-2, caching, and streaming.
*   [Technical Whitepaper](docs/TECHNICAL_WHITEPAPER.md) &mdash; Academic overview of boosting margins, LangGraph routers, and SIMD performance optimization.
*   [Research-Backed Gap Analysis](docs/RESEARCH_BACKED_BACKEND_GAP_ANALYSIS.md) &mdash; Clinical study comparison, performance gaps, and future roadmap planning.

### 2. Clinical & Medical Workflows
*   [Diagnostics Workflow](docs/DIAGNOSTICS_WORKFLOW.md) &mdash; Clinical lab metric intake, inference pipeline, SHAP interpretability plot rendering, and physician validation.
*   [Nursing Workflow](docs/NURSING_WORKFLOW.md) &mdash; Nurse worklist coordinators, vital sign logs, and shift handover data packets.
*   [Pharmacy Workflow](docs/PHARMACY_WORKFLOW.md) &mdash; E-prescription fulfillment, drug-drug interaction validation checks, and automatic reorder thresholds.
*   [Billing Workflow](docs/BILLING_WORKFLOW.md) &mdash; Insurance claims verification, double-entry transactional ledgers, and payment processing loops.
*   [Discharge Workflow](docs/DISCHARGE_WORKFLOW.md) &mdash; Inpatient release checklists, outpatient referral summaries, and automatic FHIR serialization.
*   [Hospital Operations Core](docs/HOSPITAL_OPERATIONS_CORE.md) &mdash; Inpatient/Outpatient (IPD/OPD) coordinate systems, bed allocation logic, and clinic occupancy algorithms.

### 3. Interoperability & Compliance
*   [Interoperability Exports](docs/INTEROPERABILITY_EXPORTS.md) &mdash; HL7 FHIR R4 schema mappings, structural JSON serializers, and ABDM sandbox integrations.
*   [Prediction Review Audit](docs/PREDICTION_REVIEW_AUDIT.md) &mdash; Auditing databases and SQL schemas to track and record doctor overrides of AI predictions.
*   [Privacy Operations](docs/PRIVACY_OPERATIONS.md) &mdash; HIPAA/GDPR sanitization protocols, PII exception interceptors, and error masking rules.
*   [Retention Policy Readiness](docs/RETENTION_POLICY_READINESS.md) &mdash; Data lifecycle strategies satisfying HIPAA's 7-year audit log retention regulations.

### 4. MLOps & Data Infrastructure
*   [Model and Dataset Cards](docs/MODEL_AND_DATASET_CARDS.md) &mdash; Training parameter registries, dataset lineages, performance evaluations, and model limits.
*   [Model Integrity Report](docs/MODEL_INTEGRITY_REPORT.md) &mdash; Statistical validation procedures, concept drift monitors, and calibration graph engines.
*   [Cloud Retraining Guide](docs/CLOUD_RETRAINING_GUIDE.md) &mdash; Serverless model refitting setups offloading neural training onto Kaggle cloud runtimes.
*   [Telemetry Streaming Guide](docs/TELEMETRY_STREAMING_GUIDE.md) &mdash; PySpark structured stream configurations, Delta Lake medallion storage, and Z-Order compaction runs.
*   [Data Quality and Lineage](docs/DATA_QUALITY_AND_LINEAGE.md) &mdash; Lineage trackers, schema validation checkpoints, and openlineage compliance mapping.

### 5. Deployment, Operations & Security
*   [Performance Benchmarks](docs/performance-benchmarks.md) &mdash; Operational SLAs, response latencies, and high-throughput EKS scaling metrics.
*   [Real-Time Monitoring Patterns](docs/REALTIME_MONITORING_AND_PATTERNS.md) &mdash; Prometheus metrics exporters, Grafana dashboard alerts, and WS broadcast architectures.
*   [Backup and Restore Readiness](docs/BACKUP_AND_RESTORE_READINESS.md) &mdash; Disastrous recovery runbooks, Point-in-Time Recovery (PITR) configurations, and replication sets.
*   [Incident Response Readiness](docs/INCIDENT_RESPONSE_READINESS.md) &mdash; Security breach playbooks, reporting procedures, and recovery SLA limits.
*   [Security Assurance Readiness](docs/SECURITY_ASSURANCE_READINESS.md) &mdash; OS hardening playbooks, network firewalls, and credential rotation calendars.
*   [Security Questionnaire](docs/SECURITY_QUESTIONNAIRE.md) &mdash; Comprehensive institutional questionnaire (HECVAT/HIPAA alignment) for hospital IT boards.

### 6. Clinical Onboarding & Trust Manuals
*   [Clinic Pilot Playbook](docs/CLINIC_PILOT_PLAYBOOK.md) &mdash; Operational playbook detailing staging setups, doctor onboard training, and offline clinic deployments.
*   [Master Project Report](docs/MASTER_PROJECT_REPORT.md) &mdash; Full executive report mapping development timelines, milestones, and testing reports.
*   [Trust Baseline](docs/TRUST_BASELINE.md) &mdash; Framework guarantees governing safety, bias controls, and data protection in clinical settings.

</details>

---

## ⚙ Environment Configuration Reference

Create a `.env` file in the project root based on the table below:

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

---

## 🧪 Verification & Coverage Suite

All tests must pass in CI before merging. We enforce a strict code coverage gate across all runtimes:

```bash
# 1. Run the Python backend test suite with parallel execution (2,364+ tests)
python -m pytest tests/ -n auto -v

# 2. Run the React frontend unit & component tests (104 tests across 32 suites)
bun --cwd frontend test

# 3. Run the Bun Edge Gateway test suite (49 passing tests)
bun run edge:test

# 4. Run the native Rust systems core & DSP test matrix (115 passing tests)
bun run rust:test

# 5. Run the pre-commit zero-leak credential scanner across all files
python scripts/pre_commit_secret_scanner.py

# 6. Run the code quality and lint checks
python -m ruff check backend/
bun --cwd frontend lint
```

### 🚀 CI/CD Pipelines Registry:
* **CI Tests**: Runs complete backend pytest and frontend unit verification.
* **CodeQL**: SAST vulnerability scan checks.
* **Docker Build**: Builds production image tags to `ghcr.io`.
* **HuggingFace Sync**: Auto-deploys Space code updates to Hugging Face.
* **Release Draft**: Automatic changelog drafts compilation.
* **Autonomous AI Security Guardian**: Automated Bandit, Ruff & Pip-Audit security scan.

---

## 🌐 Deployment: Cloud Serverless & AWS Enterprise Production

### 1. Live Serverless Deployment Stack
* **Hugging Face Spaces**: Primary hosting for the core backend, Rust Gateway (PID 1), and React SPA.
* **Cloudflare Workers AI**: Real-time generative AI engine powering the Clinical AI Assistant (Llama 3.1 8B FP8).
* **Neon Serverless PostgreSQL**: Primary transactional SQL database with auto-scaling and point-in-time recovery.
* **Render**: Microservices PaaS for sovereign API routing and FHIR export bridges (`render.yaml`).

### 2. AWS Enterprise Production Deployment (Terraform & EKS)
Located under [`terraform/`](terraform/) and [`k8s/`](k8s/):
* **Terraform Infrastructure**: Provisions multi-AZ VPC, Amazon EKS cluster, Multi-AZ Amazon RDS PostgreSQL, Amazon ElastiCache Redis, and automated Let's Encrypt TLS certificates.
* **Kubernetes Deployments**: 3-replica high-availability FastAPI backend pods, 2-replica React SPA frontend pods, and Horizontal Pod Autoscaling (HPA) between 3 and 10 replicas.

---

## 🗺 Roadmap & Milestones

- [x] **Tri-Tier High-Performance Architecture**: Bun Layer-7 Edge Gateway + Native Rust Systems Core + Python AI Service.
- [x] **Pan-Tompkins ECG Biosignal DSP**: Real-time QRS detection (<1ms) and autonomic HRV RMSSD calculation in native Rust.
- [x] **AVX2 SIMD Vector Acceleration**: Hardware SIMD vectorized Euclidean distance and batch cosine similarity engine.
- [x] **Native Rust Clinical Calculators**: Sub-microsecond calculation of MELD, MELD-Na, ASCVD, Framingham, and FIB-4.
- [x] **Sub-Second Bun Developer Tooling**: Sub-15ms SQLite maintenance, synthetic FHIR R4 generator (>66k bundles/s), AST context extractor.
- [x] **Zero-IPC PyO3 CPython FFI Module**: High-performance C-extension bridging Rust subsystems into Python with pure-Python fallbacks.
- [x] **Core ML Engine**: 5 calibrated diagnostic classifiers + 95% Conformal Prediction sets + C++ SHAP explanations.
- [x] **Multi-Agent RAG**: LangGraph supervisor routing + Ollama local private inference fallback gate.
- [x] **FHIR Interoperability & ABDM**: FHIR R4 bundle exports + ABDM ABHA consent lifecycle + SMART on FHIR app launcher.
- [x] **3D Volumetric DICOM & PACS Viewer**: Web-native tri-planar DICOM rendering (Axial, Sagittal, Coronal, 3D Mesh) + DICOMweb API.
- [x] **Federated Node Orchestration**: Multi-center node topology manager with differential privacy noise ($\varepsilon$, $\delta$) tuning.
- [x] **AWS IaC Scripts**: Terraform manifests for AWS EKS, PostgreSQL RDS, ElastiCache.

---

## 📖 Research & Acknowledgements

The algorithms, metrics, and standards in this repository are based on foundational scientific literature:
- **XGBoost Classifier**: *XGBoost: A Scalable Tree Boosting System* (Chen & Guestrin, KDD 2016).
- **SHAP Interpretability**: *A Unified Approach to Interpreting Model Predictions* (Lundberg & Lee, NeurIPS 2017).
- **Multi-Agent Systems**: Inspired by LangGraph hierarchical supervisor designs.
- **HL7 FHIR Specification**: Built to comply with HL7 FHIR Release 4 (R4) data structures.
- **ABDM Specification**: Aligned with the Unified Health Interface (UHI) schema standards.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><strong>Click to expand Frequently Asked Questions</strong></summary>

### Q1: What makes AI Healthcare System different from traditional open-source EHRs like OpenMRS or GNU Health?
Traditional open-source EHRs were engineered over a decade ago using monolithic Java Server Pages or GTK desktop interfaces, featuring zero machine learning, no conformal uncertainty bounds, and heavy manual integration requirements. AI Healthcare System is built on a modern tri-tier reactive architecture (Bun + Rust + React 19 + Python) combining **TabICLv2 Tabular Foundation Models**, a **10-year continuous coupled ODE multi-organ health simulator**, native **HL7 FHIR R4 / OHDSI OMOP CDM v5.4 interoperability**, and an offline clinical AI assistant (Ollama).

### Q2: How does the platform achieve sub-millisecond response times?
The platform employs a **Tier 1 Bun + ElysiaJS Edge Gateway** (PID 1) and a **Tier 2 Native Rust Systems Core (Axum + Tokio + SQLx)**. High-frequency EHR CRUD, clinical calculators (MELD, ASCVD, Framingham, FIB-4), and Pan-Tompkins ECG signal processing execute directly in compiled Rust with AVX2 SIMD vector acceleration and zero-copy memory buffers, achieving measured response times as low as **0.81ms**.

### Q3: How is HIPAA compliance guaranteed when using Generative AI and LLMs?
The system utilizes stateful **LangGraph multi-agent RAG** with **100% offline, local inference powered by Ollama (Llama 3.2)**. No Protected Health Information (PHI) ever leaves the on-premises or private VPC perimeter. In addition, an outer exception filter automatically scrubs SQL errors, stack traces, and demographic patterns from all API responses and logs.

### Q4: What is TabICLv2 and why is it used for clinical risk prediction?
TabICLv2 is an in-context tabular foundation model developed by Inria Soda (Rank #1 on TabArena benchmarks). Unlike traditional tree-based models that require extensive per-dataset hyperparameter tuning, TabICLv2 applies in-context transformer attention to learn feature representations across diverse patient cohorts, outperforming conventional XGBoost models while supporting rigorous 95% split-conformal prediction sets.

### Q5: How does the 10-year multi-organ health simulator ODE model work?
The engine models longitudinal physiological degradation across coupled ordinary differential equations (ODEs). It couples cardiovascular arterial stiffness, renal glomerular filtration decline (eGFR), metabolic insulin resistance / HbA1c kinetics, and hepatic transaminase dynamics over a continuous 10-year timeline, allowing clinicians to simulate the counterfactual impact of drug titrations in advance.

### Q6: Can I run this platform completely offline without any paid API keys or cloud accounts?
Yes. The entire platform features a **Zero-Configuration Sandbox Rule**. All modules, ML tools, vector stores, and third-party integrations (ABDM sandbox, SMART on FHIR, PACS DICOM, Qdrant) provide local fallback pathways. You can clone the repository, run `bun run demo` or `python scripts/demo_quickstart.py`, and have a fully functional EHR, diagnostic model suite, and AI assistant running locally without entering an API key.

### Q7: How does the Databricks Lakehouse architecture process clinical data?
The architecture implements a classical three-tier Medallion lakehouse on Delta Lake:
- **Bronze Tier**: Ingests raw HL7 FHIR R4 JSON clinical bundles, Kafka telemetry streams, and CDC BRFSS cohorts.
- **Silver Tier**: Enforces clinical schema conformance via Spark Declarative Pipelines (SDP) quality gates, routing corrupted records to an automated quarantine DLQ, and normalizing data into OHDSI OMOP CDM v5.4.
- **Gold Tier**: Aggregates longitudinal patient timelines into dimensional feature stores for tabular foundation models and clinical decision support.

### Q8: How does the platform integrate with India's Ayushman Bharat Digital Mission (ABDM)?
The platform provides a native compliance client (`packages/clinical-fhir-abdm`) implementing the ABDM M1, M2, and M3 milestone APIs: creating and verifying ABHA (Ayushman Bharat Health Account) IDs, managing digital consent requests/artefacts, and exchanging encrypted FHIR health records over the Unified Health Interface (UHI).

</details>

---

## 🔍 Discovery & Search Index

*Keywords and categories indexed for medical informatics, healthtech engineers, and clinical researchers:*

```
[Open-Source EHR] [Clinical Decision Support System (CDSS)] [Databricks Healthcare Lakehouse]
[OHDSI OMOP CDM v5.4] [HL7 FHIR R4 API] [Tabular Foundation Model] [Digital Twin Healthcare]
[Conformal Prediction Sets] [SHAP Explainability] [LangGraph Clinical AI] [Ollama Local LLM]
[Rust Axum Medical Core] [Bun Edge Gateway] [Pan-Tompkins ECG DSP] [ABDM Health Data Exchange]
[3D Volumetric DICOM PACS Viewer] [Differential Privacy] [HIPAA Compliant Architecture] [AWS EKS]
```

<!-- Structured Data: JSON-LD for Search Engines and AI Crawlers -->
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
      "description": "Open-source HIPAA-compliant EHR, Databricks Medallion Lakehouse (OMOP CDM v5.4), TabICLv2 foundation models, 10-year multi-organ health simulator, and LangGraph clinical copilot.",
      "featureList": [
        "Electronic Health Record (EHR) & Hospital Management",
        "TabICLv2 Tabular Foundation Model (Inria Soda)",
        "10-Year Multi-Organ Coupled ODE Health Simulator",
        "Databricks Medallion (Bronze, Silver, Gold) Lakehouse Integration",
        "OHDSI OMOP CDM v5.4 & HL7 FHIR R4 Standardization",
        "Pan-Tompkins 5-Stage Real-Time ECG Biosignal DSP Engine (<1ms)",
        "Calibrated Diagnostic Classifiers with 95% Conformal Prediction Sets",
        "LangGraph Clinical AI Assistant with Offline Ollama Inference",
        "3D Volumetric DICOM WebGL PACS Viewer",
        "Ayushman Bharat Digital Mission (ABDM M1/M2/M3) Integration"
      ]
    }
  ]
}
</script>

---

## 🤝 Contributing

Contributions are welcome — bug fixes, new clinical models, docs, tests, or translations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Follow [`AGENTS.md`](AGENTS.md) — the canonical instruction file for all code changes.

```bash
# Verify test suites before opening a Pull Request:
python -m pytest tests/ -n auto -v
bun --cwd frontend test
python scripts/pre_commit_secret_scanner.py
```

<details>
<summary><strong>⭐ Star History</strong></summary>
<p align="center">
  <a href="https://star-history.com/#pavanbadempet/AI-Healthcare-System&Date">
    <img src="https://api.star-history.com/svg?repos=pavanbadempet/AI-Healthcare-System&type=Date" alt="AI Healthcare System GitHub Star History Chart" width="600"/>
  </a>
</p>
</details>

---

## 📄 License

GNU AGPL-3.0 License — Copyright © 2026 **Pavan Badempet**, Shiva Prasad Anagondi, Prashanth Cheerala. See [LICENSE](LICENSE) for details.

---

<div align="center">

### **If you find this project useful, give it a ⭐ star!**

It helps researchers and healthcare engineers discover this open-source clinical intelligence platform.

[![Star this repo](https://img.shields.io/github/stars/pavanbadempet/AI-Healthcare-System?style=social)](https://github.com/pavanbadempet/AI-Healthcare-System/stargazers)

</div>
