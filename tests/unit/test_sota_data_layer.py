"""
Unit tests for SOTA High-Performance Data Access Engine (backend/sota_data_layer.py).
"""

import time

from backend.sota_data_layer import SOTADataLayerEngine


def test_bitemporal_versioning_and_time_travel_query():
    engine = SOTADataLayerEngine()

    # Insert initial record state
    rec = engine.insert_temporal_record("REC_100", "PAT_500", {"bp": "120/80"})
    t0 = rec.valid_from

    time.sleep(0.02)

    # Soft delete record
    engine.soft_delete_record("REC_100")

    # Time travel query: Should find record at t0
    rec_past = engine.get_as_of("REC_100", t0)
    assert rec_past is not None
    assert rec_past.data["bp"] == "120/80"

    # Current query: Should return None because it is soft-deleted
    rec_present = engine.get_as_of("REC_100", time.time())
    assert rec_present is None
