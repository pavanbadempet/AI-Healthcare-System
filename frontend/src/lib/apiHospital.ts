/**
 * AI Healthcare System — Hospital Operations API
 */
import { apiFetch } from './apiCore';

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
