import { test, expect } from '@playwright/test';

test.describe('B2B Clinical Enterprise UI Consistency', () => {
  test('Login page maintains high-contrast clinical style', async ({ page }) => {
    await page.goto('/login');
    
    // Ensure the main form is visible
    const loginForm = page.locator('form');
    await expect(loginForm).toBeVisible();

    // Verify background is strictly monochromatic (not neon/gamer)
    const bodyBg = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });
    // RGB(0,0,0) or dark variant expected, not bright glowing gradients
    expect(bodyBg).toMatch(/rgba?\(0, 0, 0|rgba?\(10, 10, 10/);

    // Take a visual snapshot to lock in the CSS rules
    await expect(page).toHaveScreenshot('login-clinical-style.png', { maxDiffPixels: 100 });
  });
});
