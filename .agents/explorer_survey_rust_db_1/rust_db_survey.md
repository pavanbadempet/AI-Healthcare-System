# Comprehensive Rust Gateway Architecture & Database Survey Report

**Author:** Rust Architecture & Database Explorer  
**Date:** 2026-08-21  
**Project:** AI Healthcare System Backend Rewrite (Python to Rust + Bun/ElysiaJS)  
**Target Workspace:** `c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System`

---

## 1. Executive Summary & Existing `rust_gateway` Architecture

### 1.1 Current State Analysis
The existing `rust_gateway/` is an Axum + Tokio edge proxy server with PyO3 FFI bindings and partial native implementations for selected endpoints.
- **Cargo Package & Dependencies (`Cargo.toml`):**
  - **Axum:** `0.8.9` (current web framework).
  - **Tokio:** `1.52.3` (async runtime with `full` features).
  - **sqlx:** `0.9.0` configured *only* with `features = ["postgres", "runtime-tokio", "tls-rustls", "chrono"]`.
  - **tower-http:** `0.7.0` (CORS, fs, trace, full compression).
  - **Authentication & Crypto:** `jsonwebtoken 10.4.0`, `bcrypt 0.19.2`, `sha2 0.10.8`.
  - **PyO3 & FFI:** `pyo3 = { version = "*", features = ["extension-module"] }`, `rust_gateway_ffi` cdylib/rlib.
  - **Other Utilities:** `mimalloc`, `sysinfo 0.33.0`, `rmp-serde 1.3.0`, `rkyv`, `tonic 0.12`, `prost 0.13`.
- **Existing Source Modules in `rust_gateway/src/`:**
  - `main.rs`: Entry point listening on port `7860`. Initializes PgPool, spawns gRPC server on `50051`, registers native routes (`/v1/auth/token`, `/v1/auth/profile`, `/v1/appointments`, `/v1/telehealth`, `/v1/claims`, `/v1/telemetry`, `/v1/interop/fhir`, `/v1/interop/vector-store`), and sets `fallback(proxy_handler_fallback)` to forward any unhandled routes to the Python backend (`PYTHON_BACKEND_URL`).
  - `lib.rs`: Exposes C-FFI functions (`calculate_egfr_ffi`, `validate_fhir_patient_ffi`, `attest_enclave_ffi`) and PyO3 Python module bindings (`rust_gateway_ffi`).
  - `auth.rs`: Native handler for `/v1/auth/token` and `/v1/auth/profile` querying `users` table via sqlx PgPool.
  - `appointments.rs`: Native CRUD endpoints for `/v1/appointments` and `/v1/appointments/doctors`.
  - `claims.rs`: CMS-1500 claim preflight validation against ICD-10/CPT billing rules.
  - `telehealth.rs`: WebRTC telehealth room session management and token generation.
  - `telemetry.rs`: OpenTelemetry metrics ingest and batching.
  - `fhir.rs`: Fast FHIR resource schema validation (Patient, Observation, Condition, Encounter, DiagnosticReport).
  - `vector_store.rs`: In-memory vectorized search engine with lock-free `ArcSwap` and Rayon parallelization.
  - `interop_grpc.rs`: gRPC Tonic service for telemetry & health check streams.
  - `clinical_calculator.rs`: CKD-EPI eGFR, FIB-4 liver score, qSOFA sepsis calculator.
  - `phi_redactor.rs`: Regex-based PHI scrubber (SSN, MRN, phone, email, names).
  - `ecg_dsp.rs`: Pan-Tompkins real-time QRS detector & bandpass filtering.
  - `dicom_slicer.rs`: DICOM byte preamble inspection and metadata parser.
  - `auth_crypto.rs`: Bcrypt hashing/verification.
  - `billing_audit.rs`: Billing fraud risk scoring.
  - `federated_aggregator.rs`: FedAvg gradient aggregator with differential privacy.
  - `tee_enclave.rs`: Confidential computing model attestation & SHA-256 integrity verification.

### 1.2 Identified Gaps & Deficiencies in Current `rust_gateway`
1. **No SQLite Support:** `Cargo.toml` lacks SQLite feature flags (`features = ["sqlite", "postgres", ...]`). `main.rs` explicitly logs: `"DATABASE_URL is not a Postgres connection. Native Edge Gateway database operations will be disabled."` and falls back to a dummy pool. This violates the **Zero-Configuration Sandbox Rule** where local development must work seamlessly with `sqlite:///./healthcare.db` without Postgres.
2. **Reverse Proxy Fallback Dependency:** Unhandled routes fall back to a Python Uvicorn server (`proxy_handler_fallback`), preventing the complete elimination of Python.
3. **Hardcoded Postgres SQL Syntax:** Existing queries in `auth.rs` and `appointments.rs` use Postgres positional parameters `$1, $2`, which break on SQLite without an abstraction layer or dual-dialect handling.
4. **Missing ORM/Entity Coverage:** Currently only 2 tables (`users`, `appointments`) have rudimentary SQL queries in `rust_gateway/`. The remaining 44 database entities in `backend/models/` have no Rust structs, queries, or migration scripts.
5. **No Embedded ONNX Runtime (`ort`):** Currently models are invoked via Python or FFI; native in-process ML inference with `ort` is needed.

---

## 2. Dual SQLite and PostgreSQL Database Strategy (`DATABASE_URL`)

### 2.1 Architecture Design
To satisfy the **Zero-Configuration Sandbox Rule** and production enterprise elasticity, the Rust backend must support both SQLite (`sqlite:///./healthcare.db` or `sqlite::memory:`) and PostgreSQL (`postgresql://...` or `postgres://...`).

```
                              ┌───────────────────────────────────┐
                              │     DATABASE_URL Environment      │
                              └─────────────────┬─────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
        ┌─────────────────────────┐                           ┌─────────────────────────┐
        │  sqlite:// or :memory:  │                           │  postgres:// or pgsql   │
        └────────────┬────────────┘                           └────────────┬────────────┘
                     │                                                     │
                     ▼                                                     ▼
        ┌─────────────────────────┐                           ┌─────────────────────────┐
        │    sqlx::SqlitePool     │                           │      sqlx::PgPool       │
        │ - PRAGMA journal_mode=WAL│                           │ - max_connections: 20   │
        │ - PRAGMA synchronous=NORM│                          │ - idle_timeout: 300s    │
        │ - foreign_keys = ON     │                           │ - RLS session context   │
        └────────────┬────────────┘                           └────────────┬────────────┘
                     │                                                     │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │          enum DbPool /            │
                              │       DbConnection Manager        │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │  sqlx Native Query Repositories   │
                              │ (Parameterized, Typed, Migrations)│
                              └───────────────────────────────────┘
```

### 2.2 Connection Pool Manager Implementation Pattern
```rust
use sqlx::{sqlite::{SqliteConnectOptions, SqlitePoolOptions}, postgres::{PgPoolOptions}, Pool, Sqlite, Postgres};
use std::str::FromStr;
use std::sync::Arc;

#[derive(Clone)]
pub enum DbPool {
    Sqlite(Pool<Sqlite>),
    Postgres(Pool<Postgres>),
}

impl DbPool {
    pub async fn new(database_url: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        if database_url.starts_with("sqlite:") || database_url.contains(".db") || database_url == ":memory:" {
            let clean_url = database_url.trim_start_matches("sqlite:///").trim_start_matches("sqlite://");
            
            let options = if clean_url == ":memory:" || clean_url.is_empty() {
                SqliteConnectOptions::from_str("sqlite::memory:")?
            } else {
                SqliteConnectOptions::from_str(&format!("sqlite://{}", clean_url))?
                    .create_if_missing(true)
            };

            let pool = SqlitePoolOptions::new()
                .max_connections(16)
                .idle_timeout(std::time::Duration::from_secs(300))
                .connect_with(options)
                .await?;

            // Execute high-performance SQLite PRAGMAs matching Python's set_sqlite_pragma
            sqlx::query("PRAGMA journal_mode = WAL;").execute(&pool).await?;
            sqlx::query("PRAGMA synchronous = NORMAL;").execute(&pool).await?;
            sqlx::query("PRAGMA cache_size = -64000;").execute(&pool).await?; // 64MB page cache
            sqlx::query("PRAGMA temp_store = MEMORY;").execute(&pool).await?;
            sqlx::query("PRAGMA mmap_size = 536870912;").execute(&pool).await?; // 512MB MMAP
            sqlx::query("PRAGMA busy_timeout = 5000;").execute(&pool).await?;
            sqlx::query("PRAGMA foreign_keys = ON;").execute(&pool).await?;

            Ok(DbPool::Sqlite(pool))
        } else {
            let mut pg_url = database_url.to_string();
            if pg_url.starts_with("postgres://") {
                pg_url = pg_url.replacen("postgres://", "postgresql://", 1);
            }
            pg_url = pg_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "");

            let pool = PgPoolOptions::new()
                .max_connections(20)
                .min_connections(2)
                .acquire_timeout(std::time::Duration::from_secs(10))
                .idle_timeout(std::time::Duration::from_secs(300))
                .connect(&pg_url)
                .await?;

            Ok(DbPool::Postgres(pool))
        }
    }
}
```

### 2.3 Schema Initializer / Database Migrations
In Python, `models.Base.metadata.create_all(bind=database.engine)` guarantees instant zero-config startup.
In Rust, we implement a dual schema migration runner:
1. **SQLite Schema Script (`schema_sqlite.sql`)**: Uses `INTEGER PRIMARY KEY AUTOINCREMENT`, `TEXT`, `REAL`, `INTEGER` with `IF NOT EXISTS`.
2. **Postgres Schema Script (`schema_postgres.sql`)**: Uses `SERIAL PRIMARY KEY` / `BIGSERIAL PRIMARY KEY`, `TIMESTAMPTZ`, `JSONB`, `DOUBLE PRECISION`.
3. **Execution on App Startup**:
   ```rust
   pub async fn init_db_schema(pool: &DbPool) -> Result<(), sqlx::Error> {
       match pool {
           DbPool::Sqlite(p) => {
               let sql = include_str!("../migrations/schema_sqlite.sql");
               for statement in sql.split(';') {
                   let trimmed = statement.trim();
                   if !trimmed.is_empty() {
                       sqlx::query(trimmed).execute(p).await?;
                   }
               }
           }
           DbPool::Postgres(p) => {
               let sql = include_str!("../migrations/schema_postgres.sql");
               for statement in sql.split(';') {
                   let trimmed = statement.trim();
                   if !trimmed.is_empty() {
                       sqlx::query(trimmed).execute(p).await?;
                   }
               }
           }
       }
       Ok(())
   }
   ```

---

## 3. Comprehensive Inventory of All 46 SQLAlchemy Models & Rust Structs

Every database model in `backend/models/` and `backend/consent_gate.py` is systematically cataloged below with exact fields, SQLite/Postgres datatypes, constraints, and equivalent Rust struct definitions.

### 3.1 Domain 1: Authentication & Users (`backend/models/auth.py`)
- **Table Name:** `users`
- **Soft Delete:** Yes (`is_deleted: i64`, `deleted_at: Option<NaiveDateTime>`)
- **Constraints:** `CHECK (role IN ('patient', 'doctor', 'nurse', 'pharmacist', 'billing', 'admin'))`
- **Fields:**
  - `id`: `INTEGER PRIMARY KEY` (i64)
  - `username`: `VARCHAR UNIQUE INDEX` (String)
  - `hashed_password`: `TEXT` (String)
  - `created_at`: `DATETIME` (Option<NaiveDateTime>)
  - `role`: `VARCHAR DEFAULT 'patient'` (String)
  - `email`: `TEXT UNIQUE INDEX` (Option<String> - Encrypted PII)
  - `full_name`: `TEXT` (Option<String> - Encrypted PII)
  - `gender`: `TEXT` (Option<String> - Encrypted PII)
  - `blood_type`: `TEXT` (Option<String> - Encrypted PII)
  - `dob`: `TEXT` (Option<String> - Encrypted PII)
  - `height`: `FLOAT` (Option<f64>)
  - `weight`: `FLOAT` (Option<f64>)
  - `existing_ailments`: `TEXT` (Option<String> - Encrypted PII)
  - `profile_picture`: `TEXT` (Option<String>)
  - `about_me`: `TEXT` (Option<String>)
  - `diet`: `VARCHAR` (Option<String>)
  - `activity_level`: `VARCHAR` (Option<String>)
  - `sleep_hours`: `FLOAT` (Option<f64>)
  - `stress_level`: `VARCHAR` (Option<String>)
  - `allow_data_collection`: `INTEGER DEFAULT 1` (i64 / bool)
  - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
  - `plan_tier`: `VARCHAR DEFAULT 'free'` (String)
  - `subscription_expiry`: `DATETIME` (Option<NaiveDateTime>)
  - `razorpay_customer_id`: `VARCHAR INDEX` (Option<String>)
  - `consultation_fee`: `FLOAT DEFAULT 500.0` (f64)
  - `specialization`: `VARCHAR` (Option<String>)
  - `psych_profile`: `TEXT` (Option<String> - Encrypted PII)
  - `totp_secret`: `TEXT` (Option<String> - Encrypted PII)
  - `is_totp_enabled`: `INTEGER DEFAULT 0` (i64 / bool)
  - `is_deleted`: `INTEGER DEFAULT 0 INDEX` (i64 / bool)
  - `deleted_at`: `DATETIME` (Option<NaiveDateTime>)

**Rust Struct Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub hashed_password: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub role: String,
    pub email: Option<String>,
    pub full_name: Option<String>,
    pub gender: Option<String>,
    pub blood_type: Option<String>,
    pub dob: Option<String>,
    pub height: Option<f64>,
    pub weight: Option<f64>,
    pub existing_ailments: Option<String>,
    pub profile_picture: Option<String>,
    pub about_me: Option<String>,
    pub diet: Option<String>,
    pub activity_level: Option<String>,
    pub sleep_hours: Option<f64>,
    pub stress_level: Option<String>,
    pub allow_data_collection: i64,
    pub facility_id: Option<i64>,
    pub plan_tier: String,
    pub subscription_expiry: Option<chrono::NaiveDateTime>,
    pub razorpay_customer_id: Option<String>,
    pub consultation_fee: f64,
    pub specialization: Option<String>,
    pub psych_profile: Option<String>,
    pub totp_secret: Option<String>,
    pub is_totp_enabled: i64,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.2 Domain 2: Appointments (`backend/models/appointments.py`)
- **Table Name:** `appointments`
- **Soft Delete:** Yes (`is_deleted`, `deleted_at`)
- **Indexes & Constraints:** `INDEX (user_id, date_time)`, `CHECK (status IN ('Scheduled', 'Rescheduled', 'Completed', 'Cancelled'))`
- **Fields:**
  - `id`: `INTEGER PRIMARY KEY` (i64)
  - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
  - `user_id`: `INTEGER REFERENCES users(id)` (i64)
  - `doctor_id`: `INTEGER REFERENCES users(id)` (Option<i64>)
  - `specialist`: `VARCHAR` (Option<String>)
  - `date_time`: `DATETIME` (Option<NaiveDateTime>)
  - `reason`: `TEXT` (Option<String>)
  - `status`: `VARCHAR DEFAULT 'Scheduled'` (String)
  - `created_at`: `DATETIME` (Option<NaiveDateTime>)
  - `is_deleted`: `INTEGER DEFAULT 0` (i64)
  - `deleted_at`: `DATETIME` (Option<NaiveDateTime>)

**Rust Struct Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Appointment {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub user_id: i64,
    pub doctor_id: Option<i64>,
    pub specialist: Option<String>,
    pub date_time: Option<chrono::NaiveDateTime>,
    pub reason: Option<String>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.3 Domain 3: Billing & Financials (`backend/models/billing.py`)
Covers 5 tables:
1. `billable_services`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
   - `service_code`: `VARCHAR UNIQUE INDEX` (String)
   - `name`: `VARCHAR` (String)
   - `service_type`: `VARCHAR` (String)
   - `department_id`: `INTEGER REFERENCES departments(id)` (Option<i64>)
   - `unit_price`: `FLOAT DEFAULT 0` (f64)
   - `status`: `VARCHAR DEFAULT 'active'` (String)
   - `created_at`: `DATETIME` (Option<NaiveDateTime>)

2. `invoices`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
   - `patient_id`: `INTEGER REFERENCES users(id) INDEX` (i64)
   - `encounter_id`: `INTEGER REFERENCES encounters(id)` (Option<i64>)
   - `admission_id`: `INTEGER REFERENCES admissions(id)` (Option<i64>)
   - `created_by_id`: `INTEGER REFERENCES users(id)` (Option<i64>)
   - `status`: `VARCHAR DEFAULT 'issued'` (String - issued, paid, partially_paid, voided, overdue)
   - `subtotal`: `FLOAT DEFAULT 0` (f64)
   - `discount_amount`: `FLOAT DEFAULT 0` (f64)
   - `tax_amount`: `FLOAT DEFAULT 0` (f64)
   - `total_amount`: `FLOAT DEFAULT 0` (f64)
   - `paid_amount`: `FLOAT DEFAULT 0` (f64)
   - `balance_amount`: `FLOAT DEFAULT 0` (f64)
   - `currency`: `VARCHAR DEFAULT 'INR'` (String)
   - `created_at`, `issued_at`: `DATETIME` (Option<NaiveDateTime>)

3. `invoice_line_items`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `invoice_id`: `INTEGER REFERENCES invoices(id) INDEX` (i64)
   - `service_id`: `INTEGER REFERENCES billable_services(id)` (Option<i64>)
   - `description`: `VARCHAR` (String)
   - `quantity`: `FLOAT DEFAULT 1` (f64)
   - `unit_price`: `FLOAT DEFAULT 0` (f64)
   - `line_total`: `FLOAT DEFAULT 0` (f64)

4. `billing_payments`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
   - `invoice_id`: `INTEGER REFERENCES invoices(id) INDEX` (i64)
   - `patient_id`: `INTEGER REFERENCES users(id) INDEX` (i64)
   - `collected_by_id`: `INTEGER REFERENCES users(id)` (Option<i64>)
   - `amount`: `FLOAT DEFAULT 0` (f64)
   - `payment_method`: `VARCHAR` (String)
   - `reference_id`: `VARCHAR` (Option<String>)
   - `status`: `VARCHAR DEFAULT 'collected'` (String)
   - `collected_at`: `DATETIME` (Option<NaiveDateTime>)

5. `insurance_claims`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `claim_number`: `VARCHAR UNIQUE INDEX` (String)
   - `patient_name`: `VARCHAR` (String)
   - `payer_name`: `VARCHAR` (String)
   - `policy_id`: `VARCHAR` (String)
   - `claim_amount`: `FLOAT DEFAULT 0` (f64)
   - `copay_amount`: `FLOAT DEFAULT 0` (f64)
   - `status`: `VARCHAR DEFAULT 'submitted'` (String)
   - `created_at`: `DATETIME` (Option<NaiveDateTime>)

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct BillableService {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub service_code: String,
    pub name: String,
    pub service_type: String,
    pub department_id: Option<i64>,
    pub unit_price: f64,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Invoice {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub encounter_id: Option<i64>,
    pub admission_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub status: String,
    pub subtotal: f64,
    pub discount_amount: f64,
    pub tax_amount: f64,
    pub total_amount: f64,
    pub paid_amount: f64,
    pub balance_amount: f64,
    pub currency: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub issued_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct InvoiceLineItem {
    pub id: i64,
    pub invoice_id: i64,
    pub service_id: Option<i64>,
    pub description: String,
    pub quantity: f64,
    pub unit_price: f64,
    pub line_total: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct BillingPayment {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub invoice_id: i64,
    pub patient_id: i64,
    pub collected_by_id: Option<i64>,
    pub amount: f64,
    pub payment_method: String,
    pub reference_id: Option<String>,
    pub status: String,
    pub collected_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct InsuranceClaim {
    pub id: i64,
    pub claim_number: String,
    pub patient_name: String,
    pub payer_name: String,
    pub policy_id: String,
    pub claim_amount: f64,
    pub copay_amount: f64,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.4 Domain 4: Clinical Orders, Observations & Diagnostics (`backend/models/clinical.py`)
Covers 6 tables:
1. `clinical_orders`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
   - `encounter_id`: `INTEGER REFERENCES encounters(id)` (Option<i64>)
   - `patient_id`: `INTEGER REFERENCES users(id)` (i64)
   - `doctor_id`: `INTEGER REFERENCES users(id)` (Option<i64>)
   - `department_id`: `INTEGER REFERENCES departments(id)` (Option<i64>)
   - `order_type`: `VARCHAR` (String - lab, radiology, pharmacy, procedure, nursing)
   - `title`: `VARCHAR` (String)
   - `priority`: `VARCHAR DEFAULT 'routine'` (String - routine, urgent, stat)
   - `status`: `VARCHAR DEFAULT 'ordered'` (String - ordered, in_progress, completed, cancelled)
   - `notes`: `TEXT` (Option<String>)
   - `created_at`, `completed_at`: `DATETIME` (Option<NaiveDateTime>)

2. `care_events`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`: `INTEGER REFERENCES hospital_facilities(id)` (Option<i64>)
   - `patient_id`: `INTEGER REFERENCES users(id)` (i64)
   - `actor_user_id`: `INTEGER REFERENCES users(id)` (Option<i64>)
   - `encounter_id`: `INTEGER REFERENCES encounters(id)` (Option<i64>)
   - `department_id`: `INTEGER REFERENCES departments(id)` (Option<i64>)
   - `event_type`: `VARCHAR` (String)
   - `title`: `VARCHAR` (String)
   - `summary`: `TEXT` (Option<String>)
   - `severity`: `VARCHAR DEFAULT 'info'` (String)
   - `created_at`: `DATETIME` (Option<NaiveDateTime>)

3. `vital_observations`:
   - Soft delete: Yes (`is_deleted`, `deleted_at`)
   - Unique/Indexes: `UNIQUE (patient_id, observed_at)`
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`, `patient_id`, `recorded_by_id`, `encounter_id`, `department_id`
   - `source`: `VARCHAR DEFAULT 'manual'` (String)
   - `heart_rate`, `systolic_bp`, `diastolic_bp`, `spo2`, `temperature_c`, `respiratory_rate`, `blood_glucose`: `FLOAT` (Option<f64>)
   - `observed_at`, `created_at`: `DATETIME` (Option<NaiveDateTime>)

4. `monitoring_signals`:
   - Unique: `UNIQUE (vital_observation_id, signal_type)`
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`, `patient_id`, `vital_observation_id`, `encounter_id`, `department_id`
   - `signal_type`: `VARCHAR` (String)
   - `severity`: `VARCHAR DEFAULT 'info'` (String - info, warning, critical)
   - `title`, `summary`, `status` (open, acknowledged, resolved), `created_at`

5. `diagnostic_results`:
   - Soft delete: Yes (`is_deleted`, `deleted_at`)
   - Index: `INDEX (patient_id, created_at)`
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `facility_id`, `order_id`, `encounter_id`, `patient_id`, `doctor_id`, `department_id`
   - `result_type`, `title`, `summary`, `abnormal_flag` (i64), `status` (final, preliminary, corrected), `review_status`, `review_note`, `reviewed_by_id`, `reviewed_at`, `created_at`

6. `spark_streaming_metrics`:
   - `id`: `INTEGER PRIMARY KEY` (i64)
   - `batch_id`: `INTEGER` (i64)
   - `records_processed`: `INTEGER` (i64)
   - `processing_time_ms`: `FLOAT` (f64)
   - `ml_latency_ms`: `FLOAT` (f64)
   - `timestamp`: `DATETIME` (Option<NaiveDateTime>)

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ClinicalOrder {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub order_type: String,
    pub title: String,
    pub priority: String,
    pub status: String,
    pub notes: Option<String>,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub completed_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct CareEvent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub actor_user_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub event_type: String,
    pub title: String,
    pub summary: Option<String>,
    pub severity: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct VitalObservation {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub recorded_by_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub source: String,
    pub heart_rate: Option<f64>,
    pub systolic_bp: Option<f64>,
    pub diastolic_bp: Option<f64>,
    pub spo2: Option<f64>,
    pub temperature_c: Option<f64>,
    pub respiratory_rate: Option<f64>,
    pub blood_glucose: Option<f64>,
    pub observed_at: Option<chrono::NaiveDateTime>,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct MonitoringSignal {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub vital_observation_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub department_id: Option<i64>,
    pub signal_type: String,
    pub severity: String,
    pub title: String,
    pub summary: String,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DiagnosticResult {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub order_id: i64,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub result_type: String,
    pub title: String,
    pub summary: String,
    pub abnormal_flag: i64,
    pub status: String,
    pub review_status: String,
    pub review_note: Option<String>,
    pub reviewed_by_id: Option<i64>,
    pub reviewed_at: Option<chrono::NaiveDateTime>,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct SparkStreamingMetrics {
    pub id: i64,
    pub batch_id: i64,
    pub records_processed: i64,
    pub processing_time_ms: f64,
    pub ml_latency_ms: f64,
    pub timestamp: Option<chrono::NaiveDateTime>,
}
```

---

### 3.5 Domain 5: Hospital Operations (`backend/models/hospital.py`)
Covers 6 tables:
1. `hospital_facilities`: `id`, `name` (unique), `facility_type`, `country`, `region`, `status`, `created_at`.
2. `departments`: `id`, `facility_id`, `name` (unique), `department_type` (OPD, IPD, Emergency, Diagnostics, Pharmacy), `location`, `description`, `status`, `created_at`.
3. `beds`: `id`, `facility_id`, `department_id`, `bed_number`, `ward`, `status` (available, occupied, maintenance), `current_patient_id`, `created_at`.
4. `encounters`: Soft delete. `id`, `facility_id`, `patient_id`, `doctor_id`, `department_id`, `encounter_type`, `reason`, `priority`, `status` (open, closed, cancelled), `started_at`, `ended_at`.
5. `admissions`: Soft delete. `id`, `facility_id`, `encounter_id`, `patient_id`, `doctor_id`, `department_id`, `bed_id`, `admitted_at`, `discharged_at`, `reason`, `status` (active, discharged, cancelled).
6. `dicom_studies`: `id`, `study_uid` (unique), `patient_id`, `modality`, `target_vault`, `file_name`, `file_size_kb`, `is_preamble_valid`, `created_at`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct HospitalFacility {
    pub id: i64,
    pub name: String,
    pub facility_type: String,
    pub country: Option<String>,
    pub region: Option<String>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Department {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub name: String,
    pub department_type: String,
    pub location: Option<String>,
    pub description: Option<String>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Bed {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub department_id: i64,
    pub bed_number: String,
    pub ward: Option<String>,
    pub status: String,
    pub current_patient_id: Option<i64>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Encounter {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub encounter_type: String,
    pub reason: Option<String>,
    pub priority: String,
    pub status: String,
    pub started_at: Option<chrono::NaiveDateTime>,
    pub ended_at: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Admission {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: i64,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub department_id: Option<i64>,
    pub bed_id: Option<i64>,
    pub admitted_at: Option<chrono::NaiveDateTime>,
    pub discharged_at: Option<chrono::NaiveDateTime>,
    pub reason: Option<String>,
    pub status: String,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DicomStudy {
    pub id: i64,
    pub study_uid: String,
    pub patient_id: Option<i64>,
    pub modality: String,
    pub target_vault: String,
    pub file_name: String,
    pub file_size_kb: i64,
    pub is_preamble_valid: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.6 Domain 6: Pharmacy & Inventory (`backend/models/pharmacy.py`)
Covers 4 tables:
1. `medication_inventory`: `id`, `facility_id`, `medication_name`, `strength`, `form`, `batch_number`, `quantity_on_hand` (f64), `reorder_level` (f64), `status`, `created_at`.
2. `prescriptions`: Soft delete. `id`, `facility_id`, `encounter_id`, `patient_id`, `doctor_id`, `diagnosis_context`, `status`, `created_at`, `dispensed_at`.
3. `prescription_items`: `id`, `prescription_id`, `inventory_id`, `medication_name`, `dosage`, `frequency`, `duration`, `quantity_prescribed` (f64), `quantity_dispensed` (f64), `instructions`, `status` (pending, dispensed, partially_dispensed, cancelled).
4. `dispense_records`: `id`, `facility_id`, `prescription_id`, `prescription_item_id`, `inventory_id`, `patient_id`, `dispensed_by_id`, `quantity_dispensed` (f64), `status`, `created_at`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct MedicationInventory {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub medication_name: String,
    pub strength: Option<String>,
    pub form: Option<String>,
    pub batch_number: Option<String>,
    pub quantity_on_hand: f64,
    pub reorder_level: f64,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Prescription {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub diagnosis_context: Option<String>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub dispensed_at: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct PrescriptionItem {
    pub id: i64,
    pub prescription_id: i64,
    pub inventory_id: Option<i64>,
    pub medication_name: String,
    pub dosage: String,
    pub frequency: String,
    pub duration: String,
    pub quantity_prescribed: f64,
    pub quantity_dispensed: f64,
    pub instructions: Option<String>,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DispenseRecord {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub prescription_id: i64,
    pub prescription_item_id: Option<i64>,
    pub inventory_id: Option<i64>,
    pub patient_id: i64,
    pub dispensed_by_id: Option<i64>,
    pub quantity_dispensed: f64,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.7 Domain 7: Health Records, Chat & Audit Logs (`backend/models/records.py`)
Covers 3 tables:
1. `health_records`: Soft delete. `id`, `user_id`, `record_type` (diabetes, heart, liver, kidney, lungs), `data` (Encrypted JSON Text), `prediction`, `timestamp`.
2. `chat_logs`: Soft delete. `id`, `user_id`, `role` (user/assistant), `content`, `timestamp`.
3. `audit_logs`: Soft delete. `id`, `facility_id`, `admin_id`, `target_user_id`, `action`, `timestamp`, `details`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct HealthRecord {
    pub id: i64,
    pub user_id: Option<i64>,
    pub record_type: String,
    pub data: Option<String>,
    pub prediction: Option<String>,
    pub timestamp: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ChatLog {
    pub id: i64,
    pub user_id: Option<i64>,
    pub role: String,
    pub content: Option<String>,
    pub timestamp: Option<chrono::NaiveDateTime>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct AuditLog {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub admin_id: i64,
    pub target_user_id: Option<i64>,
    pub action: String,
    pub timestamp: Option<chrono::NaiveDateTime>,
    pub details: Option<String>,
    pub is_deleted: i64,
    pub deleted_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.8 Domain 8: Data Governance & Schema Contracts (`backend/models/data_governance.py`)
Covers 5 tables:
1. `schema_contracts`: `id`, `contract_id` (unique), `name`, `version`, `producer`, `consumer`, `schema_definition` (JSON), `required_fields` (JSON), `compatibility_mode`, `sla_freshness_minutes`, `quality_threshold`, `created_at`, `updated_at`.
2. `contract_violations`: `id`, `contract_id`, `errors` (JSON), `record_count`, `timestamp`.
3. `data_catalog_datasets`: `id`, `dataset_id` (unique), `name`, `description`, `owner`, `schema_definition` (JSON), `tags` (JSON), `sla_hours`, `freshness_field`, `quality_score`, `row_count`, `size_bytes`, `location`, `format`, `created_at`, `updated_at`.
4. `data_catalog_lineage`: `id`, `dataset_id`, `upstream` (JSON), `downstream` (JSON), `column_lineage` (JSON), `updated_at`.
5. `feature_attribution_logs`: `id`, `model_name`, `model_version`, `features` (JSON), `attributions` (JSON), `prediction_value`, `timestamp`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct SchemaContract {
    pub id: i64,
    pub contract_id: String,
    pub name: String,
    pub version: i64,
    pub producer: String,
    pub consumer: String,
    pub schema_definition: String, // JSON serialized
    pub required_fields: String,   // JSON serialized
    pub compatibility_mode: String,
    pub sla_freshness_minutes: i64,
    pub quality_threshold: f64,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub updated_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ContractViolation {
    pub id: i64,
    pub contract_id: String,
    pub errors: String, // JSON array
    pub record_count: i64,
    pub timestamp: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DataCatalogDataset {
    pub id: i64,
    pub dataset_id: String,
    pub name: String,
    pub description: Option<String>,
    pub owner: String,
    pub schema_definition: String,
    pub tags: String,
    pub sla_hours: i64,
    pub freshness_field: String,
    pub quality_score: f64,
    pub row_count: i64,
    pub size_bytes: i64,
    pub location: Option<String>,
    pub format: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub updated_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DataCatalogLineage {
    pub id: i64,
    pub dataset_id: String,
    pub upstream: String,
    pub downstream: String,
    pub column_lineage: Option<String>,
    pub updated_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct FeatureAttributionLog {
    pub id: i64,
    pub model_name: String,
    pub model_version: String,
    pub features: String,
    pub attributions: String,
    pub prediction_value: i64,
    pub timestamp: Option<chrono::NaiveDateTime>,
}
```

---

### 3.9 Domain 9: Interoperability, ABDM & ABHA (`backend/models/interoperability.py`)
Covers 5 tables:
1. `interoperability_consents`: `id`, `facility_id`, `patient_id`, `granted_by_id`, `revoked_by_id`, `scope`, `purpose`, `recipient_type`, `status`, `abdm_request_id`, `abdm_consent_id`, `abdm_status`, `abdm_last_event_at`, `expires_at`, `revoked_at`, `created_at`.
2. `abdm_consent_events`: `id`, `facility_id`, `patient_id`, `local_consent_id`, `abdm_request_id`, `abdm_consent_id`, `event_type`, `status`, `local_consent_status`, `hi_types`, `error_code`, `notification_at`, `payload_sha256`, `created_at`.
3. `interoperability_export_profiles`: `id`, `facility_id`, `name`, `partner_system`, `resource_types`, `department_id`, `created_by_id`, `status`, `created_at`.
4. `interoperability_exports`: `id`, `facility_id`, `patient_id`, `requested_by_id`, `consent_id`, `profile_id`, `export_type`, `resource_count`, `filter_summary`, `bundle_sha256`, `manifest_signature`, `signature_algorithm`, `status`, `created_at`.
5. `abha_links`: `id`, `patient_id`, `abha_address` (unique), `kyc_transaction_id`, `consent_purpose`, `status`, `created_at`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct InteroperabilityConsent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub granted_by_id: Option<i64>,
    pub revoked_by_id: Option<i64>,
    pub scope: String,
    pub purpose: Option<String>,
    pub recipient_type: String,
    pub status: String,
    pub abdm_request_id: Option<String>,
    pub abdm_consent_id: Option<String>,
    pub abdm_status: Option<String>,
    pub abdm_last_event_at: Option<chrono::NaiveDateTime>,
    pub expires_at: Option<chrono::NaiveDateTime>,
    pub revoked_at: Option<chrono::NaiveDateTime>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct AbdmConsentEvent {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub local_consent_id: Option<i64>,
    pub abdm_request_id: String,
    pub abdm_consent_id: Option<String>,
    pub event_type: String,
    pub status: String,
    pub local_consent_status: Option<String>,
    pub hi_types: Option<String>,
    pub error_code: Option<String>,
    pub notification_at: Option<chrono::NaiveDateTime>,
    pub payload_sha256: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct InteroperabilityExportProfile {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub name: String,
    pub partner_system: Option<String>,
    pub resource_types: Option<String>,
    pub department_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct InteroperabilityExport {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: Option<i64>,
    pub requested_by_id: Option<i64>,
    pub consent_id: Option<i64>,
    pub profile_id: Option<i64>,
    pub export_type: String,
    pub resource_count: i64,
    pub filter_summary: Option<String>,
    pub bundle_sha256: Option<String>,
    pub manifest_signature: Option<String>,
    pub signature_algorithm: String,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct AbhaLink {
    pub id: i64,
    pub patient_id: Option<i64>,
    pub abha_address: String,
    pub kyc_transaction_id: Option<String>,
    pub consent_purpose: String,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.10 Domain 10: Clinical Intelligence, Alerts & AI Corrections (`backend/models/intelligence.py`)
Covers 3 tables:
1. `clinical_alerts`: `id`, `patient_id`, `alert_type`, `severity` (CRITICAL, WARNING, INFO), `message`, `source_event_id`, `is_acknowledged` (i64/bool), `acknowledged_by`, `acknowledged_at`, `created_at`.
2. `patient_insights`: `id`, `patient_id`, `insight_type` (risk_summary, trend_analysis), `content` (JSON Text), `model_version`, `created_at`.
3. `clinical_ai_corrections`: `id`, `patient_id`, `clinician_id`, `function_name`, `original_ai_output`, `corrected_output`, `override_action` (accepted, overridden, ignored), `override_reason`, `created_at`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ClinicalAlert {
    pub id: i64,
    pub patient_id: i64,
    pub alert_type: String,
    pub severity: String,
    pub message: String,
    pub source_event_id: Option<String>,
    pub is_acknowledged: i64,
    pub acknowledged_by: Option<i64>,
    pub acknowledged_at: Option<chrono::NaiveDateTime>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct PatientInsight {
    pub id: i64,
    pub patient_id: i64,
    pub insight_type: String,
    pub content: String,
    pub model_version: Option<String>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ClinicalAICorrection {
    pub id: i64,
    pub patient_id: i64,
    pub clinician_id: i64,
    pub function_name: String,
    pub original_ai_output: String,
    pub corrected_output: Option<String>,
    pub override_action: String,
    pub override_reason: Option<String>,
    pub created_at: Option<chrono::NaiveDateTime>,
}
```

---

### 3.11 Domain 11: Discharge, Nursing, Federated, SMART on FHIR & Consent
Covers remaining 7 tables:
1. `discharge_summaries` (`backend/models/discharge.py`): `id`, `facility_id`, `admission_id`, `encounter_id`, `patient_id`, `doctor_id`, `diagnosis_summary`, `hospital_course`, `medications`, `follow_up_plan`, `discharge_instructions`, `status` (draft, finalized, amended), `created_at`, `finalized_at`.
2. `nursing_tasks` (`backend/models/nursing.py`): `id`, `facility_id`, `patient_id`, `assigned_nurse_id`, `created_by_id`, `completed_by_id`, `encounter_id`, `admission_id`, `department_id`, `task_type`, `title`, `instructions`, `priority`, `status`, `due_at`, `completed_at`, `completion_note`, `created_at`.
3. `model_feedbacks` (`backend/models/federated.py`): `id`, `patient_id`, `model_name`, `input_features` (JSON), `prediction_result` (JSON), `corrected_label`, `clinician_id`, `status` (pending_sync, synced), `created_at`.
4. `federated_sync_audits` (`backend/models/federated.py`): `id`, `sync_run_id` (unique), `node_id`, `model_name`, `records_synced` (i64), `epsilon_consumed` (f64), `delta_consumed` (f64), `status` (completed, failed, rejected), `error_message`, `created_at`.
5. `smart_apps` (`backend/models/smart_app.py`): `id`, `app_name` (unique), `client_id` (unique), `redirect_uri`, `launch_url`, `scopes`, `is_active` (i64/bool), `created_at`.
6. `smart_launch_contexts` (`backend/models/smart_app.py`): `id`, `app_id`, `patient_id`, `user_id`, `launch_token` (unique), `auth_code`, `scope`, `expires_at`, `created_at`.
7. `consent_records` (`backend/consent_gate.py`): `id`, `user_id`, `eula_version`, `accepted_at`, `ip_address`, `user_agent`.

**Rust Struct Definitions:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct DischargeSummary {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub admission_id: i64,
    pub encounter_id: Option<i64>,
    pub patient_id: i64,
    pub doctor_id: Option<i64>,
    pub diagnosis_summary: String,
    pub hospital_course: String,
    pub medications: Option<String>,
    pub follow_up_plan: Option<String>,
    pub discharge_instructions: Option<String>,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
    pub finalized_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct NursingTask {
    pub id: i64,
    pub facility_id: Option<i64>,
    pub patient_id: i64,
    pub assigned_nurse_id: Option<i64>,
    pub created_by_id: Option<i64>,
    pub completed_by_id: Option<i64>,
    pub encounter_id: Option<i64>,
    pub admission_id: Option<i64>,
    pub department_id: Option<i64>,
    pub task_type: String,
    pub title: String,
    pub instructions: Option<String>,
    pub priority: String,
    pub status: String,
    pub due_at: Option<chrono::NaiveDateTime>,
    pub completed_at: Option<chrono::NaiveDateTime>,
    pub completion_note: Option<String>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ModelFeedback {
    pub id: i64,
    pub patient_id: i64,
    pub model_name: String,
    pub input_features: String,
    pub prediction_result: String,
    pub corrected_label: String,
    pub clinician_id: i64,
    pub status: String,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct FederatedSyncAudit {
    pub id: i64,
    pub sync_run_id: String,
    pub node_id: String,
    pub model_name: String,
    pub records_synced: i64,
    pub epsilon_consumed: f64,
    pub delta_consumed: f64,
    pub status: String,
    pub error_message: Option<String>,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct SmartApp {
    pub id: i64,
    pub app_name: String,
    pub client_id: String,
    pub redirect_uri: String,
    pub launch_url: String,
    pub scopes: String,
    pub is_active: i64,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct SmartLaunchContext {
    pub id: i64,
    pub app_id: i64,
    pub patient_id: i64,
    pub user_id: i64,
    pub launch_token: String,
    pub auth_code: Option<String>,
    pub scope: String,
    pub expires_at: chrono::NaiveDateTime,
    pub created_at: Option<chrono::NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct ConsentRecord {
    pub id: i64,
    pub user_id: i64,
    pub eula_version: String,
    pub accepted_at: chrono::NaiveDateTime,
    pub ip_address: Option<String>,
    pub user_agent: Option<String>,
}
```

---

## 4. Required Rust Crates and Dependencies Update

To achieve 100% feature parity, native ML inference with ONNX Runtime, and robust dual database support, `rust_gateway/Cargo.toml` must be updated with the following crates:

```toml
[package]
name = "rust_gateway"
version = "0.2.0"
edition = "2024"

[dependencies]
# Web & Async Runtime
axum = { version = "0.8.9", features = ["ws", "multipart", "macros"] }
tokio = { version = "1.52.3", features = ["full"] }
tower = { version = "0.5.2", features = ["full"] }
tower-http = { version = "0.7.0", features = ["cors", "fs", "trace", "compression-full", "timeout"] }
http-body-util = "0.1.3"

# Database & SQLx (Dual SQLite + PostgreSQL)
sqlx = { version = "0.9.0", features = [
    "runtime-tokio",
    "tls-rustls",
    "chrono",
    "sqlite",
    "postgres",
    "macros",
    "migrate",
    "json"
] }

# ML & ONNX Runtime (Native In-Process Inference)
ort = { version = "2.0.0-rc.9", features = ["load-dynamic", "ndarray"] }
ndarray = "0.16.1"

# Serialization & Data Formats
serde = { version = "1.0.228", features = ["derive"] }
serde_json = "1.0.150"
serde_urlencoded = "0.7.1"
rmp-serde = "1.3.0"
rkyv = { version = "0.8.10", features = ["validation"] }

# Auth, Security & Encryption
jsonwebtoken = "10.4.0"
bcrypt = "0.19.2"
aes-gcm = "0.10.3"
sha2 = "0.10.8"
rand = "0.8.5"
base64 = "0.22.1"

# Utilities & Telemetry
chrono = { version = "0.4.40", features = ["serde"] }
dotenvy = "0.15.7"
sysinfo = "0.33.0"
mimalloc = "0.1.43"
regex = "1.13.1"
rayon = "1.10.0"
arc-swap = "1.7.1"
reqwest = { version = "0.13.4", features = ["json", "stream"] }
tracing = "0.1.41"
tracing-subscriber = { version = "0.3.19", features = ["env-filter", "json"] }

# gRPC Interoperability
tonic = "0.12"
prost = "0.13"
prost-types = "0.13"

[build-dependencies]
tonic-build = "0.12"
prost-build = "0.13"

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true
```

---

## 5. Security & PII Encryption (AES-GCM in Rust)

In Python, `sqlalchemy_utils.StringEncryptedType` with AES/PKCS5 was used.
In Rust, we implement AES-256-GCM / PKCS#7 encryption compatible with the stored ciphertext:
```rust
use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce, Key
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine};

pub struct EncryptionService {
    key: Key<Aes256Gcm>,
}

impl EncryptionService {
    pub fn new(key_b64: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let key_bytes = BASE64.decode(key_b64)?;
        let key = *Key::<Aes256Gcm>::from_slice(&key_bytes[..32]);
        Ok(Self { key })
    }

    pub fn encrypt(&self, plaintext: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let cipher = Aes256Gcm::new(&self.key);
        let nonce = Nonce::from_slice(b"unique_nonce"); // or random 12-byte nonce
        let ciphertext = cipher.encrypt(nonce, plaintext.as_bytes())
            .map_err(|e| format!("Encryption error: {:?}", e))?;
        Ok(BASE64.encode(ciphertext))
    }

    pub fn decrypt(&self, ciphertext_b64: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let cipher = Aes256Gcm::new(&self.key);
        let ciphertext = BASE64.decode(ciphertext_b64)?;
        let nonce = Nonce::from_slice(b"unique_nonce");
        let plaintext = cipher.decrypt(nonce, ciphertext.as_ref())
            .map_err(|e| format!("Decryption error: {:?}", e))?;
        Ok(String::from_utf8(plaintext)?)
    }
}
```

---

## 6. Zero-Python ONNX Runtime ML Inference Architecture

All models (`diabetes_model.onnx`, `heart_disease_model.onnx`, `kidney_disease_model.onnx`, `liver_disease_model.onnx`, `lungs_disease_model.onnx`) and scalers (`kidney_scaler.onnx`, `liver_scaler.onnx`, `lungs_scaler.onnx`) will be evaluated in-process via `ort`.

### ML Inference Engine Implementation Structure:
```rust
use ort::{session::Session, value::Tensor};
use ndarray::Array2;
use std::sync::Arc;

pub struct MlPredictorState {
    pub diabetes_session: Arc<Session>,
    pub heart_session: Arc<Session>,
    pub kidney_session: Arc<Session>,
    pub liver_session: Arc<Session>,
    pub lungs_session: Arc<Session>,
}

impl MlPredictorState {
    pub fn load_models() -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let diabetes = Session::builder()?.commit_from_file("backend/diabetes_model.onnx")?;
        let heart = Session::builder()?.commit_from_file("backend/heart_disease_model.onnx")?;
        let kidney = Session::builder()?.commit_from_file("backend/kidney_disease_model.onnx")?;
        let liver = Session::builder()?.commit_from_file("backend/liver_disease_model.onnx")?;
        let lungs = Session::builder()?.commit_from_file("backend/lungs_disease_model.onnx")?;

        Ok(Self {
            diabetes_session: Arc::new(diabetes),
            heart_session: Arc::new(heart),
            kidney_session: Arc::new(kidney),
            liver_session: Arc::new(liver),
            lungs_session: Arc::new(lungs),
        })
    }

    pub fn predict_diabetes(&self, input: &[f32; 8]) -> Result<(f64, String), Box<dyn std::error::Error + Send + Sync>> {
        let array = Array2::from_shape_vec((1, 8), input.to_vec())?;
        let tensor = Tensor::from_array(array)?;
        let outputs = self.diabetes_session.run(ort::inputs![tensor]?)?;
        let output_tensor = outputs[0].try_extract_tensor::<f32>()?;
        let raw_val = output_tensor[[0, 0]] as f64;
        let risk = if raw_val >= 0.5 { "High Risk" } else { "Low Risk" };
        Ok((raw_val, risk.to_string()))
    }
}
```

---

## 7. Migration Roadmap & Execution Architecture

1. **Step 1: Update `rust_gateway/Cargo.toml`** with dual sqlite/postgres sqlx, `ort`, `aes-gcm`, `tracing`, and `chrono`.
2. **Step 2: Implement `src/db.rs`** with `DbPool` enum supporting SQLite WAL PRAGMAs and PostgreSQL pooling with RLS.
3. **Step 3: Add `src/models/`** containing typed structs for all 46 database entities with `sqlx::FromRow`.
4. **Step 4: Add `src/repositories/`** containing parameterized CRUD helper functions with dual dialect query support.
5. **Step 5: Add `src/ml/`** with `ort` session management for 5 organ prediction models and ONNX scalers.
6. **Step 6: Replace proxy handlers in `src/main.rs`** with native Axum routers for all ~40 modules.
