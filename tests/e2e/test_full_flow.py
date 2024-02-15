import re
from playwright.sync_api import Page, expect

def test_landing_page(page: Page):
    page.goto("http://localhost:8501")
    # Streamlit loading can be slow, wait for main container
    page.wait_for_selector("div[data-testid='stAppViewContainer']", timeout=10000)
    expect(page).to_have_title(re.compile("AI Healthcare"))

def test_signup_and_dashboard_flow(page: Page):
    # 1. Navigate
    page.goto("http://localhost:8501")
    page.wait_for_selector("div[data-testid='stAppViewContainer']", timeout=10000)
    
    # 2. Switch to Sign Up
    # Legacy design uses Emoji tabs
    signup_tab = page.get_by_role("tab", name="📝 Sign Up")
    # Logic: partial match or exact if whitespace differs slightly
    signup_tab.click()
    
    # 3. Fill Form
    # Distinct forms in tabs. We can use simplified logic or strict indexing.
    # Given the new layout, 'Username' appears in Login (Tab 1) and Signup (Tab 2).
    # We will target the Signup inputs specifically.
    
    # Signup is Tab index 1.
    signup_inputs = page.locator("form").nth(1)
    
    signup_inputs.get_by_label("Username").fill("pw_bot")
    signup_inputs.get_by_label("Password").fill("SecurePwd123")
    signup_inputs.get_by_label("Email Address").fill("pw_user@bot.com")
    signup_inputs.get_by_label("Full Name").fill("Playwright User")
    
    # New Field: Terms Agreement
    # Checkbox might be outside or inside form depending on implementation.
    # In auth_view.py, it is inside the form.
    signup_inputs.get_by_label("I agree to the Terms of Service & Medical Disclaimer").check()
    
    # 4. Submit
    # Button text changed to "Register Account"
    signup_inputs.get_by_role("button", name="Register Account").click()
    
    # 5. Expect Success
    # Message: "Account created successfully! Please switch to Login tab."
    expect(page.get_by_text("Account created successfully!")).to_be_visible(timeout=15000)
    
    # 6. Login
    # Switch to Login Tab
    page.get_by_text("🔐 Login", exact=False).click()
    
    login_inputs = page.locator("form").nth(0)
    login_inputs.get_by_label("Username").fill("pw_bot")
    login_inputs.get_by_label("Password").fill("SecurePwd123")
    
    # Button text changed to "Access Portal"
    login_inputs.get_by_role("button", name="Access Portal").click()
    
    # 7. Verify Dashboard
    expect(page.get_by_text(f"Hello, pw_bot")).to_be_visible(timeout=15000)
    
    # 8. Test Prediction Page Navigation
    # Sidebar navigation (st.radio)
    # Label is "Navigate"
    # Option is "Diabetes Prediction"
    page.get_by_text("Diabetes Prediction").click()
    
    # Wait for title
    expect(page.get_by_text("Diabetes Risk Assessment")).to_be_visible(timeout=10000)
