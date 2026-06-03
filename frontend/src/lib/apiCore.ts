/**
 * AI Healthcare System — Core API Client
 *
 * Shared fetch wrapper, auth helpers, and base configuration.
 * Domain-specific API functions are in the sub-modules:
 *   - apiAuth.ts
 *   - apiChat.ts
 *   - apiPredictions.ts
 *   - apiHospital.ts
 *   - apiAdmin.ts
 *   - apiBilling.ts
 */

import { ApiConnectionError } from './apiErrors';

const getApiBase = () => {
  const envVal = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL;
  if (envVal) return `${envVal.replace(/\/$/, '')}/v1`;
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/v1`;
  }
  return 'http://127.0.0.1:8000/v1';
};
export const API_BASE = getApiBase();

// ── Auth Store Access ────────────────────────────────────────────
let getToken: (() => string | null) | null = null;

export function setTokenGetter(fn: () => string | null) {
  getToken = fn;
}

export function authHeaders(): Record<string, string> {
  const token = getToken?.();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

// ── Generic Fetch Wrapper ────────────────────────────────────────
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiConnectionError(path);
  }

  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('healthcare-auth');
      window.location.href = '/login';
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    let errorMessage = `API Error: ${res.status}`;
    if (body.detail) {
      if (typeof body.detail === 'string') {
        errorMessage = body.detail;
      } else if (Array.isArray(body.detail)) {
        errorMessage = body.detail.map((e: { msg: string; loc?: string[]; type?: string }) => e.msg).join(", ");
      } else {
        errorMessage = JSON.stringify(body.detail);
      }
    }
    throw new Error(errorMessage);
  }

  return res.json();
}
