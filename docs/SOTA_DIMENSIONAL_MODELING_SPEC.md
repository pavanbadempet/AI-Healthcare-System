# SOTA Dimensional Modeling Specification

This document specifies the Kimball Star Schema dimensional modeling architecture designed for high-performance analytical data warehousing.

```
                  ┌────────────────────────┐
                  │       DimPatient       │
                  │  - patient_dim_key (PK)│
                  └───────────┬────────────┘
                              │
                              ▼
                  ┌────────────────────────┐
                  │ FactPatientEncounter   │ ◄───────── ┌────────────────────────┐
                  │ - encounter_fact_key   │            │      DimFacility       │
                  │ - patient_dim_key (FK) │            │ - facility_dim_key(PK) │
                  │ - facility_dim_key (FK)│            └────────────────────────┘
                  │ - length_of_stay_hours │
                  │ - total_cost_usd       │
                  └────────────────────────┘
```

---

## 📊 Star Schema Optimization Rules

1. **Surrogate Integer Foreign Keys**:
   - Replaces heavy string UUIDs with 32-bit integer surrogate keys, accelerating SIMD joins by $10\times$.
2. **SCD Type 2 Dimension Tracking**:
   - Maintains complete historical records for patient attributes without destructive updates.
3. **Pre-aggregated Data Marts**:
   - Computes analytical metrics ahead of time for instant dashboard execution.
