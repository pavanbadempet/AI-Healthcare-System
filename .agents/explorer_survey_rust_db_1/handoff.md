# Handoff Report: Rust Architecture & Database Models Survey

**Agent Folder:** `.agents/explorer_survey_rust_db_1`  
**Role:** Rust Architecture & Database Explorer  
**Date:** 2026-08-21  
**Handoff Type:** Hard (Survey Task Complete)

---

## 1. Observation
1. **Existing `rust_gateway/Cargo.toml` (lines 10-36):**
   - Currently uses `axum = "0.8.9"`, `tokio = { version = "1.52.3", features = ["full"] }`, `jsonwebtoken = "10.4.0"`, `bcrypt = "0.19.2"`.
   - `sqlx` is configured strictly with: `sqlx = { version = "0.9.0", features = ["postgres", "runtime-tokio", "tls-rustls", "chrono"] }`. The `sqlite` feature is completely missing.
   - Contains PyO3 CPython extension configuration (`pyo3 = { version = "*", features = ["extension-module"] }`).
2. **Existing `rust_gateway/src/main.rs` (lines 56-85, 145):**
   - Reads `DATABASE_URL` and executes:
     ```rust
     if db_url.contains("postgresql://") || db_url.contains("postgres://") { ... } else {
         println!("DATABASE_URL is not a Postgres connection. Native Edge Gateway database operations will be disabled.");
         "postgres://127.0.0.1/dummy_db".to_string()
     }
     ```
   - Falls back to `proxy_handler_fallback` (lines 194-265) which forwards unhandled requests to Python via `state.python_backend_url`.
3. **Existing `rust_gateway/src/` Modules:**
   - 17 modules present: `appointments.rs`, `auth.rs`, `auth_crypto.rs`, `billing_audit.rs`, `claims.rs`, `clinical_calculator.rs`, `codec.rs`, `dicom_slicer.rs`, `ecg_dsp.rs`, `federated_aggregator.rs`, `fhir.rs`, `interop_grpc.rs`, `lib.rs`, `main.rs`, `phi_redactor.rs`, `tee_enclave.rs`, `telehealth.rs`, `telemetry.rs`, `vector_store.rs`.
   - Only `users` and `appointments` tables have queries implemented.
4. **Backend Database Entities in `backend/models/` and `backend/consent_gate.py`:**
   - Exact count: 46 tables across 15 files:
     - `users` (`backend/models/auth.py:13`)
     - `appointments` (`backend/models/appointments.py:11`)
     - `billable_services`, `invoices`, `invoice_line_items`, `billing_payments`, `insurance_claims` (`backend/models/billing.py:11,28,57,72,91`)
     - `clinical_orders`, `care_events`, `vital_observations`, `monitoring_signals`, `diagnostic_results`, `spark_streaming_metrics` (`backend/models/clinical.py:11,35,57,89,120,154`)
     - `schema_contracts`, `contract_violations`, `data_catalog_datasets`, `data_catalog_lineage`, `feature_attribution_logs` (`backend/models/data_governance.py:10,28,38,59,70`)
     - `discharge_summaries` (`backend/models/discharge.py:11`)
     - `model_feedbacks`, `federated_sync_audits` (`backend/models/federated.py:13,32`)
     - `hospital_facilities`, `departments`, `beds`, `encounters`, `admissions`, `dicom_studies` (`backend/models/hospital.py:11,23,38,55,81,109`)
     - `clinical_alerts`, `patient_insights`, `clinical_ai_corrections` (`backend/models/intelligence.py:13,33,48`)
     - `interoperability_consents`, `abdm_consent_events`, `interoperability_export_profiles`, `interoperability_exports`, `abha_links` (`backend/models/interoperability.py:11,37,60,78,103`)
     - `nursing_tasks` (`backend/models/nursing.py:11`)
     - `medication_inventory`, `prescriptions`, `prescription_items`, `dispense_records` (`backend/models/pharmacy.py:11,28,53,73`)
     - `health_records`, `chat_logs`, `audit_logs` (`backend/models/records.py:13,31,43`)
     - `smart_apps`, `smart_launch_contexts` (`backend/models/smart_app.py:13,30`)
     - `consent_records` (`backend/consent_gate.py:31`)
5. **Database Configuration in `backend/database.py`:**
   - Supports local SQLite WAL mode (`PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA cache_size=-64000`, `PRAGMA mmap_size=536870912`, `PRAGMA busy_timeout=5000`, `PRAGMA foreign_keys=ON`) and PostgreSQL connection pooling with Row Level Security (RLS).

---

## 2. Logic Chain
1. *From Observation 1 & 2*: The existing `rust_gateway` cannot function as a standalone backend in local development with SQLite (`sqlite:///./healthcare.db`) because `sqlx` is missing the `sqlite` feature, `main.rs` disables database operations if not Postgres, and unhandled routes fallback to Python via proxy.
2. *From Observation 3 & 4*: Only 2 out of 46 database tables are currently queried in Rust. To eliminate Python completely, all 46 entities must have corresponding Rust structs (`#[derive(Serialize, Deserialize, sqlx::FromRow)]`) and sqlx repository queries.
3. *From Observation 1, 4 & 5*: An `enum DbPool { Sqlite(Pool<Sqlite>), Postgres(Pool<Postgres>) }` abstraction is required to dynamically instantiate either `SqlitePool` (with WAL PRAGMAs) or `PgPool` (with connection limits and timeouts) based on `DATABASE_URL`.
4. *From ORIGINAL_REQUEST R1 & R3*: All ML inference must move to the `ort` crate (ONNX Runtime) in Rust, eliminating Python and PyO3 dependencies.
5. *From Observations 1-5*: Full survey specifications, struct definitions, sqlx query patterns, and crate manifests have been compiled in `.agents/explorer_survey_rust_db_1/rust_db_survey.md`.

---

## 3. Caveats
1. **PII Encryption Compatibility:** Python used `sqlalchemy_utils.StringEncryptedType` with AES/PKCS5. Rust must use an AES-GCM or AES-CBC/PKCS7 implementation configured with the same key (`DB_ENCRYPTION_KEY` or fallback `"vK1w0r7qYn_2Bq5b-2iL5f3LqYgJ3u1QcQZ1bXoZ0r0="`) to decrypt existing database rows.
2. **Dynamic JSON Fields:** Data governance and catalog models (`schema_contracts`, `data_catalog_datasets`, etc.) store JSON columns. In SQLite these are `TEXT`, while in Postgres they are `JSONB`. In Rust, `serde_json::Value` or JSON string serialization provides clean cross-dialect compatibility.
3. **ONNX Runtime Dynamic Loading:** On Windows/Linux, `ort` with `load-dynamic` will look for `onnxruntime.dll` / `libonnxruntime.so` or download the prebuilt binary during build.

---

## 4. Conclusion
The Rust architecture and database mapping for the rewrite is completely surveyed:
- All **46 database models** across all 15 domains are fully mapped to Rust `sqlx::FromRow` structs.
- The dual SQLite/PostgreSQL `DbPool` architecture with startup schema initialization and WAL mode optimization is designed and documented.
- The dependency upgrade specification for `rust_gateway/Cargo.toml` (Axum 0.8, Tokio, sqlx with dual drivers, `ort` ONNX runtime, `aes-gcm`, `chrono`, `tower-http`) is established.
- The complete survey report is available at `.agents/explorer_survey_rust_db_1/rust_db_survey.md`.

---

## 5. Verification Method
1. **Inspect Survey Report:**
   - Verify all 46 tables and their fields in `rust_db_survey.md`.
2. **Verify Database Models:**
   - Compare `backend/models/*.py` against the catalog in `rust_db_survey.md` Section 3.
3. **Verify sqlx Dependencies:**
   - Check `Cargo.toml` proposed configuration in `rust_db_survey.md` Section 4 against `sqlx` 0.9 feature flags.
