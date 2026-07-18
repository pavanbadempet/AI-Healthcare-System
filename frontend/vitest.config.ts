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
        statements: 50,
        branches: 40,
        functions: 45,
        lines: 50,
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
        'src/components/layout/MegaMenuPanel.tsx',
        'src/components/layout/ProfileDropdown.tsx',
        'src/components/layout/TelemetryDropdown.tsx',
        'src/components/layout/LanguageSelector.tsx',
        'src/components/operations/CareTimelineHistoryChart.tsx',
        'src/lib/apiBilling.ts',
        'src/lib/apiIntelligence.ts',
        'src/lib/apiPredictions.ts',
        'src/components/operations/DischargeInstructionsPanel.tsx',
      ],
    },
  },
});
