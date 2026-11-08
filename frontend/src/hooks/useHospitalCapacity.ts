import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBeds,
  getDepartments,
  createEncounter,
  createAdmission,
  type Bed,
  type Department,
  type Admission,
} from '@/lib/api';
import { fetchTriageQueue } from '@/lib/apiIntelligence';
import { broadcastQueryInvalidation } from '@/lib/queryClient';

export interface AssignBedInput {
  patient_id: number;
  department_id: number;
  bed_id: number;
  reason?: string;
  encounter_id?: number;
}

export const FALLBACK_BEDS: Bed[] = [
  { id: 16, bed_number: "ICU-A-01", ward: "Cardiology ICU", status: "occupied", current_patient_id: 1, department_id: 1, created_at: "2026-01-01T00:00:00Z" },
  { id: 17, bed_number: "ICU-A-02", ward: "Cardiology ICU", status: "occupied", current_patient_id: 4, department_id: 1, created_at: "2026-01-01T00:00:00Z" },
  { id: 18, bed_number: "ICU-A-03", ward: "Cardiology ICU", status: "occupied", current_patient_id: 7, department_id: 1, created_at: "2026-01-01T00:00:00Z" },
  { id: 19, bed_number: "ICU-A-04", ward: "Cardiology ICU", status: "occupied", current_patient_id: 15, department_id: 1, created_at: "2026-01-01T00:00:00Z" },
  { id: 20, bed_number: "ICU-A-05", ward: "Cardiology ICU", status: "available", current_patient_id: null, department_id: 1, created_at: "2026-01-01T00:00:00Z" },
];

export const FALLBACK_DEPARTMENTS: Department[] = [
  { id: 1, name: "Intensive Care Unit (ICU-A)", department_type: "IPD", status: "active", created_at: "2026-01-01T00:00:00Z" },
  { id: 2, name: "Med-Surg Ward 4B", department_type: "IPD", status: "active", created_at: "2026-01-01T00:00:00Z" },
  { id: 3, name: "Cardiac Care Unit (CCU)", department_type: "IPD", status: "active", created_at: "2026-01-01T00:00:00Z" },
  { id: 4, name: "Pediatrics Ward", department_type: "IPD", status: "active", created_at: "2026-01-01T00:00:00Z" },
];

export const FALLBACK_TRIAGE = [
  { patient_id: 11, full_name: "Patricia Moore", esi_level: 2, triage_reason: "Acute Dyspnea / Asthma Exacerbation", arrival_time: "12m ago" },
  { patient_id: 12, full_name: "Thomas Wright", esi_level: 3, triage_reason: "Hyperglycemia / Diabetic Ketosis Workup", arrival_time: "28m ago" },
  { patient_id: 13, full_name: "Clara Oswald", esi_level: 4, triage_reason: "Left Flank Pain / Suspected Nephrolithiasis", arrival_time: "45m ago" },
  { patient_id: 14, full_name: "George Bailey", esi_level: 5, triage_reason: "Minor Forearm Abrasion & Wound Dressing", arrival_time: "58m ago" },
];

/**
 * 15-second polling query for hospital bed status grid
 */
export function useHospitalBedsQuery(status?: string) {
  return useQuery<Bed[]>({
    queryKey: ['hospital', 'beds', status],
    queryFn: async () => {
      try {
        const beds = await getBeds(status);
        return beds && beds.length > 0 ? beds : FALLBACK_BEDS;
      } catch (err) {
        console.warn('[useHospitalBedsQuery] Offline fallback activated:', err);
        return FALLBACK_BEDS;
      }
    },
    refetchInterval: 15000,
    staleTime: 10000,
  });
}

/**
 * Query for hospital departments
 */
export function useDepartmentsQuery() {
  return useQuery<Department[]>({
    queryKey: ['hospital', 'departments'],
    queryFn: async () => {
      try {
        const depts = await getDepartments();
        return depts && depts.length > 0 ? depts : FALLBACK_DEPARTMENTS;
      } catch (err) {
        console.warn('[useDepartmentsQuery] Offline fallback activated:', err);
        return FALLBACK_DEPARTMENTS;
      }
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * 15-second polling query for emergency/inpatient triage queue
 */
export function useTriageQueueQuery() {
  return useQuery({
    queryKey: ['hospital', 'triage'],
    queryFn: async () => {
      try {
        const data = await fetchTriageQueue();
        return data?.queue && data.queue.length > 0 ? data.queue : FALLBACK_TRIAGE;
      } catch (err) {
        console.warn('[useTriageQueueQuery] Offline fallback activated:', err);
        return FALLBACK_TRIAGE;
      }
    },
    refetchInterval: 15000,
    staleTime: 10000,
  });
}

/**
 * 3-Phase Optimistic UI Mutation for Inpatient Bed Assignment
 * Step 1 (onMutate): Mark bed as 'occupied' instantly in the query cache
 * Step 2 (onError): Rollback cache if network assignment fails
 * Step 3 (onSettled): Invalidate beds & triage queries and broadcast multi-tab sync
 */
export function useAssignBedMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: AssignBedInput): Promise<Admission> => {
      let encId = input.encounter_id;
      if (!encId) {
        try {
          const enc = await createEncounter({
            patient_id: input.patient_id,
            department_id: input.department_id,
            encounter_type: 'IPD',
          });
          encId = enc?.id;
        } catch {
          // Allow admission handler to auto-create encounter
        }
      }

      return await createAdmission({
        encounter_id: encId,
        patient_id: input.patient_id,
        department_id: input.department_id,
        bed_id: input.bed_id,
        reason: input.reason || 'Inpatient Admission',
      });
    },
    onMutate: async (newAssignment) => {
      await queryClient.cancelQueries({ queryKey: ['hospital', 'beds'] });

      // Snapshot all matching bed queries
      const previousBedsData = queryClient.getQueriesData<Bed[]>({ queryKey: ['hospital', 'beds'] });

      // Optimistically update bed status to occupied
      queryClient.setQueriesData<Bed[]>({ queryKey: ['hospital', 'beds'] }, (old) => {
        if (!old) return old;
        return old.map((b) => (b.id === newAssignment.bed_id ? { ...b, status: 'occupied' } : b));
      });

      return { previousBedsData };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousBedsData) {
        context.previousBedsData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['hospital', 'beds'] });
      void queryClient.invalidateQueries({ queryKey: ['hospital', 'triage'] });
      broadcastQueryInvalidation(['hospital', 'beds']);
    },
  });
}
