/**
 * AI Healthcare System — SMART on FHIR App API
 *
 * Wrappers for SMART app registration, launch, and management.
 */
import { apiFetch } from './apiCore';

// ── Types ────────────────────────────────────────────────────────
export interface SmartApp {
  id: number;
  app_name: string;
  client_id: string;
  redirect_uri: string;
  launch_url: string;
  scopes: string;
  is_active: boolean;
  created_at: string;
}

export interface SmartLaunchResponse {
  launch_token: string;
  auth_code: string;
  scope: string;
  expires_at: string;
}

// ── API Functions ────────────────────────────────────────────────
export function fetchSmartApps(): Promise<SmartApp[]> {
  return apiFetch('/smart/apps');
}

export function registerSmartApp(data: {
  app_name: string;
  redirect_uri: string;
  launch_url: string;
  scopes?: string;
}): Promise<SmartApp> {
  return apiFetch('/smart/apps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export function deleteSmartApp(appId: number): Promise<{ message: string }> {
  return apiFetch(`/smart/apps/${appId}`, { method: 'DELETE' });
}

export function launchSmartApp(
  appId: number,
  patientId: number,
): Promise<SmartLaunchResponse> {
  return apiFetch('/smart/launch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_id: appId, patient_id: patientId }),
  });
}
