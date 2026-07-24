# SOTA Data Modeling Specification

This document details the State-of-the-Art (SOTA) Medallion Lakehouse and hybrid relational-document data modeling standards.

```
┌─────────────────────────────────────────────────────────┐
│               Bronze Raw Ingestion Layer                │
│  - Raw HL7 v2 messages, DICOM headers, FHIR JSON        │
└────────────────────────────┬────────────────────────────┘
                             │  (PII Scrubbing & Deduplication)
                             ▼
┌─────────────────────────────────────────────────────────┐
│              Silver Standardized Entity Layer           │
│  - Hashed MRN identifiers, Pydantic v2 validation      │
└────────────────────────────┬────────────────────────────┘
                             │  (SIMD Vectorized Aggregation)
                             ▼
┌─────────────────────────────────────────────────────────┐
│              Gold Analytical Mart Layer                 │
│  - Sub-millisecond operational metrics, DuckDB SIMD     │
└─────────────────────────────────────────────────────────┘
```

---

## 🏛️ SOTA Modeling Patterns

1. **Medallion Data Lakehouse (Bronze -> Silver -> Gold)**:
   - Separates raw ingestion from cleansed domain entities and SIMD analytical marts.
2. **PostgreSQL JSONB + Hybrid Schemas**:
   - Rigid schema for indexed core fields combined with fast JSONB binary document storage for extensible FHIR attributes.
3. **Zero-Copy Serialization Contracts**:
   - Protobuf and MessagePack contracts for inter-service RPC transport with zero serialization overhead.
