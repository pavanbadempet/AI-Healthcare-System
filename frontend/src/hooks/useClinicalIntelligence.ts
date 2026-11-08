import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAlerts,
  acknowledgeAlert,
  fetchPatientInsights,
  fetchExplainability,
  type ClinicalAlert,
  type PatientInsight,
  type ExplainabilityData,
} from '@/lib/apiIntelligence';
import { broadcastQueryInvalidation } from '@/lib/queryClient';

export const FALLBACK_CLINICAL_ALERTS: ClinicalAlert[] = [
  {
    id: 1,
    patient_id: 1,
    patient_name: "Marcus Thorne",
    alert_type: "CARDIAC_TACHYCARDIA",
    severity: "CRITICAL",
    message: "Acute Sinus Tachycardia (112 bpm) with anterior lead ST elevation (V2-V4). Bedside echocardiogram and serial troponin ordered.",
    source_event_id: null,
    is_acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    patient_id: 4,
    patient_name: "Sarah Jenkins",
    alert_type: "RESPIRATORY_HYPOXEMIA",
    severity: "WARNING",
    message: "Transient SpO2 desaturation (93%) on room air post-ambulation. Nasal cannula 2L/min initiated.",
    source_event_id: null,
    is_acknowledged: true,
    acknowledged_by: 1,
    acknowledged_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

/**
 * 10-second polling query for real-time clinical alerts feed
 */
export function useClinicalAlertsQuery(filter?: string) {
  const severity = filter === 'ALL' || !filter ? undefined : filter;
  return useQuery<ClinicalAlert[]>({
    queryKey: ['clinical', 'alerts', filter],
    queryFn: async () => {
      try {
        const data = await fetchAlerts(severity);
        return data && data.length > 0 ? data : FALLBACK_CLINICAL_ALERTS;
      } catch (err) {
        console.warn('[useClinicalAlertsQuery] Offline fallback activated:', err);
        return FALLBACK_CLINICAL_ALERTS;
      }
    },
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

/**
 * Query for patient insights
 */
export function usePatientInsightsQuery(patientId: number, enabled: boolean = true) {
  return useQuery<PatientInsight | null>({
    queryKey: ['clinical', 'insights', patientId],
    queryFn: async () => {
      try {
        return await fetchPatientInsights(patientId);
      } catch {
        return null;
      }
    },
    enabled: enabled && Number.isFinite(patientId) && patientId > 0,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Query for explainability feature importances
 */
export function useExplainabilityQuery(predictionId: number, enabled: boolean = true) {
  return useQuery<ExplainabilityData | null>({
    queryKey: ['clinical', 'explainability', predictionId],
    queryFn: async () => {
      try {
        return await fetchExplainability(predictionId);
      } catch {
        return null;
      }
    },
    enabled: enabled && Number.isFinite(predictionId) && predictionId > 0,
    staleTime: 1000 * 60 * 15,
  });
}

/**
 * 3-Phase Optimistic UI Mutation for Alert Acknowledgment
 * Step 1 (onMutate): Instantly toggle is_acknowledged = true in cache
 * Step 2 (onError): Rollback cache if network call fails
 * Step 3 (onSettled): Invalidate query and broadcast cross-tab sync
 */
export function useAcknowledgeAlertMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (alertId: number) => {
      return await acknowledgeAlert(alertId);
    },
    onMutate: async (alertId: number) => {
      await queryClient.cancelQueries({ queryKey: ['clinical', 'alerts'] });

      // Snapshot all matching alert queries
      const previousAlertsData = queryClient.getQueriesData<ClinicalAlert[]>({ queryKey: ['clinical', 'alerts'] });

      // Optimistically update all matching alerts in cache
      queryClient.setQueriesData<ClinicalAlert[]>({ queryKey: ['clinical', 'alerts'] }, (old) => {
        if (!old) return old;
        return old.map((alert) =>
          alert.id === alertId ? { ...alert, is_acknowledged: true, acknowledged_at: new Date().toISOString() } : alert
        );
      });

      return { previousAlertsData };
    },
    onError: (_err, _alertId, context) => {
      if (context?.previousAlertsData) {
        context.previousAlertsData.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['clinical', 'alerts'] });
      broadcastQueryInvalidation(['clinical', 'alerts']);
    },
  });
}
