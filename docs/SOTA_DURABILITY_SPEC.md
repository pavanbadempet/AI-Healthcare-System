# SOTA High-Durability Commit Log Specification

This document specifies the Write-Ahead Logging (WAL), physical `fsync` disk flushing, and bit rot protection standards.

```
┌─────────────────────────────────────────────────────────────┐
│                 Append-Only Write-Ahead Log (WAL)           │
│  - Formats: SHA-256 Checksum | tx_id : timestamp : payload  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Hardware OS `fsync()` Disk Flush               │
│  - Forces hardware controller write to NVMe non-volatile SSD│
│  - Protects against power outages & sudden process crashes │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Key Durability Guarantees

1. **Hardware `fsync()` Synchronous Flush (`append_commit_record`)**:
   - Executes OS `os.fsync()` to force dirty OS kernel page caches down to non-volatile flash storage prior to returning commit HTTP 200 responses.
2. **SHA-256 Block Checksumming (`verify_wal_integrity`)**:
   - Detects drive degradation and silent bit rot corruption across long-term stored WAL transaction files.
3. **Quorum Consensus Commitment Protocol**:
   - Replicates transactions across $2f+1$ nodes to ensure zero data loss during hardware failure events.
