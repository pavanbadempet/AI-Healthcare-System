import { test, expect } from '@playwright/test';

const parseColorChannels = (color: string | null): number[] | null => {
  if (!color) {
    return null;
  }

  if (color.startsWith('#')) {
    const hex =
      color.length === 4
        ? color
            .slice(1)
            .split('')
            .map((channel) => channel + channel)
            .join('')
        : color.slice(1);

    if (hex.length !== 6 || !/^[\da-f]+$/i.test(hex)) {
      return null;
    }

    return [
      Number.parseInt(hex.slice(0, 2), 16),
      Number.parseInt(hex.slice(2, 4), 16),
      Number.parseInt(hex.slice(4, 6), 16),
    ];
  }

  const rgbMatch = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
  if (!rgbMatch) {
    return null;
  }

  return rgbMatch.slice(1).map(Number);
};

const expectNearBlack = (color: string | null, label: string) => {
  const channels = parseColorChannels(color);
  expect(channels, `${label} should be a parseable color`).not.toBeNull();

  if (!channels) {
    return;
  }

  expect(Math.max(...channels), `${label} should remain near black`).toBeLessThanOrEqual(11);
  expect(
    Math.max(...channels) - Math.min(...channels),
    `${label} should remain monochromatic`,
  ).toBeLessThanOrEqual(5);
};

const expectNearWhite = (color: string | null, label: string) => {
  const channels = parseColorChannels(color);
  expect(channels, `${label} should be a parseable color`).not.toBeNull();

  if (!channels) {
    return;
  }

  expect(Math.min(...channels), `${label} should remain high contrast`).toBeGreaterThanOrEqual(220);
  expect(
    Math.max(...channels) - Math.min(...channels),
    `${label} should remain neutral`,
  ).toBeLessThanOrEqual(35);
};

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
    expectNearBlack(clinicalShellStyles.primaryBgToken, '--bg-primary');
    expectNearBlack(clinicalShellStyles.bodyBg, 'body background');
    expectNearBlack(clinicalShellStyles.shellBg, 'login shell background');

    const headingColor = await page.locator('h1').evaluate((element) => {
      return window.getComputedStyle(element).color;
    });
    expectNearWhite(headingColor, 'heading color');
  });
});
