import { GlobalRegistrator } from '@happy-dom/global-registrator';

if (typeof window === 'undefined') {
  GlobalRegistrator.register();
}

// Suppress AbortError caused by happy-dom animation cancellation during component unmounts
const ElementClass = (globalThis as any).Element || (globalThis as any).window?.Element;
if (ElementClass?.prototype?.animate) {
  const origAnimate = ElementClass.prototype.animate;
  ElementClass.prototype.animate = function (...args: any[]) {
    const anim = origAnimate.apply(this, args);
    if (anim?.finished && typeof anim.finished.catch === 'function') {
      anim.finished.catch(() => {});
    }
    return anim;
  };
}

const AnimClass = (globalThis as any).Animation || (globalThis as any).window?.Animation;
if (AnimClass?.prototype?.cancel) {
  const origCancel = AnimClass.prototype.cancel;
  AnimClass.prototype.cancel = function (...args: any[]) {
    if (this.finished && typeof this.finished.catch === 'function') {
      this.finished.catch(() => {});
    }
    try {
      return origCancel.apply(this, args);
    } catch {
      // ignore animation abort error on cancel
    }
  };
}

if (typeof window !== 'undefined' && window.addEventListener) {
  window.addEventListener('unhandledrejection', (event: any) => {
    if (
      event?.reason?.name === 'AbortError' ||
      event?.reason?.message?.includes('The animation was canceled')
    ) {
      event.preventDefault();
      event.stopImmediatePropagation?.();
    }
  });
}

if (typeof process !== 'undefined' && process.on) {
  process.on('unhandledRejection', (reason: any) => {
    if (
      reason?.name === 'AbortError' ||
      reason?.message?.includes('The animation was canceled')
    ) {
      return;
    }
  });
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
