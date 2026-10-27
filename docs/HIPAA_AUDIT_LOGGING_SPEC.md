# HIPAA Compliance & Audit Logging Specification

## Security & Privacy Controls
- All PHI/PII queries logged to immutable append-only audit trail in Delta Bronze layer.
- TLS 1.3 enforced for all internal microservice communication (Rust Gateway to FastAPI).
- AES-256 encryption at rest across S3 buckets and RDS clinical databases.
