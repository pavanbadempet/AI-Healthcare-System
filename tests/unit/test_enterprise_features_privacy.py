from unittest.mock import patch, MagicMock
from backend.enterprise_features import EnterpriseMetrics, HEALTH_CHECK_UNHEALTHY

def test_enterprise_health_status_hides_dependency_failure_details():
    sensitive_error = "db password=health-secret patient_name=Sensitive User"
    
    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.ping.side_effect = RuntimeError(sensitive_error)
    
    # Mock ML service
    mock_ml = MagicMock()
    mock_ml.health_check.side_effect = RuntimeError(sensitive_error)
    
    with patch("backend.database.engine") as mock_engine, \
         patch("backend.ml_service.ml_service", mock_ml):
         
        # Make engine.connect() fail
        mock_engine.connect.side_effect = RuntimeError(sensitive_error)
        
        metrics = EnterpriseMetrics(redis_client=mock_redis)
        result = metrics.get_health_status()
        
        assert result["status"] == "degraded"
        assert result["checks"]["database"] == HEALTH_CHECK_UNHEALTHY
        assert result["checks"]["redis"] == HEALTH_CHECK_UNHEALTHY
        assert result["checks"]["ml_models"] == HEALTH_CHECK_UNHEALTHY
        assert sensitive_error not in str(result)
        assert "health-secret" not in str(result)
        assert "Sensitive User" not in str(result)
