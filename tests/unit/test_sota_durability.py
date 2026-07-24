"""
Unit tests for SOTA High-Durability Commit Log Engine (backend/sota_durability.py).
"""

import os
import tempfile

from backend.sota_durability import SOTADurabilityEngine


def test_wal_durability_and_integrity_verification():
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        engine = SOTADurabilityEngine(log_filepath=tmp_path)
        ack = engine.append_commit_record("TX_1001", "UPDATE_PATIENT_STATUS_DISCHARGED")

        assert ack["tx_id"] == "TX_1001"
        assert ack["status"] == "DURABLY_COMMITTED"
        assert len(ack["checksum"]) == 64

        assert engine.verify_wal_integrity()

        # Simulate silent data corruption (bit rot)
        with open(tmp_path, "a", encoding="utf-8") as f:
            f.write("BAD_CHECKSUM|TX_9999:CORRUPTED_DATA\n")

        assert not engine.verify_wal_integrity()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
