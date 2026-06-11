/**
 * AI Healthcare System — API Client (Barrel Re-export)
 *
 * This file re-exports everything from the domain-specific API modules
 * so that existing imports like `import { login } from '@/lib/api'`
 * continue to work without any changes.
 *
 * The actual implementations are in:
 *   - apiCore.ts         — fetch wrapper, auth helpers
 *   - apiAuth.ts         — login, signup, profile
 *   - apiChat.ts         — chat, streaming, health records
 *   - apiPredictions.ts  — ML prediction endpoints
 *   - apiHospital.ts     — hospital operations, encounters, care events
 *   - apiAdmin.ts        — admin, monitoring, diagnostics, pharmacy, billing
 *   - apiBilling.ts      — payments, telemedicine
 */

// ── Core ─────────────────────────────────────────────────────────
export { API_BASE, setTokenGetter, authHeaders, apiFetch } from './apiCore';

// ── Auth & Profile ──────────────────────────────────────────────
export {
  login,
  signup,
  forgotPassword,
  resetPassword,
  fetchProfile,
  updateProfile,
  type LoginResponse,
  type UserProfile,
} from './apiAuth';

// ── Chat & Records ──────────────────────────────────────────────
export {
  sendChat,
  getChatHistory,
  clearChatHistory,
  getChatSuggestions,
  getChatContext,
  streamChat,
  getRecords,
  createRecord,
  deleteRecord,
  type ChatMessage,
  type HealthRecord,
} from './apiChat';

// ── Predictions ─────────────────────────────────────────────────
export {
  predictDiabetes,
  predictHeart,
  predictLiver,
  predictKidney,
  predictLungs,
  getPatientOrganHealth,
  type PredictionResult,
  type OrganRiskDetail,
  type OrganHealthResult,
  type RecommendedOrder,
} from './apiPredictions';

// ── Hospital Operations ─────────────────────────────────────────
export {
  getDepartments,
  createDepartment,
  createBed,
  getBeds,
  createEncounter,
  createAdmission,
  createClinicalOrder,
  getDoctorPatientCareEventFeed,
  getAdminPatientCareEventFeed,
  getPatientCareEventFeed,
  type Department,
  type DepartmentCreate,
  type Bed,
  type BedCreate,
  type EncounterCreate,
  type Encounter,
  type AdmissionCreate,
  type Admission,
  type ClinicalOrderCreate,
  type ClinicalOrder,
  type CareEvent,
  type CareEventFeed,
} from './apiHospital';

// ── Admin ───────────────────────────────────────────────────────
export {
  getAdminStats,
  getAdminUsers,
  getAdminAuditLogs,
  getAdminPatients,
  getAdminPatient,
  getDoctorPatients,
  getAdminOperationsCockpit,
  getDoctorPatientMonitoringSignals,
  resolveMonitoringSignal,
  getDoctorPatientDiagnosticResults,
  getPatientDiagnosticResults,
  reviewDiagnosticResult,
  getDoctorPatientPrescriptions,
  getPatientPrescriptions,
  getAdminDataQuality,
  getAdminOperationalHealth,
  getAnalyticsReport,
  exportDoctorPatientFhirBundle,
  getDemoReadiness,
  type AuditLogEntry,
  type DoctorPatientSummary,
  type HospitalAdminMetrics,
  type MonitoringAdminMetrics,
  type MonitoringSignal,
  type VitalObservation,
  type DoctorPatientMonitoringSignals,
  type DiagnosticResult,
  type DoctorPatientDiagnosticResults,
  type DiagnosticReviewUpdate,
  type DiagnosticsAdminMetrics,
  type PharmacyAdminMetrics,
  type PrescriptionItem,
  type Prescription,
  type DoctorPatientPrescriptions,
  type BillingAdminMetrics,
  type DischargeAdminMetrics,
  type NursingAdminMetrics,
  type CareEventAdminMetrics,
  type InteroperabilityAdminMetrics,
  type AdminOperationsCockpitData,
  type FhirBundleExportResponse,
  type DemoReadinessData,
  type DataQualityReport,
  type OperationalHealthReport,
  type AnalyticsReport,
} from './apiAdmin';

// ── Billing & Telemedicine ──────────────────────────────────────
export {
  createPaymentOrder,
  verifyPayment,
  getAppointments,
  bookAppointment,
  getDoctors,
  type PaymentOrder,
  type PaymentVerification,
  type Appointment,
} from './apiBilling';
