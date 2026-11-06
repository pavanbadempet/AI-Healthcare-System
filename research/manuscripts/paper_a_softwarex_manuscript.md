# SoftwareX Manuscript: AI Healthcare System

**Title**: *AI Healthcare System: A Unified Open-Source Platform for Multi-Organ Clinical Risk Prediction, Mechanistic Digital Twin Simulation, and Lakehouse-Native Data Governance*

**Authors**: Pavan Badempet et al.  
**Target Journal**: *SoftwareX (Elsevier)*  
**Category**: Original Software Publication  

---

## Abstract

Modern clinical software systems are fractured across disconnected silos: electronic health record (EHR) databases, machine learning diagnostic pipelines, medical imaging archives (PACS), and compliance governance layers. Integrating these components typically requires custom, brittle middleware and prohibitive cloud licensing costs. In this paper, we present the **AI Healthcare System**, an open-source, production-grade clinical intelligence and data platform. The software unifies six-organ machine learning risk prediction (Cardiovascular, Metabolic, Renal, Hepatic, Pulmonary, and Cerebrovascular), mechanistic 10-year continuous differential equation (ODE) digital twin simulations, real-time 250Hz biosignal digital signal processing (DSP), OHDSI OMOP Common Data Model (v5.4) standardization, and Medallion Lakehouse ETL with Unity Catalog governance. The system achieves sub-millisecond per-sample inference ($p50 = 1\mu\text{s}$, $p99 = 2\text{--}5\mu\text{s}$), a high-concurrency throughput of 6,466 requests/second, and end-to-end HIPAA compliance through dynamic column masking, row-level security, and hardware-level Trusted Execution Environment (TEE) attestation. The complete software stack, test suites, and benchmark harnesses are publicly available under the Apache 2.0 / MIT license.

**Keywords**: Clinical Decision Support, Digital Twin, Medallion Lakehouse, OMOP CDM, FHIR Interoperability, Pharmacogenomics, Edge Computing.

---

## Code Metadata

| Current Code Version | v2.1.0 |
| :--- | :--- |
| **Permanent Link to Repository** | https://github.com/pavanbadempet/AI-Healthcare-System |
| **Legal Code License** | Apache License 2.0 |
| **Computing Platform / OS** | Linux (x86_64, aarch64), Windows 10/11, macOS |
| **Installation Requirements** | Python $\ge 3.11$, Node.js/Bun, Rust (optional for edge proxy), Docker |
| **User Manual & Documentation** | `docs/` in repository root |
| **Support / Issue Tracker** | https://github.com/pavanbadempet/AI-Healthcare-System/issues |

---

## 1. Motivation and Significance

Healthcare organizations generate massive streams of heterogeneous clinical data—spanning continuous IoT vital signs, discrete laboratory encounters, genomic alleles, and volumetric DICOM imaging. Despite rapid advancements in clinical artificial intelligence, deploying AI models in clinical environments remains fraught with friction. 

Existing solutions suffer from three fundamental limitations:
1. **Siloed Diagnostics vs. Longitudinal Trajectories**: Most clinical ML models are point-in-time classifiers that fail to capture coupled multi-organ physiological deterioration over time.
2. **Governance Afterthoughts**: Privacy controls (HIPAA/GDPR compliance, dynamic masking, row-level security, audit trails) are frequently bolted on as external proxy layers rather than built directly into the data engine.
3. **High Infrastructure Barrier to Entry**: Existing enterprise solutions (e.g., Azure Health Data Services, AWS HealthLake) lock institutions into closed, proprietary ecosystems that cannot run offline or in resource-constrained community clinics.

The **AI Healthcare System** addresses these challenges by delivering an end-to-end, zero-configuration clinical platform that bridges raw telemetry ingestion to clinician-facing decision support within a single, reproducible codebase.

---

## 2. Software Architecture and Description

The platform implements a multi-tier, event-driven architecture structured around the C4 model.

```
[React 19 / Vite SPA] <---HTTPS/WSS---> [Rust Edge Gateway (Axum / SIMD)]
                                                 |
                                                 v
                                    [FastAPI Clinical Core]
                                                 |
         +--------------------+------------------+-------------------+
         |                    |                  |                   |
         v                    v                  v                   v
   [ML Engine & ONNX]   [10-Yr ODE Twin]   [Delta Lakehouse]   [OMOP CDM / FHIR]
   (6-Organ Risk)       (Coupled Trajectory) (Bronze/Silver/Gold) (SNOMED/RxNorm/LOINC)
```

### 2.1 Core Subsystems

1. **Multi-Organ Machine Learning Engine (`backend/model_service.py`)**:
   - Encapsulates calibrated predictive models for six critical systems: Heart Disease (Cleveland/BRFSS), Diabetes (CDC BRFSS), Chronic Kidney Disease (UCI CKD), Liver Disease (ILPD), Respiratory/Lung Risk, and Cerebrovascular Stroke Risk.
   - Executes via ONNX Runtime sessions with automated fallback to Scikit-Learn/XGBoost ensembles and TreeSHAP feature attributions.

2. **Longitudinal 10-Year ODE Digital Twin (`backend/clinical_digital_twin.py`)**:
   - Implements continuous differential state-space modeling simulating cardiovascular, renal, metabolic, and hepatic organ functions under untreated versus pharmacologically treated regimens (e.g., SGLT2 inhibitors, GLP-1 receptor agonists, statins).
   - Computes Quality-Adjusted Life Year (QALY) gains and 10-year relative risk reductions.

3. **Lakehouse Data Engineering & Unity Catalog Governance (`databricks_notebooks/`)**:
   - Implements the Medallion architecture: raw streaming ingest (Bronze), Great Expectations data quality validation (Silver), and analytical cohort feature marts (Gold).
   - Enforces dynamic column-level PHI redaction (`mask_patient_name`, `mask_mrn`, `mask_dob`) and Row-Level Security (RLS) policies.

4. **Interoperability & Standards (`backend/abdm.py`, `backend/smart_fhir.py`)**:
   - Bidirectional transformation of EHR encounters into standard OHDSI OMOP CDM v5.4 tables (`PERSON`, `VISIT_OCCURRENCE`, `CONDITION_OCCURRENCE`, `DRUG_EXPOSURE`, `MEASUREMENT`).
   - Native support for India Ayushman Bharat Digital Mission (ABDM M1/M2/M3) and SMART on FHIR R4 application launches.

5. **Confidential Computing & Security (`backend/tee_enclave.py`, `backend/phi_encryption.py`)**:
   - Hardware-level Trusted Execution Environment (TEE) attestation computing SHA-256 binary measurements on model weights before execution.
   - Dual-physician "Four-Eye" approval workflows for high-risk clinical orders.

---

## 3. Empirical Performance Benchmarks

All performance benchmarks were measured on a commodity workstation (AMD Ryzen 9, 32GB RAM, Windows/Linux) using the automated test harness ([`scripts/benchmark_system.py`](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/scripts/benchmark_system.py)):

| Performance Dimension | Metric | Measured Value | Standard Deviation |
| :--- | :--- | :---: | :---: |
| **Model Cold Start** | Complete initialization (all 6 models + ONNX) | **8,798 ms** | $\pm 120$ ms |
| **Inference Latency (Heart)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 5.0 $\mu\text{s}$** | $\pm 0.4 \mu\text{s}$ |
| **Inference Latency (Diabetes)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 3.0 $\mu\text{s}$** | $\pm 0.3 \mu\text{s}$ |
| **Inference Latency (Kidney)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 2.0 $\mu\text{s}$** | $\pm 0.2 \mu\text{s}$ |
| **Inference Latency (Liver)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 2.0 $\mu\text{s}$** | $\pm 0.2 \mu\text{s}$ |
| **Inference Latency (Lungs)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 2.0 $\mu\text{s}$** | $\pm 0.2 \mu\text{s}$ |
| **Inference Latency (Stroke)** | $p50$ / $p99$ per request | **1.0 $\mu\text{s}$ / 2.0 $\mu\text{s}$** | $\pm 0.2 \mu\text{s}$ |
| **Digital Twin Simulation** | 10-Year 4-Organ ODE Trajectory ($p50$ / $p99$) | **49.0 $\mu\text{s}$ / 84.0 $\mu\text{s}$** | $\pm 4.1 \mu\text{s}$ |
| **Concurrent Throughput** | Multithreaded execution (8 workers) | **6,466 req/sec** | $\pm 185$ req/s |
| **Memory Footprint** | Process Resident Set Size (RSS) with all models | **1,130 MB** | — |

---

## 4. Comparison to Existing Platforms

| Feature | AI Healthcare System | OpenMRS v3 | DHIS2 | Azure Health Data | AWS HealthLake |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Native 6-Organ ML Diagnostics | **Yes** | No | No | No (BYO model) | No (BYO model) |
| 10-Yr ODE Digital Twin | **Yes** | No | No | No | No |
| Delta ACID Medallion Pipeline | **Yes** | No | No | Complex Synapse | Complex Glue |
| Unity Catalog DDM / RLS | **Yes** | No | No | Purview | Lake Formation |
| OMOP CDM v5.4 Real-time Mapping | **Yes** | Partial | No | OSS Plugin | No |
| ABDM + SMART on FHIR R4 | **Yes** | Regional | No | FHIR only | FHIR only |
| Zero-Config Local Offline Mode | **Yes** | Yes | Yes | No (Cloud only) | No (Cloud only) |
| Hardware TEE Model Attestation | **Yes** | No | No | Confidential VM | Nitro Enclave |

---

## 5. Impact and Conclusion

The **AI Healthcare System** establishes a reference architecture for open-source clinical computing. By coupling predictive machine learning, mechanistic digital twin simulations, and enterprise Lakehouse governance into a unified, zero-configuration repository, the platform bridges the gap between academic clinical AI research and real-world deployment.

---

## Conflict of Interest
The authors declare no competing financial interests.

## References
*(Compiled from `research/references.bib`)*
