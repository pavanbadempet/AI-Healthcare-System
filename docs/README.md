# 📚 AI Healthcare System — Documentation Index

> Canonical index and navigation hub for system architecture, clinical workflows, compliance, guides, and engineering reports.

---

## 🏛️ Directory Organization

```
docs/
├── architecture/     # Core system design, Lakehouse specs, ADRs, and runbooks
├── clinical/         # Clinical workflows, nursing, pharmacy, billing, and FHIR mappings
├── compliance/       # HIPAA security specs, privacy operations, retention, and audit logs
├── guides/           # Data engineering guides, telemetry streaming, model retraining, and conventions
├── reports/          # Production readiness gates, test reports, model cards, and benchmarks
├── assets/           # UI walkthrough screenshots, architecture diagrams, and previews
├── omop/             # OMOP CDM logic and condition era definitions
├── openapi_spec.json # OpenAPI 3.0 REST API specification
└── postman_collection.json # Postman v2.1 API testing collection
```

---

## 🏛️ Architecture (`docs/architecture/`)

System topology, dual-layer Lakehouse vs serving core, ADR records, and agent routing.

| Document | Description |
| :--- | :--- |
| **[AI_AGENT_ARCHITECTURE.md](architecture/AI_AGENT_ARCHITECTURE.md)** | Multi-Agent LangGraph clinical supervisor state machine and routing contracts. |
| **[AI_Healthcare_System_Master_Architecture_Runbook.md](architecture/AI_Healthcare_System_Master_Architecture_Runbook.md)** | End-to-end master runbook for system operations and deployment. |
| **[architecture-decisions.md](architecture/architecture-decisions.md)** | Comprehensive Architecture Decision Records (ADRs 001–024). |
| **[ENTERPRISE_LAKEHOUSE_PRODUCT_ARCHITECTURE.md](architecture/ENTERPRISE_LAKEHOUSE_PRODUCT_ARCHITECTURE.md)** | Databricks Delta Lake Medallion architecture and Lakeflow pipeline specs. |
| **[INTEROPERABILITY_EXPORTS.md](architecture/INTEROPERABILITY_EXPORTS.md)** | HL7 FHIR R4, ABDM ABHA, and DICOMweb interoperability specifications. |
| **[API_CONTRACT_INDEX.md](architecture/API_CONTRACT_INDEX.md)** | Comprehensive API route index and schema contract reference. |
| **[REALTIME_MONITORING_AND_PATTERNS.md](architecture/REALTIME_MONITORING_AND_PATTERNS.md)** | Real-time clinical telemetry, alerting thresholds, and monitoring architecture. |
| **[paper_a_architecture_diagram.md](architecture/paper_a_architecture_diagram.md)** | Academic architectural diagrams and subsystem component models. |
| **[paper_a_system_comparison.md](architecture/paper_a_system_comparison.md)** | Benchmark and architectural comparison against existing healthcare systems. |
| **[TECHNICAL_WHITEPAPER.md](architecture/TECHNICAL_WHITEPAPER.md)** | Enterprise technical whitepaper for clinical stakeholders. |
| **[AI_AGENT_BACKEND_ENGINEERING_PLAYBOOK.md](architecture/AI_AGENT_BACKEND_ENGINEERING_PLAYBOOK.md)** | Backend engineering playbook for FastAPI, SQLAlchemy, and async pipelines. |
| **[AI_AGENT_DATABASE_ENGINEERING_PLAYBOOK.md](architecture/AI_AGENT_DATABASE_ENGINEERING_PLAYBOOK.md)** | Database indexing, partitioning, and migration playbooks. |
| **[AI_AGENT_DATA_ENGINEERING_PLAYBOOK.md](architecture/AI_AGENT_DATA_ENGINEERING_PLAYBOOK.md)** | PySpark, Delta Lake, and Lakehouse engineering standards. |
| **[AI_AGENT_FRONTEND_ENGINEERING_PLAYBOOK.md](architecture/AI_AGENT_FRONTEND_ENGINEERING_PLAYBOOK.md)** | React 19 SPA, Tailwind CSS, and WebGL DICOM viewer engineering guidelines. |
| **[MASTER_PERFORMANCE_ARCHITECTURE_PLAN.md](architecture/MASTER_PERFORMANCE_ARCHITECTURE_PLAN.md)** | Sub-millisecond latency tuning and edge gateway performance plans. |
| **[DIGITAL_TWIN_PHYSIOLOGY.md](architecture/DIGITAL_TWIN_PHYSIOLOGY.md)** | Real-time biophysical simulation and physiological state modeling. |

---

## 🩺 Clinical Workflows (`docs/clinical/`)

Clinical domain processes, nursing interventions, pharmacy dispensation, and billing workflows.

| Document | Description |
| :--- | :--- |
| **[DIAGNOSTICS_WORKFLOW.md](clinical/DIAGNOSTICS_WORKFLOW.md)** | TabICLv2 and XGBoost ML screening, SHAP attribution, and clinician review flow. |
| **[BILLING_WORKFLOW.md](clinical/BILLING_WORKFLOW.md)** | ANSI X12 837P insurance claims, 835 EDI adjudication, and invoicing. |
| **[NURSING_WORKFLOW.md](clinical/NURSING_WORKFLOW.md)** | Nurse station task queues, vitals logging, and medication administration records. |
| **[PHARMACY_WORKFLOW.md](clinical/PHARMACY_WORKFLOW.md)** | Drug interaction checking, e-prescriptions, and dispensary workflows. |
| **[DISCHARGE_WORKFLOW.md](clinical/DISCHARGE_WORKFLOW.md)** | Patient discharge summaries, clinician finalization, and post-discharge care. |
| **[CARE_EVENT_FEEDS.md](clinical/CARE_EVENT_FEEDS.md)** | Real-time clinical event feeds, WebSocket notifications, and bedside alerts. |
| **[CLINIC_PILOT_PLAYBOOK.md](clinical/CLINIC_PILOT_PLAYBOOK.md)** | Controlled pilot rollout guide for small clinics and specialist practices. |
| **[HOSPITAL_OPERATIONS_CORE.md](clinical/HOSPITAL_OPERATIONS_CORE.md)** | Core operational workflows, bed tracking, and department triage. |
| **[FHIR_R4_OBSERVATION_MAPPINGS.md](clinical/FHIR_R4_OBSERVATION_MAPPINGS.md)** | Mapping tables between internal clinical models and HL7 FHIR R4 resources. |
| **[CONFORMAL_CALIBRATION.md](clinical/CONFORMAL_CALIBRATION.md)** | Non-conformity scores and guaranteed error rate bounds for clinical models. |

---

## 🔒 Compliance & Security (`docs/compliance/`)

Regulatory adherence, HIPAA security safeguards, privacy policies, and audit logging.

| Document | Description |
| :--- | :--- |
| **[HIPAA_AUDIT_LOGGING_SPEC.md](compliance/HIPAA_AUDIT_LOGGING_SPEC.md)** | HIPAA Security Rule §164.312(b) audit trail specification and PHI masking. |
| **[SECURITY_QUESTIONNAIRE.md](compliance/SECURITY_QUESTIONNAIRE.md)** | Enterprise security assessment answers for procurement and compliance audits. |
| **[PRIVACY_OPERATIONS.md](compliance/PRIVACY_OPERATIONS.md)** | DPDP Act (India), GDPR (EU), and HIPAA (US) data privacy operational rules. |
| **[LEGAL_AND_LIABILITY.md](compliance/LEGAL_AND_LIABILITY.md)** | Legal liability boundaries, clinician-in-the-loop disclaimers, and terms. |
| **[RETENTION_POLICY_READINESS.md](compliance/RETENTION_POLICY_READINESS.md)** | Data retention, automated archiving, and cryptographic purging policies. |
| **[SECURITY_ASSURANCE_READINESS.md](compliance/SECURITY_ASSURANCE_READINESS.md)** | SOC 2 / ISO 27001 readiness posture, pen test frameworks, and RBAC. |
| **[SECURITY_DEPENDENCY_AUDIT.md](compliance/SECURITY_DEPENDENCY_AUDIT.md)** | Supply chain security, pip/npm vulnerability scanners, and SBOM. |
| **[BACKUP_AND_RESTORE_READINESS.md](compliance/BACKUP_AND_RESTORE_READINESS.md)** | RPO/RTO metrics, disaster recovery playbooks, and automated backup drills. |
| **[INCIDENT_RESPONSE_READINESS.md](compliance/INCIDENT_RESPONSE_READINESS.md)** | Security incident escalation matrix, containment protocols, and notifications. |
| **[TRUST_BASELINE.md](compliance/TRUST_BASELINE.md)** | Clinic trust architecture, zero-leak telemetry, and confidentiality bounds. |
| **[CONTRACT_PACKET_CHECKLIST.md](compliance/CONTRACT_PACKET_CHECKLIST.md)** | Pre-pilot legal agreements, BAAs, and clinic data processing terms. |
| **[DATA_ENCRYPTION_AT_REST.md](compliance/DATA_ENCRYPTION_AT_REST.md)** | AES-256-GCM encryption at rest, envelope key management, and TEE attestation. |

---

## 📖 Guides & Development (`docs/guides/`)

Developer onboarding, Lakehouse training, telemetry streaming, and commit standards.

| Document | Description |
| :--- | :--- |
| **[DATA_ENGINEERING_MASTER_GUIDE.md](guides/DATA_ENGINEERING_MASTER_GUIDE.md)** | Comprehensive PySpark, Delta Lake 4.x, and Lakeflow pipeline engineering guide. |
| **[DATA_ENGINEERING_INTERVIEW_GUIDE.md](guides/DATA_ENGINEERING_INTERVIEW_GUIDE.md)** | In-depth data architecture, medallion ETL patterns, and system design questions. |
| **[TELEMETRY_STREAMING_GUIDE.md](guides/TELEMETRY_STREAMING_GUIDE.md)** | High-throughput biometrics ingestion via Kafka / Redis Streams and WebSockets. |
| **[CLOUD_RETRAINING_GUIDE.md](guides/CLOUD_RETRAINING_GUIDE.md)** | Cloud retraining pipeline for clinical ML models using Databricks and GPU kernels. |
| **[Healthcare_Retraining_Colab.ipynb](guides/Healthcare_Retraining_Colab.ipynb)** | Interactive Google Colab notebook for retraining clinical classifiers with GPU. |
| **[PLUGIN_INTEGRATION_GUIDE.md](guides/PLUGIN_INTEGRATION_GUIDE.md)** | Extending the healthcare platform with custom clinical AI and EHR plugins. |
| **[COMMIT_CONVENTIONS.md](guides/COMMIT_CONVENTIONS.md)** | Strict Conventional Commit standards and git hygiene for contributors. |
| **[DATA_QUALITY_AND_LINEAGE.md](guides/DATA_QUALITY_AND_LINEAGE.md)** | Data quality gates, Great Expectations schemas, and Delta Lake lineage tracking. |
| **[DELTA_COMPACTION_TUNING.md](guides/DELTA_COMPACTION_TUNING.md)** | Delta Lake bin-packing, Z-ordering, and OPTIMIZE compaction tuning parameters. |
| **[wiki_initial_pages.md](guides/wiki_initial_pages.md)** | Internal knowledge base seeds and team onboarding documents. |

---

## 📊 Reports & Evaluations (`docs/reports/`)

Production readiness gates, ML model cards, validation audits, and performance benchmarks.

| Document | Description |
| :--- | :--- |
| **[PRODUCTION_READINESS_GATE.md](reports/PRODUCTION_READINESS_GATE.md)** | Mandatory pre-deployment checklist across Backend, Lakehouse, and Security. |
| **[MASTER_PROJECT_REPORT.md](reports/MASTER_PROJECT_REPORT.md)** | Complete executive project report, architecture accomplishments, and metrics. |
| **[MODEL_AND_DATASET_CARDS.md](reports/MODEL_AND_DATASET_CARDS.md)** | TabICLv2 and ensemble model cards, BRFSS/MIMIC datasets, and calibration stats. |
| **[MODEL_INTEGRITY_REPORT.md](reports/MODEL_INTEGRITY_REPORT.md)** | Validation and integrity audit for disease screening classifiers. |
| **[OPERATIONAL_HEALTH.md](reports/OPERATIONAL_HEALTH.md)** | Live telemetry health checks, endpoint uptime, and infrastructure readiness. |
| **[PREDICTION_REVIEW_AUDIT.md](reports/PREDICTION_REVIEW_AUDIT.md)** | Audit log report for clinician approvals and overrides on ML predictions. |
| **[RESEARCH_BACKED_BACKEND_GAP_ANALYSIS.md](reports/RESEARCH_BACKED_BACKEND_GAP_ANALYSIS.md)** | Clinical and research gap analysis evaluating backend robustness. |
| **[performance-benchmarks.md](reports/performance-benchmarks.md)** | Load testing metrics, Axum edge proxy benchmarks, and latency profiles. |
| **[TEST_INFRA.md](reports/TEST_INFRA.md)** | Pytest test architecture, fixture scoping, and xdist parallelization. |
| **[TEST_READY.md](reports/TEST_READY.md)** | Authoritative declaration and execution log for comprehensive E2E test suites. |
