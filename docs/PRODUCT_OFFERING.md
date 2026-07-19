# AI Healthcare System - Commercial Product Offerings & Packaging Spec

To successfully position the platform for commercial sales and bypass payment gateway restrictions, the codebase is modularized into four distinct commercial products. This document defines the packaging, target buyer, and monetization strategy for each.

---

```
+-----------------------------------------------------------------------------------+
|                            AI HEALTHCARE SYSTEM                                   |
+--------------------------+-----------------------------+--------------------------+
|  1. EMBEDDABLE WIDGETS   |  2. ENTERPRISE EHR PLUGINS  |   3. BACK-OFFICE SAAS    |
|  - CASA Patient Booking  |  - LangGraph Care Assistant |   - Billing Audit Agent  |
|  - Telehealth Scribe     |  - FHIR Data Integrator     |   - Consent Gatekeeper   |
+--------------------------+-----------------------------+--------------------------+
```

---

## Product 1: CASA (Conversational Agentic Scheduling Assistant)
*The Patient Booking & Screening Widget*

* **What it does**: A conversational assistant that handles patient appointment booking, resolves scheduling conflicts, matches patients with doctors based on specialization, and runs symptom pre-screening (calculating risk metrics for diabetes and heart disease) during onboarding.
* **Target Buyer**: Independent Medical Clinics, Dental Practices, Physical Therapy Centers, and Patient Portals.
* **How it is packaged**: An embeddable Javascript widget (IFrame or Web Component) that clinics paste directly onto their public website homepage.
* **Monetization Model**: Monthly subscription per clinic location (e.g., $49/month) or a flat fee per booking processed.

---

## Product 2: Clinical Care Copilot (SMART on FHIR Plugin)
*The EHR Doctor Assistant*

* **What it does**: A stateful LangGraph-powered chat assistant that retrieves patient histories, reviews clinical notes, searches real-time research (Tavily), and provides synthesized summaries to help doctors prepare for appointments.
* **Target Buyer**: Hospitals and Large Healthcare Networks looking to enhance their EHR software.
* **How it is packaged**: A **SMART on FHIR app** registered in the Epic App Orchard or Cerner App Gallery, launching natively inside the EHR workspace.
* **Monetization Model**: Enterprise annual license based on the number of active clinicians (e.g., $120/provider/year).

---

## Product 3: Telehealth Auto-Scribe
*The Audio-to-SOAP Note Converter*

* **What it does**: Captures audio transcripts from telehealth calls and utilizes the `scribe_agent.py` module to automatically compile structured, formatted HIPAA-compliant clinical notes (S.O.A.P. notes) for medical charts.
* **Target Buyer**: Telehealth Platforms, Virtual Care Providers, and Mental Health SaaS products.
* **How it is packaged**: An API Integration (REST API endpoints) that telehealth developers plug into their existing video call interfaces.
* **Monetization Model**: Usage-based pricing based on minutes of audio transcribed and analyzed (e.g., $0.05 per session minute).

---

## Product 4: ClinicOps Auditor
*The Operations & Compliance Dashboard*

* **What it does**: Runs autonomous agents in the background to audit clinical operations:
  - **Billing Agent**: Audits invoices to detect claims denial risks before submission.
  - **Safety Agent**: Audits EHR accesses against patient privacy consent forms.
  - **Wellness Agent**: Flags gaps in patient medication compliance.
* **Target Buyer**: Clinic Administrators, Chief Compliance Officers, and Practice Managers.
* **How it is packaged**: A standalone administrative Web Dashboard.
* **Monetization Model**: B2B SaaS Subscription tiered by practice size (e.g., $199/month for up to 10 practitioners).
