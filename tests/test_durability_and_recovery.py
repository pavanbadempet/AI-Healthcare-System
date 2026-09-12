"""Tests for Level 11 Autonomous Continuous Durability & Zero-Data-Loss Disaster Recovery OS.

Verifies:
1. Continuous streaming WAL delta journaling, monotonic LSN, and microsecond PITR.
2. Ephemeral restore sandbox rehearsals with foreign key validation and Proof of Recoverability (PoR).
3. Air-gapped ransomware shield with WORM retention locks, Merkle root verification, and tamper detection.
4. Multi-region consensus quorum replication, epoch fencing, and sub-second zero-RPO failover.
5. FastAPI /v1/durability endpoints integration.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.durability.continuous_wal_archiver import (
    ContinuousWalArchiver,
)
from backend.durability.multi_region_failover import (
    MultiRegionFailoverCoordinator,
)
from backend.durability.restore_verifier import (
    AutonomousRestoreVerifier,
)
from backend.durability.worm_immutability_shield import (
    WormImmutabilityShield,
    WormRetentionActiveError,
)
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# =========================================================================
# 1. Continuous Streaming WAL & Microsecond PITR Tests
# =========================================================================

def test_continuous_wal_mutation_and_lsn_ordering():
    """Verify continuous WAL record appending, monotonic LSNs, and hash chaining."""
    archiver = ContinuousWalArchiver()

    r1 = archiver.record_mutation(
        tx_id="TX-001",
        table_name="patients",
        operation="INSERT",
        row_id="PT-101",
        after_image={"id": "PT-101", "name": "John Doe", "stage": "Stage II"},
    )
    r2 = archiver.record_mutation(
        tx_id="TX-002",
        table_name="prescriptions",
        operation="INSERT",
        row_id="RX-201",
        after_image={"id": "RX-201", "patient_id": "PT-101", "drug": "Osimertinib"},
    )

    assert r1.lsn == 1
    assert r2.lsn == 2
    assert r2.prev_record_hash == r1.record_hash
    assert r1.crc32 > 0
    assert r2.crc32 > 0

    is_valid, msg, corrupted = archiver.verify_wal_integrity()
    assert is_valid is True
    assert msg == "WAL_CHAIN_VERIFIED_ZERO_CORRUPTION"
    assert len(corrupted) == 0


def test_wal_chain_integrity_and_bit_rot_detection():
    """Verify bit rot or payload tampering in WAL stream is caught by CRC32 / SHA-256."""
    archiver = ContinuousWalArchiver()
    archiver.record_mutation("TX-1", "vitals", "INSERT", "V-1", after_image={"hr": 78})
    archiver.record_mutation("TX-2", "vitals", "UPDATE", "V-1", after_image={"hr": 115})

    # Tamper with the CRC32 or after_image of the first record
    archiver._wal_stream[0].crc32 ^= 0xFFFFFFFF

    is_valid, msg, corrupted = archiver.verify_wal_integrity()
    assert is_valid is False
    assert "CRC32 bit rot corruption" in msg
    assert 1 in corrupted


def test_microsecond_point_in_time_recovery():
    """Verify granular point-in-time recovery to exact microsecond checkpoints."""
    base_state = {
        "patients": {
            "PT-500": {"id": "PT-500", "diagnosis": "Asthma", "status": "Stable"},
        },
        "prescriptions": {},
    }
    archiver = ContinuousWalArchiver(base_snapshot=base_state)

    # T1: Update diagnosis
    t1 = "2026-09-13T10:00:00.100000Z"
    archiver.record_mutation(
        "TX-10", "patients", "UPDATE", "PT-500",
        before_image=base_state["patients"]["PT-500"],
        after_image={"id": "PT-500", "diagnosis": "Severe Persistent Asthma", "status": "Exacerbation"},
        custom_timestamp=t1,
    )

    # T2: Add prescription
    t2 = "2026-09-13T10:00:00.200000Z"
    archiver.record_mutation(
        "TX-11", "prescriptions", "INSERT", "RX-777",
        after_image={"id": "RX-777", "patient_id": "PT-500", "med": "Prednisone 40mg"},
        custom_timestamp=t2,
    )

    # T3: Accidental deletion of prescription
    t3 = "2026-09-13T10:00:00.300000Z"
    archiver.record_mutation(
        "TX-12", "prescriptions", "DELETE", "RX-777",
        before_image={"id": "RX-777", "patient_id": "PT-500", "med": "Prednisone 40mg"},
        custom_timestamp=t3,
    )

    # Current state at T3 has prescription deleted
    curr_state = archiver.point_in_time_recovery(t3)
    assert "RX-777" not in curr_state["prescriptions"]

    # PITR Rewind to T2: prescription RX-777 must be recovered!
    recovered_t2 = archiver.point_in_time_recovery(t2)
    assert "RX-777" in recovered_t2["prescriptions"]
    assert recovered_t2["prescriptions"]["RX-777"]["med"] == "Prednisone 40mg"
    assert recovered_t2["patients"]["PT-500"]["diagnosis"] == "Severe Persistent Asthma"

    # PITR Rewind to before T1: original diagnosis "Asthma"
    t_before = "2026-09-13T09:59:59.000000Z"
    recovered_t0 = archiver.point_in_time_recovery(t_before)
    assert recovered_t0["patients"]["PT-500"]["diagnosis"] == "Asthma"
    assert len(recovered_t0["prescriptions"]) == 0


# =========================================================================
# 2. Autonomous Ephemeral Restore Verifier & PoR Tests
# =========================================================================

def test_ephemeral_restore_verification_and_por_certificate():
    """Verify automated rehearsal execution, foreign key validation, and PoR certificate."""
    base = {
        "patients": {"P-1": {"id": "P-1", "name": "Alice"}},
        "prescriptions": {},
    }
    archiver = ContinuousWalArchiver(base_snapshot=base)
    archiver.record_mutation(
        "TX-1", "prescriptions", "INSERT", "RX-1",
        after_image={"id": "RX-1", "patient_id": "P-1", "drug": "Metformin"},
    )

    verifier = AutonomousRestoreVerifier()
    cert = verifier.verify_rehearsal(archiver)

    assert cert.status == "RECOVERY_VERIFIED_COMPLIANT"
    assert cert.rpo_seconds == 0.0
    assert cert.rto_seconds < 1.0
    assert cert.foreign_key_violations == 0
    assert cert.data_checksum_valid is True
    assert cert.table_row_counts["patients"] == 1
    assert cert.table_row_counts["prescriptions"] == 1
    assert len(cert.certificate_signature) == 64  # SHA-256 HMAC


def test_restore_verification_foreign_key_failure_detection():
    """Verify restore verifier catches orphaned child records violating foreign key integrity."""
    base = {
        "patients": {"P-1": {"id": "P-1"}},
        "prescriptions": {},
    }
    archiver = ContinuousWalArchiver(base_snapshot=base)
    # Insert prescription referencing non-existent patient P-999
    archiver.record_mutation(
        "TX-ERR", "prescriptions", "INSERT", "RX-ORPHAN",
        after_image={"id": "RX-ORPHAN", "patient_id": "P-999", "drug": "Insulin"},
    )

    verifier = AutonomousRestoreVerifier()
    cert = verifier.verify_rehearsal(archiver)

    assert cert.status == "RECOVERY_FAILED_INVARIANTS"
    assert cert.foreign_key_violations == 1


# =========================================================================
# 3. Air-Gapped Ransomware Shield & Immutable WORM Storage Tests
# =========================================================================

def test_worm_snapshot_creation_and_merkle_verification():
    """Verify content-defined chunking, Merkle tree root computation, and WORM manifest."""
    shield = WormImmutabilityShield()
    sample_data = "PATIENT_RECORD_PHI_IMMUTABLE_" * 500  # ~15 KB

    manifest = shield.create_immutable_snapshot(sample_data, retention_days=2555)
    assert manifest.snapshot_id.startswith("WORM-SNAP-")
    assert manifest.is_locked is True
    assert len(manifest.chunk_hashes) > 0
    assert len(manifest.merkle_root) == 64
    assert len(manifest.signature) == 64

    is_valid, msg = shield.verify_snapshot_integrity(manifest.snapshot_id)
    assert is_valid is True
    assert msg == "WORM_INTEGRITY_VERIFIED_TAMPER_FREE"


def test_worm_immutability_deletion_lock():
    """Verify WORM retention lock mathematically rejects deletion during retention window."""
    shield = WormImmutabilityShield()
    manifest = shield.create_immutable_snapshot("CLINICAL_TRIAL_DATA", retention_days=365)

    with pytest.raises(WormRetentionActiveError, match="IMMUTABILITY VIOLATION"):
        shield.attempt_deletion_or_overwrite(manifest.snapshot_id)


def test_worm_ransomware_tamper_detection():
    """Verify ransomware modifying chunk data breaks Merkle verification immediately."""
    shield = WormImmutabilityShield()
    manifest = shield.create_immutable_snapshot("CRITICAL_ICU_AUDIT_LOG_2026", retention_days=100)

    target_chunk = manifest.chunk_hashes[0]
    # Simulate ransomware modifying block bytes on disk
    shield.tamper_chunk_for_testing(target_chunk)

    is_valid, msg = shield.verify_snapshot_integrity(manifest.snapshot_id)
    assert is_valid is False
    assert "Tampering detected" in msg


# =========================================================================
# 4. Multi-Region Quorum Replication & Zero-RPO Failover Tests
# =========================================================================

def test_multi_region_quorum_replication():
    """Verify synchronous quorum consensus replication across 3 regions."""
    coord = MultiRegionFailoverCoordinator()
    assert coord.active_leader == "node-us-east-1"
    assert coord.epoch_token == 1

    # Replicate LSN 100
    has_quorum, acks, msg = coord.replicate_transaction_quorum(lsn=100)
    assert has_quorum is True
    assert acks == 3
    assert "Quorum achieved" in msg


def test_disaster_failover_zero_rpo_and_epoch_fencing():
    """Verify primary failure triggers leader fencing and zero-data-loss failover."""
    coord = MultiRegionFailoverCoordinator()
    # Synchronize all nodes to LSN 50
    coord.replicate_transaction_quorum(lsn=50)

    # Catastrophic failure of active leader (node-us-east-1)
    event = coord.simulate_disaster_and_failover()

    assert event.previous_leader == "node-us-east-1"
    assert event.promoted_leader in ("node-us-west-2", "node-edge-dr-1")
    assert event.epoch_fencing_token == 2
    assert event.rpo_lost_lsns == 0  # Zero data loss!
    assert event.rto_duration_ms < 50.0
    assert event.status == "AUTONOMOUS_ZERO_RPO_FAILOVER_SUCCESS"
    assert coord.active_leader == event.promoted_leader


# =========================================================================
# 5. FastAPI /v1/durability Route Integration Tests
# =========================================================================

def test_route_durability_health(client: TestClient):
    """Verify durability health check reporting continuous WAL and replication state."""
    resp = client.get("/v1/durability/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "continuous_wal" in data
    assert "recovery_metrics" in data
    assert "multi_region_replication" in data
    assert "worm_immutability" in data


def test_route_wal_record_and_pitr(client: TestClient):
    """Verify transaction logging and point-in-time restore over HTTP."""
    wal_req = {
        "tx_id": "TX-HTTP-001",
        "table_name": "vital_signs",
        "operation": "INSERT",
        "row_id": "VS-900",
        "after_image": {"patient_id": "PT-001", "spo2": 99.0, "hr": 72},
    }
    resp_log = client.post("/v1/durability/wal/record", json=wal_req)
    assert resp_log.status_code == 200
    log_data = resp_log.json()
    assert log_data["chain_valid"] is True
    assert log_data["current_lsn"] >= 1

    # PITR restore
    pitr_req = {"target_lsn": log_data["current_lsn"]}
    resp_restore = client.post("/v1/durability/pitr/restore", json=pitr_req)
    assert resp_restore.status_code == 200
    restore_data = resp_restore.json()
    assert "vital_signs" in restore_data["restored_state"]
    assert "VS-900" in restore_data["restored_state"]["vital_signs"]


def test_route_restore_verify(client: TestClient):
    """Verify automated restore rehearsal endpoint returns PoR certificate."""
    resp = client.post("/v1/durability/restore/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_compliant"] is True
    assert data["status"] == "RECOVERY_VERIFIED_COMPLIANT"
    assert "certificate" in data
    assert data["rpo_seconds"] == 0.0


def test_route_worm_snapshot_lifecycle(client: TestClient):
    """Verify WORM snapshot creation and cryptographic integrity verification."""
    snap_req = {
        "payload_str": "ONCOLOGY_BIOPSY_REPORT_2026_GENOMICS_IMMUTABLE",
        "retention_days": 1825,
    }
    resp_snap = client.post("/v1/durability/worm/create-snapshot", json=snap_req)
    assert resp_snap.status_code == 200
    snap_data = resp_snap.json()
    snap_id = snap_data["manifest"]["snapshot_id"]

    # Verify integrity
    verify_req = {"snapshot_id": snap_id}
    resp_verify = client.post("/v1/durability/worm/verify-integrity", json=verify_req)
    assert resp_verify.status_code == 200
    assert resp_verify.json()["is_valid"] is True


def test_route_disaster_failover(client: TestClient):
    """Verify simulated disaster failover endpoint triggers sub-second standby promotion."""
    resp = client.post("/v1/durability/failover/simulate-disaster")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "AUTONOMOUS_ZERO_RPO_FAILOVER_SUCCESS"
    assert data["rpo_lost_lsns"] == 0
    assert data["rto_duration_ms"] < 100.0
    assert data["epoch_fencing_token"] >= 2
