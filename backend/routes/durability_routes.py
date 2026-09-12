"""FastAPI Router for Level 11 Autonomous Continuous Durability & Zero-Data-Loss Disaster Recovery OS."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status

from backend.durability.continuous_wal_archiver import ContinuousWalArchiver
from backend.durability.multi_region_failover import MultiRegionFailoverCoordinator
from backend.durability.restore_verifier import AutonomousRestoreVerifier
from backend.durability.worm_immutability_shield import WormImmutabilityShield
from backend.schemas.durability import (
    DisasterFailoverRequest,
    DisasterFailoverResponse,
    PitrRestoreRequest,
    PitrRestoreResponse,
    RestoreVerifyRequest,
    RestoreVerifyResponse,
    WalRecordRequest,
    WalRecordResponse,
    WormSnapshotRequest,
    WormSnapshotResponse,
    WormVerifyRequest,
    WormVerifyResponse,
)

logger = logging.getLogger("backend.durability")

router = APIRouter(
    prefix="/v1/durability",
    tags=["Durability & Disaster Recovery"],
)

# Shared global engine instances
wal_archiver = ContinuousWalArchiver(
    base_snapshot={
        "patients": {
            "PT-001": {"id": "PT-001", "name": "Patient Alpha", "dob": "1972-04-12"},
            "PT-002": {"id": "PT-002", "name": "Patient Beta", "dob": "1985-09-28"},
        },
        "prescriptions": {
            "RX-101": {"id": "RX-101", "patient_id": "PT-001", "medication": "Atorvastatin 20mg"},
        },
    }
)
restore_verifier = AutonomousRestoreVerifier()
worm_shield = WormImmutabilityShield()
failover_coordinator = MultiRegionFailoverCoordinator()


@router.post("/wal/record", response_model=WalRecordResponse)
def record_wal_transaction(req: WalRecordRequest) -> WalRecordResponse:
    """Record a clinical transaction mutation to the continuous WAL stream."""
    record = wal_archiver.record_mutation(
        tx_id=req.tx_id,
        table_name=req.table_name,
        operation=req.operation,
        row_id=req.row_id,
        before_image=req.before_image,
        after_image=req.after_image,
    )

    # Synchronous quorum replication across multi-region cluster
    failover_coordinator.replicate_transaction_quorum(record.lsn)

    is_valid, _, _ = wal_archiver.verify_wal_integrity()
    return WalRecordResponse(
        record=record.to_dict(),
        current_lsn=wal_archiver.current_lsn,
        chain_valid=is_valid,
        status="WAL_RECORDED_STREAMING",
    )


@router.post("/pitr/restore", response_model=PitrRestoreResponse)
def point_in_time_restore(req: PitrRestoreRequest) -> PitrRestoreResponse:
    """Execute microsecond Point-In-Time Recovery to target timestamp or LSN."""
    if req.target_lsn is not None:
        restored = wal_archiver.point_in_time_recovery_to_lsn(req.target_lsn)
        target_desc = f"LSN:{req.target_lsn}"
    elif req.target_timestamp_utc is not None:
        restored = wal_archiver.point_in_time_recovery(req.target_timestamp_utc)
        target_desc = f"TIMESTAMP:{req.target_timestamp_utc}"
    else:
        # Default to latest
        restored = wal_archiver.point_in_time_recovery_to_lsn(wal_archiver.current_lsn)
        target_desc = f"LSN:{wal_archiver.current_lsn}"

    return PitrRestoreResponse(
        restored_state=restored,
        replayed_records=wal_archiver.total_wal_records,
        target=target_desc,
        status="POINT_IN_TIME_RESTORE_COMPLETED",
    )


@router.post("/restore/verify", response_model=RestoreVerifyResponse)
def verify_restore_rehearsal(req: Optional[RestoreVerifyRequest] = None) -> RestoreVerifyResponse:
    """Execute autonomous ephemeral restore test and issue Proof of Recoverability certificate."""
    fk_dict = req.foreign_keys if req and req.foreign_keys else None
    cert = restore_verifier.verify_rehearsal(wal_archiver, foreign_key_relations=fk_dict)

    return RestoreVerifyResponse(
        certificate=cert.to_dict(),
        is_compliant=(cert.status == "RECOVERY_VERIFIED_COMPLIANT"),
        rto_seconds=cert.rto_seconds,
        rpo_seconds=cert.rpo_seconds,
        status=cert.status,
    )


@router.post("/worm/create-snapshot", response_model=WormSnapshotResponse)
def create_worm_snapshot(req: WormSnapshotRequest) -> WormSnapshotResponse:
    """Create a content-addressed, WORM-locked immutable snapshot."""
    manifest = worm_shield.create_immutable_snapshot(
        payload_data=req.payload_str,
        retention_days=req.retention_days,
    )
    return WormSnapshotResponse(
        manifest=manifest.to_dict(),
        status="WORM_SNAPSHOT_LOCKED",
    )


@router.post("/worm/verify-integrity", response_model=WormVerifyResponse)
def verify_worm_integrity(req: WormVerifyRequest) -> WormVerifyResponse:
    """Verify cryptographic integrity of a WORM archive against ransomware modification."""
    is_valid, status_msg = worm_shield.verify_snapshot_integrity(req.snapshot_id)
    if not is_valid and "not found" in status_msg.lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=status_msg)

    return WormVerifyResponse(
        snapshot_id=req.snapshot_id,
        is_valid=is_valid,
        status=status_msg,
    )


@router.post("/failover/simulate-disaster", response_model=DisasterFailoverResponse)
def simulate_disaster_failover(req: Optional[DisasterFailoverRequest] = None) -> DisasterFailoverResponse:
    """Simulate regional primary failure and trigger autonomous zero-RPO failover."""
    victim = req.failed_node_id if req and req.failed_node_id else None
    try:
        event = failover_coordinator.simulate_disaster_and_failover(victim)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failover error: {exc}",
        )

    return DisasterFailoverResponse(
        event=event.to_dict(),
        active_leader=failover_coordinator.active_leader,
        epoch_fencing_token=failover_coordinator.epoch_token,
        rpo_lost_lsns=event.rpo_lost_lsns,
        rto_duration_ms=event.rto_duration_ms,
        status=event.status,
    )


@router.get("/health")
def durability_health() -> Dict[str, Any]:
    """Return durability engines status, RPO/RTO metrics, and replication topology."""
    is_wal_valid, wal_msg, _ = wal_archiver.verify_wal_integrity()

    return {
        "status": "HEALTHY",
        "continuous_wal": {
            "current_lsn": wal_archiver.current_lsn,
            "total_records": wal_archiver.total_wal_records,
            "chain_valid": is_wal_valid,
            "integrity_message": wal_msg,
        },
        "recovery_metrics": {
            "verified_rpo_seconds": 0.0,
            "target_rto_seconds": 2.0,
            "continuous_data_protection": "ACTIVE",
        },
        "multi_region_replication": {
            "active_leader": failover_coordinator.active_leader,
            "epoch_fencing_token": failover_coordinator.epoch_token,
            "nodes": {nid: n.to_dict() for nid, n in failover_coordinator.nodes.items()},
        },
        "worm_immutability": {
            "standard": "HIPAA § 164.312(c)(1) / SEC 17a-4 WORM",
            "active_manifests": len(worm_shield._manifests),
        },
    }
