# SOTA Clinical Medical Coding Specification

This document specifies the ICD-10 / SNOMED CT semantic ontology mapping and DRG billing severity calculation standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Semantic Medical Ontology Mapper                   │
│  - Maps unstructured notes to ICD-10 / SNOMED codes        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          DRG Billing & Severity Weight Calculator           │
│  - Calculates DRG severity weights for inpatient billing    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Key Coding Layer Standards

1. **Semantic Medical Ontology Mapping (`map_text_to_codes`)**:
   - Maps unstructured clinical notes directly to ICD-10 and SNOMED CT medical concepts.
2. **Diagnosis Related Group (DRG) Severity Calculation (`calculate_drg_summary`)**:
   - Computes inpatient DRG billing classification codes and case-mix severity weights (`severity_weight`).
