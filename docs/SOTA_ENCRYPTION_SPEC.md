# SOTA AES-256-GCM Cryptography Specification

This document specifies the authenticated encryption (AEAD) standard protecting all PHI patient health records at rest and in transit.

```
┌─────────────────────────────────────────────────────────────┐
│                 HKDF-SHA256 Key Derivation                  │
│  - Converts master key & 16-byte random salt to 256-bit key │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              AES-256-GCM Authenticated Encryption           │
│  - 96-bit (12-byte) unique random nonce per payload        │
│  - Authenticated Tag Verification against tampering         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Key Cryptographic Protection Standards

1. **AES-256-GCM Authenticated Encryption (`encrypt_payload`)**:
   - Provides both confidentiality and tamper-proof authentication tag integrity.
2. **HKDF-SHA256 Key Derivation (`derive_key`)**:
   - Standardized RFC 5869 key derivation converting master secrets to cryptographically independent sub-keys.
3. **Hardware SIMD Acceleration (AES-NI)**:
   - Executes encryption/decryption natively in CPU hardware registers for sub-microsecond speeds.
