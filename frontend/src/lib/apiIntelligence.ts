/**
 * AI Healthcare System — Clinical Intelligence API
 *
 * Live alerts, patient insights, and ML explainability endpoints.
 */
import { apiFetch, API_BASE, authHeaders } from './apiCore';

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

export interface AdvisoryBoardDebate {
  status: string;
  patient_id: number;
  patient_vitals_context: string;
  debate: {
    round1: {
      cardiologist: string;
      endocrinologist: string;
    };
    round2: {
      cardiologist_rebuttal: string;
      endocrinologist_rebuttal: string;
    };
    round3: {
      coordinator_synthesis: {
        consensus_note: string;
        icd10_codes: string[];
        lifestyle_plan: string[];
        treatment_plan: string[];
      };
    };
  };
  telemetry: {
    duration_seconds: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
  };
}

export function fetchAdvisoryBoard(patientId: number): Promise<AdvisoryBoardDebate> {
  return apiFetch(`/predict/advisory-board/${patientId}`);
}

// ── Phase 10 Types & APIs ──────────────────────────────────────────

export interface ScribeSOAPNote {
  telemetry: {
    duration: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
  };
  data: {
    subjective: string;
    objective: string;
    assessment: string;
    plan: string;
    icd10_codes: string[];
    billing_codes: string[];
    prescriptions: {
      medication_name: string;
      dosage: string;
      frequency: string;
      duration: string;
      quantity_prescribed: number;
    }[];
    billing_items: {
      description: string;
      amount: number;
    }[];
  };
}

export interface ClinicalTrialMatch {
  matches: {
    trial_id: string;
    title: string;
    match_percentage: number;
    eligible: boolean;
    reasons: string[];
    referral_letter: string;
  }[];
}

export interface CounterfactualRecourseData {
  baseline_risk: number;
  optimized_risk: number;
  recourse_recommendation: Record<string, number>;
  changes_applied: Record<string, string>;
}

export interface DrugSafetyAlert {
  type: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  evidence: string;
}

export interface DrugSafetyCheckResponse {
  telemetry: {
    duration: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost: number;
  };
  alerts: DrugSafetyAlert[];
}

export function generateScribeSOAP(patientId: number, transcript: string): Promise<ScribeSOAPNote> {
  return apiFetch(`/predict/scribe/${patientId}`, {
    method: 'POST',
    body: JSON.stringify({ transcript }),
  });
}

export function commitScribeSOAP(payload: {
  patient_id: number;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  icd10_codes: string[];
  billing_codes: string[];
  prescriptions: ScribeSOAPNote['data']['prescriptions'];
  billing_items: ScribeSOAPNote['data']['billing_items'];
}): Promise<{ status: string; message: string }> {
  return apiFetch(`/predict/scribe/commit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchClinicalTrials(patientId: number): Promise<ClinicalTrialMatch> {
  return apiFetch(`/predict/clinical-trials/${patientId}`);
}

export function fetchCounterfactualRecourse(
  patientId: number,
  targetModel: string,
  features: Record<string, number>
): Promise<CounterfactualRecourseData> {
  return apiFetch(`/predict/counterfactual/${patientId}`, {
    method: 'POST',
    body: JSON.stringify({ target_model: targetModel, features }),
  });
}

export function checkPrescribingSafety(payload: {
  patient_id: number;
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  additional_allergies?: string[];
}): Promise<DrugSafetyCheckResponse> {
  return apiFetch(`/pharmacy/check-safety`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}


// ── 10/10 Healthcare Itches Upgrade Helpers ─────────────────────

export function fetchMedicationPricing(medicationName: string): Promise<any> {
  return apiFetch(`/pharmacy/compare-pricing?medication_name=${encodeURIComponent(medicationName)}`);
}

export function fetchGenericSubstitution(brandedName: string): Promise<any> {
  return apiFetch(`/pharmacy/generic-substitute?branded_name=${encodeURIComponent(brandedName)}`);
}

export function fetchClinicalConsensus(patientId: number): Promise<any> {
  return apiFetch(`/predict/consensus/${patientId}`);
}

export function fetchTriageQueue(): Promise<any> {
  return apiFetch(`/hospital/triage-queue`);
}

export function fetchExternalRecords(patientId: number): Promise<any> {
  return apiFetch(`/interop/external-records/${patientId}`);
}

export function fetchHealthPassport(patientId: number): Promise<any> {
  return apiFetch(`/interop/health-passport/${patientId}`);
}

export function orderLabKit(payload: {
  patient_id: number;
  kit_type: string;
  shipping_address: string;
}): Promise<any> {
  return apiFetch(`/diagnostics/lab-kits`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchLabKits(patientId: number): Promise<any> {
  return apiFetch(`/diagnostics/lab-kits/${patientId}`);
}

export function bookSpecialCareAppointment(payload: {
  patient_id: number;
  doctor_id?: number;
  specialist: string;
  date_time: string;
  reason: string;
  request_female_clinician?: boolean;
  home_visit_van?: boolean;
}): Promise<any> {
  return apiFetch(`/appointments/special-care`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchRecommendedSpecialists(patientId: number): Promise<any> {
  return apiFetch(`/appointments/recommend-specialists/${patientId}`);
}

export function fetchProcedureCostEstimate(procedureType: string, insuranceProvider?: string, region?: string): Promise<any> {
  const providerParam = insuranceProvider ? `&insurance_provider=${encodeURIComponent(insuranceProvider)}` : '';
  const regionParam = region ? `&region=${encodeURIComponent(region)}` : '';
  return apiFetch(`/billing/estimate?procedure_type=${encodeURIComponent(procedureType)}${providerParam}${regionParam}`);
}

export async function uploadLabReportImage(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/report/analyze/report`, {
    method: 'POST',
    headers: {
      ...authHeaders(),
    },
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}



