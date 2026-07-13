import importlib
import sys
import types


def _load_enterprise_features(monkeypatch):
    for module_name in ["backend.enterprise_features", "redis"]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    redis_module = types.ModuleType("redis")

    class Redis:
        pass

    redis_module.Redis = Redis
    monkeypatch.setitem(sys.modules, "redis", redis_module)
    return importlib.import_module("backend.enterprise_features")


class FailingEngine:
    def __init__(self, message: str):
        self.message = message

    def connect(self):
        raise RuntimeError(self.message)


class FailingRedis:
    def __init__(self, message: str):
        self.message = message

    def ping(self):
        raise RuntimeError(self.message)


class FailingMLService:
    def __init__(self, message: str):
        self.message = message

    def health_check(self):
        raise RuntimeError(self.message)


def test_enterprise_health_status_hides_dependency_failure_details(monkeypatch):
    enterprise_features = _load_enterprise_features(monkeypatch)
    sensitive_error = "db password=health-secret patient_name=Sensitive User"

    fake_database = types.ModuleType("backend.database")
    fake_database.engine = FailingEngine(sensitive_error)
    fake_ml_module = types.ModuleType("backend.ml_service")
    fake_ml_module.ml_service = FailingMLService(sensitive_error)
    monkeypatch.setitem(sys.modules, "backend.database", fake_database)
    monkeypatch.setitem(sys.modules, "backend.ml_service", fake_ml_module)

    metrics = enterprise_features.EnterpriseMetrics(redis_client=FailingRedis(sensitive_error))

    result = metrics.get_health_status()

    assert result["status"] == "degraded"
    assert result["checks"]["database"] == enterprise_features.HEALTH_CHECK_UNHEALTHY
    assert result["checks"]["redis"] == enterprise_features.HEALTH_CHECK_UNHEALTHY
    assert result["checks"]["ml_models"] == enterprise_features.HEALTH_CHECK_UNHEALTHY
    assert sensitive_error not in str(result)
    assert "health-secret" not in str(result)
    assert "Sensitive User" not in str(result)
