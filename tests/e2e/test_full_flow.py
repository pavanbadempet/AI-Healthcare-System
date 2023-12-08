import re
from playwright.sync_api import Page, expect

def test_landing_page(page: Page):
    page.goto("http://localhost:8501")
    # Streamlit loading can be slow, wait for main container
    page.wait_for_selector("div[data-testid='stAppViewContainer']", timeout=10000)
    expect(page).to_have_title(re.compile("AIO Healthcare"))

def test_signup_and_dashboard_flow(page: Page):
    # 1. Navigate
    page.goto("http://localhost:8501")
    page.wait_for_selector("div[data-testid='stAppViewContainer']", timeout=10000)
    
    # 2. Switch to Sign Up
    # Streamlit Tabs - use role='tab' to disambiguate from button
    signup_tab = page.get_by_role("tab", name="Sign Up")
    signup_tab.click()
    
    # 3. Fill Form
    # New UI uses simpler labels
    page.get_by_label("Full Name").fill("Playwright User")
    page.get_by_label("Email").fill("pw_user@bot.com")
    
    
    # Locate specific inputs for Signup (Tab 2, so likely index 1)
    page.get_by_label("Username").nth(1).fill("pw_bot")
    page.locator("input[type='password']").nth(1).fill("SecurePwd123")
    
    # 4. Submit
    page.get_by_role("button", name="Sign Up").click()
    
    # 5. Expect Success
    expect(page.get_by_text("Account Created!")).to_be_visible(timeout=15000)
    
    # 6. Login
    # Switch to Login Tab
    page.get_by_role("tab", name="Login").click()
    
    page.get_by_label("Username").nth(0).fill("pw_bot")
    page.locator("input[type='password']").nth(0).fill("SecurePwd123")
    page.get_by_role("button", name="Login").click()
    
    # 7. Verify Dashboard
    expect(page.get_by_text(f"Hello, pw_bot")).to_be_visible(timeout=15000)
    
    # 8. Test Prediction Page Navigation
    # Sidebar navigation (st.radio)
    # Label is "Navigate"
    # Option is "Diabetes Prediction"
    page.get_by_text("Diabetes Prediction").click()
    
    # Wait for title
    expect(page.get_by_text("Diabetes Risk Assessment")).to_be_visible(timeout=10000)
