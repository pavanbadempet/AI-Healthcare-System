/**
 * AI Healthcare System — Auth & Profile API
 */
import { apiFetch, API_BASE } from './apiCore';

// ── Auth ─────────────────────────────────────────────────────────
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Login failed');
  }
  return res.json();
}

export async function signup(data: {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ username: string }> {
  return apiFetch('/signup', { method: 'POST', body: JSON.stringify(data) });
}

export async function forgotPassword(email: string): Promise<{ status: string; message: string }> {
  return apiFetch('/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string): Promise<{ status: string; message: string }> {
  return apiFetch('/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// ── Profile ──────────────────────────────────────────────────────
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  gender?: string;
  dob?: string;
  blood_type?: string;
  height?: string;
  weight?: string;
  about_me?: string;
  profile_picture?: string;
  plan_tier?: string;
}

export async function fetchProfile(): Promise<UserProfile> {
  return apiFetch('/profile');
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  return apiFetch('/profile', { method: 'PUT', body: JSON.stringify(data) });
}

export interface ConsentStatusResponse {
  accepted: boolean;
  eula_version: string;
  current_version: string;
  accepted_at?: string;
  requires_reaccept: boolean;
}

export async function checkConsentStatus(): Promise<ConsentStatusResponse> {
  return apiFetch('/consent/status');
}

export async function acceptEula(version: string = '1.0'): Promise<{ status: string; eula_version: string; accepted_at: string }> {
  return apiFetch('/consent/accept', {
    method: 'POST',
    body: JSON.stringify({ eula_version: version })
  });
}
