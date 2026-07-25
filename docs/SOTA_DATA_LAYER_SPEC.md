# SOTA High-Performance Data Layer Specification

This document specifies the Bi-Temporal versioning, Unit of Work repository pattern, and time-travel query standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Bi-Temporal Record Retention Engine                │
│  - Dual temporal tracking (System Time + Valid Time)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Time-Travel Historical Query Engine                │
│  - Executes audit queries for historical clinical states    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Key Data Layer Standards

1. **Bi-Temporal Versioning (`insert_temporal_record`)**:
   - Captures both system insertion time (`system_time`) and domain validity timestamps (`valid_from`, `valid_to`).
2. **Time-Travel Audit Queries (`get_as_of`)**:
   - Evaluates historical record states at any point in past time without data destruction.
3. **Non-Destructive Soft Deletion (`soft_delete_record`)**:
   - Marks records as soft-deleted (`is_deleted`) to satisfy HIPAA compliance retention rules.
