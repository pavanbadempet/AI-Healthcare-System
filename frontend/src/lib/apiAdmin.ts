/**
 * AI Healthcare System — Admin, Monitoring, Diagnostics, Pharmacy, Billing Metrics API
 */
import { apiFetch } from './apiCore';
import type { UserProfile } from './apiAuth';

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
  spark_info?: {
    spark_batch_id: number;
    spark_latency_ms: number;
    spark_ml_latency_ms: number;
    spark_records_processed: number;
    spark_timestamp: string;
  } | null;
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

  return { hospital, monitoring, diagnostics, pharmacy, billing, discharge, nursing, events, interoperability };
}

export interface FhirBundleExportResponse {
  bundle: { resourceType: string; entry?: unknown[] };
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
    gender_distribution: { male_ratio: number; female_ratio: number };
  };
  model_performance: Record<string, number>;
  pipeline_execution: { duration_seconds: number; status: string };
}

export async function getAnalyticsReport(): Promise<AnalyticsReport> {
  return apiFetch<AnalyticsReport>('/admin/analytics/report');
}

export interface AttributionDriftModelReport {
  status: string;
  drift_score: number;
  sample_count: number;
  production_relative_attributions: Record<string, number>;
  baseline_relative_attributions: Record<string, number>;
  message?: string;
  features_logged?: number;
}

export type AttributionDriftReport = Record<string, AttributionDriftModelReport>;

export async function getAttributionDriftReport(): Promise<AttributionDriftReport> {
  return apiFetch<AttributionDriftReport>('/admin/attribution-drift');
}

export interface SemanticCacheStats {
  hits: number;
  misses: number;
  size: number;
  entries: { query: string; response_length: number }[];
}

export interface SemanticCacheResponse {
  status: string;
  stats: SemanticCacheStats;
}

export async function getSemanticCacheStats(): Promise<SemanticCacheResponse> {
  return apiFetch<SemanticCacheResponse>('/admin/semantic-cache');
}

export async function clearSemanticCache(): Promise<{ status: string; message: string }> {
  return apiFetch<{ status: string; message: string }>('/admin/semantic-cache', { method: 'DELETE' });
}

// --- AI Registry & Model Cards ---
export interface AIFunctionDetails {
  id: string;
  name: string;
  module: string;
  endpoints: string[];
  audience: string[];
  risk_category: string;
  clinical_safety_required: boolean;
  medical_disclaimer_required: boolean;
  human_review_required: boolean;
  basis_transparency_required: boolean;
  uses_ai_provider: boolean;
  provider_boundary: string;
  prompt_keys: string[];
  notes: string;
}

export interface AIFunctionRegistryResponse {
  source: string;
  functions: AIFunctionDetails[];
}


export interface DatasetCardDetails {
  id: string;
  name: string;
  source: string;
  local_artifact: string;
  local_artifact_exists: boolean;
  artifact_size_bytes: number;
  task: string;
  intended_use: string;
  known_limitations: string[];
  contains_production_patient_data: boolean;
}

export interface ModelCardDetails {
  id: string;
  name: string;
  endpoint: string;
  artifact: string;
  artifact_exists: boolean;
  artifact_size_bytes: number;
  model_family: string;
  dataset_card_id: string;
  clinical_use_category: string;
  intended_use: string;
  target_users: string[];
  feature_count: number;
  output: string;
  limitations: string[];
  human_review_required: boolean;
  medical_disclaimer_required: boolean;
  post_deployment_monitoring_required: boolean;
}

export interface ModelCardsResponse {
  source: string;
  model_cards: ModelCardDetails[];
  dataset_cards: DatasetCardDetails[];
  privacy_note: string;
}

export async function getAIFunctionRegistry(): Promise<AIFunctionRegistryResponse> {
  return apiFetch<AIFunctionRegistryResponse>('/admin/ai-functions');
}

export async function getModelCards(): Promise<ModelCardsResponse> {
  return apiFetch<ModelCardsResponse>('/admin/model-cards');
}


export interface FederatedSimResults {
  acc_central: number;
  acc_federated: number;
  history: number[];
}

export interface FederatedSimResponse {
  status: string;
  results: FederatedSimResults;
}

export async function runFederatedSimulation(epochs: number, epsilon: number): Promise<FederatedSimResponse> {
  return apiFetch<FederatedSimResponse>(`/admin/federated-sim?epochs=${epochs}&epsilon=${epsilon}`, {
    method: 'POST',
  });
}

export async function fetchFhirAuditEvents(): Promise<any> {
  return apiFetch<any>('/fhir/AuditEvent');
}




