# PHI Data Encryption at Rest Specifications

## Envelope Encryption Design
- **Data Encryption Key (DEK)**: 256-bit symmetric key generated locally per patient record block using cryptographic CSPRNG.
- **Key Encryption Key (KEK)**: Asymmetric master key managed in cloud KMS (AWS KMS / GCP Cloud KMS).
- **Cipher Suite**: AES-256-GCM with 96-bit initialization vector (IV) and 128-bit authentication tag.
