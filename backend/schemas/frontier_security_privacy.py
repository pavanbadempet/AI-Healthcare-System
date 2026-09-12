"""Pydantic schemas for Frontier Cryptographic Security & Post-Quantum Privacy."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CpAbeEncryptRequest(BaseModel):
    """Request to encrypt clinical data under a boolean ciphertext policy tree."""
    plaintext: Optional[str] = Field(None, description="Sensitive clinical data string")
    data: Optional[Any] = Field(None, description="Arbitrary JSON clinical data or structure")
    policy: str = Field(
        ...,
        description="Boolean access policy, e.g. '(ROLE:ONCOLOGIST AND DEPT:CANCER_CARE) OR USER_ID:P-101'",
    )


class CpAbeEncryptResponse(BaseModel):
    """Encrypted envelope bound to policy tree."""
    envelope: Dict[str, Any]
    policy: str
    policy_parsed: Optional[Dict[str, Any]] = None
    status: str = "ENCRYPTED_UNDER_POLICY"


class CpAbeDecryptRequest(BaseModel):
    """Request to decrypt ciphertext policy envelope using user attribute credentials."""
    envelope: Dict[str, Any]
    user_id: str = Field(..., description="Clinician or patient identifier")
    user_attributes: List[str] = Field(..., description="Certified attributes possessed by user")


class CpAbeDecryptResponse(BaseModel):
    """Decrypted plaintext data."""
    plaintext: str
    decrypted_data: Optional[Any] = None
    decrypted_by: str
    status: str = "POLICY_SATISFIED_DECRYPTED"


class FheEvaluateRiskRequest(BaseModel):
    """Request to evaluate clinical risk directly on encrypted ciphertext."""
    vitals: Optional[Dict[str, float]] = Field(
        default=None,
        description="Biometric and lab features",
    )
    encrypted_vitals: Optional[Any] = Field(
        default=None,
        description="Pre-encrypted vitals ciphertext vector",
    )
    patient_id: Optional[str] = Field(
        default=None,
        description="Confidential patient identifier",
    )
    include_decryption_demo: bool = Field(
        default=True,
        description="Perform client-side decryption demonstration",
    )


class FheEvaluateRiskResponse(BaseModel):
    """Encrypted result computed without server ever seeing plaintext."""
    status: str = "COMPLETED"
    encrypted_score: Optional[Dict[str, Any]] = None
    encrypted_risk_result: Optional[Dict[str, Any]] = None
    decrypted_score: Optional[float] = None
    risk_category: Optional[str] = None
    privacy_guarantee: str = "Zero-Knowledge Ciphertext Arithmetic (Ring-LWE)"


class PqcHybridKemRequest(BaseModel):
    """Request to initiate NIST FIPS 203 Hybrid Classical-Quantum Key Exchange."""
    peer_classical_pub: Optional[str] = Field(None, description="Peer classical ECDH/X25519 public key hex")
    peer_pqc_pub: Optional[Dict[str, Any]] = Field(None, description="Peer ML-KEM (Kyber-1024) public key")


class PqcHybridKemResponse(BaseModel):
    """Hybrid key encapsulation output."""
    status: str = "KEY_EXCHANGE_SUCCESS"
    quantum_resistant_algorithm: str = "ML-KEM-1024 (NIST FIPS 203)"
    classical_algorithm: str = "X25519 (RFC 7748)"
    shared_secret_hex: str
    classical_ephemeral_pub: str
    quantum_ciphertext: Dict[str, Any]
    algorithm_suite: str = "HYBRID_X25519_ML_KEM_1024_NIST_FIPS_203"


class AuditLogRequest(BaseModel):
    """Request to record a forward-secure audit trail entry."""
    actor: str
    action: str
    patient_id: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """Recorded audit entry with Merkle hash linkage."""
    entry: Dict[str, Any]
    current_epoch: int
    chain_valid: bool
    status: str = "AUDIT_APPENDED_FORWARD_SECURE"


class AuditAdvanceEpochResponse(BaseModel):
    """Result of irreversibly advancing the cryptographic ratchet."""
    new_epoch: int
    status: str = "RATCHET_ADVANCED_PAST_KEYS_DESTROYED"

