# CONTEXT.md — Backend Deep Reference

> Extended reference for `backend/`. Read `backend/AGENTS.md` first — this file is for when you need deeper detail.

---

## Module Responsibilities

### AI Layer

| Module | Role |
|--------|------|
| `core_ai.py` | **Canonical AI provider entry point.** Multi-tier text inference plus embeddings, vision generation, and Ollama model management. Exposes `generate()`, `chat()`, `chat_stream()`, `embed_text()`, `generate_vision_content()`, `is_available()`. No other module may call AI provider APIs directly. |
| `ai_function_registry.py` | Static governance inventory of AI-facing backend functions, intended audiences, clinical risk categories, disclaimer requirements, human-review flags, transparency requirements, and provider-boundary expectations. Exposed to admins at `GET /admin/ai-functions`. |
| `model_cards.py` | Static model and dataset cards for prediction model intended use, local artifacts, public training datasets, limitations, human-review requirements, and disclaimer requirements. Exposed to admins at `GET /admin/model-cards`. |
| `prompt_registry.py` | Version-controlled prompt templates. All system prompts are registered here. Supports versioning, A/B testing, activation. |
| `agent.py` | LangGraph-based medical agent with supervisor routing (research / analyze / respond / guardrail). Uses `CoreAIWrapper` which delegates to `core_ai.py`. |
| `chat_context.py` | Medical-domain RAG context builder. Analyzes questions, queries health records/predictions/chat history, assembles structured context with citation tracking. |
| `streaming_chat.py` | SSE streaming chat endpoint. `POST /chat/stream` with heartbeat keepalive, cloud provider override via headers. |

### Data Layer

| Module | Role |
|--------|------|
| `models.py` | SQLAlchemy ORM models: `User`, `HealthRecord`, `ChatLog`, `Appointment` |
| `database.py` | Engine creation from `DATABASE_URL`, `SessionLocal` factory, `get_db()` dependency |
| `schemas.py` | Pydantic request/response schemas |
| `rag.py` | JSON-backed vector store and semantic search. Embeddings are delegated to `core_ai.embed_text()`. Retrieval is always user-scoped and can be facility-scoped for hospital contexts; facility-scoped searches exclude legacy documents without matching facility metadata. Enhanced with `RetrievedChunk`, `Citation`, `RAGResult` dataclasses and token budget management. |

### ML Layer

| Module | Role |
|--------|------|
| `prediction.py` | ML model loading (`initialize_models()`), prediction endpoints for diabetes/heart/liver/kidney/lungs, SHAP explanation routes, and clinician/admin audit events for accepted, overridden, or ignored AI prediction decisions |
| `train_diabetes.py` | Diabetes model training script |
| `train_heart.py` | Heart disease model training script |
| `train_liver.py` | Liver disease model training script |
| `advanced_ai.py` | Enterprise features: ensemble prediction, model monitoring, WebSocket streaming |
| `explainability.py` | SHAP-based model explanation |
| `explanation.py` | Prediction explanation endpoints |

### Service Layer

| Module | Role |
|--------|------|
| `main.py` | FastAPI app assembly, middleware stack, security headers, request tracing via `X-Request-ID`, exception masking, router mounting, and startup model loading |
| `auth.py` | JWT authentication, user registration, login, `get_current_user()` dependency |
| `audit.py` | PHI-safe audit event writer and admin audit-log response serializer |
| `sales_readiness.py` | Admin-only matrix for India-first, EU, US, and other-market sales readiness |
| `hospital_operations.py` | Core hospital workflows: departments, OPD/IPD/emergency encounters, admissions, beds, orders, timelines, and operations summaries |
| `monitoring.py` | Vitals capture, deterministic clinician-review signals, doctor patient monitoring views, and admin batch-pattern summaries |
| `diagnostics.py` | Lab/radiology result lifecycle, clinician review workflow, patient result access, and diagnostics operations metrics |
| `pharmacy.py` | Medication inventory, prescription creation, pharmacist dispensing, patient/doctor access views, and pharmacy operations metrics |
| `billing.py` | Billable service catalog, invoice issuance, cashier payment collection, patient billing access, and revenue metrics |
| `discharge.py` | Discharge summaries, admission finalization, bed release, patient discharge access, and discharge operations metrics |
| `nursing.py` | Nursing task assignment, nurse worklists, task completion, patient/doctor task views, and nursing operations metrics |
| `care_events.py` | Role-scoped care-event feeds and dashboard metrics over shared patient timeline events |
| `data_quality.py` | PHI-safe aggregate data quality checks, OpenLineage-shaped lineage events, and quarantine summaries for patient accounts, encounters, vitals, diagnostics, prescriptions, invoices, and interoperability exports. Exposed to admins at `GET /admin/data-quality`. |
| `operational_health.py` | PHI-safe backend operational readiness report for database reachability, duplicate route detection, expected security headers, AI registry validation, data-quality availability, ABDM readiness, DICOMweb readiness, SMART on FHIR readiness, backup readiness, incident-response readiness, retention-policy readiness, and security-assurance readiness. Exposed to admins at `GET /admin/operational-health`. |
| `backup_readiness.py` | PHI-safe backup and restore readiness metadata from deployment runbook environment settings, including restore-test freshness, retention, encryption, owner, and runbook evidence without executing backups or exposing credentials. Exposed to admins at `GET /admin/backup-readiness`. |
| `incident_response.py` | PHI-safe incident response and alert readiness metadata from deployment runbook environment settings, including owners, channels, severity runbooks, breach contacts, and threshold coverage without sending alerts or exposing contacts/secrets. Exposed to admins at `GET /admin/incident-readiness`. |
| `retention_policy.py` | PHI-safe retention policy readiness metadata for patient records, chat logs, audit logs, interoperability exports, vector records, and lakehouse datasets without executing deletion, archive, or legal-hold workflows. Exposed to admins at `GET /admin/retention-readiness`. |
| `security_assurance.py` | PHI-safe security assurance readiness metadata for secret scans, dependency scans, SBOM generation, vulnerability scans, penetration-test evidence, and open critical/high findings without running scanners or exposing contacts/URLs/secrets. Exposed to admins at `GET /admin/security-assurance`. |
| `privacy_operations.py` | PHI-safe privacy operation planner for patient deletion propagation across patient-scoped database tables, vector-store records, lakehouse datasets, interoperability consents/exports, backups, and audit-retention review. Exposed to admins at `GET /admin/privacy/deletion-plan/{patient_id}`. |
| `fhir.py` | FHIR R4-shaped Patient, Encounter, Observation, DiagnosticReport, MedicationRequest, Invoice, CareEvent, and Bundle serialization helpers |
| `abdm.py` | India-first ABDM connector helpers: readiness checks, supported HI type/purpose validation, consent request payload generation, consent callback normalization, payload hashing, and gated outbound submission |
| `dicomweb.py` | DICOMweb/PACS readiness and study metadata-link helpers for QIDO-RS, WADO-RS metadata, and STOW-RS endpoint planning without image bytes |
| `smart_fhir.py` | SMART on FHIR readiness and authorization URL helpers for EHR launch planning without token exchange or secret exposure |
| `terminology.py` | PHI-safe seed terminology catalog for LOINC, SNOMED CT, and ICD-10-CM coding lookups used by integration mapping and demos |
| `interoperability.py` | Standards-friendly FHIR-style export bundles, patient consent controls, reusable export profiles, resource/department filters, signed export manifests, ABDM readiness/consent request/callback endpoints, DICOMweb metadata/readiness endpoints, SMART on FHIR readiness/authorization endpoints, terminology lookup endpoints, assigned-clinician access checks, and admin interoperability metrics |
| `chat.py` | Synchronous chat endpoint + health records CRUD + PDF download |
| `admin.py` | Admin panel endpoints for user management, audit review, operational readiness, backup readiness, incident readiness, retention readiness, security assurance, data quality, AI governance inventories, and privacy deletion-plan review |
| `payments.py` | Razorpay subscription management |
| `appointments.py` | Telemedicine appointment booking |
| `email_service.py` | Email notifications |
| `security.py` | Rate limiting middleware |
| `pdf_service.py` / `pdf_generator.py` | Medical report PDF generation |

---

## AI Inference Fallback Chain

```
Request arrives
    │
    ├─ Has x-ai-provider + x-ai-api-key headers?
    │   └─ Yes → Cloud API (OpenAI / Anthropic / OpenRouter)
    │
    ├─ Ollama running at OLLAMA_BASE_URL?
    │   └─ Yes → Ollama local inference (zero cloud-provider cost when local)
    │
    ├─ GOOGLE_API_KEY set and valid?
    │   └─ Yes → Gemini cloud inference (free tier)
    │
    └─ All unavailable → Return error / fallback message
```

---

## Database Schema (Key Tables)

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `users` | id, username, email, hashed_password, role, full_name, dob, gender, height, weight, blood_type, about_me, diet, activity_level, sleep_hours, stress_level, plan_tier | Extended with lifestyle fields for context |
| `health_records` | id, user_id, record_type, data (JSON), prediction, timestamp | Stores all checkup results |
| `chat_logs` | id, user_id, role, content, timestamp | Chat history for RAG |
| `appointments` | id, patient_id, doctor_id, date, status | Telemedicine scheduling |
| `medication_inventory` | id, medication_name, strength, form, batch_number, quantity_on_hand, reorder_level, status | Pharmacy stock tracking |
| `prescriptions` | id, encounter_id, patient_id, doctor_id, diagnosis_context, status, created_at, dispensed_at | Clinician-created prescriptions |
| `prescription_items` | id, prescription_id, inventory_id, medication_name, dosage, frequency, duration, quantity_prescribed, quantity_dispensed, status | Prescription line items |
| `dispense_records` | id, prescription_id, prescription_item_id, inventory_id, patient_id, dispensed_by_id, quantity_dispensed, status | Pharmacy dispense audit trail |
| `billable_services` | id, service_code, name, service_type, department_id, unit_price, status | Service catalog for hospital billing |
| `invoices` | id, patient_id, encounter_id, admission_id, status, subtotal, discount_amount, tax_amount, total_amount, paid_amount, balance_amount, currency | Patient billing invoices |
| `invoice_line_items` | id, invoice_id, service_id, description, quantity, unit_price, line_total | Invoice line-item detail |
| `billing_payments` | id, invoice_id, patient_id, collected_by_id, amount, payment_method, reference_id, status, collected_at | Cashier payment records |
| `discharge_summaries` | id, admission_id, encounter_id, patient_id, doctor_id, diagnosis_summary, hospital_course, medications, follow_up_plan, discharge_instructions, status, finalized_at | Clinician-authored discharge records |
| `nursing_tasks` | id, patient_id, assigned_nurse_id, created_by_id, completed_by_id, encounter_id, admission_id, department_id, task_type, title, priority, status, due_at, completed_at | Nursing worklist and care coordination tasks |
| `interoperability_consents` | id, patient_id, granted_by_id, revoked_by_id, scope, purpose, recipient_type, status, abdm_request_id, abdm_consent_id, abdm_status, abdm_last_event_at, expires_at, revoked_at, created_at | Patient-granted export consent artifacts with optional ABDM lifecycle references |
| `abdm_consent_events` | id, patient_id, local_consent_id, abdm_request_id, abdm_consent_id, event_type, status, local_consent_status, hi_types, error_code, notification_at, payload_sha256, created_at | PHI-safe ABDM consent callback event log; stores hashes and metadata, not raw callback payloads |
| `interoperability_export_profiles` | id, name, partner_system, resource_types, department_id, created_by_id, status, created_at | Admin-managed reusable export scopes for partner EHR/HIS mapping |
| `interoperability_exports` | id, patient_id, requested_by_id, consent_id, profile_id, export_type, resource_count, filter_summary, bundle_sha256, manifest_signature, signature_algorithm, status, created_at | Export log, profile/filter context, and signed manifest metadata for FHIR-style patient bundle requests |

---

## Adding New Endpoints

1. Create or extend a router file in `backend/`
2. Use `Depends(database.get_db)` for DB sessions
3. Use `Depends(auth.get_current_user)` for authenticated routes
4. For AI features: call the relevant `core_ai` function (`generate()`, `chat()`, `chat_stream()`, `embed_text()`, vision/Ollama helpers) - never import provider SDKs
5. For prompts: register in `prompt_registry.py`, retrieve via `get_prompt()`
6. Mount the router in `main.py`
7. Update `backend/AGENTS.md` module table if adding a new module
