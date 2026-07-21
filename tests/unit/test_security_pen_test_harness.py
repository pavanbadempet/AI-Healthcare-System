import pytest
from backend.security_pen_test_harness import SecurityPenTestHarness, run_security_compliance_audit


def test_security_pen_test_harness():
    harness = SecurityPenTestHarness()
    res = harness.run_automated_pen_test()
    assert res.owasp_top_10_passed is True
    assert res.sql_injection_vulnerabilities == 0
    assert res.soc2_compliance_pass is True


def test_run_security_compliance_audit_helper():
    info = run_security_compliance_audit()
    assert info["owasp_passed"] is True
    assert info["soc2_pass"] is True
    assert len(info["findings"]) == 7
