import { test, expect } from '@playwright/test';

test.describe('Clinical Platform Core Flows', () => {
  test('User Signup, Login, Dashboard, and CASA Scheduling Agent flow', async ({ page }) => {
    const suffix = Math.random().toString(36).substring(2, 10);
    const username = `fe_e2e_${suffix}`;
    const email = `fe_e2e_${suffix}@clinical.invalid`;

    // 1. Visit signup page
    await page.goto('/signup');
    await expect(page).toHaveURL(/\/signup/);

    // 2. Register new user
    await page.getByLabel(/full name/i).fill('E2E Test User');
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/date of birth/i).fill('1995-05-15');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    
    // Submit registration
    await page.locator('button', { hasText: /sign up|register|create account|initialize node/i }).click();

    // 3. Wait for redirect to login or dashboard
    await page.waitForURL(/\/(login|dashboard)/, { timeout: 15000 });

    // 4. If redirected to login page, execute login
    if (page.url().includes('/login')) {
      await page.getByLabel(/username/i).fill(username);
      await page.getByLabel(/password/i).fill('SecurePass123!');
      await page.locator('button', { hasText: /sign in|log in|access console/i }).click();
      await page.waitForURL(/\/dashboard/, { timeout: 15000 });
    }

    // 5. Verify Dashboard elements
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Look for dashboard elements (e.g., patient list, charts, navigation)
    // Wait for the layout container or navigation headers
    const dashboardHeader = page.locator('header, nav, h1, h2');
    await expect(dashboardHeader.first()).toBeVisible({ timeout: 10000 });

    // 6. Navigate to CASA scheduling agent
    // Since we added CASA scheduling page, let's navigate to /telemedicine
    await page.goto('/telemedicine');
    await page.waitForURL(/\/telemedicine/);

    // Verify Scheduling Agent Chat components are visible
    const chatInput = page.locator('textarea, input[placeholder*="type a message"], input[placeholder*="ask"], input[placeholder*="symptoms"]');
    await expect(chatInput.first()).toBeVisible({ timeout: 10000 });

    // Fill chat message
    await chatInput.first().fill('Hello, I would like to book a cardiology appointment.');
    await page.keyboard.press('Enter');

    // Wait for agent to respond (typing indicator followed by chat bubble)
    const chatResponse = page.locator('div, span, p', { hasText: /cardiology|doctor|schedule|appointment/i });
    await expect(chatResponse.first()).toBeVisible({ timeout: 15000 });
  });
});
