# GitHub Wiki & Project Board Setup Blueprint

This document contains the initial structure, pre-written documentation pages for your GitHub Wiki, and a task list blueprint for your GitHub Projects board.

---

## 📘 Part 1: GitHub Wiki - Initial Home Page

*Create your first page on the **Wiki** tab, name it `Home`, and paste the following content:*

```markdown
# Welcome to the Privacy-First Clinical AI & EMR Platform Wiki

This platform is a state-of-the-art Electronic Medical Record (EMR) and real-time clinical telemetry platform designed with HIPAA compliance, local AI co-pilots, and sub-second rendering interfaces.

## 🛰️ 1. Technical Architecture Overview

The system consists of three main components:
1. **Frontend (Vite React SPA)**: A highly responsive React 19 single-page application optimized using compiler-level memoization, Web Workers for multi-threaded vital waveform rendering, and client-side ONNX machine learning inference.
2. **Backend (FastAPI)**: Python-based asynchronous REST API orchestrating EHR workflows, HAPI FHIR integrations, database migrations, and LangGraph multi-agent supervisor systems.
3. **Database (SQLite/PostgreSQL)**: Managed via SQLAlchemy models and Alembic migrations.

## 📊 2. Clinical Data Pipeline & ML Calibrations

To maintain diagnostic safety and interpretability in clinical workflows, the platform implements:
* **Inductive Conformal Prediction**: Produces prediction sets for diagnostic models with a user-defined confidence level ($1 - \alpha$) to quantify model uncertainty and prevent false confidence.
* **Validated Clinical Calculators**: Direct pipeline calculations for CKD-EPI eGFR (2021), FIB-4 Index for liver fibrosis, and log-linear Cox proportional hazards regressions for Framingham 10-Year Cardiovascular Risk.

## ⚡ 3. High-Performance UI Optimizations

The user interface implements SOTA client performance features to handle high-frequency hospital monitors:
* **Multi-Threaded Rendering**: Offloads SpO2 and ECG canvas wave calculations to background Web Workers using the `OffscreenCanvas` API.
* **Render Cascades Isolation**: Implements React `useDeferredValue` for registry searches and wraps EMR subpanels in `React.memo` to isolate state update boundaries.
* **Asset Code-Splitting**: Lazily loads heavy modules (like the 400KB `onnxruntime-web` package) only when client predictions are executed.

---

### Navigation
* [[System Architecture Guide]]
* [[Local EMR Database Schema]]
* [[Deployment & Setup Manual]]
```

---

## 📋 Part 2: GitHub Projects - Task Board Blueprint

*Create a new **GitHub Project**, choose the **Board** layout, and add the following columns and task cards:*

### Column: 📝 Todo

#### Task 1: Setup Local WebLLM Cache Optimizer
* **Description**: Create a service worker caching policy for `@mlc-ai/web-llm` model weights to avoid downloading 4GB of LLM weights on browser reloads.
* **Labels**: `area:frontend`, `enhancement`

#### Task 2: Implement Audit Log Cryptographic Hashing
* **Description**: Secure the `audit_logs` database table by chaining hashes (Merkle Tree style) to prevent tampering with HIPAA operational history.
* **Labels**: `area:backend`, `security`

#### Task 3: Add WebGPU Fallback for ONNX Models
* **Description**: Enhance client-side predictions to gracefully fallback from WebGPU execution providers to WebAssembly (WASM) threads when GPU drivers are missing.
* **Labels**: `area:mlops`, `bug`

### Column: ⚙️ In Progress

#### Task 4: Integrate FHIR EMR Synchronization
* **Description**: Hook the patient admission workflow to fetch external records from public HAPI FHIR sandboxes dynamically.
* **Labels**: `area:interoperability`, `feature`

### Column: ✅ Done

#### Task 5: Implement Telemetry WebSocket Debouncing
* **Description**: Throttle real-time vital update triggers to 2Hz using a React scheduler to prevent Virtual DOM render flooding.
* **Labels**: `performance`, `completed`

#### Task 6: Add React 19 Compiler Preset
* **Description**: Configure Babel and Rolldown to run the compiler-level memoization preset on production bundles.
* **Labels**: `performance`, `completed`
