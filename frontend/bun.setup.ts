import { GlobalRegistrator } from '@happy-dom/global-registrator';
GlobalRegistrator.register();

import '@testing-library/jest-dom';
import { mock } from 'bun:test';
import React from 'react';

const fetchMock = mock(() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }));
(globalThis as any).fetch = fetchMock;
(globalThis as any).fetchMock = fetchMock;

(globalThis as any).vi = {
  fn: (impl?: any) => mock(impl || (() => Promise.resolve({}))),
  spyOn: () => mock(),
  stubEnv: (key: string, val: string) => { process.env[key] = val; },
  clearAllMocks: () => {},
  resetAllMocks: () => {},
  mock: (mod: string, factory: () => any) => mock.module(mod, factory),
};
(globalThis as any).jest = (globalThis as any).vi;

mock.module('react-router-dom', () => ({
  useNavigate: () => (() => {}),
  useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), () => {}],
  Link: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
  NavLink: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
}));

mock.module('@/lib/i18n', () => ({
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
    value: mock(() => ({
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
    }))
  });
}
