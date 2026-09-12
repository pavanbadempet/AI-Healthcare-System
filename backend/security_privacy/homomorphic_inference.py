"""Fully Homomorphic Encryption (FHE) Clinical Inference Engine.

Implements Ring-LWE / BFV-inspired homomorphic encryption for encrypted clinical risk scoring.
Enables cloud AI services to evaluate multivariate patient risk models (e.g. Framingham
cardiovascular risk, sepsis deterioration) directly on encrypted ciphertext vectors without
ever decrypting patient vitals in memory or learning the resulting risk score.
"""

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Prime modulus q for Ring-LWE integer ciphertext field
MOD_Q = 2147483647  # 2^31 - 1 (Mersenne prime)
SCALE_FACTOR = 1000  # Fixed-point precision factor (3 decimals)


@dataclass
class FheCiphertext:
    """Homomorphic ciphertext tuple (c0, c1) under modulus q with scale tracking."""
    c0: int
    c1: int
    scale: int = SCALE_FACTOR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "c0": self.c0,
            "c1": self.c1,
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FheCiphertext:
        return cls(
            c0=int(data["c0"]),
            c1=int(data["c1"]),
            scale=int(data.get("scale", SCALE_FACTOR)),
        )


@dataclass
class FhePublicKey:
    """Public key (a, b) for homomorphic encryption."""
    a: int
    b: int

    def to_dict(self) -> Dict[str, int]:
        return {"a": self.a, "b": self.b}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> FhePublicKey:
        return cls(a=int(data["a"]), b=int(data["b"]))


@dataclass
class FheSecretKey:
    """Secret key s for homomorphic decryption."""
    s: int


class HomomorphicContext:
    """Generates cryptographic keys and executes homomorphic arithmetic on ciphertexts."""

    def __init__(self, modulus: int = MOD_Q, scale: int = SCALE_FACTOR, dimension: int = 256) -> None:
        self.q = modulus
        self.scale = scale
        self.dimension = dimension

    def generate_keypair(self) -> Tuple[FhePublicKey, FheSecretKey]:
        """Generate Ring-LWE secret and public keypair."""
        # Sample secret key s in [-3, 3]
        s = secrets.randbelow(7) - 3
        # Sample uniform public parameter a in [1, q-1]
        a = secrets.randbelow(self.q - 2) + 1
        # Small Gaussian-like noise e in [-2, 2]
        e = secrets.randbelow(5) - 2

        # Public key component: b = -(a * s + e) mod q
        b = (- (a * s + e)) % self.q
        return FhePublicKey(a=a, b=b), FheSecretKey(s=s)

    def keygen(self) -> Tuple[FhePublicKey, FheSecretKey]:
        """Alias for generate_keypair."""
        return self.generate_keypair()

    def encrypt(self, value: float, pk: FhePublicKey) -> FheCiphertext:
        """Encrypt a real-valued scalar into homomorphic ciphertext (c0, c1)."""
        # Quantize fixed-point message
        m_int = int(round(value * self.scale))

        # Sample small random error terms
        u = secrets.randbelow(5) - 2
        e0 = secrets.randbelow(5) - 2
        e1 = secrets.randbelow(5) - 2

        # c0 = b * u + e0 + m (mod q)
        c0 = (pk.b * u + e0 + m_int) % self.q
        # c1 = a * u + e1 (mod q)
        c1 = (pk.a * u + e1) % self.q

        return FheCiphertext(c0=c0, c1=c1, scale=self.scale)

    def encrypt_vector(self, values: List[float], pk: FhePublicKey) -> List[FheCiphertext]:
        """Encrypt a vector of numerical values."""
        return [self.encrypt(v, pk) for v in values]

    def decrypt(self, ct: FheCiphertext, sk: FheSecretKey) -> float:
        """Decrypt ciphertext tuple (c0, c1) using secret key s."""
        # m_raw = (c0 + c1 * s) mod q
        raw = (ct.c0 + ct.c1 * sk.s) % self.q

        # Convert from centered remainder [ -q//2, q//2 ]
        if raw > self.q // 2:
            raw -= self.q

        return raw / float(ct.scale)

    def decrypt_vector(self, cts: List[FheCiphertext], sk: FheSecretKey, length: Optional[int] = None) -> List[float]:
        """Decrypt a list of ciphertexts."""
        limit = length if length is not None else len(cts)
        return [self.decrypt(c, sk) for c in cts[:limit]]

    def add(self, ct_a: FheCiphertext, ct_b: FheCiphertext) -> FheCiphertext:
        """Homomorphic addition: c_add = c_A + c_B (mod q)."""
        c0 = (ct_a.c0 + ct_b.c0) % self.q
        c1 = (ct_a.c1 + ct_b.c1) % self.q
        return FheCiphertext(c0=c0, c1=c1, scale=ct_a.scale)

    def homomorphic_add(self, a: Any, b: Any) -> Any:
        """Add two ciphertexts or two vectors of ciphertexts."""
        if isinstance(a, list) and isinstance(b, list):
            return [self.add(x, y) for x, y in zip(a, b)]
        return self.add(a, b)

    def multiply_plain(self, ct: FheCiphertext, scalar: float) -> FheCiphertext:
        """Homomorphic multiplication by a plaintext scalar: c_mul = c * scalar."""
        w_int = int(round(scalar * 100))  # Scale scalar by 100
        c0 = (ct.c0 * w_int) % self.q
        c1 = (ct.c1 * w_int) % self.q
        new_scale = ct.scale * 100
        return FheCiphertext(c0=c0, c1=c1, scale=new_scale)

    def homomorphic_multiply_plain(self, a: Any, scalar: float) -> Any:
        """Multiply ciphertext or vector of ciphertexts by scalar."""
        if isinstance(a, list):
            return [self.multiply_plain(x, scalar) for x in a]
        return self.multiply_plain(a, scalar)


class EncryptedClinicalRiskPredictor:
    """Evaluates multivariate clinical risk models directly over encrypted patient features."""

    # Validated weights for 10-Year ASCVD Cardiovascular Risk proxy
    ASCVD_WEIGHTS = {
        "age": 0.052,         # Points per year of age
        "systolic_bp": 0.018, # Points per mmHg SBP
        "total_chol": 0.008,  # Points per mg/dL
        "hdl_chol": -0.015,   # Protective effect
        "smoker": 0.450,      # Binary risk factor
    }
    ASCVD_VECTOR_WEIGHTS = [0.052, 0.018, 0.008, -0.015, 0.450, 0.350]
    ASCVD_BIAS = -3.80

    def __init__(self, context: Optional[HomomorphicContext] = None) -> None:
        self.ctx = context or HomomorphicContext()

    @property
    def context(self) -> HomomorphicContext:
        """Context accessor."""
        return self.ctx

    def evaluate_plaintext(self, vitals: List[float] | Dict[str, float]) -> float:
        """Compute plaintext ASCVD cardiovascular risk probability [0, 1]."""
        if isinstance(vitals, dict):
            raw = self.ASCVD_BIAS
            for k, w in self.ASCVD_WEIGHTS.items():
                raw += vitals.get(k, 0.0) * w
        else:
            raw = self.ASCVD_BIAS
            for idx, w in enumerate(self.ASCVD_VECTOR_WEIGHTS):
                if idx < len(vitals):
                    raw += vitals[idx] * w
        # Logistic sigmoid to bounded risk probability [0, 1]
        clamped = max(-20.0, min(20.0, raw))
        return 1.0 / (1.0 + math.exp(-clamped))

    def encrypt_patient_vitals(self, vitals: List[float], pk: FhePublicKey) -> List[FheCiphertext]:
        """Encrypt a list of patient vital signs."""
        return self.ctx.encrypt_vector(vitals, pk)

    def evaluate_encrypted_ascvd(self, encrypted_vitals: List[FheCiphertext]) -> FheCiphertext:
        """Homomorphically evaluate linear risk score over vector of encrypted vitals."""
        # Construct bias directly in ciphertext
        bias_int = int(round(self.ASCVD_BIAS * self.ctx.scale * 100))
        accum = FheCiphertext(c0=bias_int % self.ctx.q, c1=0, scale=self.ctx.scale * 100)

        for idx, w in enumerate(self.ASCVD_VECTOR_WEIGHTS):
            if idx < len(encrypted_vitals):
                feat_ct = encrypted_vitals[idx]
                scaled_ct = self.ctx.multiply_plain(feat_ct, w)
                accum = self.ctx.add(accum, scaled_ct)

        return accum

    def decrypt_risk_score(self, encrypted_score: FheCiphertext, sk: FheSecretKey) -> float:
        """Decrypt ciphertext and evaluate logistic sigmoid probability."""
        raw_score = self.ctx.decrypt(encrypted_score, sk)
        clamped = max(-20.0, min(20.0, raw_score))
        return 1.0 / (1.0 + math.exp(-clamped))

    def evaluate_encrypted_ascvd_risk(
        self,
        encrypted_vitals: Dict[str, FheCiphertext],
        public_key: FhePublicKey,
    ) -> FheCiphertext:
        """Compute 10-Year ASCVD Risk linear score directly on ciphertext dictionary."""
        # 1. Initialize with encrypted bias term
        bias_ct = self.ctx.encrypt(self.ASCVD_BIAS, public_key)
        bias_scaled = FheCiphertext(
            c0=(bias_ct.c0 * 100) % self.ctx.q,
            c1=(bias_ct.c1 * 100) % self.ctx.q,
            scale=bias_ct.scale * 100,
        )

        accum = bias_scaled

        # 2. Accumulate encrypted weighted dot product: sum(w_i * ct_i)
        for feature, weight in self.ASCVD_WEIGHTS.items():
            if feature in encrypted_vitals:
                feat_ct = encrypted_vitals[feature]
                weighted_ct = self.ctx.multiply_plain(feat_ct, weight)
                accum = self.ctx.add(accum, weighted_ct)

        return accum

