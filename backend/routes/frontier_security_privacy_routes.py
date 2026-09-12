"""API Routes for Frontier Cryptographic Security and Post-Quantum Privacy Suite."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status

from backend.schemas.frontier_security_privacy import (
    AuditAdvanceEpochResponse,
    AuditLogRequest,
    AuditLogResponse,
    CpAbeDecryptRequest,
    CpAbeDecryptResponse,
    CpAbeEncryptRequest,
    CpAbeEncryptResponse,
    FheEvaluateRiskRequest,
    FheEvaluateRiskResponse,
    PqcHybridKemRequest,
    PqcHybridKemResponse,
)
from backend.security_privacy.cp_abe_engine import (
    AccessDeniedCryptographicPolicyError,
    CpAbeAuthority,
    EncryptedAbeEnvelope,
    PolicySyntaxError,
)
from backend.security_privacy.forward_secure_audit import (
    ForwardSecureAuditLog,
)
from backend.security_privacy.homomorphic_inference import (
    EncryptedClinicalRiskPredictor,
    FheCiphertext,
    HomomorphicContext,
)
from backend.security_privacy.post_quantum_crypto import (
    PostQuantumKemEngine,
    PqcPublicKey,
)

logger = logging.getLogger("backend.frontier_security_privacy")

router = APIRouter(
    prefix="/v1/security-privacy",
    tags=["Frontier Security & Privacy"],
)

# Global authority and engine instances
cp_abe_authority = CpAbeAuthority()
homomorphic_ctx = HomomorphicContext()
risk_predictor = EncryptedClinicalRiskPredictor(context=homomorphic_ctx)
pqc_engine = PostQuantumKemEngine()
audit_log = ForwardSecureAuditLog()


@router.post("/cp-abe/encrypt", response_model=CpAbeEncryptResponse)
def encrypt_under_policy(req: CpAbeEncryptRequest) -> CpAbeEncryptResponse:
    """Encrypt clinical data under a boolean ciphertext policy tree."""
    plaintext = req.plaintext
    if plaintext is None and req.data is not None:
        import json
        plaintext = json.dumps(req.data)
    if plaintext is None:
        plaintext = ""

    try:
        envelope = cp_abe_authority.encrypt(plaintext, req.policy)
    except PolicySyntaxError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy syntax: {exc}",
        )

    envelope_dict = {
        "policy_tree": envelope.policy_tree,
        "ciphertext_base64": envelope.ciphertext_base64,
        "iv_base64": envelope.iv_base64,
        "auth_tag_base64": envelope.auth_tag_base64,
        "leaf_shares": envelope.leaf_shares,
    }
    return CpAbeEncryptResponse(
        envelope=envelope_dict,
        policy=req.policy,
        policy_parsed={"type": envelope.policy_tree.get("operator", "LEAF")},
    )


@router.post("/cp-abe/decrypt", response_model=CpAbeDecryptResponse)
def decrypt_under_policy(req: CpAbeDecryptRequest) -> CpAbeDecryptResponse:
    """Decrypt payload if user attributes satisfy the ciphertext policy tree."""
    user_key = cp_abe_authority.issue_user_key(req.user_id, req.user_attributes)
    envelope = EncryptedAbeEnvelope(
        policy_tree=req.envelope["policy_tree"],
        ciphertext_base64=req.envelope["ciphertext_base64"],
        iv_base64=req.envelope["iv_base64"],
        auth_tag_base64=req.envelope["auth_tag_base64"],
        leaf_shares=req.envelope["leaf_shares"],
    )

    try:
        plaintext = cp_abe_authority.decrypt(envelope, user_key)
    except AccessDeniedCryptographicPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cryptographic Access Denied: {exc}",
        )

    import json
    dec_data = None
    try:
        dec_data = json.loads(plaintext)
    except Exception:
        dec_data = plaintext

    return CpAbeDecryptResponse(
        plaintext=plaintext,
        decrypted_data=dec_data,
        decrypted_by=req.user_id,
    )


@router.post("/fhe/evaluate-risk", response_model=FheEvaluateRiskResponse)
def evaluate_homomorphic_risk(req: FheEvaluateRiskRequest) -> FheEvaluateRiskResponse:
    """Evaluate clinical risk model directly over encrypted ciphertext vectors."""
    pk, sk = homomorphic_ctx.generate_keypair()

    if req.encrypted_vitals is not None:
        if isinstance(req.encrypted_vitals, list):
            ct_list = [FheCiphertext.from_dict(x) for x in req.encrypted_vitals]
            encrypted_score = risk_predictor.evaluate_encrypted_ascvd(ct_list)
        elif isinstance(req.encrypted_vitals, dict):
            ct_dict = {k: FheCiphertext.from_dict(v) for k, v in req.encrypted_vitals.items()}
            encrypted_score = risk_predictor.evaluate_encrypted_ascvd_risk(ct_dict, pk)
        else:
            raise HTTPException(status_code=400, detail="Invalid encrypted_vitals format")
    else:
        vitals = req.vitals or {
            "age": 55.0,
            "systolic_bp": 142.0,
            "total_chol": 215.0,
            "hdl_chol": 42.0,
            "smoker": 1.0,
        }
        encrypted_vitals = {
            k: homomorphic_ctx.encrypt(v, pk) for k, v in vitals.items()
        }
        encrypted_score = risk_predictor.evaluate_encrypted_ascvd_risk(encrypted_vitals, pk)

    decrypted_score = None
    risk_cat = None
    if req.include_decryption_demo:
        decrypted_score = round(homomorphic_ctx.decrypt(encrypted_score, sk), 2)
        if decrypted_score < 0:
            risk_cat = "LOW_CARDIOVASCULAR_RISK"
        elif decrypted_score < 1.5:
            risk_cat = "BORDERLINE_RISK"
        else:
            risk_cat = "ELEVATED_10_YEAR_ASCVD_RISK"

    return FheEvaluateRiskResponse(
        status="COMPLETED",
        encrypted_score=encrypted_score.to_dict(),
        encrypted_risk_result=encrypted_score.to_dict(),
        decrypted_score=decrypted_score,
        risk_category=risk_cat,
        privacy_guarantee="Zero-Knowledge Ciphertext Arithmetic (Ring-LWE)",
    )


@router.post("/pqc/generate-keypair")
def generate_pqc_keypair() -> Dict[str, Any]:
    """Generate ML-KEM (Kyber-1024) public and private keypair."""
    pk, sk = pqc_engine.generate_keypair()
    return {
        "public_key": pk.to_dict(),
        "algorithm": "ML_KEM_1024_NIST_FIPS_203",
    }


@router.post("/pqc/hybrid-kem-exchange", response_model=PqcHybridKemResponse)
def hybrid_kem_exchange(req: Optional[PqcHybridKemRequest] = None) -> PqcHybridKemResponse:
    """Execute dual-mode Classical (X25519) + Quantum (ML-KEM-1024) hybrid key encapsulation."""
    try:
        if req is None or req.peer_pqc_pub is None:
            peer_pk, _ = pqc_engine.generate_keypair()
            import secrets
            peer_classical = secrets.token_hex(32)
        else:
            peer_pk = PqcPublicKey.from_dict(req.peer_pqc_pub)
            peer_classical = req.peer_classical_pub or secrets.token_hex(32)

        result = pqc_engine.hybrid_key_exchange(
            peer_classical_pub=peer_classical,
            peer_pqc_pub=peer_pk,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PQC parameters: {exc}",
        )

    return PqcHybridKemResponse(
        status="KEY_EXCHANGE_SUCCESS",
        quantum_resistant_algorithm="ML-KEM-1024 (NIST FIPS 203)",
        classical_algorithm="X25519 (RFC 7748)",
        shared_secret_hex=result.shared_secret_hex,
        classical_ephemeral_pub=result.classical_ephemeral_pub,
        quantum_ciphertext=result.quantum_ciphertext.to_dict(),
        algorithm_suite=result.algorithm_suite,
    )


@router.post("/audit/forward-secure-log", response_model=AuditLogResponse)
def log_forward_secure_audit(req: AuditLogRequest) -> AuditLogResponse:
    """Append a tamper-evident audit record under current epoch's ratcheted key."""
    entry = audit_log.record_entry(
        actor=req.actor,
        action=req.action,
        patient_id=req.patient_id,
        details=req.details,
    )
    is_valid, _, _ = audit_log.verify_chain_integrity()

    return AuditLogResponse(
        entry=entry.to_dict(),
        current_epoch=audit_log.current_epoch,
        chain_valid=is_valid,
    )


@router.post("/audit/advance-epoch", response_model=AuditAdvanceEpochResponse)
def advance_audit_epoch() -> AuditAdvanceEpochResponse:
    """Irreversibly ratchet the audit signing key forward to the next epoch."""
    new_epoch = audit_log.advance_epoch()
    return AuditAdvanceEpochResponse(new_epoch=new_epoch)


@router.get("/audit/verify")
def verify_audit_log() -> Dict[str, Any]:
    """Verify entire Merkle DAG integrity and monotonic epoch order."""
    is_valid, status_str, violations = audit_log.verify_chain_integrity()
    return {
        "valid": is_valid,
        "status": status_str,
        "violations": violations,
        "current_epoch": audit_log.current_epoch,
        "recent_entries": audit_log.get_recent_entries(limit=10),
    }


@router.get("/health")
def security_privacy_health() -> Dict[str, Any]:
    """Return security & privacy engine operational status."""
    is_valid, status_str, _ = audit_log.verify_chain_integrity()
    return {
        "status": "HEALTHY",
        "cp_abe": {"engine": "Ciphertext-Policy Attribute-Based Encryption", "curve": "F_p Shamir Threshold"},
        "fhe": {"engine": "Ring-LWE Homomorphic Vector Evaluator", "modulus": homomorphic_ctx.q},
        "pqc": {"engine": "ML-KEM Kyber-1024 + X25519 Hybrid", "standard": "NIST FIPS 203"},
        "audit": {"epoch": audit_log.current_epoch, "chain_status": status_str, "integrity": is_valid},
    }
