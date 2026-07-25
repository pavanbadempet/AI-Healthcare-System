"""
Unit tests for SOTA Federated Privacy Engine (backend/sota_federated_privacy_layer.py).
"""

from backend.sota_federated_privacy_layer import SOTAFederatedPrivacyLayerEngine


def test_federated_gradient_aggregation_with_differential_privacy():
    engine = SOTAFederatedPrivacyLayerEngine()

    hospital_weights = [0.85, 0.87, 0.84, 0.86]
    result = engine.aggregate_gradients_with_dp(hospital_weights, epsilon=0.5, delta=1e-5)

    assert result.hospital_nodes_count == 4
    assert isinstance(result.aggregated_weight_mean, float)
    assert result.epsilon_privacy_budget == 0.5
    assert result.is_differential_privacy_applied
    assert result.execution_time_ms >= 0.0
