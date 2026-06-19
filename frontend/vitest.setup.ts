import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { createElement } from 'react';

// Expose 'vi' as 'jest' globally for backward compatibility with existing Jest-based tests
(globalThis as any).jest = vi;

// Stub API URL for test predictability
vi.stubEnv('VITE_PUBLIC_API_URL', 'http://127.0.0.1:8000');

// Canvas Mock
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
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
      addColorStop: vi.fn(),
    })),
  })),
});

// ResizeObserver Mock
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  configurable: true,
  value: MockResizeObserver,
});

// Global mock for react-router-dom
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    Link: ({ children, to, ...props }: any) => {
      // Return a plain anchor tag so it renders nicely in testing-library
      return createElement('a', { href: to, ...props }, children);
    },
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/' }),
    useParams: () => ({}),
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
    Navigate: ({ to }: any) => null,
  };
});

// Global mock for i18n
vi.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    language: 'en',
    setLanguage: vi.fn(),
    t: {
      commandCenter: "Command Center",
      patientRegistry: "Patient Registry",
      engageCopilot: "Engage Copilot",
      liveTelemetry: "Live Hospital Workflow Layer",
      language: "Language",
      signIn: "Sign In",
      username: "Username",
      password: "Password",
      accessConsole: "Access Console",
      welcome: "Attending",
      riskAssessment: "Predictive Diagnostics",
      telemedicine: "Telemedicine Scheduler",
      infrastructure: "Capacity Board",
      adminConsole: "Admin Panel",
      logout: "Log Out"
    }
  })
}));
