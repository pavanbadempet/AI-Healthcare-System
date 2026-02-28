import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    print("Starting Playwright keep-alive script...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to Streamlit app...")
        
        try:
            # We don't await full load if it takes too long, we just want to hit the page
            page.goto("https://ai-healthcare-system.streamlit.app/", timeout=60000)
            print("Page loaded. Checking for sleep overlay...")
            
            # Wait a few seconds for the DOM to settle or the sleep overlay to appear
            page.wait_for_timeout(5000)
            
            # Streamlit "app has gone to sleep" button text
            button = page.get_by_text("Yes, get this app back up!", exact=True)
            
            if button.count() > 0 and button.first.is_visible():
                print("💤 App is asleep! Clicking the wake-up button...")
                button.first.click()
                print("✅ Clicked. Waiting 10 seconds for boot process to start...")
                page.wait_for_timeout(10000)
            else:
                print("☀️ App appears to be awake (or wake-up button not found).")
                
        except Exception as e:
            print(f"❌ Playwright encountered an error: {e}")
            
        finally:
            print("Closing browser.")
            browser.close()

if __name__ == "__main__":
    main()
