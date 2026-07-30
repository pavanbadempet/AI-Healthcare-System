import '@testing-library/jest-dom';
import { vi } from 'vitest';
import React from 'react';

const fetchMock = vi.fn();
(globalThis as any).fetch = fetchMock;
(globalThis as any).fetchMock = fetchMock;

vi.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    language: 'en',
    setLanguage: () => {},
  }),
  LanguageProvider: ({ children }: any) => children,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
    useParams: () => ({}),
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
    Link: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
    NavLink: ({ children, to, ...props }: any) => React.createElement('a', { href: typeof to === 'string' ? to : '#', ...props }, children),
  };
});

process.env.VITE_PUBLIC_API_URL = 'http://127.0.0.1:8000';

const CanvasElement = (globalThis as any).HTMLCanvasElement || (globalThis as any).window?.HTMLCanvasElement;
if (CanvasElement && CanvasElement.prototype) {
  Object.defineProperty(CanvasElement.prototype, 'getContext', {
    configurable: true,
    value: vi.fn(() => ({
      clearRect: vi.fn(),
      fillRect: vi.fn(),
      strokeRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      fill: vi.fn(),
      arc: vi.fn(),
      closePath: vi.fn(),
      fillText: vi.fn(),
      measureText: vi.fn(() => ({ width: 0 })),
      createLinearGradient: vi.fn(() => ({
        addColorStop: vi.fn()
      }))
    }))
  });
}
