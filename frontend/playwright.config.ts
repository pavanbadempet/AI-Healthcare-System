import path from 'path';
import { defineConfig, devices } from '@playwright/test';

// Ensure modules in frontend/node_modules are resolvable when running tests in ../tests/e2e
const nodeModulesPath = path.resolve(__dirname, 'node_modules');
if (!process.env.NODE_PATH) {
  process.env.NODE_PATH = nodeModulesPath;
} else if (!process.env.NODE_PATH.includes(nodeModulesPath)) {
  process.env.NODE_PATH = `${nodeModulesPath}${path.delimiter}${process.env.NODE_PATH}`;
}
try {
  const Module = require('module');
  if (Module._initPaths) {
    Module._initPaths();
  }
} catch {
  // Ignore in environments where _initPaths is not available
}

export default defineConfig({
  testDir: '../tests/e2e',
  testMatch: /.*\.spec\.ts/,
  timeout: 120000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'bun run start',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
