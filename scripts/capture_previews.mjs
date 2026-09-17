import pkg from '../frontend/node_modules/@playwright/test/index.js';
const { chromium } = pkg;
import path from 'path';

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.5,
  });

  const page = await context.newPage();

  // Navigate to login first to set origin localStorage
  await page.goto('http://127.0.0.1:3000/login');
  await page.evaluate(() => {
    localStorage.setItem('healthcare-auth', JSON.stringify({
      state: {
        token: 'mock-valid-jwt-token-for-preview',
        user: {
          id: 1,
          username: 'Dr. Sarah Lin',
          email: 'clinician@hospital.org',
          role: 'doctor',
          name: 'Dr. Sarah Lin, MD'
        }
      },
      version: 0
    }));
  });

  console.log('Navigating to http://127.0.0.1:3000/dashboard...');
  await page.goto('http://127.0.0.1:3000/dashboard', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
  const dest = path.resolve('docs/assets', 'clinical-workstation-preview.png');
  await page.screenshot({ path: dest, fullPage: false });
  console.log('[CAPTURED] clinical-workstation-preview.png');

  await browser.close();
  console.log('Done!');
})();
