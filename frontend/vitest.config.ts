import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./bun.setup.ts'],
    exclude: ['**/node_modules/**', '**/dist/**', 'tests/**'],
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
