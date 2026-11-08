# AI Healthcare System — E2E Test Infrastructure Specification

> Authoritative test infrastructure and methodology specification for the full-stack AI Healthcare System rewrite.

---

## 1. Overview & Testing Philosophy

The AI Healthcare System rewrite migrates from a Python/FastAPI backend to a high-performance Rust (Axum/Tokio) + Bun (ElysiaJS) dual-tier architecture. To ensure strict behavioral parity, zero breaking changes for the React 19 frontend, and total reliability:

1. **Opaque-Box Testing**: All test suites in `e2e_tests/` interact strictly over HTTP/1.1, HTTP/2, WebSockets, and Server-Sent Events (SSE) interfaces. Tests are decoupled from the internal backend programming language (whether Python baseline, Rust Axum, or Bun ElysiaJS).
2. **Deterministic Contract Adherence**: Every endpoint is validated against the exact REST API contracts (URL path, HTTP method, query parameters, request body schemas, response status codes, and JSON payload shapes) documented in `PROJECT.md` and the route survey.
3. **Environment Agnostic (`E2E_API_URL`)**: The test harness automatically switches between live HTTP execution (e.g. `http://127.0.0.1:8000` or `http://127.0.0.1:8001`) and direct in-process FastAPI `TestClient` depending on the `E2E_API_URL` environment variable.
4. **4-Tier Stratification**:
   - **Tier 1**: Feature Coverage (>=5 test cases per domain across all 40 domains, >200 tests).
   - **Tier 2**: Boundary, Edge & Corner Cases (Validation failures, 401/403/404/422 status codes, malformed payloads, SQL injection resilience, empty inputs).
   - **Tier 3**: Cross-Feature Combinations (Multi-step end-to-end integration workflows connecting Auth, Appointments, Clinical Orders, Pharmacy, Diagnostics, and Billing).
   - **Tier 4**: Real-World Application Scenarios (Comprehensive clinical workflows simulating real hospital operations: emergency triage, ICU sepsis alerts, inpatient drug dispensing with safety checks, real-time vitals telemetry).

---

## 2. Directory Layout

```
e2e_tests/
├── harness/                           # Reusable test harness and client utilities
│   ├── __init__.py
│   ├── client.py                      # Opaque-box HTTP/WS client with automatic URL resolution
│   ├── auth.py                        # Authentication manager & token generator for test roles
│   ├── fixtures.py                    # Domain test data factories and mock payloads
│   └── reporter.py                    # Test result accumulator and report generator
├── tiers/
│   ├── __init__.py
│   ├── tier1_feature_coverage/        # Tier 1: Happy-path feature coverage across 40 domains
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_prediction.py
│   │   ├── test_hospital_operations.py
│   │   ├── test_billing.py
│   │   ├── test_pharmacy.py
│   │   ├── test_appointments.py
│   │   ├── test_diagnostics.py
│   │   ├── test_chat_records.py
│   │   ├── test_nursing.py
│   │   ├── test_monitoring.py
│   │   ├── test_discharge.py
│   │   ├── test_care_events.py
│   │   ├── test_telemetry.py
│   │   ├── test_fhir_r4.py
│   │   ├── test_interoperability.py
│   │   ├── test_admin_dashboard.py
│   │   ├── test_unified_data_platform.py
│   │   ├── test_lakehouse_engineering.py
│   │   ├── test_smart_on_fhir.py
│   │   ├── test_recommendation_engine.py
│   │   ├── test_four_eye_governance.py
│   │   ├── test_ollama_ai.py
│   │   ├── test_longitudinal_prediction.py
│   │   ├── test_federated_learning.py
│   │   ├── test_clinical_intelligence.py
│   │   ├── test_abdm_sandbox.py
│   │   ├── test_streaming_chat.py
│   │   ├── test_dicomweb_pacs.py
│   │   ├── test_i18n_audio.py
│   │   ├── test_peak_healthcare.py
│   │   ├── test_reports_payments.py
│   │   ├── test_consent_gate.py
│   │   ├── test_fhir_compression.py
│   │   ├── test_multi_cloud_mesh.py
│   │   ├── test_explanation.py
│   │   ├── test_readiness_modules.py
│   │   └── test_system_licensing.py
│   ├── tier2_boundary_corner_cases/   # Tier 2: Boundary, error, and security checks
│   │   ├── __init__.py
│   │   ├── test_auth_boundaries.py
│   │   ├── test_prediction_boundaries.py
│   │   ├── test_hospital_boundaries.py
│   │   ├── test_billing_pharmacy_boundaries.py
│   │   ├── test_interop_fhir_boundaries.py
│   │   ├── test_data_platform_boundaries.py
│   │   └── test_security_input_resilience.py
│   ├── tier3_cross_feature_combinations/ # Tier 3: Multi-step cross-module flows
│   │   ├── __init__.py
│   │   ├── test_patient_journey_flow.py
│   │   ├── test_clinical_order_to_billing_flow.py
│   │   ├── test_risk_to_specialist_referral_flow.py
│   │   └── test_inpatient_admission_to_discharge_flow.py
│   └── tier4_real_world_scenarios/    # Tier 4: Real-world clinical operations
│       ├── __init__.py
│       ├── test_emergency_triage_scenario.py
│       ├── test_icu_sepsis_pipeline_scenario.py
│       ├── test_pharmacy_dispense_safety_scenario.py
│       └── test_realtime_telemetry_monitoring_scenario.py
├── conftest.py                        # Pytest fixtures and test environment config
└── run_e2e.py                         # Standalone command-line test runner & reporting engine
```

---

## 3. Test Client & Authentication Harness

The test harness provides an opaque HTTP client (`E2EClient`) that abstracts the target backend:

```python
# Live server mode (e.g. Rust Axum on 8001 or Bun on 8000):
export E2E_API_URL="http://127.0.0.1:8000"
python e2e_tests/run_e2e.py

# In-process FastAPI TestClient mode (development baseline):
unset E2E_API_URL
python e2e_tests/run_e2e.py
```

### Role Simulation
The test client handles authentication and credential generation for multiple standard roles:
- **Admin**: System superuser (`admin`, `admin_dashboard`, `audit_logs`, `licensing`)
- **Doctor / Clinician**: Medical professional (`diagnostics`, `prescriptions`, `clinical_orders`, `admissions`)
- **Nurse**: Inpatient care provider (`nursing_tasks`, `vitals`, `handoff_cards`)
- **Patient**: End user (`profile`, `appointments`, `prescriptions`, `patient_feed`, `my_invoices`)
- **Unauthenticated / Anonymous**: Validates 401 Unauthorized / 403 Forbidden guards

---

## 4. 40-Domain Coverage Breakdown

| # | Domain Prefix | Tier 1 Tests | Tier 2 Boundaries | Tier 3 Flows | Tier 4 Scenarios |
|---|---------------|-------------|-------------------|--------------|------------------|
| 1 | `/v1` (Auth) | 6 | 6 | ✓ | ✓ |
| 2 | `/v1/predict` (Prediction) | 8 | 8 | ✓ | ✓ |
| 3 | `/v1/hospital` (Hospital Operations) | 8 | 6 | ✓ | ✓ |
| 4 | `/v1/billing` (Billing & Invoices) | 7 | 6 | ✓ | ✓ |
| 5 | `/v1/pharmacy` (Pharmacy & Safety) | 7 | 6 | ✓ | ✓ |
| 6 | `/v1/appointments` (Appointments & CASA) | 7 | 5 | ✓ | ✓ |
| 7 | `/v1/diagnostics` (Diagnostics & Lab) | 6 | 5 | ✓ | ✓ |
| 8 | `/v1/chat` & `/v1/records` (Chat & Records) | 6 | 5 | ✓ | - |
| 9 | `/v1/nursing` (Nursing Tasks & Handoff) | 6 | 5 | ✓ | ✓ |
| 10 | `/v1/monitoring` (Vitals & Signals) | 6 | 5 | ✓ | ✓ |
| 11 | `/v1/discharge` (Discharge Summaries) | 6 | 5 | ✓ | ✓ |
| 12 | `/v1/events` (Care Events Feed) | 6 | 5 | ✓ | ✓ |
| 13 | `/v1/telemetry` (Telemetry & HL7) | 5 | 5 | - | ✓ |
| 14 | `/v1/fhir` (FHIR R4 Resources) | 6 | 5 | ✓ | - |
| 15 | `/v1/interop` (Interoperability & ABDM) | 8 | 6 | ✓ | - |
| 16 | `/v1/admin` (Admin Dashboard & Security) | 8 | 6 | - | - |
| 17 | `/api/v1/data-platform` (Unified Platform) | 8 | 6 | - | - |
| 18 | `/v1/lakehouse` (Lakehouse Engineering) | 5 | 5 | - | - |
| 19 | `/v1/smart` (SMART on FHIR) | 5 | 5 | - | - |
| 20 | `/v1/recommendations` (Recommendation Engine) | 5 | 5 | ✓ | - |
| 21 | `/v1/governance` (Four-Eye AI Governance) | 5 | 5 | - | - |
| 22 | `/v1/ai` (Ollama AI Models) | 5 | 5 | - | - |
| 23 | `/v1/predict/longitudinal` (Longitudinal ML) | 5 | 5 | - | - |
| 24 | `/v1/federated` (Federated Learning Sync) | 5 | 5 | - | - |
| 25 | `/v1/intelligence` (Clinical Intelligence) | 5 | 5 | - | - |
| 26 | `/v1/abdm` (ABDM Sandbox Bridge) | 5 | 5 | - | - |
| 27 | `/v1/chat/stream` (Streaming Chat SSE) | 5 | 5 | - | - |
| 28 | `/v1/dicomweb` (DICOMweb PACS) | 5 | 5 | - | - |
| 29 | `/v1/audio` (i18n Audio Processing) | 5 | 5 | - | - |
| 30 | `/v1/digital-twin` (Peak Healthcare Twin) | 5 | 5 | - | - |
| 31 | `/v1/analyze` & `/v1/payments` (Reports & Pay) | 5 | 5 | ✓ | - |
| 32 | `/v1/consent` (Consent Gate) | 5 | 5 | - | - |
| 33 | `/v1/fhir/compress` (FHIR Compression) | 5 | 5 | - | - |
| 34 | `/v1/mesh` (Multi-Cloud Pipeline Mesh) | 5 | 5 | - | - |
| 35 | `/v1/explain` (ML Explanations & SHAP) | 5 | 5 | - | - |
| 36 | `/v1/admin/sales-readiness` (Sales Audit) | 5 | 5 | - | - |
| 37 | `/v1/demo-readiness` (Demo Sandbox) | 5 | 5 | - | - |
| 38 | `/v1/licensing` (Enterprise Licensing) | 5 | 5 | - | - |
| 39 | `/healthz` & `/metrics` (System & Metrics) | 6 | 5 | - | - |
| 40 | `/{catchall}` (Static & Frontend SPA Fallback) | 5 | 5 | - | - |

---

## 5. Execution Guide

### Using Standalone E2E Runner (Recommended)
```bash
# Run all tiers against default in-process or configured URL
python e2e_tests/run_e2e.py

# Run specific tier
python e2e_tests/run_e2e.py --tier 1
python e2e_tests/run_e2e.py --tier 2
python e2e_tests/run_e2e.py --tier 3
python e2e_tests/run_e2e.py --tier 4

# Run against live Rust/Bun backend
python e2e_tests/run_e2e.py --url http://127.0.0.1:8000

# Export JSON test report
python e2e_tests/run_e2e.py --json-report e2e_results.json
```

### Using Pytest Directly
```bash
# Run with parallel workers
pytest e2e_tests/ -n auto -v

# Run specific tier
pytest e2e_tests/tiers/tier1_feature_coverage/ -n auto -v
pytest e2e_tests/tiers/tier2_boundary_corner_cases/ -n auto -v
pytest e2e_tests/tiers/tier3_cross_feature_combinations/ -n auto -v
pytest e2e_tests/tiers/tier4_real_world_scenarios/ -n auto -v
```
