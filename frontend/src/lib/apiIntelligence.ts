/**
 * AI Healthcare System — Clinical Intelligence API
 *
 * Live alerts, patient insights, and ML explainability endpoints.
 */
import { apiFetch } from './apiCore';

// ── Types ────────────────────────────────────────────────────────
export interface ClinicalAlert {
  id: number;
  patient_id: number;
  alert_type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
  source_event_id: string | null;
  is_acknowledged: boolean;
  acknowledged_by: number | null;
  acknowledged_at: string | null;
  created_at: string;
}

export interface PatientInsight {
  id: number;
  patient_id: number;
  insight_type: string;
  content: Record<string, unknown>;
  model_version: string | null;
  created_at: string;
}

export interface ExplainabilityData {
  prediction_id: number;
  model_name: string;
  feature_importances: Record<string, number>;
  explanation_text: string;
}

// ── API Functions ────────────────────────────────────────────────
export function fetchAlerts(severity?: string): Promise<ClinicalAlert[]> {
  const qs = severity ? `?severity=${severity}` : '';
  return apiFetch(`/intelligence/alerts${qs}`);
}

export function acknowledgeAlert(alertId: number): Promise<{ message: string }> {
  return apiFetch(`/intelligence/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  });
}

export function fetchPatientInsights(patientId: number): Promise<PatientInsight> {
  return apiFetch(`/intelligence/insights/${patientId}`);
}

export function fetchExplainability(predictionId: number): Promise<ExplainabilityData> {
  return apiFetch(`/intelligence/explainability/${predictionId}`);
}
