import { test, expect } from '@playwright/test';

test.describe('B2B Clinical Enterprise UI Consistency', () => {
  test('Login page maintains high-contrast clinical style', async ({ page }) => {
    await page.goto('/login');
    
    // Ensure the main form is visible
    const loginForm = page.locator('form');
    await expect(loginForm).toBeVisible();

    // Verify background is strictly monochromatic (not neon/gamer)
    const clinicalShellStyles = await page.evaluate(() => {
      const bodyStyles = window.getComputedStyle(document.body);
      const shell = document.querySelector('.min-h-screen');
      const shellStyles = shell ? window.getComputedStyle(shell) : null;
      return {
        bodyBg: bodyStyles.backgroundColor,
        primaryBgToken: window.getComputedStyle(document.documentElement).getPropertyValue('--bg-primary').trim(),
        shellBg: shellStyles?.backgroundColor ?? null,
      };
    });
    // Compiled CSS must be loaded; transparent default styles can make unstyled pages pass weak checks.
    expect(['#000', '#000000', '#09090b']).toContain(clinicalShellStyles.primaryBgToken);
    expect(['rgb(0, 0, 0)', 'rgb(9, 9, 11)']).toContain(clinicalShellStyles.bodyBg);
    expect(['rgb(0, 0, 0)', 'rgb(9, 9, 11)']).toContain(clinicalShellStyles.shellBg);

    // Take a visual snapshot to lock in the CSS rules
    await expect(page).toHaveScreenshot('login-clinical-style.png', { maxDiffPixels: 100 });
  });
});
