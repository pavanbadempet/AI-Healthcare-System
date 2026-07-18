# ClinOS Master Architecture & System Runbook

This document is the master technical reference and runbook for the **ClinOS Privacy-First Clinical AI & EMR Interoperability Platform**. It details every component, directory, algorithm, configuration, and security control implemented across the system.

---

## 📂 1. Directory Structure Reference

The repository is organized as a decoupled, multi-language codebase:

*   **`backend/`**: FastAPI (Python 3.11+) core server.
    *   `backend/models/`: SQLAlchemy database model declarations.
    *   `backend/schemas/`: Pydantic input/output validation models.
    *   `backend/agents/` / `backend/langgraph_orchestrator.py`: Multi-agent supervisor and routing nodes.
    *   `backend/core_ai.py` / `backend/prediction.py`: ML models loading, inference, and safety calibrations.
    *   `backend/data_engineering_platform.py`: Spark and Polars ETL engine.
*   **`frontend/`**: Vite React single-page application (TypeScript, TailwindCSS).
    *   `frontend/src/components/layout/`: Global navigation and layout wrappers.
    *   `frontend/src/components/operations/`: Waveform canvas drawers and monitoring panels.
    *   `frontend/src/lib/apiCore.ts`: In-memory request caches and fetch clients.
*   **`android/`**: Kotlin Jetpack Compose mobile EMR application.
*   **`rust_gateway/`**: High-performance reverse proxy and gRPC/WebSocket routing gateway.
*   **`airflow/`**: Ingestion scheduler, model drift validation, and maintenance DAGs.
*   **`monitoring/`**: Prometheus metrics and Grafana dashboard templates.
*   **`terraform/` & `k8s/`**: Infrastructure-as-code and horizontal pod configurations.

---

## 🛰️ 2. Core Backend Architecture (FastAPI)

The API gateway binds to host `127.0.0.1` and port `8000` in development, exposing RESTful endpoints under `/api/v1/`:

### A. Dependency Injection & Session Lifecycle
Route controllers obtain database connections using FastAPI's dependency injection engine (`Depends(database.get_db)`). Sessions are isolated per request thread, auto-committing on success and executing `db.rollback()` if unhandled exceptions are raised during execution.

### B. Microservices Routing
In distributed modes, request handling is routed based on component targets:
*   `/api/v1/auth` -> Routed to `auth-service` container.
*   `/api/v1/patients` -> Routed to `clinical-service` container.
*   `/api/v1/telemetry` -> Routed to `telemetry-service` container (handling real-time socket connections).
*   `/api/v1/billing` -> Routed to `billing-service` container.
*   `/api/v1/interop` -> Routed to `interop-service` container.

---

## 🗂️ 3. Relational EMR Schema (SQLAlchemy Models)

The relational SQLite database (`healthcare.db`) maps EMR schemas using SQLAlchemy:

### A. Patients (`users` table where `role="patient"`)
Stores demographics, MRN numbers, and risk levels:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # admin, doctor, nurse, patient, billing
    full_name = Column(String, nullable=True)
    dob = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    facility_id = Column(Integer, ForeignKey("hospital_facilities.id"), nullable=True)
```

### B. Vital Observations (`vital_observations`)
Tracks patient telemetry coordinates:
```python
class VitalObservation(Base, SoftDeleteMixin):
    __tablename__ = "vital_observations"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    heart_rate = Column(Float, nullable=True)
    systolic_bp = Column(Float, nullable=True)
    diastolic_bp = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    observed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

### C. Monitoring Signals (`monitoring_signals`)
Stores rule-based clinical alerts triggered by vital observation anomalies:
```python
class MonitoringSignal(Base):
    __tablename__ = "monitoring_signals"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    signal_type = Column(String)  # tachycardia, hypoxia, fever
    severity = Column(String, default="info")  # info, warning, critical
    title = Column(String)
    summary = Column(Text)
    status = Column(String, default="open", index=True)  # open, acknowledged, resolved
```

---

## ⚡ 4. High-Performance Frontend Rendering

The Vite SPA implements several SOTA frontend enhancements to support sub-second layouts:

### A. Multi-Threaded OffscreenCanvas
The dashboard monitors render high-frequency real-time waveforms (like ECG and SpO2) at 60 FPS without UI stutters by transferring canvas render loops to background Web Workers:
```typescript
// Main UI thread transferring control
const canvas = canvasRef.current;
const offscreen = canvas.transferControlToOffscreen();
worker.postMessage({ type: 'INIT', canvas: offscreen }, [offscreen]);
```
The Web Worker thread listens to WebSocket telemetry events, processes calculations, and draws directly onto the screen buffer, preventing main-thread blocking.

### B. Short-Term GET Request Caching
API queries use an in-memory short-term Map cache configured with a 10-second Time-To-Live (TTL):
*   `GET` requests query the local cache map first.
*   `POST`, `PUT`, or `DELETE` requests automatically evict the cache, ensuring the UI remains up-to-date.
*   Bypassed in test environments (`process.env.NODE_ENV === 'test'`) to avoid mock collision issues.

### C. Hover-Gesture API Prefetching
Hovering over a top navigation tab triggers background prefetching:
```typescript
onMouseEnter={() => prefetchRoute('/dashboard')}
```
This pre-warms the cache by dispatching the corresponding API query in the background, making layout transitions instantaneous.

### D. React 19 Compiler Memoization
All rendering components are memoized at compile-time using the React 19 Compiler (`babel-plugin-react-compiler` via the modern `@rolldown/plugin-babel` build plugin), eliminating the overhead of manual `useMemo`/`useCallback` hooks.

---

## 🧠 5. Clinical AI & Machine Learning Systems

The platform deploys local, on-device machine learning classifiers and LLM co-pilots:

### A. On-Device Diagnostic Classifiers (ONNX)
Five predictive risk classifiers (Diabetes, Heart, Liver, Kidney, Lungs) run directly in the browser via `onnxruntime-web`:
*   Dynamic code splitting lazy-loads the 400KB `onnxruntime-web` package only when inference is triggered.
*   The models execute using WebGPU acceleration, falling back to multi-threaded WebAssembly (WASM) if GPU drivers are missing.

### B. Conformal Prediction Calibration
To guarantee clinical safety margins, XGBoost models output **prediction sets** matching a user-defined confidence level ($1 - \alpha$, e.g., $95\%$):
$$
\hat{C}(X) = \{ y \in \mathcal{Y} : s(X, y) \le q_{1-\alpha} \}
$$
Where $s(X, y)$ is the non-conformity score, and $q_{1-\alpha}$ is the calibration quantile.

### C. Local Browser AI Assistant (WebLLM)
Conversational summaries and chart reviews are compiled on-device:
*   Quantized LLMs (e.g. `Llama-3-8B-Instruct-q4f16_1-MLC`) run client-side using `@mlc-ai/web-llm`.
*   Model weights are cached locally inside the browser's Cache Storage API, ensuring zero data egress.

### D. AI Safety Confidence Thresholds & Blocking
*   **Minimum Confidence Threshold (`0.15`)**: If a model's risk score confidence is under 15%, the output is blocked and hidden from the UI.
*   **High-Risk Confidence Threshold (`0.30`)**: If a prediction is high-risk but has under 30% confidence, the UI displays an **Elevated Caution warning banner** instructing manual clinician verification.

---

## 🔒 6. HIPAA Security Safeguards

The system implements multiple technical safeguards to comply with HIPAA requirements:

### A. Symmetric PHI Encryption at Rest
Protected Health Information (PHI) columns (names, emails, phones, addresses) are encrypted in the database using **AES-128-CBC + HMAC-SHA256** symmetric encryption:
*   Requires the `PHI_ENCRYPTION_KEY` environment variable in production.
*   If the key is missing in staging or testing, the system outputs warnings and falls back to plaintext to prevent startup blocking.

### B. Anonymized FHIR-Compliant Auditing
All EMR reads, writes, and clinical queries generate FHIR-compliant `AuditEvent` records. To prevent security leaks in server logs, the audit logging engine (`audit_log.py`) **never** writes patient names, DOBs, or clinical findings to log files, registering only patient references (e.g., `Patient/42`), the action code, the actor ID, and the outcome code.

### C. Consent Gates & Access Controls
*   **Token Scoping**: Patient users are restricted from querying any ID other than their own authenticated JWT token subject.
*   **Clinician Authorization**: Access to historical records or external FHIR bundles requires an active consent relationship recorded in the database.

---

## 🇮🇳 7. Indian ABDM Interoperability

The platform supports integration with the **Ayushman Bharat Digital Mission (ABDM)** gateway:
*   **Microservice Interface**: Integrations are routed to a dedicated service running on port `8003` (`ABDM_FHIR_SERVICE_URL`).
*   **Consent Request Handshake**: Dispatches requests to the NHA gateway specifying ABHA address matching, purpose codes, and active date ranges.
*   **FHIR Bridges**: Translates internal databases to standard FHIR formats (Patient, MedicationRequest, DiagnosticReport) for inter-hospital exchanges.

---

## 📊 8. Ingestion & Data Engineering (PySpark & Airflow)

Clinical data pipelines are managed using PySpark, Polars, and Apache Airflow:

### A. PySpark Medallion Lakehouse
*   **Bronze Layer**: Parallel raw ingestion using a `ThreadPoolExecutor` (up to 8 concurrent workers) from databases (JDBC), paginated APIs, files (Parquet/CSV), and real-time Kafka streams.
*   **Silver Layer**: Deduplicates data (`.dropDuplicates()`), cleans null columns, and performs terminology lookups to map medical codes to standardized names.
*   **Gold Layer**: Generates aggregated, analytics-ready datasets.

### B. Polars Fallback Engine
To speed up local development and testing, the pipeline automatically falls back to a lightweight **Polars** engine if PySpark is not available.

### C. Airflow Orchestration DAGs
Schedules clinical workflows under `airflow/dags/`:
*   `healthcare_data_pipeline`: Ingestion ETL scheduler.
*   `model_retraining_dag`: Weekly ML model evaluations and retraining.
*   `delta_lake_operations`: Maintenance operations (`OPTIMIZE`/`VACUUM`) for Delta tables.
*   `lineage_emitter`: Integrates with OpenLineage to track data lineage.

---

## 🐳 9. Infrastructure & Scaling

The enterprise version of the platform runs as a decoupled microservices architecture:
*   **Docker Compose**: Pre-configured configurations (`docker-compose.microservices.yml`) spin up isolated containers for the API services, load balancer gateway, and database servers.
*   **Kubernetes (`k8s/`)**: Implements Horizontal Pod Autoscalers (HPA) to scale up `telemetry-service` pods when active vital connections peak.
*   **Terraform (`terraform/`)**: Configures cloud resources (AWS ECS, RDS, IAM).
*   **Rust Ingress Gateway**: Uses the custom Axum-based `rust_gateway` to load-balance incoming HTTP/WebSocket traffic, terminate SSL, and validate tokens.

---

## 🧪 10. Verification & Test Commands

*   **Backend Pytest Suite** (optimized with `pytest-xdist` parallelization):
    ```bash
    python -m pytest tests/ -n auto -v
    ```
*   **Frontend Vitest Suite**:
    ```bash
    npm --prefix frontend run test
    ```
*   **Production Build Transpilation**:
    ```bash
    npm --prefix frontend run build
```
