# ClinOS Monetization Strategy: Product vs. Components

This document outlines the two distinct commercial pathways for ClinOS: selling a unified **End-User Product** to medical practitioners vs. selling **Modular Developer Components** to tech founders and IT departments.

---

## Monetization Matrix

| Monetization Model | Channel / Buyer | Pricing | Delivery Mechanism |
| :--- | :--- | :--- | :--- |
| **1. Unified Product (EHR)** | Clinics, Solo Doctors | $500 - $1,500 (One-Time) | Self-hosted Docker / local Windows installer bundle. |
| **2. White-Label System** | Franchise Clinic Groups | Custom Enterprise Quote | Source code licensing with customization rights. |
| **3. Standalone SDKs** | Healthtech Developers | $15 - $99 per package | Instant Polar.sh/GitHub private repository access. |
| **4. Premium UI Widgets** | Frontend Developers | $29 per component pack | NPM registry or private GitHub widget library. |
| **5. Integration Adapters** | Enterprise Hospitals | $2,000 Setup + Support | Customized HL7 Receiver or ABDM gateway pipeline. |

---

## Pathway A: The Unified Product (Direct-to-Clinic)
*Targeting medical practitioners looking for a clean, private, offline-first clinical workstation.*

*   **Self-Hosted EHR Installer**: A one-time purchase executable (Windows/Docker) that starts the local database, Vite React web interface, and local ML models.
*   **Data Migration Services (High Margin)**: Billed at a flat fee (e.g., INR 15,000) to clean, parse, and import patient records from their legacy system (Excel, old PDF sheets) into the SQLite/Vector database.
*   **Custom Setup & Onboarding**: Training clinic staff, configuring local backup drives, and setting up network routing for in-clinic tablet access.

---

## Pathway B: The Modular Components (Direct-to-Developers)
*Targeting software developers and healthtech startups who want to bypass months of R&D by purchasing production-ready, pre-licensed codebase assets.*

### 🛠️ Standalone Codebase Components (Polar.sh)
1.  **Offline Cryptographic Licenser (`fastapi-license-gate`)**:
    *   *What it is*: The `licensing.py` layer.
    *   *Who buys it*: Any B2B developer looking to implement offline signed license keys in their own software.
2.  **Calibrated ML Risk Models (`clinical-tabular`)**:
    *   *What it is*: The five chronic classifiers from `backend/prediction.py`.
    *   *Who buys it*: Startups looking for pre-calibrated models with conformal confidence bounds.
3.  **ABDM Interop Connector (`abdm-gateway`)**:
    *   *What it is*: The Ayushman Bharat Digital Mission interface in `backend/abdm.py`.
    *   *Who buys it*: Indian healthtech companies seeking immediate government compliance.
4.  **HL7 Receiver & FHIR Bundle Parser**:
    *   *What it is*: The HL7 receiver and FHIR export schemas.
    *   *Who buys it*: Enterprise legacy system integrators.

### 🎨 Frontend Components (React widgets)
*   **Interactive Onboarding / Guide Drawer**: The help circle sidebar from `TopNav.tsx`.
*   **Telemetry Pulse Widget**: The real-time connection status signal that tracks online status and queues pending local writes.
