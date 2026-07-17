import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import types
import importlib

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

def run_debug():
    sensitive_error = "db password=health-secret patient_name=Sensitive User"
    fake_database = types.ModuleType("backend.database")
    fake_database.engine = FailingEngine(sensitive_error)
    fake_ml_module = types.ModuleType("backend.ml_service")
    fake_ml_module.ml_service = FailingMLService(sensitive_error)
    sys.modules["backend.database"] = fake_database
    sys.modules["backend.ml_service"] = fake_ml_module
    
    enterprise_features = importlib.import_module("backend.enterprise_features")
    metrics = enterprise_features.EnterpriseMetrics(redis_client=FailingRedis(sensitive_error))
    
    try:
        result = metrics.get_health_status()
        print("RESULT:", result)
    except Exception as e:
        print("RAISED:", type(e), e)

if __name__ == "__main__":
    run_debug()
