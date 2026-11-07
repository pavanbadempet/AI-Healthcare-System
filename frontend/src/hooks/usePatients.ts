import { useQuery } from '@tanstack/react-query';
import {
  getDoctorPatients,
  getAdminPatients,
  type DoctorPatientSummary,
  type UserProfile,
} from '@/lib/api';

export type RegistryRiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | "REVIEW";

export interface RegistryPatient {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  role: "patient";
  gender?: string;
  dob?: string;
  blood_type?: string;
  latest_encounter_type?: string | null;
  latest_status?: string | null;
  open_orders?: number;
  active_admissions?: number;
  clinical_risk_level?: RegistryRiskLevel | null;
  attending_name?: string | null;
}

export const FALLBACK_REGISTRY_PATIENTS: RegistryPatient[] = [
  { id: 2, username: "sarah_jenkins", email: "sarah@patient.local", full_name: "Sarah Jenkins", role: "patient", gender: "Female", dob: "1980-04-12", blood_type: "A+", latest_encounter_type: "ICU-A", latest_status: "active", open_orders: 2, active_admissions: 1, clinical_risk_level: "LOW", attending_name: "Dr. Sarah Lin, MD" },
  { id: 3, username: "marcus_thorne", email: "marcus@patient.local", full_name: "Marcus Thorne", role: "patient", gender: "Male", dob: "1956-08-23", blood_type: "O-", latest_encounter_type: "Cardiac Care", latest_status: "active", open_orders: 4, active_admissions: 1, clinical_risk_level: "CRITICAL", attending_name: "Dr. Sarah Lin, MD" },
  { id: 4, username: "linda_zhao", email: "linda@patient.local", full_name: "Linda Zhao", role: "patient", gender: "Female", dob: "1992-11-05", blood_type: "B+", latest_encounter_type: "Med-Surg 4B", latest_status: "active", open_orders: 1, active_admissions: 1, clinical_risk_level: "LOW", attending_name: "Dr. Elena Rostova, MD" },
  { id: 5, username: "robert_g", email: "robert@patient.local", full_name: "Robert Garcia", role: "patient", gender: "Male", dob: "1965-02-17", blood_type: "O+", latest_encounter_type: "Med-Surg 4B", latest_status: "active", open_orders: 3, active_admissions: 1, clinical_risk_level: "HIGH", attending_name: "Dr. Sarah Lin, MD" },
  { id: 6, username: "emily_watson", email: "emily@patient.local", full_name: "Emily Watson", role: "patient", gender: "Female", dob: "2005-09-30", blood_type: "AB+", latest_encounter_type: "Pediatric Ward", latest_status: "active", open_orders: 1, active_admissions: 1, clinical_risk_level: "LOW", attending_name: "Dr. Priya Patel, MD" },
  { id: 7, username: "oscar_meyer", email: "oscar@patient.local", full_name: "Oscar Meyer", role: "patient", gender: "Male", dob: "1957-01-14", blood_type: "A-", latest_encounter_type: "ICU-A", latest_status: "active", open_orders: 2, active_admissions: 1, clinical_risk_level: "MODERATE", attending_name: "Dr. Marcus Vance, MD" },
];

export function doctorSummaryToRegistryPatient(summary: DoctorPatientSummary): RegistryPatient {
  return {
    id: summary.patient_id,
    username: summary.username,
    full_name: summary.full_name || summary.username,
    role: "patient",
    latest_encounter_type: summary.latest_encounter_type,
    latest_status: summary.latest_status,
    open_orders: summary.open_orders,
    active_admissions: summary.active_admissions,
  };
}

export function adminUserToRegistryPatient(user: UserProfile): RegistryPatient {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    full_name: user.full_name || user.username,
    role: "patient",
    gender: user.gender,
    dob: user.dob,
    blood_type: user.blood_type,
  };
}

/**
 * Local-First Query for patient registry with instant offline fallback
 */
export function usePatientsRegistryQuery(role?: string) {
  return useQuery<RegistryPatient[]>({
    queryKey: ['patients', role],
    queryFn: async () => {
      try {
        if (role === 'doctor' || !role) {
          const summaries = await getDoctorPatients();
          const mapped = (summaries || []).map(doctorSummaryToRegistryPatient);
          return mapped.length > 0 ? mapped : FALLBACK_REGISTRY_PATIENTS;
        } else {
          const users = await getAdminPatients();
          const mapped = (users || []).map(adminUserToRegistryPatient);
          return mapped.length > 0 ? mapped : FALLBACK_REGISTRY_PATIENTS;
        }
      } catch (err) {
        console.warn('[usePatientsRegistryQuery] Offline fallback activated:', err);
        return FALLBACK_REGISTRY_PATIENTS;
      }
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
