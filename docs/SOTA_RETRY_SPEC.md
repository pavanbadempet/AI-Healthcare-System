# SOTA Resilient Retry Engine Specification

This document specifies the exponential backoff, jitter, and transient failure retry policy implemented across external API integrations and LLM providers.

```
┌─────────────────────────────────────────────────────────────┐
│                 Full Jitter Exponential Backoff             │
│  - Formula: sleep = random(0, min(max_delay, base * 2^i))   │
│  - Eliminates thundering herd retry spikes                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Transient vs Non-Transient Error Classifier       │
│  - Retries: 429 Rate Limit, 502/503/504, Connection Reset   │
│  - Fails Fast: 400 Bad Request, 401 Unauthorized, 404       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔁 Key Resilient Retry Rules

1. **Full Jitter Formula (`calculate_jitter_backoff`)**:
   - `sleep = random(0, min(max_delay, base_delay * 2^attempt))` prevents synchronized thundering herd retries.
2. **Fail Fast on Non-Transient Failures**:
   - Only retries transient network socket exceptions and HTTP rate-limiting codes (`TimeoutError`, `ConnectionResetError`).
3. **Bounded Retry Budget (`max_retries`)**:
   - Limits retry loop attempts to prevent resource exhaustion during extended outages.
