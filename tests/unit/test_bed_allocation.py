"""
Unit tests for Bed Allocation Optimizer
"""

import pytest
from backend.ml.bed_allocation_optimizer import BedAllocationOptimizer, bed_optimizer


def test_allocate_patient_bed_success():
    res = bed_optimizer.allocate_patient_bed(
        patient_id=101,
        acuity_level="ICU",
        requires_isolation=True,
    )
    assert res["allocation_status"] == "SUCCESS"
    assert res["allocated_bed_id"] == "ICU-101"
    assert res["is_isolation"] is True


def test_allocate_patient_bed_waitlisted():
    res = bed_optimizer.allocate_patient_bed(
        patient_id=102,
        acuity_level="ICU",
        requires_isolation=True,
        available_beds=[
            {"bed_id": "ICU-101", "ward": "ICU", "is_occupied": True, "is_isolation": True}
        ],
    )
    assert res["allocation_status"] == "WAITLISTED"
    assert res["allocated_bed_id"] is None
