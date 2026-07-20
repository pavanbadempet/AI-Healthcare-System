# 🏥 clinical-fhir-abdm — HL7 FHIR R4 & ABDM Consent Manager Integration

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> A production-ready, high-fidelity python engine for compiling database objects into standard HL7 FHIR R4 resources, building bundles, and managing ABDM (Ayushman Bharat Digital Mission) consent manager callbacks.

---

## 🔬 Core Features

* **HL7 FHIR R4 Resource Mapping**: Out-of-the-box converters to compile database records into fully validated FHIR R4 schemas:
  - `Patient` & `Encounter`
  - `Observation` & `DiagnosticReport`
  - `MedicationRequest`
  - `Invoice` & `AuditEvent`
* **Bundle Compilation**: Easily group multiple clinical resources into standardized, transmission-ready FHIR `Bundle` payloads.
* **ABDM Consent Workflow**: Fully implements settings, readiness audits, and normalization functions for consent request payloads and status updates.

---

## 🚀 Installation

Install the package via pip:

```bash
pip install clinical-fhir-abdm
```

---

## 📖 Code Reference & Quick Start

### 1. Building FHIR R4 Resources
Compile clinical data into standard FHIR R4 schemas:

```python
from clinical_fhir_abdm import patient_resource, observation_resource, build_bundle

# Convert database patient model to FHIR Patient resource
patient = patient_resource(
    id="123",
    first_name="Jane",
    last_name="Doe",
    gender="female",
    birth_date="1990-05-15",
    phone="555-0199",
    email="jane.doe@example.com"
)

# Convert lab results to FHIR Observation resource
observation = observation_resource(
    id="obs-456",
    patient_id="123",
    code="883-9",
    display="ABO + Rh Group",
    value="A Rh Pos",
    status="final",
    issued_at="2026-07-19T11:30:00Z"
)

# Bundle resources for transmission
bundle = build_bundle(
    bundle_id="bundle-789",
    resources=[patient, observation],
    bundle_type="transaction"
)
```

### 2. ABDM Consent Management
Prepare and validate consent request parameters for official sandbox validation:

```python
from clinical_fhir_abdm import ABDMSettings, prepare_consent_request

settings = ABDMSettings(
    gateway_url="https://dev.abdm.gov.in/gateway",
    client_id="your-client-id",
    client_secret="your-client-secret",
    hiu_id="your-hiu-id",
    hip_id="your-hip-id"
)

# Compile a secure ABDM consent request payload
consent_payload = prepare_consent_request(
    patient_id="patient-id@sbx",
    purpose_code="TREATMENT",
    hi_types=["OPConsultation", "DiagnosticReport", "Prescription"],
    access_mode="VIEW",
    date_range={
        "from": "2026-01-01T00:00:00Z",
        "to": "2026-12-31T23:59:59Z"
    },
    expiry="2026-07-26T23:59:59Z",
    settings=settings
)
```
