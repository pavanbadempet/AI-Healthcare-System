# SOTA Clinical AI Safety & Guardrails Specification

This document specifies the safety architecture protecting against prompt injection, PHI leakage, and clinical advisory risks.

```
┌─────────────────────────────────────────────────────────────┐
│                 Input Adversarial Guardrail                 │
│  - Regex & NLP jailbreak scanner                            │
│  - Blocks "ignore instructions" & prompt leakage attempts   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Output Safety & Redaction Pipeline             │
│  - Automated PHI (SSN, Phone, Email) regex scrubber         │
│  - Automatic clinical disclaimer enforcement                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Key AI Safety Rules

1. **Adversarial Jailbreak Scanners (`sanitize_user_prompt`)**:
   - Detects and rejects DAN mode, instruction overrides, and prompt leakage vectors.
2. **Automated PHI / PII Scrubber (`redact_phi`)**:
   - Sanitizes SSNs, phone numbers, and email patterns prior to downstream model storage or logging.
3. **Mandatory Medical Disclaimer Enforcement (`apply_clinical_guardrails`)**:
   - Guarantees medical disclaimer compliance on all AI clinical responses.
