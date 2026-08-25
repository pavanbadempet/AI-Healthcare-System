"""
Pytest configuration and fixtures for the E2E Test Suite.
Provides authenticated clients and opaque-box test helpers.
"""
import os
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.auth import TestAuthManager
from e2e_tests.harness.fixtures import TestDataFactory


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("E2E_API_URL", "")


@pytest.fixture(scope="function")
def e2e_client(base_url):
    return E2EClient(base_url=base_url)


@pytest.fixture(scope="function")
def admin_client(base_url):
    token = TestAuthManager.generate_token(username="admin_e2e", role="admin", user_id=1, facility_id=1)
    return E2EClient(base_url=base_url, auth_token=token)


@pytest.fixture(scope="function")
def doctor_client(base_url):
    token = TestAuthManager.generate_token(username="doctor_e2e", role="doctor", user_id=2, facility_id=1)
    return E2EClient(base_url=base_url, auth_token=token)


@pytest.fixture(scope="function")
def nurse_client(base_url):
    token = TestAuthManager.generate_token(username="nurse_e2e", role="nurse", user_id=3, facility_id=1)
    return E2EClient(base_url=base_url, auth_token=token)


@pytest.fixture(scope="function")
def patient_client(base_url):
    token = TestAuthManager.generate_token(username="patient_e2e", role="patient", user_id=4, facility_id=1)
    return E2EClient(base_url=base_url, auth_token=token)


@pytest.fixture(scope="session")
def auth_mgr():
    return TestAuthManager


@pytest.fixture(scope="session")
def data_factory():
    return TestDataFactory
