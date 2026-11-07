import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAppointments,
  getDoctors,
  bookAppointment,
  type Appointment,
} from '@/lib/api';
import { broadcastQueryInvalidation } from '@/lib/queryClient';

export interface BookAppointmentInput {
  doctor_id: number;
  appointment_date: string;
  notes?: string;
  specialist?: string;
}

/**
 * Local-First Query for patient/doctor appointments
 */
export function useAppointmentsQuery(patientId?: number) {
  return useQuery<Appointment[]>({
    queryKey: ['appointments', patientId],
    queryFn: async () => {
      const data = await getAppointments();
      if (patientId !== undefined) {
        // Filter by patient ID if specified
        return (data || []).filter((item: any) => item.patient_id === patientId || item.user_id === patientId);
      }
      return data || [];
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Query for active doctors list
 */
export function useDoctorsQuery() {
  return useQuery({
    queryKey: ['doctors'],
    queryFn: async () => {
      const docs = await getDoctors();
      return docs || [];
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * 3-Phase Optimistic UI Mutation for booking an appointment
 * Step 1 (onMutate): Snapshot existing list, optimistically prepend temporary appointment
 * Step 2 (onError): Rollback cache on network failure
 * Step 3 (onSettled): Invalidate query and broadcast cross-tab sync
 */
let optimisticAppointmentCounter = 0;

export function useBookAppointmentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: BookAppointmentInput) => {
      return await bookAppointment({
        doctor_id: input.doctor_id,
        appointment_date: input.appointment_date,
        notes: input.notes,
      });
    },
    onMutate: async (newBooking) => {
      // Step 1: Snapshot and optimistically insert
      await queryClient.cancelQueries({ queryKey: ['appointments'] });

      const previousAppointmentsData = queryClient.getQueriesData<Appointment[]>({ queryKey: ['appointments'] });

      const optimisticAppointment: Appointment = {
        id: -(Date.now() * 1000 + (++optimisticAppointmentCounter % 1000)),
        doctor_id: newBooking.doctor_id,
        appointment_date: newBooking.appointment_date,
        status: 'scheduled',
        notes: newBooking.notes || '',
        doctor: {
          name: newBooking.specialist || 'Doctor',
          specialization: newBooking.specialist || 'General Physician',
        },
      };

      queryClient.setQueriesData<Appointment[]>(
        { queryKey: ['appointments'] },
        (old = []) => [optimisticAppointment, ...old]
      );

      return { previousAppointmentsData, tempId: optimisticAppointment.id };
    },
    onError: (_err, _variables, context) => {
      // Step 2: Rollback to previous state on failure
      if (context?.previousAppointmentsData) {
        context.previousAppointmentsData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      // Step 3: Invalidate and broadcast to other tabs
      void queryClient.invalidateQueries({ queryKey: ['appointments'] });
      broadcastQueryInvalidation(['appointments']);
    },
  });
}
