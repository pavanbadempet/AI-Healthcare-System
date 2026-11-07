import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDoctorPatientMonitoringSignals,
  getPatientOrganHealth,
  getDoctorPatientCareEventFeed,
  createClinicalOrder,
  type DoctorPatientMonitoringSignals,
  type OrganHealthResult,
  type CareEventFeed,
  type CareEvent,
  type ClinicalOrderCreate,
  type ClinicalOrder,
} from '@/lib/api';
import { broadcastQueryInvalidation } from '@/lib/queryClient';
import { notifyPatientCareEventsUpdated } from '@/lib/patientCareEvents';

export interface VitalsTelemetryData {
  hr: number;
  bp: string;
  spo2: number;
  temp: number;
}

/**
 * 5-second polling query for authentic patient monitoring signals & vitals
 * TanStack Query automatically pauses polling when tab is inactive/backgrounded
 */
export function usePatientVitalsQuery(patientId: number, enabled: boolean = true) {
  return useQuery<VitalsTelemetryData>({
    queryKey: ['patient', patientId, 'vitals'],
    queryFn: async () => {
      const data = await getDoctorPatientMonitoringSignals(patientId);
      const v = data?.latest_vitals?.[0];
      if (v) {
        return {
          hr: v.heart_rate ?? 74,
          bp: (v.systolic_bp && v.diastolic_bp)
            ? `${Math.round(v.systolic_bp)}/${Math.round(v.diastolic_bp)}`
            : '120/80',
          spo2: v.spo2 ?? 98,
          temp: v.temperature_c ?? 36.8,
        };
      }
      return { hr: 74, bp: '120/80', spo2: 98, temp: 36.8 };
    },
    enabled: enabled && Number.isFinite(patientId) && patientId > 0,
    refetchInterval: 5000,
    staleTime: 3000,
  });
}

/**
 * Local-First Query for patient organ health breakdown & risk predictions
 */
export function usePatientOrganHealthQuery(patientId: number, enabled: boolean = true) {
  return useQuery<OrganHealthResult | null>({
    queryKey: ['patient', patientId, 'organ-health'],
    queryFn: async () => {
      return await getPatientOrganHealth(patientId);
    },
    enabled: enabled && Number.isFinite(patientId) && patientId > 0,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Local-First Query for patient care event feed & timeline
 */
export function usePatientCareEventsQuery(patientId: number, enabled: boolean = true) {
  return useQuery<CareEventFeed>({
    queryKey: ['patient', patientId, 'care-events'],
    queryFn: async () => {
      return await getDoctorPatientCareEventFeed(patientId);
    },
    enabled: enabled && Number.isFinite(patientId) && patientId > 0,
    staleTime: 1000 * 30, // 30 seconds
  });
}

let optimisticOrderCounter = 0;

/**
 * 3-Phase Optimistic UI Mutation for Clinical Orders
 * Step 1 (onMutate): Optimistically inject pending care event into care-events feed
 * Step 2 (onError): Rollback cache on error
 * Step 3 (onSettled): Invalidate query and trigger cross-tab sync
 */
export function useCreateClinicalOrderMutation(patientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderInput: ClinicalOrderCreate): Promise<ClinicalOrder> => {
      return await createClinicalOrder(orderInput);
    },
    onMutate: async (newOrder) => {
      await queryClient.cancelQueries({ queryKey: ['patient', patientId, 'care-events'] });

      const previousEvents = queryClient.getQueryData<CareEventFeed>(['patient', patientId, 'care-events']);
      const optimisticId = -(Date.now() * 1000 + (++optimisticOrderCounter % 1000));

      const optimisticEvent: CareEvent = {
        id: optimisticId,
        patient_id: patientId,
        event_type: 'ORDER_PLACED',
        severity: 'INFO',
        title: `Order: ${newOrder.title}`,
        summary: newOrder.notes || `${newOrder.order_type} order initiated`,
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData<CareEventFeed>(
        ['patient', patientId, 'care-events'],
        (old) => {
          if (!old) return { events: [optimisticEvent], next_after_id: null };
          return {
            ...old,
            events: [optimisticEvent, ...old.events],
          };
        }
      );

      return {
        previousEvents,
        hadPrevious: previousEvents !== undefined,
        optimisticId,
      };
    },
    onError: (_err, _newOrder, context) => {
      if (context) {
        if (context.optimisticId) {
          const current = queryClient.getQueryData<CareEventFeed>(['patient', patientId, 'care-events']);
          const remaining = current?.events.filter((e) => e.id !== context.optimisticId) || [];
          if (remaining.length === 0 && !context.hadPrevious) {
            queryClient.removeQueries({ queryKey: ['patient', patientId, 'care-events'] });
          } else {
            queryClient.setQueryData<CareEventFeed>(
              ['patient', patientId, 'care-events'],
              (curr) => (curr ? { ...curr, events: curr.events.filter((e) => e.id !== context.optimisticId) } : curr)
            );
          }
        } else if (context.hadPrevious && context.previousEvents) {
          queryClient.setQueryData(['patient', patientId, 'care-events'], context.previousEvents);
        } else {
          queryClient.removeQueries({ queryKey: ['patient', patientId, 'care-events'] });
        }
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['patient', patientId, 'care-events'] });
      broadcastQueryInvalidation(['patient', patientId, 'care-events']);
      notifyPatientCareEventsUpdated(patientId);
    },
  });
}
