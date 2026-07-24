"""
Unit tests for SOTA Backup & Recovery Engine (backend/sota_backup.py).
"""

from backend.sota_backup import SOTABackupEngine


def test_backup_snapshot_creation_and_integrity_verification():
    engine = SOTABackupEngine()
    payload = b"DATABASE_PATIENT_RECORDS_BACKUP_BLOB_CONTENT_123"

    manifest = engine.create_snapshot(payload, backup_type="FULL")
    assert manifest.snapshot_id.startswith("SNAP_")
    assert manifest.total_bytes == len(payload)
    assert manifest.is_immutable_worm

    is_valid = engine.verify_snapshot_integrity(manifest, payload)
    assert is_valid

    # Corrupt data verification failure
    corrupted = payload + b"_CORRUPTED"
    assert not engine.verify_snapshot_integrity(manifest, corrupted)
