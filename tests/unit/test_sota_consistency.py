"""
Unit tests for SOTA Distributed Consistency Engine (backend/sota_consistency.py).
"""

from backend.sota_consistency import SOTAConsistencyEngine


def test_hlc_crdt_lww_consistency():
    engine = SOTAConsistencyEngine(node_id="node_us_east_1")

    # Set initial value
    reg1 = engine.set_lww_value("PATIENT_BED_ASSIGNMENT_101", "BED_A")
    assert engine.get_value("PATIENT_BED_ASSIGNMENT_101") == "BED_A"

    # Update value with higher HLC counter
    reg2 = engine.set_lww_value("PATIENT_BED_ASSIGNMENT_101", "BED_B")
    assert engine.get_value("PATIENT_BED_ASSIGNMENT_101") == "BED_B"
    assert (reg2.timestamp.physical_time_ms, reg2.timestamp.logical_counter) > (
        reg1.timestamp.physical_time_ms,
        reg1.timestamp.logical_counter,
    )
