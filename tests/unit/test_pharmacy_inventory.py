"""
Unit tests for Pharmacy Inventory Optimizer
"""

from backend.ml.pharmacy_inventory_optimizer import pharmacy_optimizer


def test_evaluate_medication_stock_reorder():
    res = pharmacy_optimizer.evaluate_medication_stock(
        medication_id="MED-001",
        medication_name="Amoxicillin 500mg",
        current_units=20,
        average_daily_usage=10.0,
        lead_time_days=5,
    )
    assert res["needs_reorder"] is True
    assert res["inventory_status"] in ["REORDER_NOW", "CRITICAL_LOW"]


def test_evaluate_medication_stock_optimal():
    res = pharmacy_optimizer.evaluate_medication_stock(
        medication_id="MED-002",
        medication_name="Ibuprofen 400mg",
        current_units=500,
        average_daily_usage=10.0,
        lead_time_days=5,
    )
    assert res["needs_reorder"] is False
    assert res["inventory_status"] == "OPTIMAL"
