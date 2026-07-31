import { GlobalRegistrator } from '@happy-dom/global-registrator';

if (typeof window === 'undefined') {
  GlobalRegistrator.register();
}

import '@testing-library/jest-dom';
import { vi } from 'vitest';
import React from 'react';

vi.mock('react-router-dom', () => ({
  useNavigate: () => (() => {}),
  useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), () => {}],
  Link: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
  NavLink: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
}));

vi.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    language: 'en',
    setLanguage: () => {},
  }),
  LanguageProvider: ({ children }: any) => children,
}));

process.env.VITE_PUBLIC_API_URL = 'http://127.0.0.1:8000';

const CanvasElement = (globalThis as any).HTMLCanvasElement || (globalThis as any).window?.HTMLCanvasElement;
if (CanvasElement && CanvasElement.prototype) {
  Object.defineProperty(CanvasElement.prototype, 'getContext', {
    configurable: true,
    value: () => ({
      clearRect: () => {},
      fillRect: () => {},
      strokeRect: () => {},
      beginPath: () => {},
      moveTo: () => {},
      lineTo: () => {},
      stroke: () => {},
      fill: () => {},
      arc: () => {},
      closePath: () => {},
      fillText: () => {},
      measureText: () => ({ width: 0 }),
      createLinearGradient: () => ({
        addColorStop: () => {}
      })
    })
  });
}
