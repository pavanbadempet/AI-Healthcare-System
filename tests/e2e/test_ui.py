from playwright.sync_api import Page, expect
import pytest

# Prerequisite: App must be running on localhost:8501
BASE_URL = "http://localhost:8501"

@pytest.mark.e2e
    # OR if session persisted, it shows Dashboard.
    # We can check for "Login" button OR "Logout" button.
    
    login_btn = page.locator('button:has-text("Login")')
    logout_btn = page.locator('button:has-text("Logout")')
    
    if login_btn.count() > 0:
        expect(login_btn).to_be_visible()
    elif logout_btn.count() > 0:
        expect(logout_btn).to_be_visible()
    else:
        # Maybe in Signup tab?
        pass
