import pytest
from backend.privacy_sovereignty_router import GlobalDataSovereigntyRouter, run_data_sovereignty_check


def test_global_data_sovereignty_router():
    router = GlobalDataSovereigntyRouter()
    res = router.verify_data_residency("P-99", "GDPR_EU")
    assert res.residency_compliant is True
    assert res.target_region == "eu-central-1"
    assert "node-eu-central-1-primary" in res.allowed_storage_nodes


def test_run_data_sovereignty_check_helper():
    info = run_data_sovereignty_check("P-100", "ABDM_IN")
    assert info["residency_compliant"] is True
    assert info["target_region"] == "ap-south-1"
