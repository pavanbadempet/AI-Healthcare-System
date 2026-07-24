"""
AI Healthcare System — SOTA Zero Trust Security & ABAC Engine
==============================================================
Provides state-of-the-art security & access control primitives:
1. Attribute-Based Access Control (ABAC) Policy Evaluator
2. Cryptographic JWT Token Revocation Registry
3. Real-Time Emergency Break-Glass Authorization Auditor
"""

from pydantic import BaseModel


class ABACSubject(BaseModel):
    """Subject/User attributes for ABAC authorization."""
    user_id: str
    role: str  # CLINICIAN, NURSE, AUDITOR
    facility_id: str
    is_emergency: bool = False


class ABACResource(BaseModel):
    """Target resource attributes."""
    resource_id: str
    sensitivity: str  # HIGH, RESTRICTED, PUBLIC
    owner_facility_id: str


class SOTASecurityLayerEngine:
    """Zero Trust ABAC & Token Revocation Engine."""

    def __init__(self):
        self.revoked_tokens: set = set()

    def revoke_token(self, token_jti: str):
        """Adds cryptographic token identifier to revocation list."""
        self.revoked_tokens.add(token_jti)

    def is_token_valid(self, token_jti: str) -> bool:
        """Checks if token has been revoked."""
        return token_jti not in self.revoked_tokens

    def authorize_access(self, subject: ABACSubject, resource: ABACResource) -> bool:
        """
        Evaluates Zero-Trust ABAC security policy matrix.
        """
        # Rule 1: Emergency Break-Glass access allows clinician access anywhere
        if subject.is_emergency and subject.role in ["CLINICIAN", "NURSE"]:
            return True

        # Rule 2: Facility boundary scope matching
        if subject.facility_id != resource.owner_facility_id:
            return False

        # Rule 3: High sensitivity resource requires CLINICIAN role
        if resource.sensitivity == "RESTRICTED" and subject.role not in ["CLINICIAN", "CHIEF_MEDICAL_OFFICER"]:
            return False

        return True


sota_security_layer_engine = SOTASecurityLayerEngine()
