import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/tests/**',
      '**/.next/**',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        statements: 60,
        branches: 50,
        functions: 55,
        lines: 60,
      },
      exclude: [
        '**/node_modules/**',
        '**/dist/**',
        '**/tests/**',
        '**/.next/**',
        'vite.config.ts',
        'vitest.config.ts',
        'vitest.setup.ts',
        'src/lib/next-compat/**',
        'src/lib/api.ts',
        'src/lib/apiChat.ts',
        'src/lib/onnxInference.ts',
        'src/lib/prefetch.ts',
        'src/lib/webllm.ts',
        'src/components/layout/nav-config.ts',
        'src/components/layout/TopNavMenuPanel.tsx',
        'src/components/layout/TopNavModeDropdown.tsx',
        'src/components/layout/TopNavWorkspaceDropdown.tsx',
        'src/components/layout/TopNavRoleSelector.tsx',
        'src/components/operations/CareTimelineHistoryChart.tsx',
        'src/lib/apiBilling.ts',
        'src/lib/apiIntelligence.ts',
        'src/lib/apiPredictions.ts',
        'src/components/operations/DischargeInstructionsPanel.tsx',
      ],
    },
  },
});
