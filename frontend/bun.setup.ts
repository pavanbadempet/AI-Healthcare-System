import { GlobalRegistrator } from '@happy-dom/global-registrator';

GlobalRegistrator.register();

const matchers = await import('@testing-library/jest-dom/matchers');
const { expect, mock } = await import('bun:test');

expect.extend(matchers as any);

const vi = {
  fn: (impl?: any) => mock(impl || (() => {})),
  spyOn: (obj: any, method: string) => mock(),
  stubEnv: (key: string, val: string) => { process.env[key] = val; },
  clearAllMocks: () => {},
  resetAllMocks: () => {},
  mock: (moduleName: string, factory: () => any) => {
    mock.module(moduleName, factory);
  },
};

const fetchMock = vi.fn();
(globalThis as any).fetch = fetchMock;
(globalThis as any).fetchMock = fetchMock;

(globalThis as any).vi = vi;
(globalThis as any).jest = vi;

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
