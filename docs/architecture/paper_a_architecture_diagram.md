# Paper A: Formal System Architecture & C4 Component Specification

This document presents the formal **C4 Model Architectural Diagrams** for the AI Healthcare System, serving as primary figures for the **SoftwareX** system architecture paper.

---

## 1. System Context Diagram (C4 Level 1)

```mermaid
C4Context
    title System Context Diagram - AI Healthcare System

    Person(clinician, "Clinician / Physician", "Reviews patient risk profiles, multi-organ digital twin simulations, and executes four-eye treatment approvals.")
    Person(patient, "Patient / Citizen", "Interacts with telehealth companion, views personal health records, and manages ABDM consent artifacts.")
    Person(researcher, "Clinical Researcher", "Queries anonymized OMOP CDM cohorts and population health features governed by Unity Catalog.")

    System(ai_health_sys, "AI Healthcare System", "Unified platform providing multi-organ ML diagnostics, 10-year ODE digital twin simulation, Medallion Lakehouse ETL, and HIPAA-compliant data governance.")

    System_Ext(abdm_network, "ABDM Network (India)", "National Health Authority ABDM gateway for ABHA verification and consent-based health data exchange.")
    System_Ext(pacs_server, "Hospital PACS Archive", "DICOMweb / WADO-RS imaging archive for CT, MRI, and X-ray radiology studies.")
    System_Ext(emr_epic_cerner, "Hospital EHR (Epic / Cerner)", "SMART on FHIR clinical data source and destination for validated clinical orders.")
    System_Ext(neon_cloud, "Neon Serverless Postgres", "Cloud PostgreSQL for multi-tenant clinical transactions and real-time frontend caching.")

    Rel(clinician, ai_health_sys, "Uses web portal for diagnostics & four-eye signoffs", "HTTPS / WSS")
    Rel(patient, ai_health_sys, "Interacts with companion & views records", "HTTPS")
    Rel(researcher, ai_health_sys, "Executes governed SQL queries via Unity Catalog", "JDBC / Arrow")

    Rel(ai_health_sys, abdm_network, "Exchanges FHIR bundles & consent artifacts", "HTTPS / mTLS")
    Rel(ai_health_sys, pacs_server, "Streams radiology series & CT slices", "WADO-RS / DICOMweb")
    Rel(ai_health_sys, emr_epic_cerner, "Launches via SMART on FHIR OAuth2", "OAuth2.0 / FHIR R4")
    Rel(ai_health_sys, neon_cloud, "Synchronizes read-replicas & aggregates", "PostgreSQL Wire Protocol")
```

---

## 2. Container Diagram (C4 Level 2)

```mermaid
C4Container
    title Container Architecture Diagram - AI Healthcare System

    Container(spa, "Single-Page Application (SPA)", "React 19, TypeScript, Vite, Tailwind CSS, Lucide", "Responsive clinical cockpit, real-time 250Hz ECG canvas, DICOM WebWorker viewer, and Data Engineering Command Center.")
    Container(rust_proxy, "Edge Gateway Proxy (PID 1)", "Rust, Axum, Tokio, PyO3 FFI", "Sub-millisecond TLS termination, SIMD Pan-Tompkins DSP peak detection, and token-level PHI redaction.")
    Container(backend_api, "Core Clinical Backend API", "Python 3.12, FastAPI, Uvicorn, Pydantic v2", "Business logic, schema contracts, four-eye signoffs, CPIC pharmacogenomics, and TEE enclave attestation.")
    Container(ml_service, "ML & Digital Twin Engine", "Scikit-Learn, ONNX Runtime, TabPFN, PyTorch", "6-organ ML risk inference, TreeSHAP feature attributions, and coupled 10-year ODE state-space digital twin.")
    Container(lakehouse, "Medallion Lakehouse Engine", "Databricks, Delta Lake, PySpark, DLT", "Continuous Bronze ingestion, Great Expectations quality gating, Silver standardization, and Gold cohort aggregates.")
    ContainerDb(db_relational, "Relational Database", "Neon PostgreSQL / SQLite", "ACID transactions, audit logs, appointments, user credentials, and clinical events.")
    ContainerDb(vector_db, "Clinical Vector Store", "TurboVec / Qdrant", "Dense vector embeddings for clinical RAG, semantic caching, and guideline retrieval.")

    Rel(spa, rust_proxy, "Sends API requests & telemetry streams", "HTTPS / WSS (Port 3000 -> 8000)")
    Rel(rust_proxy, backend_api, "Forwards authenticated & sanitized requests", "Unix Domain Socket / IPC")
    Rel(backend_api, ml_service, "Dispatches risk scoring & digital twin simulations", "In-Process / PyO3 / ONNX")
    Rel(backend_api, lakehouse, "Triggers ETL pipelines & queries OMOP CDM tables", "Delta Standalone / PySpark")
    Rel(backend_api, db_relational, "Reads/writes transactional state", "SQLAlchemy / Asyncpg")
    Rel(backend_api, vector_db, "Queries semantic cache & medical literature", "Cosine Similarity / SIMD")
```

---

## 3. Detailed Component Diagram - Backend Engine (C4 Level 3)

```mermaid
graph TD
    subgraph API_Routers["1. Presentation & Routing Layer"]
        R_Pred["/predict/* (6-Organ ML)"]
        R_Lake["/v1/lakehouse/* (Delta & OMOP)"]
        R_Mesh["/v1/mesh/* (Multi-Cloud)"]
        R_Four["/v1/governance/four-eye/*"]
        R_DSP["/v1/telemetry/ecg/*"]
    end

    subgraph Security_Governance["2. Governance, Security & TEE Layer"]
        SG_TEE["ConfidentialEnclave (SHA-256 Model Attestation)"]
        SG_DDM["Dynamic Data Masking (SQL Functions)"]
        SG_RLS["Row-Level Security Filter"]
        SG_Drift["SchemaDriftDetector (ORM vs Pydantic vs DB)"]
        SG_Audit["HIPAA Audit Logger"]
    end

    subgraph Clinical_Intelligence["3. Clinical AI & Simulation Subsystems"]
        CI_ML["ModelService (6-Organ Ensemble + ONNX)"]
        CI_Twin["ClinicalDigitalTwinEngine (10-Yr Coupled ODE)"]
        CI_PGx["PrecisionPharmacogenomicsEngine (CPIC Rules)"]
        CI_OMOP["OMOPCDMEngine (SNOMED / RxNorm / LOINC)"]
        CI_DSP["Pan-Tompkins DSP Engine (250Hz Rust SIMD)"]
        CI_RAG["Clinical RAG + Semantic Cache"]
    end

    subgraph Storage_Persistence["4. Persistence & Lakehouse Layer"]
        ST_Delta["Delta Lake ACID Tables (Bronze/Silver/Gold)"]
        ST_Neon["Neon Serverless PostgreSQL (52 Tables)"]
        ST_Vec["TurboVec Semantic Cache"]
    end

    R_Pred --> SG_TEE
    SG_TEE --> CI_ML
    R_Pred --> CI_Twin
    R_Pred --> CI_PGx

    R_Lake --> CI_OMOP
    R_Lake --> ST_Delta

    R_DSP --> CI_DSP

    R_Four --> SG_Audit
    SG_Audit --> ST_Neon

    CI_RAG --> ST_Vec
    SG_Drift --> ST_Neon
```
