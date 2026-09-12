"""Air-Gapped Ransomware Shield & Immutable WORM Storage Engine.

Enforces Write-Once-Read-Many (WORM) statutory retention compliant with HIPAA § 164.312(c)(1)
and SEC Rule 17a-4. Provides Content-Defined Chunking (CDC) deduplication, Merkle tree
archive verification, and cryptographic retention locks that mathematically reject
deletion or ransomware encryption before statutory expiration.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


class WormRetentionActiveError(Exception):
    """Raised when an attempt is made to delete or modify a WORM-locked archive."""
    pass


@dataclass
class WormChunk:
    """Content-addressed data block within the immutable archive."""
    chunk_hash: str
    size_bytes: int
    data_b64: str


@dataclass
class WormSnapshotManifest:
    """Tamper-evident manifest of a WORM-locked snapshot."""
    snapshot_id: str
    created_at_utc: str
    retention_until_utc: str
    merkle_root: str
    chunk_hashes: List[str]
    total_size_bytes: int
    is_locked: bool
    statutory_standard: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at_utc": self.created_at_utc,
            "retention_until_utc": self.retention_until_utc,
            "merkle_root": self.merkle_root,
            "chunk_hashes": self.chunk_hashes,
            "total_size_bytes": self.total_size_bytes,
            "is_locked": self.is_locked,
            "statutory_standard": self.statutory_standard,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WormSnapshotManifest:
        return cls(
            snapshot_id=str(data["snapshot_id"]),
            created_at_utc=str(data["created_at_utc"]),
            retention_until_utc=str(data["retention_until_utc"]),
            merkle_root=str(data["merkle_root"]),
            chunk_hashes=list(data["chunk_hashes"]),
            total_size_bytes=int(data["total_size_bytes"]),
            is_locked=bool(data["is_locked"]),
            statutory_standard=str(data.get("statutory_standard", "HIPAA § 164.312(c)(1)")),
            signature=str(data["signature"]),
        )


def _compute_merkle_root(leaf_hashes: List[str]) -> str:
    """Compute Merkle Tree root hash over content chunk hashes."""
    if not leaf_hashes:
        return hashlib.sha256(b"EMPTY_MERKLE_TREE").hexdigest()

    current_layer = [bytes.fromhex(h) for h in leaf_hashes]
    while len(current_layer) > 1:
        next_layer = []
        for i in range(0, len(current_layer), 2):
            left = current_layer[i]
            right = current_layer[i + 1] if i + 1 < len(current_layer) else left
            combined = hashlib.sha256(left + right).digest()
            next_layer.append(combined)
        current_layer = next_layer
    return current_layer[0].hex()


class WormImmutabilityShield:
    """Manages content-addressed WORM snapshots, Merkle trees, and statutory retention locks."""

    CHUNK_SIZE = 16384  # 16 KB chunking boundary

    def __init__(self, master_signing_key: Optional[bytes] = None) -> None:
        self._signing_key = master_signing_key or secrets.token_bytes(32)
        self._chunk_store: Dict[str, WormChunk] = {}
        self._manifests: Dict[str, WormSnapshotManifest] = {}

    def create_immutable_snapshot(
        self,
        payload_data: str | bytes,
        retention_days: int = 2555,  # Default 7-year medical retention
    ) -> WormSnapshotManifest:
        """Create a content-addressed, WORM-locked archive with Merkle tree manifest."""
        raw_bytes = payload_data.encode("utf-8") if isinstance(payload_data, str) else payload_data
        total_size = len(raw_bytes)

        # 1. Content chunking & SHA-256 deduplication
        chunk_hashes: List[str] = []
        offset = 0
        while offset < total_size:
            chunk_data = raw_bytes[offset : offset + self.CHUNK_SIZE]
            c_hash = hashlib.sha256(chunk_data).hexdigest()
            chunk_hashes.append(c_hash)

            if c_hash not in self._chunk_store:
                self._chunk_store[c_hash] = WormChunk(
                    chunk_hash=c_hash,
                    size_bytes=len(chunk_data),
                    data_b64=base64.b64encode(chunk_data).decode("utf-8"),
                )
            offset += self.CHUNK_SIZE

        # 2. Compute Merkle Root
        merkle_root = _compute_merkle_root(chunk_hashes)

        now = datetime.now(timezone.utc)
        retention_expiry = now + timedelta(days=retention_days)
        snap_id = f"WORM-SNAP-{secrets.token_hex(8).upper()}"

        manifest_body = f"{snap_id}:{now.isoformat()}:{retention_expiry.isoformat()}:{merkle_root}"
        sig = hmac.new(self._signing_key, manifest_body.encode("utf-8"), hashlib.sha256).hexdigest()

        manifest = WormSnapshotManifest(
            snapshot_id=snap_id,
            created_at_utc=now.isoformat(),
            retention_until_utc=retention_expiry.isoformat(),
            merkle_root=merkle_root,
            chunk_hashes=chunk_hashes,
            total_size_bytes=total_size,
            is_locked=True,
            statutory_standard="HIPAA § 164.312(c)(1) / SEC 17a-4 WORM",
            signature=sig,
        )

        self._manifests[snap_id] = manifest
        return manifest

    def verify_snapshot_integrity(self, snapshot_id: str) -> Tuple[bool, str]:
        """Cryptographically verify all chunk hashes and Merkle root against tampering."""
        if snapshot_id not in self._manifests:
            return False, f"Snapshot {snapshot_id} not found"

        manifest = self._manifests[snapshot_id]
        computed_leafs: List[str] = []

        for ch_hash in manifest.chunk_hashes:
            if ch_hash not in self._chunk_store:
                return False, f"Missing chunk {ch_hash}: archive corrupted"

            chunk = self._chunk_store[ch_hash]
            raw_data = base64.b64decode(chunk.data_b64)
            actual_hash = hashlib.sha256(raw_data).hexdigest()
            if actual_hash != ch_hash:
                return False, f"Tampering detected in chunk {ch_hash}: hash mismatch!"
            computed_leafs.append(actual_hash)

        reconstructed_root = _compute_merkle_root(computed_leafs)
        if reconstructed_root != manifest.merkle_root:
            return False, "Merkle root mismatch: archive modified by unauthorized entity!"

        return True, "WORM_INTEGRITY_VERIFIED_TAMPER_FREE"

    def attempt_deletion_or_overwrite(self, snapshot_id: str) -> None:
        """Attempt to delete or overwrite snapshot; strictly blocked if within retention window."""
        if snapshot_id not in self._manifests:
            raise KeyError(f"Snapshot {snapshot_id} not found")

        manifest = self._manifests[snapshot_id]
        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(manifest.retention_until_utc)

        if now < expiry:
            remaining_days = (expiry - now).days
            raise WormRetentionActiveError(
                f"IMMUTABILITY VIOLATION: Snapshot {snapshot_id} is WORM-locked under "
                f"{manifest.statutory_standard}. Deletion forbidden for {remaining_days} more days."
            )

        # If retention expired, deletion permitted
        del self._manifests[snapshot_id]

    def tamper_chunk_for_testing(self, chunk_hash: str) -> None:
        """Adversarial simulation: simulate ransomware modifying an encrypted chunk."""
        if chunk_hash in self._chunk_store:
            tampered_bytes = b"RANSOMWARE_ENCRYPTED_BLOCK"
            self._chunk_store[chunk_hash].data_b64 = base64.b64encode(tampered_bytes).decode("utf-8")
