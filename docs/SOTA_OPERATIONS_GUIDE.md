# SOTA Operations & Playbook Guide

Welcome to the State-of-the-Art (SOTA) Operations Guide for AI Healthcare System. This document outlines the technical administration, clinical AI agents suite, and self-healing telemetry setup of the platform.

---

## 1. SOTA Clinical AI Agents Suite

AI Healthcare System deploys six specialized autonomous AI agents to automate clinical reasoning, security patching, self-healing, and emergency telemetry routing.

### A. Clinical Billing Auditor (`ClinicalBillingAgent`)
*   **Role**: Audits clinical SOAP notes for billing integrity, assigns ICD-10/CPT coding, and predicts claims denial risks.
*   **Endpoint**: `POST /v1/admin/agents/billing-audit?soap_note={text}`
*   **Workflow**:
    1. Clinician enters SOAP notes.
    2. Agent verifies clinical documentation suitability.
    3. Recommends coding adjustments to minimize billing rejection risk.

### B. Discharge Coordinator (`ClinicalDischargeAgent`)
*   **Role**: Compiles care transition summaries, follow-up timelines, and patient discharge instructions.
*   **Endpoint**: `POST /v1/admin/agents/discharge-summary?patient_id={id}`
*   **Workflow**:
    1. Aggregates patient vital histories and active medications.
    2. Builds formatted instructions tailored for patient compliance.

### C. Ward Shift Nurse (`ClinicalNursingAgent`)
*   **Role**: Generates handover summaries and prioritizing task lists during shift changes.
*   **Endpoint**: `POST /v1/admin/agents/nursing-handoff?patient_id={id}`
*   **Workflow**:
    1. Summarizes vital trends and telemetry anomalies from the last 24 hours.
    2. Recommends vital monitoring frequencies (e.g. Q4h) and fall risk flags.

### D. Security Auto-Patcher (`ClinicalPatchAgent`)
*   **Role**: Audits dependencies and configuration postures, applying virtual hotpatch rules.
*   **Endpoint**: `POST /v1/admin/agents/security-patch`
*   **Workflow**:
    1. Audits pinned packages in `requirements.txt`.
    2. Flags environment drift (CORS wildcards, default keys).
    3. Suggests runtime input validation blocks.

### E. Self-Healing Recoverer (`ClinicalFixingAgent`)
*   **Role**: Diagnoses operational errors and triggers database or cache self-recovery.
*   **Endpoint**: `POST /v1/admin/agents/auto-fix`
*   **Workflow**:
    1. Inspects active exceptions (e.g., SQLite locks).
    2. Auto-executes DB vacuuming, lock clearing, or cache flushes.

### F. Telephony Coordinator (`ClinicalCallingAgent`)
*   **Role**: Routes urgent telemetry alarms to on-call doctors and creates call scripts.
*   **Endpoint**: `POST /v1/admin/agents/auto-call`
*   **Workflow**:
    1. Receives active cardiac alarm signals.
    2. Matches on-call specialist directory.
    3. Generates synthesized audio scripts for telephony delivery.

---

## 2. System Maintenance & GDPR Retention

### Database Indexing & Compacts
Admin users can optimize transactional engines (SQLite/PostgreSQL) and the Vector Store database in one click:
*   **Endpoint**: `POST /v1/admin/maintenance`
*   **Actions**:
    *   Rebuilds B-tree indexing pages.
    *   Prunes soft-deleted data nodes and logs older than 30 days.
    *   Compacts local vector spaces for rapid semantic search.

---

## 3. Telemetry Scrapers & Dashboards

### Scrapers & Metrics
*   **Prometheus Scraping Target**: Port `7860` (Rust Gateway) and Port `8000` (FastAPI).
*   **Endpoint**: `/metrics` (exposes CPU, RAM, active database connections, and request velocity).
*   **Grafana Dashboard**: Configured dynamically via `datasource.yml` and `dashboard_provider.yml`. It monitors:
    *   `rust_gateway_cpu_usage_percent`
    *   `rust_gateway_memory_used_bytes`
    *   `http_request_duration_seconds_bucket` (p95 boundaries)
