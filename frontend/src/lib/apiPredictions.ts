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
  clinical_indices?: Record<string, any>;
  attributions?: Record<string, number>;
  patient_explanation?: string;
  _fallback?: boolean;
}

import { runClientInference } from './onnxInference';

const MEDICAL_DISCLAIMER = "This prediction is based on a machine learning model. It is for informational and educational support only and does NOT constitute a medical diagnosis. Please consult a qualified healthcare professional or doctor for official diagnosis, treatment, or medical advice.";

export async function predictDiabetes(data: Record<string, number>, computeMode: 'local' | 'remote' = 'remote'): Promise<PredictionResult> {
  if (computeMode === 'local') {
    try {
      const features = [
        data.hypertension ?? 0,
        data.high_chol ?? 0,
        data.bmi ?? 25.0,
        data.smoking_history ?? 0,
        data.heart_disease ?? 0,
        data.physical_activity ?? 1,
        data.general_health ?? 3,
        data.gender ?? 1,
        data.age_bucket ?? 6
      ];
      const res = await runClientInference('diabetes', features);
      return { ...res, disclaimer: MEDICAL_DISCLAIMER };
    } catch (err) {
      console.warn('[ONNX WASM] Falling back to backend for diabetes prediction:', err);
      const remoteRes = await apiFetch<PredictionResult>('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
      return { ...remoteRes, _fallback: true };
    }
  }
  return apiFetch<PredictionResult>('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictHeart(data: Record<string, number>, computeMode: 'local' | 'remote' = 'remote'): Promise<PredictionResult> {
  if (computeMode === 'local') {
    try {
      const features = [
        data.age ?? 50,
        data.sex ?? 1,
        data.cp ?? 3,
        data.trestbps ?? 120,
        data.chol ?? 200,
        data.fbs ?? 0,
        data.restecg ?? 0,
        data.thalach ?? 150,
        data.exang ?? 0,
        data.oldpeak ?? 0.0,
        data.slope ?? 1,
        data.ca ?? 0,
        data.thal ?? 1
      ];
      const res = await runClientInference('heart', features);
      return { ...res, disclaimer: MEDICAL_DISCLAIMER };
    } catch (err) {
      console.warn('[ONNX WASM] Falling back to backend for heart prediction:', err);
      const remoteRes = await apiFetch<PredictionResult>('/predict/heart', { method: 'POST', body: JSON.stringify(data) });
      return { ...remoteRes, _fallback: true };
    }
  }
  return apiFetch<PredictionResult>('/predict/heart', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLiver(data: Record<string, number>, computeMode: 'local' | 'remote' = 'remote'): Promise<PredictionResult> {
  if (computeMode === 'local') {
    try {
      const features = [
        data.Age ?? 40,
        data.Gender ?? 1,
        data.Total_Bilirubin ?? 1.0,
        data.Direct_Bilirubin ?? 0.3,
        data.Alkaline_Phosphotase ?? 150,
        data.Alamine_Aminotransferase ?? 35,
        data.Aspartate_Aminotransferase ?? 35,
        data.Total_Proteins ?? 6.5,
        data.Albumin ?? 3.5,
        data.Albumin_and_Globulin_Ratio ?? 1.0
      ];
      const res = await runClientInference('liver', features);
      return { ...res, disclaimer: MEDICAL_DISCLAIMER };
    } catch (err) {
      console.warn('[ONNX WASM] Falling back to backend for liver prediction:', err);
      const remoteRes = await apiFetch<PredictionResult>('/predict/liver', { method: 'POST', body: JSON.stringify(data) });
      return { ...remoteRes, _fallback: true };
    }
  }
  return apiFetch<PredictionResult>('/predict/liver', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictKidney(data: Record<string, number>, computeMode: 'local' | 'remote' = 'remote'): Promise<PredictionResult> {
  if (computeMode === 'local') {
    try {
      const features = [
        data.age ?? 45,
        data.bp ?? 80,
        data.sg ?? 1.020,
        data.al ?? 0,
        data.su ?? 0,
        data.rbc ?? 1,
        data.pc ?? 1,
        data.pcc ?? 0,
        data.ba ?? 0,
        data.bgr ?? 120,
        data.bu ?? 35,
        data.sc ?? 1.0,
        data.sod ?? 135,
        data.pot ?? 4.0,
        data.hemo ?? 15.0,
        data.pcv ?? 40,
        data.wc ?? 8000,
        data.rc ?? 5.0,
        data.htn ?? 0,
        data.dm ?? 0,
        data.cad ?? 0,
        data.appet ?? 1,
        data.pe ?? 0,
        data.ane ?? 0
      ];
      const res = await runClientInference('kidney', features);
      return { ...res, disclaimer: MEDICAL_DISCLAIMER };
    } catch (err) {
      console.warn('[ONNX WASM] Falling back to backend for kidney prediction:', err);
      const remoteRes = await apiFetch<PredictionResult>('/predict/kidney', { method: 'POST', body: JSON.stringify(data) });
      return { ...remoteRes, _fallback: true };
    }
  }
  return apiFetch<PredictionResult>('/predict/kidney', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLungs(data: Record<string, number>, computeMode: 'local' | 'remote' = 'remote'): Promise<PredictionResult> {
  if (computeMode === 'local') {
    try {
      const features = [
        data.GENDER ?? 1,
        data.AGE ?? 50,
        data.SMOKING ?? 0,
        data.YELLOW_FINGERS ?? 0,
        data.ANXIETY ?? 0,
        data.PEER_PRESSURE ?? 0,
        data.CHRONIC_DISEASE ?? 0,
        data.FATIGUE ?? 0,
        data.ALLERGY ?? 0,
        data.WHEEZING ?? 0,
        data.ALCOHOL_CONSUMING ?? 0,
        data.COUGHING ?? 0,
        data.SHORTNESS_OF_BREATH ?? 0,
        data.SWALLOWING_DIFFICULTY ?? 0,
        data.CHEST_PAIN ?? 0
      ];
      const res = await runClientInference('lungs', features);
      return { ...res, disclaimer: MEDICAL_DISCLAIMER };
    } catch (err) {
      console.warn('[ONNX WASM] Falling back to backend for lungs prediction:', err);
      const remoteRes = await apiFetch<PredictionResult>('/predict/lungs', { method: 'POST', body: JSON.stringify(data) });
      return { ...remoteRes, _fallback: true };
    }
  }
  return apiFetch<PredictionResult>('/predict/lungs', { method: 'POST', body: JSON.stringify(data) });
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

export async function fetchPatientExplanation(
  modelName: string,
  payload: {
    prediction: string;
    confidence: number;
    risk_level: string;
    attributions: Record<string, number>;
  }
): Promise<{ patient_explanation: string }> {
  return apiFetch(`/predict/explain-text/${modelName}`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

