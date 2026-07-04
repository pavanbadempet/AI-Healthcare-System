import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://127.0.0.1:3000')
        await page.wait_for_timeout(2000)
        await page.screenshot(path='screenshot_before.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
