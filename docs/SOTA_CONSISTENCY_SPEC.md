# SOTA Distributed Consistency Specification

This document specifies the Conflict-Free Replicated Data Types (CRDTs), Hybrid Logical Clocks (HLC), and Last-Write-Wins (LWW) conflict resolution standards.

```
┌─────────────────────────────────────────────────────────────┐
│              Hybrid Logical Clock (HLC) Engine              │
│  - Combines physical epoch time + monotonic logical counter │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          CRDT Last-Write-Wins (LWW) State Register          │
│  - Lock-free eventual & causal consistency across regions   │
│  - Mathematically deterministic conflict resolution          │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚖️ Key Consistency Standards

1. **Hybrid Logical Clock (HLC) Timestamps (`generate_hlc`)**:
   - Ensures strict causal ordering across multi-region microservices without NTP clock skew errors.
2. **Conflict-Free Replicated Data Types (CRDTs) (`set_lww_value`)**:
   - Enables lock-free concurrent updates that mathematically converge to identical states across all database replicas.
3. **Deterministic Last-Write-Wins (LWW) Conflict Resolution**:
   - Resolves write conflicts by comparing tuple `(physical_time_ms, logical_counter)`.
