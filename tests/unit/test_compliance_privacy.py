import importlib
import sys
import types


def _load_compliance(monkeypatch):
    for module_name in ["backend.compliance", "redis"]:
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    redis_module = types.ModuleType("redis")

    class Redis:
        pass

    redis_module.Redis = Redis
    monkeypatch.setitem(sys.modules, "redis", redis_module)
    return importlib.import_module("backend.compliance")


class FailingDb:
    def __init__(self, message: str):
        self.message = message

    def connect(self):
        raise RuntimeError(self.message)


def test_gdpr_access_request_hides_sensitive_failure_details(monkeypatch, caplog):
    compliance = _load_compliance(monkeypatch)
    sensitive_error = "db password=gdpr-secret patient_name=Sensitive User"
    gdpr = compliance.GDPRCompliance(FailingDb(sensitive_error))
    caplog.set_level("ERROR", logger="backend.compliance")

    result = gdpr._process_access_request(42, "DSAR_TEST")

    assert result == {
        "status": "failed",
        "request_id": "DSAR_TEST",
        "error": compliance.COMPLIANCE_OPERATION_FAILURE_MESSAGE,
    }
    assert sensitive_error not in caplog.text
    assert "gdpr-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_compliance_report_hides_sensitive_failure_details(monkeypatch, caplog):
    compliance = _load_compliance(monkeypatch)
    sensitive_error = "db password=report-secret patient_name=Sensitive User"
    manager = object.__new__(compliance.ComplianceManager)
    manager.db = FailingDb(sensitive_error)
    caplog.set_level("ERROR", logger="backend.compliance")

    result = manager._generate_hipaa_audit_report()

    assert result == {"error": compliance.COMPLIANCE_REPORT_FAILURE_MESSAGE}
    assert sensitive_error not in caplog.text
    assert "report-secret" not in caplog.text
    assert "Sensitive User" not in caplog.text
