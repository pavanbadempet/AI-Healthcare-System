# SOTA Micro-Architecture CPU Cache Locality Specification

This document specifies Structure-of-Arrays (SoA) memory layouts, 64-byte CPU cache line alignments, and zero-allocation object reuse pools.

```
┌─────────────────────────────────────────────────────────────┐
│          Structure-of-Arrays (SoA) Contiguous Layout        │
│  - Fits clinical arrays into CPU L1/L2 data caches contiguously│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          64-Byte CPU Cache-Line Boundary Alignment          │
│  - Prevents CPU cache line splitting & false sharing        │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Cache Locality Standards

1. **Structure-of-Arrays Memory Transformation (`convert_aos_to_soa`)**:
   - Transforms Array-of-Structures (AoS) clinical data into contiguous Structure-of-Arrays (SoA) vectors for maximum CPU cache hit ratios.
2. **Microsecond Conversion Tracking (`layout_conversion_time_us`)**:
   - Measures memory layout transformation efficiency in sub-microseconds.
