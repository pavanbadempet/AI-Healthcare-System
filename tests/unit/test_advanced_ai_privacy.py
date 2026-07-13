import importlib
import sys
import types

import numpy as np


def _load_advanced_ai(monkeypatch):
    for module_name in ["backend.advanced_ai", "redis"]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    redis_module = types.ModuleType("redis")

    class Redis:
        pass

    redis_module.Redis = Redis
    monkeypatch.setitem(sys.modules, "redis", redis_module)
    return importlib.import_module("backend.advanced_ai")


def test_generate_explanation_hides_failure_details(monkeypatch, caplog):
    advanced_ai = _load_advanced_ai(monkeypatch)
    service = object.__new__(advanced_ai.RealTimePredictionService)
    sensitive_prediction = "prediction token=advanced-secret patient_name=Sensitive User"
    caplog.set_level("ERROR", logger="backend.advanced_ai")

    result = service._generate_explanation(
        "diabetes",
        np.array([120, 30, 45]),
        sensitive_prediction,
        {"agreement_rate": 1.0, "uncertainty": 0.0},
    )

    assert result == {
        "method": "failed",
        "error": advanced_ai.ADVANCED_AI_FAILURE_MESSAGE,
    }
    assert sensitive_prediction not in str(result)
    assert "advanced-secret" not in str(result)
    assert "Sensitive User" not in str(result)
    assert sensitive_prediction not in caplog.text
    assert "advanced-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
