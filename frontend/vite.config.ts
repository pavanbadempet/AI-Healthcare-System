import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 3000,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          // React core — rarely changes, long-lived cache
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router') ||
              id.includes('node_modules/scheduler/')) {
            return 'vendor-react';
          }
          // WebLLM — local browser AI, huge package
          if (id.includes('node_modules/@mlc-ai/web-llm') || id.includes('node_modules/@mlc-ai/')) {
            return 'vendor-webllm';
          }
          // ONNX runtime web — local browser inference
          if (id.includes('node_modules/onnxruntime-web')) {
            return 'vendor-onnx';
          }
          // Framer Motion — animation library
          if (id.includes('node_modules/framer-motion/') ||
              id.includes('node_modules/motion/')) {
            return 'vendor-motion';
          }
          // Recharts + D3 — only Dashboard uses these
          if (id.includes('node_modules/recharts/') ||
              id.includes('node_modules/d3-') ||
              id.includes('node_modules/victory-vendor/')) {
            return 'vendor-charts';
          }
          // Markdown rendering — only Chat uses these
          if (id.includes('node_modules/react-markdown/') ||
              id.includes('node_modules/remark-') ||
              id.includes('node_modules/unified/') ||
              id.includes('node_modules/micromark') ||
              id.includes('node_modules/mdast-') ||
              id.includes('node_modules/hast-') ||
              id.includes('node_modules/unist-')) {
            return 'vendor-markdown';
          }
        },
      },
    },
  },
});
