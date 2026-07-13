import os

from playwright.sync_api import sync_playwright


def main():
    frontend_url = os.getenv("FRONTEND_URL")
    if not frontend_url:
        print("FRONTEND_URL is not set; skipping frontend keep-alive.")
        return

    print("Starting Playwright keep-alive script...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to frontend: {frontend_url}")

        try:
            # Do not wait indefinitely; the request itself is enough to wake hosted apps.
            page.goto(frontend_url, timeout=60000)
            page.wait_for_timeout(5000)
            print("Frontend ping completed.")
        except Exception as e:
            print(f"Playwright encountered an error: {e}")
        finally:
            print("Closing browser.")
            browser.close()


if __name__ == "__main__":
    main()
