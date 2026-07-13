"""
E2E tests for the Next.js frontend.
Requires:
  - Backend running on http://127.0.0.1:8000
  - Frontend running on http://127.0.0.1:3000
Run with: python -m pytest tests/e2e -m e2e
"""
import re
import urllib.error
import urllib.request
import uuid

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:3000"
BACKEND_URL = "http://127.0.0.1:8000"

pytestmark = pytest.mark.e2e


def _service_available(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 200 <= response.status < 500
    except (OSError, urllib.error.URLError):
        return False


def _goto_or_skip(page: Page, path: str):
    try:
        page.goto(f"{BASE_URL}{path}")
    except Exception as exc:
        pytest.skip(f"Frontend not running at {BASE_URL}: {exc}")


def test_landing_page(page: Page):
    """Login page should load and render correctly."""
    _goto_or_skip(page, "/login")
    # Next.js renders a login page with a sign-in form
    expect(page.locator("button", has_text=re.compile("access console|sign in", re.IGNORECASE))).to_be_visible(timeout=15000)


def test_signup_and_dashboard_flow(page: Page):
    """Full signup → login → dashboard → prediction flow."""

    if not _service_available(f"{BACKEND_URL}/healthz"):
        pytest.skip(f"Backend not running at {BACKEND_URL}")

    suffix = uuid.uuid4().hex[:8]
    username = f"pw_e2e_{suffix}"
    email = f"pw_e2e_{suffix}@test.invalid"

    # 1. Navigate to Signup
    _goto_or_skip(page, "/signup")
    page.wait_for_load_state("networkidle")

    # 2. Fill Signup Form
    page.get_by_label("Full Name").fill("Playwright User")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Date of Birth").fill("1990-01-01")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill("SecurePwd123")

    # 3. Submit Signup
    page.locator("button", has_text=re.compile("initialize node|create account|sign up|register", re.IGNORECASE)).click()

    # 4. Should redirect to login or dashboard
    page.wait_for_url(re.compile(r"/(login|dashboard)"), timeout=15000)

    # 5. If redirected to login, log in
    if "/login" in page.url:
        page.get_by_label("Username").fill(username)
        page.get_by_label("Password").fill("SecurePwd123")
        page.locator("button", has_text=re.compile("access console|sign in|log in", re.IGNORECASE)).click()
        page.wait_for_url(re.compile(r"/dashboard"), timeout=15000)

    # 6. Verify Dashboard loaded
    expect(page.get_by_role("heading", name="Nexus Vitalis")).to_be_visible(timeout=10000)

    # 7. Navigate to Diabetes Prediction
    page.goto(f"{BASE_URL}/predict/diabetes")
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=Diabetes Risk Assessment")).to_be_visible(timeout=10000)
