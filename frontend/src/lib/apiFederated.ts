/**
 * AI Healthcare System — Federated Learning API
 *
 * Differential-privacy sync, audit trail, and model feedback endpoints.
 */
import { apiFetch } from './apiCore';

// ── Types ────────────────────────────────────────────────────────
export interface FederatedStats {
  pending_count: number;
  total_epsilon_spent: number;
}

export interface SyncAudit {
  id: number;
  sync_run_id: string;
  node_id: string;
  model_name: string;
  records_synced: number;
  epsilon_consumed: number;
  delta_consumed: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface SyncResponse {
  sync_run_id: string;
  records_synced: number;
  epsilon_consumed: number;
  noisy_gradients: Record<string, number[]>;
  status: string;
}

// ── API Functions ────────────────────────────────────────────────
export function fetchFederatedStats(): Promise<FederatedStats> {
  return apiFetch('/federated/stats');
}

export function fetchFederatedAudits(): Promise<SyncAudit[]> {
  return apiFetch('/federated/audits');
}

export function triggerFederatedSync(data: {
  model_name: string;
  epsilon?: number;
  sensitivity?: number;
}): Promise<SyncResponse> {
  return apiFetch('/federated/sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export function submitModelFeedback(data: {
  patient_id: number;
  model_name: string;
  input_features: Record<string, unknown>;
  prediction_result: Record<string, unknown>;
  corrected_label: string;
}): Promise<{ message: string }> {
  return apiFetch('/federated/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}
