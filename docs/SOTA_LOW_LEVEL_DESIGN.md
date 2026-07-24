# SOTA Low Level Design (LLD) Specification

This document details the State-of-the-Art (SOTA) Low Level Design (LLD) object-oriented and structural patterns implemented in [`backend/sota_lld.py`](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/backend/sota_lld.py).

---

## 🧩 SOTA Design Patterns

### 1. 🪶 Flyweight Pattern (`MedicalCodeFlyweightFactory`)
- **Problem**: Storing millions of ICD-10/SNOMED objects per patient record causes severe RAM fragmentation.
- **Solution**: Shared immutable flyweight objects reuse medical concept instances, maintaining zero allocation overhead for repetitive concepts.

### 2. 🔀 Strategy & State Pattern (`PatientTriageContext`)
- **Problem**: Complex `if-elif-else` branches evaluating patient risk profiles stall CPU branch predictors.
- **Solution**: Dynamic Strategy objects (`CardiacRiskStrategy`, `MetabolicRiskStrategy`) encapsulate risk formulas into virtual table dispatches.

### 3. 📐 Template Method Pattern (`BaseFHIRResourceConverter`)
- **Problem**: Inconsistent FHIR payload mapping leads to code duplication and missing PII sanitization.
- **Solution**: Rigid template method algorithm skeleton enforces zero-copy data extraction, mandatory PII scrubbing, and compliant FHIR R4 JSON construction.
