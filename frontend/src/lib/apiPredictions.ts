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

export interface OrganRiskDetail {
  risk_probability: number;
  status: "Stable" | "Elevated" | "Guarded" | "Critical";
}

export interface RecommendedOrder {
  order_type: string;
  title: string;
  reason: string;
}

export interface OrganHealthResult {
  patient_id: number;
  patient_name: string;
  age: number;
  gender: string;
  vitals_source: string;
  vitals: {
    heart_rate: number;
    systolic_bp: number;
    diastolic_bp: number;
    spo2: number;
    temperature_c: number;
    respiratory_rate: number;
  };
  health_index: number;
  organ_risks: {
    heart: OrganRiskDetail;
    lungs: OrganRiskDetail;
    kidney: OrganRiskDetail;
    diabetes: OrganRiskDetail;
    liver: OrganRiskDetail;
  };
  labs_source?: string;
  labs?: {
    serum_creatinine: number;
    blood_urea: number;
    total_bilirubin: number;
    direct_bilirubin: number;
    alt: number;
    ast: number;
  };
  recommended_orders?: RecommendedOrder[];
  ai_clinical_synthesis?: string;
  disclaimer: string;
}

export async function getPatientOrganHealth(patientId: number): Promise<OrganHealthResult> {
  return apiFetch(`/predict/organ_health/${patientId}`, { method: 'GET' });
}

