"""Pydantic schemas for Level 11 Autonomous Continuous Durability & Zero-Data-Loss Disaster Recovery OS."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WalRecordRequest(BaseModel):
    """Request to append transaction mutation to continuous WAL stream."""
    tx_id: str = Field(..., description="Unique transaction ID")
    table_name: str = Field(..., description="Affected clinical table")
    operation: str = Field(..., description="INSERT, UPDATE, DELETE")
    row_id: str = Field(..., description="Primary key value")
    before_image: Optional[Dict[str, Any]] = Field(None, description="Row state before transaction")
    after_image: Optional[Dict[str, Any]] = Field(None, description="Row state after transaction")


class WalRecordResponse(BaseModel):
    """Response containing recorded WAL record and chain status."""
    record: Dict[str, Any]
    current_lsn: int
    chain_valid: bool
    status: str = "WAL_RECORDED_STREAMING"


class PitrRestoreRequest(BaseModel):
    """Request to execute microsecond Point-In-Time Recovery."""
    target_timestamp_utc: Optional[str] = Field(None, description="Exact target timestamp (ISO 8601 with microseconds)")
    target_lsn: Optional[int] = Field(None, description="Exact target Log Sequence Number")


class PitrRestoreResponse(BaseModel):
    """Point-In-Time recovered state."""
    restored_state: Dict[str, Any]
    replayed_records: int
    target: str
    status: str = "POINT_IN_TIME_RESTORE_COMPLETED"


class RestoreVerifyRequest(BaseModel):
    """Request to execute autonomous ephemeral restore rehearsal."""
    foreign_keys: Optional[Dict[str, Any]] = Field(None, description="Optional custom foreign key relations")


class RestoreVerifyResponse(BaseModel):
    """Proof of Recoverability certificate."""
    certificate: Dict[str, Any]
    is_compliant: bool
    rto_seconds: float
    rpo_seconds: float
    status: str


class WormSnapshotRequest(BaseModel):
    """Request to create an immutable WORM snapshot."""
    payload_str: str = Field(..., description="Clinical data payload to snapshot")
    retention_days: int = Field(2555, description="Statutory retention window in days (default 7 years)")


class WormSnapshotResponse(BaseModel):
    """Created WORM snapshot manifest."""
    manifest: Dict[str, Any]
    status: str = "WORM_SNAPSHOT_LOCKED"


class WormVerifyRequest(BaseModel):
    """Request to verify integrity of a WORM snapshot."""
    snapshot_id: str = Field(..., description="ID of WORM snapshot to audit")


class WormVerifyResponse(BaseModel):
    """Verification result of WORM snapshot."""
    snapshot_id: str
    is_valid: bool
    status: str


class DisasterFailoverRequest(BaseModel):
    """Request to trigger disaster recovery failover simulation."""
    failed_node_id: Optional[str] = Field(None, description="Node to simulate catastrophic failure on")


class DisasterFailoverResponse(BaseModel):
    """Result of autonomous failover."""
    event: Dict[str, Any]
    active_leader: str
    epoch_fencing_token: int
    rpo_lost_lsns: int
    rto_duration_ms: float
    status: str
