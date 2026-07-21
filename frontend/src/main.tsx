import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,           // 30 s — data stays fresh, skip refetch on revisit
      gcTime: 600_000,             // 10 min — keep inactive results in memory
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
      retry: 1,
      structuralSharing: true,     // skip re-render when response is identical
    },
  },
});

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>
  );
}

// Register AI Healthcare System Service Worker for offline-first resilience
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('AI Healthcare System ServiceWorker registered: ', registration.scope);
      })
      .catch((err) => {
        console.error('AI Healthcare System ServiceWorker registration failed: ', err);
      });
  });
}

