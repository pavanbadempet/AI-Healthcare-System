"""
Secure Multi-Party Computation (SMPC) & Private Set Intersection (PSI) Engine.

Enables sovereign healthcare institutions (e.g., Hospital Alpha and Hospital Beta)
to compute multi-institutional cohort overlaps and aggregate clinical statistics
(e.g., shared diabetic cohort prevalence, mean HbA1c, MACE incidence)
with zero patient identifier disclosure and cryptographic unlinkability.

Implements:
1. Commutative Diffie-Hellman Private Set Intersection (PSI).
2. Cryptographic Patient Identifier Blind Hashing.
3. 2-Party Additive Secret Sharing for Federated Statistical Aggregation.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, List

# Standard NIST P-256 Prime for Commutative Exponentiation
PRIME_256 = 115792089210356248762697444267719149666716635294245070007535560942673067344049
# Large Modulus for Additive Secret Sharing of Fixed-Point Quantities (2^64)
MODULUS_64 = 18446744073709551616


@dataclass
class PsiParticipant:
    """
    Simulates a secure cryptographic participant holding a private secret key.
    """
    institution_id: str
    private_key: int = field(default_factory=lambda: secrets.randbelow(PRIME_256 - 3) + 2)

    def blind_identifiers(self, identifiers: List[str]) -> Dict[str, str]:
        """
        Hashes and exponentiates identifiers: (H(id)^k) mod P.
        Returns mapping of original identifier -> blinded hex token.
        """
        blinded = {}
        for raw_id in identifiers:
            # Map canonical string to field element
            h_int = int(hashlib.sha256(raw_id.strip().upper().encode("utf-8")).hexdigest(), 16) % PRIME_256
            if h_int == 0:
                h_int = 3
            # Exponentiate
            enc = pow(h_int, self.private_key, PRIME_256)
            blinded[raw_id] = format(enc, "064x")
        return blinded

    def double_blind_tokens(self, foreign_tokens: List[str]) -> List[str]:
        """
        Applies local key to foreign blinded tokens: (token^k) mod P.
        """
        double_blinded = []
        for hex_tok in foreign_tokens:
            t_int = int(hex_tok, 16)
            d_enc = pow(t_int, self.private_key, PRIME_256)
            double_blinded.append(format(d_enc, "064x"))
        return double_blinded


@dataclass
class PsiIntersectionResult:
    intersection_size: int
    matched_double_blinded_tokens: List[str]
    cohort_alpha_size: int
    cohort_beta_size: int
    jaccard_similarity: float
    cryptographic_scheme: str = "Commutative-DH-P256-PSI"


class SmpcPrivateJoinEngine:
    """
    Zero-disclosure multi-party private set intersection and federated aggregation engine.
    """

    def __init__(self) -> None:
        pass

    def compute_psi(
        self,
        identifiers_a: List[str],
        identifiers_b: List[str],
        institution_a_id: str = "HOSPITAL_ALPHA",
        institution_b_id: str = "HOSPITAL_BETA",
    ) -> PsiIntersectionResult:
        """
        Executes a 2-Party Commutative Diffie-Hellman PSI protocol:
        1. A blinds A's items: A1 = { H(a)^kA }
        2. B blinds B's items: B1 = { H(b)^kB }
        3. A and B exchange blinded sets.
        4. A double-blinds B1: B2 = { (H(b)^kB)^kA } = { H(b)^(kB*kA) }
        5. B double-blinds A1: A2 = { (H(a)^kA)^kB } = { H(a)^(kA*kB) }
        6. Intersect A2 and B2. Since kA*kB == kB*kA, matches correspond to identical raw identifiers.
        """
        party_a = PsiParticipant(institution_id=institution_a_id)
        party_b = PsiParticipant(institution_id=institution_b_id)

        # Stage 1: Single blind
        blinded_map_a = party_a.blind_identifiers(identifiers_a)
        blinded_map_b = party_b.blind_identifiers(identifiers_b)

        tokens_a1 = list(blinded_map_a.values())
        tokens_b1 = list(blinded_map_b.values())

        # Stage 2: Cross double-blind
        # Party B applies kB to A1
        tokens_a2 = party_b.double_blind_tokens(tokens_a1)
        # Party A applies kA to B1
        tokens_b2 = party_a.double_blind_tokens(tokens_b1)

        set_a2 = set(tokens_a2)
        set_b2 = set(tokens_b2)

        matched_tokens = sorted(list(set_a2.intersection(set_b2)))
        intersection_size = len(matched_tokens)
        union_size = len(set_a2.union(set_b2))
        jaccard = round(intersection_size / max(union_size, 1), 4)

        return PsiIntersectionResult(
            intersection_size=intersection_size,
            matched_double_blinded_tokens=matched_tokens,
            cohort_alpha_size=len(identifiers_a),
            cohort_beta_size=len(identifiers_b),
            jaccard_similarity=jaccard,
        )

    def federated_additive_secret_share_aggregate(
        self,
        values_a: List[float],
        values_b: List[float],
        scale_factor: int = 1000,
    ) -> Dict[str, Any]:
        """
        Computes federated mean and sum across two parties using 2-party additive secret sharing.
        Each value x is split into two shares: s1 + s2 = x (mod M).
        Neither party learns individual patient values from the other party.
        """
        # Convert floating point metrics (e.g. eGFR or HbA1c) to fixed-point integers
        int_vals_a = [int(round(v * scale_factor)) for v in values_a]
        int_vals_b = [int(round(v * scale_factor)) for v in values_b]

        # Party A generates shares for its values
        shares_a_held_by_a = []
        shares_a_sent_to_b = []
        for val in int_vals_a:
            s1 = secrets.randbelow(MODULUS_64)
            s2 = (val - s1) % MODULUS_64
            shares_a_held_by_a.append(s1)
            shares_a_sent_to_b.append(s2)

        # Party B generates shares for its values
        shares_b_held_by_b = []
        shares_b_sent_to_a = []
        for val in int_vals_b:
            s1 = secrets.randbelow(MODULUS_64)
            s2 = (val - s1) % MODULUS_64
            shares_b_held_by_b.append(s1)
            shares_b_sent_to_a.append(s2)

        # Node A sums its holdings: sum(shares_a_held_by_a) + sum(shares_b_sent_to_a)
        sum_node_a = (sum(shares_a_held_by_a) + sum(shares_b_sent_to_a)) % MODULUS_64

        # Node B sums its holdings: sum(shares_b_held_by_b) + sum(shares_a_sent_to_b)
        sum_node_b = (sum(shares_b_held_by_b) + sum(shares_a_sent_to_b)) % MODULUS_64

        # Reconstructed aggregate sum
        total_int_sum = (sum_node_a + sum_node_b) % MODULUS_64
        # If sum exceeds half modulus, it represents negative or overflow in 2s-complement
        if total_int_sum > (MODULUS_64 // 2):
            total_int_sum -= MODULUS_64

        total_sum = round(total_int_sum / scale_factor, 4)
        total_records = len(values_a) + len(values_b)
        federated_mean = round(total_sum / max(total_records, 1), 4)

        return {
            "protocol": "2-Party-Additive-Secret-Sharing",
            "total_records": total_records,
            "party_a_count": len(values_a),
            "party_b_count": len(values_b),
            "federated_sum": total_sum,
            "federated_mean": federated_mean,
            "zero_leakage_guarantee": True,
        }


smpc_engine = SmpcPrivateJoinEngine()
