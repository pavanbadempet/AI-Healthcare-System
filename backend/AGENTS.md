# AGENTS.md - Backend

> Scoped rules for `backend/`. Read root `AGENTS.md` first.

## Module Ownership

| Module | Responsibility |
| --- | --- |
| `main.py` | FastAPI app, middleware, request tracing, router mounting |
| `core_ai.py` | **All AI inference/provider access** - text, chat, streaming, embeddings, vision, and Ollama management. Single entry point. |
| `ai_function_registry.py` | Admin-visible inventory of AI-facing functions, clinical safety controls, disclaimer requirements, human-review flags, and provider boundaries |
| `model_cards.py` | Admin-visible model and dataset evidence cards for local prediction models and public training artifacts |
| `agent.py` | LangGraph medical agent orchestration (supervisor -> research/analyze -> generate) |
| `chat.py` | Synchronous chat + health records CRUD |
| `streaming_chat.py` | SSE streaming chat with RAG context and heartbeat |
| `chat_context.py` | Medical-domain RAG context builder |
| `prompt_registry.py` | Version-controlled prompt templates |
| `rag.py` | User/facility-scoped vector store and semantic search; embeddings are delegated to `core_ai.py` |
| `prediction.py` | ML model loading, prediction endpoints, SHAP explanation routes, and clinician/admin audit events for AI prediction review decisions |
| `audit.py` | PHI-safe audit event persistence and admin-facing audit log serialization |
| `sales_readiness.py` | Admin-only regulated-market sales readiness matrix |
| `hospital_operations.py` | Departments, OPD/IPD/emergency encounters, admissions, beds, orders, care timelines, and operations views |
| `monitoring.py` | Vitals observations, clinician-review monitoring signals, and aggregate pattern summaries |
| `diagnostics.py` | Lab/radiology result posting, clinician review workflow, patient result access, and diagnostics metrics |
| `pharmacy.py` | Medication inventory, prescriptions, dispensing, patient/doctor pharmacy views, and pharmacy metrics |
| `billing.py` | Billable service catalog, invoices, cashier payments, patient billing views, and revenue metrics |
| `discharge.py` | Discharge summaries, admission finalization, bed release, patient discharge views, and discharge metrics |
| `nursing.py` | Nursing task assignment, nurse worklists, task completion, patient/doctor task views, and nursing metrics |
| `care_events.py` | Role-scoped care-event feeds and dashboard event metrics over the shared care timeline |
| `data_quality.py` | PHI-safe aggregate data quality checks, OpenLineage-shaped events, and quarantine summaries for admin readiness views |
| `operational_health.py` | PHI-safe backend operational readiness report over DB reachability, route uniqueness, security headers, AI registry, data quality, ABDM readiness, DICOMweb readiness, and SMART on FHIR readiness |
| `backup_readiness.py` | PHI-safe backup and restore readiness metadata from deployment runbook environment settings; does not execute backups or expose credentials |
| `incident_response.py` | PHI-safe incident response and alert readiness metadata from deployment runbook environment settings; does not page responders or expose contacts/secrets |
| `retention_policy.py` | PHI-safe retention policy readiness metadata for patient records, chat logs, audit logs, interoperability exports, vector records, and lakehouse datasets |
| `security_assurance.py` | PHI-safe security assurance readiness metadata for secret scans, dependency scans, SBOM, vulnerability scans, penetration-test evidence, and open critical/high findings |
| `privacy_operations.py` | PHI-safe privacy operation plans for patient deletion propagation across database rows, vector records, lakehouse datasets, interoperability artifacts, backups, and audit retention |
| `fhir.py` | FHIR R4-shaped serialization helpers and bundle validation for local interoperability exports |
| `abdm.py` | Configuration-driven ABDM consent request payload builder, consent callback normalization, readiness checks, and gated connector submission |
| `dicomweb.py` | Configuration-driven DICOMweb readiness and study metadata-link helpers without pixel data or PACS calls |
| `smart_fhir.py` | Configuration-driven SMART on FHIR readiness and authorization URL helpers without token exchange |
| `terminology.py` | PHI-safe seed terminology catalog for LOINC, SNOMED CT, and ICD-10-CM integration mapping |
| `interoperability.py` | FHIR-style patient bundle exports, patient consent controls, reusable export profiles, resource/department filters, signed export manifests, ABDM readiness/consent request/callback endpoints, assigned-doctor/admin access, and interoperability metrics |
| `auth.py` | JWT authentication, password hashing |
| `models.py` | SQLAlchemy ORM models |
| `database.py` | Engine, session factory, `get_db()` |

## Rules

- **AI Provider Abstraction**: Never import `google.generativeai` or `httpx` for AI calls outside `core_ai.py`. Use `core_ai.generate()`, `core_ai.chat()`, `core_ai.chat_stream()`, `core_ai.embed_text()`, or the relevant `core_ai` provider helper.
- **Prompt Management**: Never inline system prompts in route handlers. Register them in `prompt_registry.py` and retrieve via `get_prompt("name")`.
- **Database Sessions**: Always use `Depends(database.get_db)` in FastAPI routes. Never create `SessionLocal()` manually in route handlers.
- **Schema Changes**: Update `models.py`, `schemas.py`, and `main.py` migration/startup logic together when changing persisted fields.
- **Error Handling**: Log errors with `logger.error()`, never expose stack traces to clients. Return structured `{"detail": "..."}` errors.
- **HIPAA Awareness**: Health data (predictions, records, chat logs) must be scoped to `current_user.id`. Never return another user's data.
- **ML Models**: Model files (`*.pkl`) live in project root or `models/`. Loading is centralized in `prediction.initialize_models()`.

## Recommended Tests

```bash
python -m pytest tests/ -v -k "test_chat or test_auth or test_prediction"
```
