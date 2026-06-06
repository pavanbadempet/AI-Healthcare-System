const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message, err.stack));
  
  try {
    console.log('Navigating to http://127.0.0.1:3000/login...');
    await page.goto('http://127.0.0.1:3000/login');
    await page.waitForTimeout(5000);
    const content = await page.content();
    console.log('HTML content length:', content.length);
  } catch (err) {
    console.error('Navigation error:', err);
  } finally {
    await browser.close();
  }
})();
