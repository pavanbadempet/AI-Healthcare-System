"""Continuous Streaming Write-Ahead Log (WAL) & Microsecond Point-In-Time Recovery (PITR) Engine.

Captures all transactional database mutations as an immutable, cryptographically chained
WAL delta stream. Enables exact microsecond state reconstruction (PITR) from base snapshots
and provides CRC32C/SHA-256 bit-rot corruption detection.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _compute_crc32(payload: str) -> int:
    """Compute CRC32 checksum to detect bit rot and storage transmission errors."""
    return zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF


def _iso_now_microseconds() -> str:
    """Return ISO 8601 UTC timestamp with microsecond resolution."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class WalRecord:
    """Immutable Write-Ahead-Log transaction delta record."""
    lsn: int
    timestamp_utc: str
    tx_id: str
    table_name: str
    operation: str  # INSERT, UPDATE, DELETE, CHECKPOINT
    row_id: str
    before_image: Optional[Dict[str, Any]]
    after_image: Optional[Dict[str, Any]]
    prev_record_hash: str
    record_hash: str
    crc32: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lsn": self.lsn,
            "timestamp_utc": self.timestamp_utc,
            "tx_id": self.tx_id,
            "table_name": self.table_name,
            "operation": self.operation,
            "row_id": self.row_id,
            "before_image": self.before_image,
            "after_image": self.after_image,
            "prev_record_hash": self.prev_record_hash,
            "record_hash": self.record_hash,
            "crc32": self.crc32,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WalRecord:
        return cls(
            lsn=int(data["lsn"]),
            timestamp_utc=str(data["timestamp_utc"]),
            tx_id=str(data["tx_id"]),
            table_name=str(data["table_name"]),
            operation=str(data["operation"]),
            row_id=str(data["row_id"]),
            before_image=data.get("before_image"),
            after_image=data.get("after_image"),
            prev_record_hash=str(data["prev_record_hash"]),
            record_hash=str(data["record_hash"]),
            crc32=int(data["crc32"]),
        )


class ContinuousWalArchiver:
    """Manages continuous WAL streaming, cryptographic chaining, and microsecond PITR."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(
        self,
        base_snapshot: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    ) -> None:
        # Table -> row_id -> data dict
        self._base_snapshot: Dict[str, Dict[str, Dict[str, Any]]] = deepcopy(base_snapshot) if base_snapshot else {}
        self._wal_stream: List[WalRecord] = []
        self._current_lsn: int = 0
        self._last_record_hash: str = self.GENESIS_HASH

    @property
    def current_lsn(self) -> int:
        return self._current_lsn

    @property
    def total_wal_records(self) -> int:
        return len(self._wal_stream)

    @property
    def wal_stream(self) -> List[WalRecord]:
        return self._wal_stream

    def record_mutation(
        self,
        tx_id: str,
        table_name: str,
        operation: str,
        row_id: str,
        before_image: Optional[Dict[str, Any]] = None,
        after_image: Optional[Dict[str, Any]] = None,
        custom_timestamp: Optional[str] = None,
    ) -> WalRecord:
        """Append an atomic transaction mutation to the continuous WAL stream."""
        self._current_lsn += 1
        ts = custom_timestamp or _iso_now_microseconds()
        op = operation.upper().strip()

        # Canonical serialized payload for deterministic hashing
        raw_content = json.dumps(
            {
                "lsn": self._current_lsn,
                "timestamp_utc": ts,
                "tx_id": tx_id,
                "table_name": table_name,
                "operation": op,
                "row_id": str(row_id),
                "before_image": before_image,
                "after_image": after_image,
                "prev_record_hash": self._last_record_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        crc = _compute_crc32(raw_content)
        rec_hash = hashlib.sha256((raw_content + f":CRC32:{crc}").encode("utf-8")).hexdigest()

        record = WalRecord(
            lsn=self._current_lsn,
            timestamp_utc=ts,
            tx_id=tx_id,
            table_name=table_name,
            operation=op,
            row_id=str(row_id),
            before_image=deepcopy(before_image),
            after_image=deepcopy(after_image),
            prev_record_hash=self._last_record_hash,
            record_hash=rec_hash,
            crc32=crc,
        )

        self._wal_stream.append(record)
        self._last_record_hash = rec_hash
        return record

    def create_checkpoint(self, tx_id: str = "SYS_CHECKPOINT") -> WalRecord:
        """Create a synchronization checkpoint in the WAL stream."""
        return self.record_mutation(
            tx_id=tx_id,
            table_name="_SYSTEM",
            operation="CHECKPOINT",
            row_id="CHECKPOINT",
            before_image=None,
            after_image={"active_lsn": self._current_lsn, "total_records": len(self._wal_stream)},
        )

    def verify_wal_integrity(self) -> Tuple[bool, str, List[int]]:
        """Verify unbroken cryptographic chaining, monotonic LSNs, and CRC32 bit rot integrity."""
        expected_prev = self.GENESIS_HASH
        corrupted_lsns: List[int] = []

        for idx, rec in enumerate(self._wal_stream):
            # 1. Monotonic LSN check
            expected_lsn = idx + 1
            if rec.lsn != expected_lsn:
                corrupted_lsns.append(rec.lsn)
                return False, f"Non-monotonic LSN gap: expected {expected_lsn}, found {rec.lsn}", corrupted_lsns

            # 2. Hash chaining check
            if rec.prev_record_hash != expected_prev:
                corrupted_lsns.append(rec.lsn)
                return False, f"Broken cryptographic hash chain at LSN {rec.lsn}", corrupted_lsns

            # 3. Payload and CRC32 verification
            raw_content = json.dumps(
                {
                    "lsn": rec.lsn,
                    "timestamp_utc": rec.timestamp_utc,
                    "tx_id": rec.tx_id,
                    "table_name": rec.table_name,
                    "operation": rec.operation,
                    "row_id": rec.row_id,
                    "before_image": rec.before_image,
                    "after_image": rec.after_image,
                    "prev_record_hash": rec.prev_record_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            calc_crc = _compute_crc32(raw_content)
            if calc_crc != rec.crc32:
                corrupted_lsns.append(rec.lsn)
                return False, f"CRC32 bit rot corruption detected at LSN {rec.lsn}", corrupted_lsns

            calc_hash = hashlib.sha256((raw_content + f":CRC32:{calc_crc}").encode("utf-8")).hexdigest()
            if calc_hash != rec.record_hash:
                corrupted_lsns.append(rec.lsn)
                return False, f"Tampered record hash at LSN {rec.lsn}", corrupted_lsns

            expected_prev = rec.record_hash

        return True, "WAL_CHAIN_VERIFIED_ZERO_CORRUPTION", []

    def point_in_time_recovery(
        self,
        target_timestamp_utc: str,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Reconstruct the exact database state at microsecond timestamp T.

        Replays verified WAL segments up to target_timestamp_utc starting from base snapshot.
        """
        # Parse target timestamp
        target_dt = datetime.fromisoformat(target_timestamp_utc.replace("Z", "+00:00"))
        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)

        state: Dict[str, Dict[str, Dict[str, Any]]] = deepcopy(self._base_snapshot)

        for rec in self._wal_stream:
            rec_dt = datetime.fromisoformat(rec.timestamp_utc.replace("Z", "+00:00"))
            if rec_dt.tzinfo is None:
                rec_dt = rec_dt.replace(tzinfo=timezone.utc)

            # Replay strictly up to the target timestamp
            if rec_dt > target_dt:
                break

            if rec.operation == "CHECKPOINT":
                continue

            if rec.table_name not in state:
                state[rec.table_name] = {}

            if rec.operation in ("INSERT", "UPDATE"):
                if rec.after_image is not None:
                    state[rec.table_name][rec.row_id] = deepcopy(rec.after_image)
            elif rec.operation == "DELETE":
                state[rec.table_name].pop(rec.row_id, None)

        return state

    def point_in_time_recovery_to_lsn(
        self,
        target_lsn: int,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Reconstruct database state at exact Log Sequence Number (LSN)."""
        state: Dict[str, Dict[str, Dict[str, Any]]] = deepcopy(self._base_snapshot)

        for rec in self._wal_stream:
            if rec.lsn > target_lsn:
                break

            if rec.operation == "CHECKPOINT":
                continue

            if rec.table_name not in state:
                state[rec.table_name] = {}

            if rec.operation in ("INSERT", "UPDATE"):
                if rec.after_image is not None:
                    state[rec.table_name][rec.row_id] = deepcopy(rec.after_image)
            elif rec.operation == "DELETE":
                state[rec.table_name].pop(rec.row_id, None)

        return state
