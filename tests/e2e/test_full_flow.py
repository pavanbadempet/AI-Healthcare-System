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
    # Using locator.all() or filter to distinguish between Login and Signup tokens if they are identical
    # However, unique labels are best.
    # Assuming Username/Password are ambiguous, we'll try to find the one visible in the active tab context.
    # We can assume the Signup fields are the ones appearing APART from the login ones.
    
    # Alternatively, focus on placeholder text if available
    # page.get_by_placeholder("Create a username").fill("pw_bot")
    
    # For now, let's try the 'last' occurrence if it's the second tab
    # Or strict indexing on the inputs themselves
    
    inputs = page.get_by_label("Username").all()
    # 2nd one should be signup if 1st is login
    if len(inputs) > 1:
        inputs[1].fill("pw_bot")
    else:
        # Fallback if only one is found (e.g. dynamic rendering)
        page.get_by_label("Username").fill("pw_bot")

    pw_inputs = page.get_by_label("Password").all()
    if len(pw_inputs) > 1:
        pw_inputs[1].fill("SecurePwd123")
    else:
        page.get_by_label("Password").fill("SecurePwd123")
        
    page.get_by_label("Email").fill("pw_user@bot.com")
    page.get_by_label("Full Name").fill("Playwright User")
    
    # 4. Submit
    # 'Sign Up' button might also be ambiguous if text matches tab
    page.get_by_role("button", name="Sign Up", exact=True).click()
    
    # 5. Expect Success
    expect(page.get_by_text("Account Created!")).to_be_visible(timeout=15000)
    
    # 6. Login
    page.get_by_text("Login", exact=True).click()
    
    # Re-fetch inputs as DOM might have shifted? mostly same
    # Login is usually first
    page.get_by_label("Username").first.fill("pw_bot")
    page.get_by_label("Password").first.fill("SecurePwd123")
    page.get_by_role("button", name="Login", exact=True).click()
    
    # 7. Verify Dashboard
    expect(page.get_by_text(f"Hello, pw_bot")).to_be_visible(timeout=15000)
    
    # 8. Test Prediction Page Navigation
    # Sidebar navigation (st.radio)
    # Label is "Navigate"
    # Option is "Diabetes Prediction"
    page.get_by_text("Diabetes Prediction").click()
    
    # Wait for title
    expect(page.get_by_text("Diabetes Risk Assessment")).to_be_visible(timeout=10000)
