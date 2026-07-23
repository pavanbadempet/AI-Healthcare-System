"""
Pharmacy Inventory & Reorder Optimization Engine
=================================================
Predicts medication consumption rates, safety stock reorder thresholds,
and expiration risk alerts across hospital pharmacy stock.
"""

from typing import Dict, List, Optional


class PharmacyInventoryOptimizer:
    """Calculates pharmacy reorder points and stock expiration risks."""

    def evaluate_medication_stock(
        self,
        medication_id: str,
        medication_name: str,
        current_units: int,
        average_daily_usage: float,
        lead_time_days: int = 5,
        days_to_expiration: Optional[int] = None,
    ) -> Dict[str, any]:
        # Safety stock buffer = 2 days of usage
        safety_stock = int(average_daily_usage * 2)
        reorder_point = int((average_daily_usage * lead_time_days) + safety_stock)

        needs_reorder = current_units <= reorder_point
        days_of_stock_remaining = round(current_units / average_daily_usage, 1) if average_daily_usage > 0 else 999.0

        is_expiration_risk = False
        if days_to_expiration is not None and days_to_expiration <= 30:
            is_expiration_risk = True

        status = "CRITICAL_LOW" if current_units <= safety_stock else ("REORDER_NOW" if needs_reorder else "OPTIMAL")

        return {
            "medication_id": medication_id,
            "medication_name": medication_name,
            "current_units": current_units,
            "reorder_point_units": reorder_point,
            "days_of_stock_remaining": days_of_stock_remaining,
            "needs_reorder": needs_reorder,
            "is_expiration_risk": is_expiration_risk,
            "inventory_status": status,
        }


# Singleton optimizer instance
pharmacy_optimizer = PharmacyInventoryOptimizer()
