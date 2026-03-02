"""
E2E tests for the Next.js frontend.
Requires:
  - Backend running on http://127.0.0.1:8000
  - Frontend running on http://127.0.0.1:3000
Run with: cd frontend && npx playwright test
"""
import re
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:3000"


def test_landing_page(page: Page):
    """Login page should load and render correctly."""
    page.goto(f"{BASE_URL}/login")
    # Next.js renders a login page with a sign-in form
    expect(page.locator("button", has_text=re.compile("sign in", re.IGNORECASE))).to_be_visible(timeout=15000)


def test_signup_and_dashboard_flow(page: Page):
    """Full signup → login → dashboard → prediction flow."""

    # 1. Navigate to Signup
    page.goto(f"{BASE_URL}/signup")
    page.wait_for_load_state("networkidle")

    # 2. Fill Signup Form
    page.get_by_label("Full Name").fill("Playwright User")
    page.get_by_label("Username").fill("pw_e2e_bot")
    page.get_by_label("Email").fill("pw_e2e@test.com")
    page.get_by_label("Password").fill("SecurePwd123")

    # 3. Submit Signup
    page.locator("button", has_text=re.compile("create account|sign up|register", re.IGNORECASE)).click()

    # 4. Should redirect to login or dashboard
    page.wait_for_url(re.compile(r"/(login|dashboard)"), timeout=15000)

    # 5. If redirected to login, log in
    if "/login" in page.url:
        page.get_by_label("Username").fill("pw_e2e_bot")
        page.get_by_label("Password").fill("SecurePwd123")
        page.locator("button", has_text=re.compile("sign in|log in", re.IGNORECASE)).click()
        page.wait_for_url(re.compile(r"/dashboard"), timeout=15000)

    # 6. Verify Dashboard loaded
    expect(page.locator("text=Command Center")).to_be_visible(timeout=10000)

    # 7. Navigate to Diabetes Prediction
    page.goto(f"{BASE_URL}/predict/diabetes")
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=Diabetes Risk Assessment")).to_be_visible(timeout=10000)
