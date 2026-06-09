/**
 * AI Healthcare System — Predictions API
 */
import { apiFetch } from './apiCore';

export interface PredictionResult {
  prediction: string;
  probability?: number;
  confidence?: number;
  risk_level?: string;
  raw?: number;
  advice?: string[];
  explanation?: string;
  disclaimer?: string;
}

export async function predictDiabetes(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictHeart(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/heart', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLiver(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/liver', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictKidney(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/kidney', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLungs(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/lungs', { method: 'POST', body: JSON.stringify(data) });
}
