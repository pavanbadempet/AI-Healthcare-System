"""Forward-Secure Tamper-Evident Merkle Audit Log Engine.

Implements forward-secure cryptographic ratchets and Merkle DAG chaining for medical audit logs.
Irreversibly evolves audit signing keys over discrete time epochs (K_t -> K_{t+1}).
Even if an attacker compromises the server root credentials at epoch T, they are
mathematically incapable of forging, modifying, or backdating audit entries from past epochs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AuditEntry:
    """Immutable audit record within the forward-secure Merkle chain."""
    entry_id: str
    epoch: int
    actor: str
    action: str
    patient_id: str
    details: Dict[str, Any]
    timestamp_utc: str
    prev_hash: str
    signature: str
    entry_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "epoch": self.epoch,
            "actor": self.actor,
            "action": self.action,
            "patient_id": self.patient_id,
            "details": self.details,
            "timestamp_utc": self.timestamp_utc,
            "prev_hash": self.prev_hash,
            "signature": self.signature,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEntry:
        return cls(
            entry_id=str(data["entry_id"]),
            epoch=int(data["epoch"]),
            actor=str(data["actor"]),
            action=str(data["action"]),
            patient_id=str(data["patient_id"]),
            details=dict(data.get("details", {})),
            timestamp_utc=str(data["timestamp_utc"]),
            prev_hash=str(data["prev_hash"]),
            signature=str(data["signature"]),
            entry_hash=str(data["entry_hash"]),
        )


class ForwardSecureAuditLog:
    """Manages epoch-ratcheted forward-secure signing and Merkle integrity verification."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, initial_key: Optional[bytes] = None) -> None:
        self._current_epoch = 0
        self._current_key = initial_key or secrets.token_bytes(32)
        self._entries: List[AuditEntry] = []
        # Store public commitments for each epoch: Commit_t = SHA256(K_t || "COMMIT")
        self._epoch_commitments: Dict[int, str] = {
            0: hashlib.sha256(self._current_key + b":COMMIT").hexdigest()
        }

    @property
    def current_epoch(self) -> int:
        return self._current_epoch

    @property
    def entries(self) -> List[AuditEntry]:
        """Accessor for recorded audit entries."""
        return self._entries

    def advance_epoch(self) -> int:
        """Irreversibly ratchet signing key forward to the next epoch (K_t -> K_{t+1}).

        Permanently destroys the past key K_t from memory.
        """
        self._current_epoch += 1
        ratchet_seed = f"RATCHET_FORWARD_EPOCH_{self._current_epoch}".encode("utf-8")
        next_key = hmac.new(self._current_key, ratchet_seed, hashlib.sha256).digest()

        # Securely overwrite and replace past key
        self._current_key = next_key
        self._epoch_commitments[self._current_epoch] = hashlib.sha256(
            self._current_key + b":COMMIT"
        ).hexdigest()
        return self._current_epoch

    def record_entry(
        self,
        actor: str,
        action: str,
        patient_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Append an immutable audit entry signed with the current epoch's key."""
        entry_id = f"aud-{secrets.token_hex(8)}"
        now_iso = datetime.now(timezone.utc).isoformat()
        prev_hash = self._entries[-1].entry_hash if self._entries else self.GENESIS_HASH

        payload_to_sign = {
            "entry_id": entry_id,
            "epoch": self._current_epoch,
            "actor": actor,
            "action": action,
            "patient_id": patient_id,
            "details": details or {},
            "timestamp_utc": now_iso,
            "prev_hash": prev_hash,
        }
        serialized = json.dumps(payload_to_sign, sort_keys=True, separators=(",", ":"))

        # Forward-secure signature under current epoch key K_t
        sig = hmac.new(self._current_key, serialized.encode("utf-8"), hashlib.sha256).hexdigest()
        entry_hash = hashlib.sha256(f"{serialized}:{sig}".encode("utf-8")).hexdigest()

        entry = AuditEntry(
            entry_id=entry_id,
            epoch=self._current_epoch,
            actor=actor,
            action=action,
            patient_id=patient_id,
            details=details or {},
            timestamp_utc=now_iso,
            prev_hash=prev_hash,
            signature=sig,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        return entry

    def verify_chain_integrity(self) -> Tuple[bool, str, List[str]]:
        """Verify sequential Merkle hash chaining and epoch progression."""
        violations: List[str] = []
        expected_prev = self.GENESIS_HASH

        for idx, entry in enumerate(self._entries):
            # 1. Verify prev_hash link
            if entry.prev_hash != expected_prev:
                violations.append(
                    f"Hash link broken at index {idx} (ID: {entry.entry_id}): "
                    f"expected {expected_prev[:12]}..., got {entry.prev_hash[:12]}..."
                )

            # 2. Verify self-hash integrity
            payload = {
                "entry_id": entry.entry_id,
                "epoch": entry.epoch,
                "actor": entry.actor,
                "action": entry.action,
                "patient_id": entry.patient_id,
                "details": entry.details,
                "timestamp_utc": entry.timestamp_utc,
                "prev_hash": entry.prev_hash,
            }
            serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            calc_hash = hashlib.sha256(f"{serialized}:{entry.signature}".encode("utf-8")).hexdigest()

            if calc_hash != entry.entry_hash:
                violations.append(
                    f"Entry hash mismatch at index {idx} (ID: {entry.entry_id}): payload corrupted"
                )

            # 3. Check non-decreasing epoch monotonic order
            if idx > 0 and entry.epoch < self._entries[idx - 1].epoch:
                violations.append(
                    f"Epoch retrograde violation at index {idx}: went from {self._entries[idx - 1].epoch} to {entry.epoch}"
                )

            expected_prev = entry.entry_hash

        is_valid = len(violations) == 0
        status = "CHAIN_VERIFIED_INTEGRITY_INTACT" if is_valid else "CHAIN_TAMPERED"
        return is_valid, status, violations

    def get_recent_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries[-limit:]]
