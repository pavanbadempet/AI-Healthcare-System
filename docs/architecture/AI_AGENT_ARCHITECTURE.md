# Clinical AI Platform Architecture — AI Healthcare System

> Comprehensive architecture specification for clinical intelligence, multi-agent workflows, diagnostic foundation models, and patient safety governance.

---

## 1. Architecture Overview

The AI Healthcare System architecture delivers privacy-preserving, auditable, and resilient clinical artificial intelligence across three foundational layers:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             CLINICAL APPLICATION LAYER                           │
│  React 19 Frontend  •  3D DICOM PACS  •  SMART on FHIR Launcher  •  ABDM Gateway │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTP / SSE / WebSockets
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                    HIGH-PERFORMANCE EDGE PROXY & ROUTING                         │
│       Rust Axum Gateway (PID 1)  •  PyO3 Zero-Copy FFI  •  Correlation Tracing   │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                     CLINICAL AI & ML INTELLIGENCE LAYER                          │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌────────────────────────┐ │
│  │  Multi-Tier Gateway   │ │ LangGraph Supervisor  │ │ TabICLv2 Foundation &  │ │
│  │  (Ollama/Gemini/Cloud)│ │ Multi-Agent Workflow  │ │ Quad-Ensembles + SHAP  │ │
│  └───────────────────────┘ └───────────────────────┘ └────────────────────────┘ │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌────────────────────────┐ │
│  │ Clinical Workflow     │ │ Medical RAG & Vector  │ │ Clinical Governance,   │ │
│  │ Agents (SOAP/Care/RN) │ │ Context Retrieval     │ │ Prompts & Model Cards  │ │
│  └───────────────────────┘ └───────────────────────┘ └────────────────────────┘ │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                       STORAGE, LAKEHOUSE & AUDIT LAYER                           │
│  PostgreSQL / SQLite WAL  •  Delta Lake Medallion  •  HIPAA Retention & Audit Logs│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Tier Clinical Inference Gateway (`backend/core_ai.py`)

All provider-backed generative AI and embedding calls route through a single, isolated gateway module with automatic tiered fallback:

```
Tier A: Local Ollama (Primary)     ──► Zero third-party network egress; prompts stay on-premise
Tier B: Cloud AI Fallback (Gemini) ──► Automatic failover when local daemon is unreachable
Tier C: Request-Level Cloud LLM   ──► Admin-authenticated fallback via secure headers
```

### Public Interface
External modules interact exclusively with the high-level functional API:
- `generate(prompt, system)`: Single-shot structured generation.
- `chat(messages, system)`: Multi-turn conversational consultation.
- `chat_stream(messages, system)`: Real-time Server-Sent Events (SSE) token streaming.
- `embed_text(text, task_type)`: Dense semantic embeddings for clinical RAG indexing.
- `generate_vision_content(prompt, image)`: Multimodal clinical imaging analysis.
- `is_available()`: Health check probe verifying gateway availability.

> [!IMPORTANT]
> No backend route or service may import third-party provider SDKs directly. All generative and embedding calls are encapsulated in `backend.core_ai`.

---

## 3. LangGraph Multi-Agent Clinical Decision Support (`backend/chat.py` & `backend/agent.py`)

Clinical consultation utilizes a stateful LangGraph multi-agent supervisor pattern to decompose complex patient inquiries:

```
                     ┌───────────────────────────┐
                     │ Patient Query + EHR State │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │  Clinical Supervisor Node │
                     └──────┬─────────────┬──────┘
                            │             │
              ┌─────────────┘             └─────────────┐
              ▼                                         ▼
   ┌───────────────────────┐                 ┌───────────────────────┐
   │ Medical Research Node │                 │ Diagnostic Data Node  │
   │ (RAG + Tavily Search) │                 │ (EHR Records & ML)    │
   └──────────┬────────────┘                 └──────────┬────────────┘
              │                                         │
              └─────────────┐             ┌─────────────┘
                            ▼             ▼
                     ┌───────────────────────────┐
                     │ Response Synthesizer Node │
                     │ (Safety Filter & Citation)│
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │ Stream SSE / REST Payload │
                     └───────────────────────────┘
```

- **Supervisor Node**: Evaluates user intent, determines whether external medical literature (Tavily), local RAG memory, or diagnostic ML predictions are required.
- **Medical Research Node**: Retrieves grounded evidence with full citation tracking and token-budget enforcement.
- **Diagnostic Node**: Ingests patient vital histories, lab results, and active risk models.
- **Synthesizer Node**: Applies clinical disclaimer guardrails, checks for emergency red flags, and constructs structured responses.

---

## 4. Diagnostic Foundation Models & ML Classifiers (`backend/prediction.py`)

Diagnostic prediction combines tabular foundation models with calibrated tree ensembles:

1. **TabICLv2 In-Context Tabular Foundation Model**:
   - Ranked #1 open-source foundation model on TabArena benchmarks (`tabicl>=2.1.1`).
   - Executes zero-shot in-context classification over clinical tabular datasets without cloud dependencies.
2. **Calibrated Quad-Ensemble Classifiers**:
   - Ensembles `XGBoost`, `LightGBM`, `CatBoost`, and `RandomForest` for five major chronic disease panels (Diabetes, Coronary Heart Disease, Liver Disease, Chronic Kidney Disease, Lung Cancer).
   - Calibrated via Platt Scaling and Isotonic Regression to output reliable posterior probabilities.
3. **95% Conformal Prediction Bounds**:
   - Generates non-empty prediction sets at guaranteed coverage thresholds (\(1 - \alpha = 0.95\)), providing clinicians with rigorous mathematical uncertainty intervals.
4. **C++ TreeSHAP Explainability**:
   - Generates real-time patient-specific feature attribution plots detailing the exact clinical biomarkers driving each risk calculation.

---

## 5. Specialized Clinical Workflow Agents (`backend/agents/`)

Domain-specific assistants handle operational tasks via deterministic structured prompting and Pydantic validation:

### 5.1 Clinical Billing & Coding Agent (`ClinicalBillingAgent`)
- **Module**: `backend/agents/billing_agent.py`
- **Endpoint**: `POST /v1/billing/invoices/{invoice_id}/audit`
- **Responsibilities**:
  - Parses clinical SOAP narratives and physician documentation.
  - Recommends appropriate ICD-10 diagnosis and CPT procedure codes.
  - Predicts claims denial risk (`LOW`, `MEDIUM`, `HIGH`) based on medical necessity criteria.
  - Detects missing clinical justifications before insurance submission.

### 5.2 Clinical Discharge Planning Agent (`ClinicalDischargeAgent`)
- **Module**: `backend/agents/discharge_agent.py`
- **Endpoint**: `POST /v1/discharge/summaries/generate/{patient_id}`
- **Responsibilities**:
  - Synthesizes patient demographics, telemetry vital trends, and diagnostic risk scores.
  - Formulates structured care transition plans, plain-language patient instructions, and follow-up schedules.
  - Flags post-discharge "red-flag" emergency symptoms requiring immediate medical evaluation.

### 5.3 Clinical Nursing Shift Handoff Agent (`ClinicalNursingAgent`)
- **Module**: `backend/agents/nursing_agent.py`
- **Endpoint**: `POST /v1/nursing/patients/{patient_id}/handoff`
- **Responsibilities**:
  - Ingests active patient conditions, 24-hour telemetry vital trends, and system alerts.
  - Formulates SBAR (Situation, Background, Assessment, Recommendation) nursing handoff summaries.
  - Prioritizes upcoming shift nursing interventions, medication administration schedules, and safety watch items.

---

## 6. Medical RAG & Context Retrieval (`backend/chat_context.py` & `backend/rag.py`)

Clinical conversational interactions are grounded in patient records and medical reference material:

```
Patient Query ──► Intent & Condition Classifier
                        │
                        ├──► Patient Demographics & Baseline Vitals
                        ├──► Condition-Specific Lab History (e.g. HbA1c, Creatinine)
                        ├──► Recent ML Diagnostic Risk Assessments
                        └──► Semantic Vector Chunks (SQLite Vector Store)
                        │
                        ▼
                Token Budget Truncation & Instruction Hierarchy Scrubbing
                        │
                        ▼
                Structured Clinical Prompt Context
```

- **Context Assembly**: `chat_context.py` builds deterministic context slices with token-budget enforcement to prevent context overflow.
- **Instruction Hierarchy Defense**: Patient-provided inputs, lab reports, and search snippets are treated as untrusted data. Prompt templates instruct models to treat retrieved text solely as evidence and ignore any embedded prompt injection instructions.
- **Tenant Isolation**: Vector search enforces explicit `user_id` and optional `facility_id` access control filters.

---

## 7. Safety, Governance & Regulatory Transparency

### 7.1 Version-Controlled Prompt Registry (`backend/prompt_registry.py`)
All system prompts are centralized, versioned, and immutable:
```python
from backend.prompt_registry import get_prompt

template = get_prompt("medical_qa", version="2.0")
```
Inline prompts in route handlers are strictly prohibited.

### 7.2 AI Function Governance Inventory (`backend/ai_function_registry.py`)
Exposed at `GET /v1/admin/ai-functions`, this registry inventories all AI capabilities against WHO AI governance and EU AI Act principles:
- Intended audience and clinical risk category.
- Mandatory medical disclaimer requirements.
- Human-in-the-loop review mandates.
- Provider abstraction boundary enforcement.

### 7.3 Model & Dataset Cards (`backend/model_cards.py`)
Exposed at `GET /v1/admin/model-cards`, providing transparency for all diagnostic ML models:
- Training dataset source and provenance.
- Performance characteristics, evaluation metrics, and known limitations.
- Human review requirements and post-deployment monitoring criteria.

### 7.4 Clinician Review Audit Trail (`POST /v1/predict/reviews`)
Clinicians can accept, override, or annotate AI predictions. Decisions are written to a HIPAA-compliant audit log recording clinician ID, decision code, and timestamp without storing raw PHI in audit metadata.

---

## 8. System Maintenance & Compliance Data Retention (`backend/maintenance.py`)

Automated maintenance ensures compliance with HIPAA/GDPR data retention mandates:

- **Storage Optimization**: Runs SQLite/PostgreSQL `VACUUM` and `ANALYZE` and index optimization.
- **Policy Retention Purging**: Enforces data retention schedules (1 year for chat history, 6 years for clinical audit logs) through `backend/data_retention.py`.
- **Execution Interfaces**:
  - Secure Admin Endpoint: `POST /v1/admin/maintenance`
  - Automated CLI Script: `python scripts/run_maintenance.py`

---

## 9. Component Dependency Flow

```
streaming_chat.py ──► core_ai.py ──► Local Ollama / Cloud Fallback
       │                  ▲
       ├── chat_context.py│
       └── prompt_registry.py

billing.py   ──► agents/billing_agent.py   ──► core_ai.py
discharge.py ──► agents/discharge_agent.py ──► core_ai.py
nursing.py   ──► agents/nursing_agent.py   ──► core_ai.py

chat.py ──► agent.py (LangGraph) ──► core_ai.py
              └── rag.py (Vector Store)

prediction.py ──► TabICL / Quad-Ensembles ──► SHAP Explainability
admin.py      ──► ai_function_registry.py & model_cards.py
admin.py      ──► maintenance.py ──► data_retention.py
```
