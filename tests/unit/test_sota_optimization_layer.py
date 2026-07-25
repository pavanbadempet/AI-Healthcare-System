"""
Unit tests for SOTA Resource Optimization Engine (backend/sota_optimization_layer.py).
"""

from backend.sota_optimization_layer import SOTAOptimizationLayerEngine


def test_linear_programming_resource_allocation():
    engine = SOTAOptimizationLayerEngine()

    available_beds = ["BED_ICU_1", "BED_ICU_2"]
    patient_priorities = {"PAT_CRITICAL": 10, "PAT_STABLE": 3, "PAT_MODERATE": 6}

    result = engine.optimize_resource_allocation(available_beds, patient_priorities)

    assert result.is_pareto_optimal
    assert len(result.assignments) == 2
    assert result.assignments[0].assigned_slot == "PATIENT_PAT_CRITICAL"
    assert result.assignments[1].assigned_slot == "PATIENT_PAT_MODERATE"
    assert result.objective_value > 0.0
