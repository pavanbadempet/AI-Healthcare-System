/**
 * AI Healthcare System — API Client
 *
 * Typed wrapper around all backend endpoints.
 * Auto-injects auth token from Zustand store.
 */

import { ApiConnectionError } from './apiErrors';

const getApiBase = () => {
  const envVal = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL;
  if (envVal) return envVal.replace(/\/$/, '');
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'http://127.0.0.1:8000';
};
const API_BASE = getApiBase();

// ── Auth Store Access ────────────────────────────────────────────
let getToken: (() => string | null) | null = null;

export function setTokenGetter(fn: () => string | null) {
  getToken = fn;
}

function authHeaders(): Record<string, string> {
  const token = getToken?.();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

// ── Generic Fetch Wrapper ────────────────────────────────────────
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
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

// ── Chat ─────────────────────────────────────────────────────────
export interface ChatMessage {
  role: string;
  content: string;
  timestamp?: string;
}

export async function sendChat(message: string): Promise<{ reply: string }> {
  return apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message }) });
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  return apiFetch('/chat/history');
}

export async function clearChatHistory(): Promise<void> {
  await apiFetch('/chat/history', { method: 'DELETE' });
}

export async function getChatSuggestions(): Promise<{ suggestions: string[] }> {
  return apiFetch('/chat/suggestions');
}

export async function getChatContext(query: string): Promise<{ context: string; sources: any[] }> {
  return apiFetch(`/chat/context?q=${encodeURIComponent(query)}`);
}

// ── SSE Streaming Chat ───────────────────────────────────────────
export function streamChat(
  message: string,
  history: { role: string; content: string }[],
  onChunk: (data: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (err: string) => void,
  ragScope: string = "patient",
  cloudProvider?: string,
  cloudApiKey?: string,
  model?: string
) {
  const controller = new AbortController();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  };

  if (cloudProvider) headers['x-ai-provider'] = cloudProvider;
  if (cloudApiKey) headers['x-ai-api-key'] = cloudApiKey;

  let receivedContent = false;

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, history, model, rag_scope: ragScope }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (res.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('healthcare-auth');
          window.location.href = '/login';
        }
        throw new Error('Unauthorized');
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream');
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.reply) {
                receivedContent = true;
              }
              onChunk(data);
              if (data.status === 'complete') { onDone(); return; }
              if (data.status === 'error') { onError(data.error || 'Unknown error'); return; }
            } catch { /* skip malformed */ }
          }
        }
      }
      onDone();
    })
    .catch(async (err) => {
      if (err.name === 'AbortError') return;

      if (!receivedContent) {
        console.warn("Streaming chat failed or was blocked, falling back to synchronous chat...", err);
        try {
          const syncRes = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...authHeaders(),
            },
            body: JSON.stringify({ message, history }),
          });
          if (syncRes.status === 401) {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('healthcare-auth');
              window.location.href = '/login';
            }
            throw new Error('Unauthorized');
          }
          if (!syncRes.ok) throw new Error(`HTTP ${syncRes.status}`);
          const syncData = await syncRes.json();
          const replyText = syncData.response || syncData.reply || "";
          
          onChunk({ reply: replyText });
          onDone();
          return;
        } catch (fallbackErr: any) {
          onError(fallbackErr.message || "Connection interrupted.");
          return;
        }
      }

      onError(err.message || "Connection interrupted.");
    });

  return () => controller.abort();
}

// ── Health Records ───────────────────────────────────────────────
export interface HealthRecord {
  id: number;
  record_type: string;
  data: Record<string, unknown>;
  prediction: string;
  timestamp: string;
}

export async function getRecords(): Promise<HealthRecord[]> {
  return apiFetch('/records');
}

export async function createRecord(data: {
  record_type: string;
  data: Record<string, unknown>;
  prediction: string;
}): Promise<HealthRecord> {
  return apiFetch('/records', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteRecord(id: number): Promise<void> {
  await apiFetch(`/records/${id}`, { method: 'DELETE' });
}

// ── Predictions ──────────────────────────────────────────────────
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

// ── Admin ────────────────────────────────────────────────────────
export interface AuditLogEntry {
  id: number;
  facility_id: number | null;
  actor_user_id: number | null;
  target_user_id: number | null;
  action: string;
  timestamp: string;
  details: string;
}

export async function getAdminStats(): Promise<Record<string, unknown>> {
  return apiFetch('/admin/stats');
}

export async function getAdminUsers(): Promise<UserProfile[]> {
  return apiFetch('/admin/users');
}

export async function getAdminAuditLogs(): Promise<AuditLogEntry[]> {
  return apiFetch('/admin/audit-logs');
}

export async function getAdminPatients(): Promise<UserProfile[]> {
  return apiFetch('/admin/patients');
}

export async function getAdminPatient(patientId: number): Promise<UserProfile> {
  return apiFetch(`/admin/patients/${patientId}`);
}

export interface DoctorPatientSummary {
  patient_id: number;
  username: string;
  full_name?: string | null;
  latest_encounter_id?: number | null;
  latest_encounter_type?: string | null;
  latest_status?: string | null;
  open_orders?: number;
  active_admissions?: number;
}

export async function getDoctorPatients(): Promise<DoctorPatientSummary[]> {
  return apiFetch('/hospital/doctor/patients');
}

// --- Hospital Operations Cockpit ---
export interface HospitalAdminMetrics {
  total_departments?: number;
  total_beds?: number;
  occupied_beds?: number;
  open_encounters?: number;
  active_admissions?: number;
  open_orders?: number;
  clinical_safety_note?: string;
  [key: string]: unknown;
}

export interface MonitoringAdminMetrics {
  total_vital_observations?: number;
  open_signals?: number;
  clinical_safety_note?: string;
  [key: string]: unknown;
}

export interface MonitoringSignal {
  id: number;
  patient_id: number;
  vital_observation_id?: number | null;
  encounter_id?: number | null;
  department_id?: number | null;
  signal_type: string;
  severity: string;
  title: string;
  summary: string;
  status: string;
  created_at: string;
}

export interface VitalObservation {
  id: number;
  patient_id: number;
  recorded_by_id?: number | null;
  encounter_id?: number | null;
  department_id?: number | null;
  source: string;
  heart_rate?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  spo2?: number | null;
  temperature_c?: number | null;
  respiratory_rate?: number | null;
  observed_at: string;
  created_at: string;
}

export interface DoctorPatientMonitoringSignals {
  patient_id: number;
  latest_vitals: VitalObservation[];
  open_signals: MonitoringSignal[];
  clinical_safety_note?: string;
}

export async function getDoctorPatientMonitoringSignals(patientId: number): Promise<DoctorPatientMonitoringSignals> {
  return apiFetch(`/monitoring/doctor/patients/${patientId}/signals`);
}

export async function resolveMonitoringSignal(signalId: number): Promise<MonitoringSignal> {
  return apiFetch(`/monitoring/signals/${signalId}/resolve`, { method: 'PUT' });
}

export interface DiagnosticResult {
  id: number;
  order_id: number;
  encounter_id?: number | null;
  patient_id: number;
  doctor_id?: number | null;
  department_id?: number | null;
  result_type: string;
  title: string;
  summary: string;
  abnormal_flag: boolean;
  status: string;
  review_status: string;
  review_note?: string | null;
  reviewed_by_id?: number | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface DoctorPatientDiagnosticResults {
  patient_id: number;
  results: DiagnosticResult[];
  clinical_safety_note?: string;
}

export interface DiagnosticReviewUpdate {
  review_status: 'reviewed' | 'needs_follow_up' | 'withheld';
  review_note?: string;
}

export async function getDoctorPatientDiagnosticResults(patientId: number): Promise<DoctorPatientDiagnosticResults> {
  return apiFetch(`/diagnostics/doctor/patients/${patientId}/results`);
}

export async function getPatientDiagnosticResults(): Promise<DiagnosticResult[]> {
  return apiFetch('/diagnostics/patient/results');
}

export async function reviewDiagnosticResult(
  resultId: number,
  data: DiagnosticReviewUpdate
): Promise<DiagnosticResult> {
  return apiFetch(`/diagnostics/results/${resultId}/review`, { method: 'PUT', body: JSON.stringify(data) });
}

export interface DiagnosticsAdminMetrics {
  total_results?: number;
  pending_review?: number;
  abnormal_results?: number;
  clinical_safety_note?: string;
  [key: string]: unknown;
}

export interface PharmacyAdminMetrics {
  total_inventory_items?: number;
  low_stock_items?: number;
  total_prescriptions?: number;
  active_prescriptions?: number;
  dispensed_prescriptions?: number;
  clinical_safety_note?: string;
  [key: string]: unknown;
}

export interface PrescriptionItem {
  id: number;
  prescription_id: number;
  inventory_id?: number | null;
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  quantity_prescribed: number;
  quantity_dispensed: number;
  instructions?: string | null;
  status: string;
}

export interface Prescription {
  id: number;
  encounter_id?: number | null;
  patient_id: number;
  doctor_id?: number | null;
  diagnosis_context?: string | null;
  status: string;
  created_at: string;
  dispensed_at?: string | null;
  items: PrescriptionItem[];
}

export interface DoctorPatientPrescriptions {
  patient_id: number;
  prescriptions: Prescription[];
  clinical_safety_note?: string;
}

export async function getDoctorPatientPrescriptions(patientId: number): Promise<DoctorPatientPrescriptions> {
  return apiFetch(`/pharmacy/doctor/patients/${patientId}/prescriptions`);
}

export async function getPatientPrescriptions(): Promise<Prescription[]> {
  return apiFetch('/pharmacy/patient/prescriptions');
}

export interface BillingAdminMetrics {
  total_services?: number;
  total_invoices?: number;
  total_billed?: number;
  total_collected?: number;
  outstanding_balance?: number;
  operations_note?: string;
  [key: string]: unknown;
}

export interface DischargeAdminMetrics {
  total_summaries?: number;
  draft_summaries?: number;
  finalized_summaries?: number;
  active_admissions?: number;
  discharged_admissions?: number;
  clinical_safety_note?: string;
  [key: string]: unknown;
}

export interface NursingAdminMetrics {
  total_tasks?: number;
  assigned_tasks?: number;
  completed_tasks?: number;
  overdue_tasks?: number;
  operations_note?: string;
  [key: string]: unknown;
}

export interface CareEventAdminMetrics {
  total_events?: number;
  events_by_severity?: Record<string, number>;
  operations_note?: string;
  [key: string]: unknown;
}

export interface InteroperabilityAdminMetrics {
  total_exports?: number;
  active_consents?: number;
  total_resources_exported?: number;
  standards_note?: string;
  [key: string]: unknown;
}

export interface AdminOperationsCockpitData {
  hospital: HospitalAdminMetrics;
  monitoring: MonitoringAdminMetrics;
  diagnostics: DiagnosticsAdminMetrics;
  pharmacy: PharmacyAdminMetrics;
  billing: BillingAdminMetrics;
  discharge: DischargeAdminMetrics;
  nursing: NursingAdminMetrics;
  events: CareEventAdminMetrics;
  interoperability: InteroperabilityAdminMetrics;
}

export async function getAdminOperationsCockpit(): Promise<AdminOperationsCockpitData> {
  const [
    hospital,
    monitoring,
    diagnostics,
    pharmacy,
    billing,
    discharge,
    nursing,
    events,
    interoperability,
  ] = await Promise.all([
    apiFetch<HospitalAdminMetrics>('/hospital/admin/operations'),
    apiFetch<MonitoringAdminMetrics>('/monitoring/admin/patterns'),
    apiFetch<DiagnosticsAdminMetrics>('/diagnostics/admin/metrics'),
    apiFetch<PharmacyAdminMetrics>('/pharmacy/admin/metrics'),
    apiFetch<BillingAdminMetrics>('/billing/admin/metrics'),
    apiFetch<DischargeAdminMetrics>('/discharge/admin/metrics'),
    apiFetch<NursingAdminMetrics>('/nursing/admin/metrics'),
    apiFetch<CareEventAdminMetrics>('/events/admin/metrics'),
    apiFetch<InteroperabilityAdminMetrics>('/interop/admin/metrics'),
  ]);

  return {
    hospital,
    monitoring,
    diagnostics,
    pharmacy,
    billing,
    discharge,
    nursing,
    events,
    interoperability,
  };
}

export interface Department {
  id: number;
  name: string;
  department_type: string;
  location?: string | null;
  description?: string | null;
  status: string;
  created_at: string;
}

export interface DepartmentCreate {
  name: string;
  department_type: string;
  location?: string;
  description?: string;
}

export interface Bed {
  id: number;
  department_id: number;
  bed_number: string;
  ward?: string | null;
  status: string;
  current_patient_id?: number | null;
  created_at: string;
}

export interface BedCreate {
  department_id: number;
  bed_number: string;
  ward?: string;
  status?: string;
}

export async function getDepartments(): Promise<Department[]> {
  return apiFetch('/hospital/departments');
}

export async function createDepartment(data: DepartmentCreate): Promise<Department> {
  return apiFetch('/hospital/departments', { method: 'POST', body: JSON.stringify(data) });
}

export async function createBed(data: BedCreate): Promise<Bed> {
  return apiFetch('/hospital/beds', { method: 'POST', body: JSON.stringify(data) });
}

export async function getBeds(status?: string): Promise<Bed[]> {
  const url = status ? `/hospital/beds?status=${status}` : '/hospital/beds';
  return apiFetch<Bed[]>(url);
}

export interface EncounterCreate {
  patient_id: number;
  doctor_id?: number;
  department_id?: number;
  encounter_type: string;
  reason?: string;
  priority?: string;
}

export interface Encounter {
  id: number;
  patient_id: number;
  doctor_id?: number | null;
  department_id?: number | null;
  encounter_type: string;
  reason?: string | null;
  priority: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
}

export interface AdmissionCreate {
  encounter_id: number;
  patient_id: number;
  doctor_id?: number;
  department_id?: number;
  bed_id?: number;
  admitted_at?: string;
  reason?: string;
}

export interface Admission {
  id: number;
  encounter_id: number;
  patient_id: number;
  doctor_id?: number | null;
  department_id?: number | null;
  bed_id?: number | null;
  admitted_at: string;
  discharged_at?: string | null;
  reason?: string | null;
  status: string;
}

export interface ClinicalOrderCreate {
  encounter_id?: number;
  patient_id: number;
  doctor_id?: number;
  department_id?: number;
  order_type: string;
  title: string;
  priority?: string;
  notes?: string;
}

export interface ClinicalOrder {
  id: number;
  encounter_id?: number | null;
  patient_id: number;
  doctor_id?: number | null;
  department_id?: number | null;
  order_type: string;
  title: string;
  priority: string;
  status: string;
  notes?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface CareEvent {
  id: number;
  patient_id: number;
  actor_user_id?: number | null;
  encounter_id?: number | null;
  department_id?: number | null;
  event_type: string;
  title: string;
  summary?: string | null;
  severity: string;
  created_at: string;
}

export interface CareEventFeed {
  events: CareEvent[];
  next_after_id?: number | null;
  patient_id?: number;
  clinical_safety_note?: string;
}

export async function createEncounter(data: EncounterCreate): Promise<Encounter> {
  return apiFetch('/hospital/encounters', { method: 'POST', body: JSON.stringify(data) });
}

export async function createAdmission(data: AdmissionCreate): Promise<Admission> {
  return apiFetch('/hospital/admissions', { method: 'POST', body: JSON.stringify(data) });
}

export async function createClinicalOrder(data: ClinicalOrderCreate): Promise<ClinicalOrder> {
  return apiFetch('/hospital/orders', { method: 'POST', body: JSON.stringify(data) });
}

export async function getDoctorPatientCareEventFeed(patientId: number, limit = 25): Promise<CareEventFeed> {
  return apiFetch(`/events/doctor/patients/${patientId}/feed?limit=${limit}`);
}

export async function getAdminPatientCareEventFeed(patientId: number, limit = 25): Promise<CareEventFeed> {
  return apiFetch(`/events/admin/patients/${patientId}/feed?limit=${limit}`);
}

export async function getPatientCareEventFeed(limit = 25): Promise<CareEventFeed> {
  return apiFetch(`/events/patient/feed?limit=${limit}`);
}

export interface FhirBundleExportResponse {
  bundle: {
    resourceType: string;
    entry?: unknown[];
  };
  export: {
    id: number;
    patient_id?: number;
    export_type?: string;
    resource_count: number;
    bundle_sha256?: string;
    manifest_signature?: string;
  };
  manifest: {
    resourceType?: string;
    export_id?: number;
    bundle_sha256?: string;
    signature_algorithm?: string;
    signature?: string;
  };
  standards_note?: string;
}

export async function exportDoctorPatientFhirBundle(patientId: number): Promise<FhirBundleExportResponse> {
  return apiFetch(`/interop/doctor/patients/${patientId}/fhir-bundle`);
}

// ── Payments ─────────────────────────────────────────────────────
export interface PaymentOrder {
  id: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentVerification {
  success: boolean;
  message?: string;
  plan_tier?: string;
}

export async function createPaymentOrder(planId: string): Promise<PaymentOrder> {
  return apiFetch('/payments/create-order', { method: 'POST', body: JSON.stringify({ plan_id: planId }) });
}

export async function verifyPayment(data: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }): Promise<PaymentVerification> {
  return apiFetch('/payments/verify', { method: 'POST', body: JSON.stringify(data) });
}

// ── Telemedicine ─────────────────────────────────────────────────
export interface Appointment {
  id: number;
  doctor_id: number;
  appointment_date: string;
  status: string;
  notes?: string;
  doctor?: { name: string; specialization: string };
}

interface BackendAppointment {
  id: number;
  user_id: number;
  doctor_id: number | null;
  specialist: string;
  date_time: string;
  reason: string;
  status: string;
}

interface BackendDoctor {
  id: number;
  full_name?: string;
  name?: string;
  specialization?: string;
}

function splitAppointmentDate(value: string): { date: string; time: string } {
  const direct = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
  if (direct) {
    return { date: direct[1], time: direct[2] };
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error('Invalid appointment date');
  }

  const pad = (n: number) => String(n).padStart(2, '0');
  return {
    date: `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}`,
    time: `${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`,
  };
}

function normalizeAppointment(appointment: BackendAppointment): Appointment {
  return {
    id: appointment.id,
    doctor_id: appointment.doctor_id ?? 0,
    appointment_date: appointment.date_time,
    status: appointment.status,
    notes: appointment.reason,
    doctor: {
      name: appointment.specialist,
      specialization: appointment.specialist,
    },
  };
}

export async function getAppointments(): Promise<Appointment[]> {
  const appointments = await apiFetch<BackendAppointment[]>('/appointments/');
  return appointments.map(normalizeAppointment);
}

export async function bookAppointment(data: { doctor_id: number; appointment_date: string; notes?: string }): Promise<Appointment> {
  const { date, time } = splitAppointmentDate(data.appointment_date);
  const appointment = await apiFetch<BackendAppointment>('/appointments/', {
    method: 'POST',
    body: JSON.stringify({
      doctor_id: data.doctor_id,
      specialist: 'General Physician',
      date,
      time,
      reason: data.notes || '',
    }),
  });
  return normalizeAppointment(appointment);
}

export async function getDoctors(): Promise<{ id: number; name: string; specialization: string }[]> {
  const doctors = await apiFetch<BackendDoctor[]>('/appointments/doctors');
  return doctors.map((doctor) => ({
    id: doctor.id,
    name: doctor.name || doctor.full_name || 'Doctor',
    specialization: doctor.specialization || 'General Physician',
  }));
}

export interface DemoReadinessData {
  status: string;
  demo_mode: boolean;
  environment: string;
  required: Record<string, unknown>;
  optional: Record<string, unknown>;
  missing_required: string[];
  capabilities: Record<string, boolean>;
  clinical_safety_note?: string;
  privacy_note?: string;
  source: string;
}

export async function getDemoReadiness(): Promise<DemoReadinessData> {
  return apiFetch<DemoReadinessData>('/demo-readiness/');
}

export interface DataQualityReport {
  overall_score: number;
  failed_checks: string[];
  datasets: Array<{
    name: string;
    record_count: number;
    pii_exposed: boolean;
    lineage: {
      source_tables: string[];
      upstream_modules: string[];
      downstream_uses: string[];
      freshness_field: string;
    };
  }>;
  checks: Array<{
    id: string;
    dataset: string;
    description: string;
    severity: string;
    status: string;
    total_count: number;
    failed_count: number;
    score: number;
  }>;
}

export interface OperationalHealthReport {
  status: string;
  checks: Array<{
    id: string;
    name: string;
    status: string;
    total_count: number;
    failed_count: number;
    detail: string | null;
  }>;
}

export async function getAdminDataQuality(): Promise<DataQualityReport> {
  return apiFetch<DataQualityReport>('/admin/data-quality');
}

export async function getAdminOperationalHealth(): Promise<OperationalHealthReport> {
  return apiFetch<OperationalHealthReport>('/admin/operational-health');
}

export interface AnalyticsReport {
  report_generated_at: string | null;
  total_records_analyzed: number;
  prevalence_rates: Record<string, number>;
  demographics: {
    avg_age: number;
    avg_bmi: number;
    gender_distribution: {
      male_ratio: number;
      female_ratio: number;
    };
  };
  model_performance: Record<string, number>;
  pipeline_execution: {
    duration_seconds: number;
    status: string;
  };
}

export async function getAnalyticsReport(): Promise<AnalyticsReport> {
  return apiFetch<AnalyticsReport>('/admin/analytics/report');
}


