import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useHospitalBedsQuery,
  useAssignBedMutation,
  type Bed,
} from '@/hooks/useHospitalCapacity';
import {
  useClinicalAlertsQuery,
  useAcknowledgeAlertMutation,
} from '@/hooks/useClinicalIntelligence';
import {
  useAppointmentsQuery,
  useBookAppointmentMutation,
} from '@/hooks/useAppointments';
import {
  useCreateClinicalOrderMutation,
} from '@/hooks/usePatientDetail';
import * as api from '@/lib/api';
import * as apiIntelligence from '@/lib/apiIntelligence';

// Mock dependencies
vi.mock('@/lib/api', () => ({
  getAppointments: vi.fn(),
  getDoctors: vi.fn(),
  bookAppointment: vi.fn(),
  getBeds: vi.fn(),
  getDepartments: vi.fn(),
  createEncounter: vi.fn(),
  createAdmission: vi.fn(),
  createClinicalOrder: vi.fn(),
  getDoctorPatientMonitoringSignals: vi.fn(),
  getPatientOrganHealth: vi.fn(),
  getDoctorPatientCareEventFeed: vi.fn(),
}));

vi.mock('@/lib/apiIntelligence', () => ({
  fetchAlerts: vi.fn(),
  acknowledgeAlert: vi.fn(),
  fetchTriageQueue: vi.fn(),
  fetchPatientInsights: vi.fn(),
  fetchExplainability: vi.fn(),
}));

describe('Adversarial Stress-Testing: Optimistic Mutations & Rollback Mechanics', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, gcTime: 60000, networkMode: 'always' },
        mutations: { retry: false, networkMode: 'always' },
      },
    });
  });

  const createWrapper = () => ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('VULNERABILITY PROOF 1: useAssignBedMutation fails to roll back when viewing filtered beds ("available")', async () => {
    // Capacity.tsx uses useHospitalBedsQuery("available"), so queryKey is ['hospital', 'beds', 'available']
    const initialBeds: Bed[] = [
      { id: 10, bed_number: 'ICU-01', ward: 'ICU-A', status: 'available', department_id: 1, created_at: '2026-01-01' },
      { id: 20, bed_number: 'ICU-02', ward: 'ICU-A', status: 'available', department_id: 1, created_at: '2026-01-01' },
    ];

    queryClient.setQueryData(['hospital', 'beds', 'available'], initialBeds);

    // Mock API failure on server
    vi.mocked(api.createAdmission).mockRejectedValueOnce(new Error('500 Server Internal Error / DB Conflict'));

    const { result } = renderHook(() => ({
      assign: useAssignBedMutation(),
    }), { wrapper: createWrapper() });

    // Attempt bed assignment which will fail on network
    let errorCaught: any = null;
    try {
      await act(async () => {
        await result.current.assign.mutateAsync({
          patient_id: 99,
          department_id: 1,
          bed_id: 10,
          reason: 'Emergency ICU Admission',
        });
      });
    } catch (err) {
      errorCaught = err;
    }

    expect(errorCaught).toBeDefined();

    // Verify cache state for ['hospital', 'beds', 'available']:
    // It SHOULD be rolled back to 'available', but let's check what it actually is!
    const bedsAfterRollback = queryClient.getQueryData<Bed[]>(['hospital', 'beds', 'available']);
    const bed10 = bedsAfterRollback?.find(b => b.id === 10);

    // This assertion will EXPOSE if bed 10 was left as 'occupied' despite network failure!
    expect(bed10?.status).toBe('available');
  });

  it('VULNERABILITY PROOF 2: useAcknowledgeAlertMutation fails to roll back when viewing filtered alerts ("ALL")', async () => {
    // ClinicalIntelligence.tsx uses useClinicalAlertsQuery('ALL'), so queryKey is ['clinical', 'alerts', 'ALL']
    const initialAlerts = [
      {
        id: 50,
        patient_id: 3,
        alert_type: 'CARDIAC_TACHYCARDIA',
        severity: 'CRITICAL' as const,
        message: 'Acute Sinus Tachycardia',
        source_event_id: null,
        is_acknowledged: false,
        acknowledged_by: null,
        acknowledged_at: null,
        created_at: new Date().toISOString(),
      },
    ];

    queryClient.setQueryData(['clinical', 'alerts', 'ALL'], initialAlerts);

    // Mock rejection from server
    vi.mocked(apiIntelligence.acknowledgeAlert).mockRejectedValueOnce(new Error('Network timeout'));

    const { result } = renderHook(() => ({
      ack: useAcknowledgeAlertMutation(),
    }), { wrapper: createWrapper() });

    let errorCaught: any = null;
    try {
      await act(async () => {
        await result.current.ack.mutateAsync(50);
      });
    } catch (err) {
      errorCaught = err;
    }

    expect(errorCaught).toBeDefined();

    // Check if the alert in ['clinical', 'alerts', 'ALL'] rolled back to is_acknowledged: false
    const alertsAfterRollback = queryClient.getQueryData<any[]>(['clinical', 'alerts', 'ALL']);
    const alert50 = alertsAfterRollback?.find(a => a.id === 50);

    // This assertion will EXPOSE if the alert is left as is_acknowledged: true despite network failure!
    expect(alert50?.is_acknowledged).toBe(false);
  });

  it('VULNERABILITY PROOF 3: useBookAppointmentMutation fails to roll back for patient-specific queries (["appointments", patientId])', async () => {
    const patientId = 42;
    const initialAppointments = [
      {
        id: 1,
        doctor_id: 1,
        patient_id: patientId,
        appointment_date: '2026-10-01T10:00:00',
        status: 'scheduled',
        notes: 'Routine checkup',
        doctor: { name: 'Dr. Vance', specialization: 'Cardiology' },
      },
    ];

    queryClient.setQueryData(['appointments', patientId], initialAppointments);

    vi.mocked(api.bookAppointment).mockRejectedValueOnce(new Error('Network error / 409 Conflict'));

    const { result } = renderHook(() => ({
      book: useBookAppointmentMutation(),
    }), { wrapper: createWrapper() });

    let errorCaught: any = null;
    try {
      await act(async () => {
        await result.current.book.mutateAsync({
          doctor_id: 2,
          appointment_date: '2026-10-05T14:00:00',
          notes: 'Specialist consultation',
        });
      });
    } catch (err) {
      errorCaught = err;
    }

    expect(errorCaught).toBeDefined();

    // Check if ['appointments', 42] rolled back
    const apptsAfterRollback = queryClient.getQueryData<any[]>(['appointments', patientId]);
    // The list should have only the initial appointment (length 1), not the optimistic one
    expect(apptsAfterRollback).toHaveLength(1);
    expect(apptsAfterRollback?.[0].id).toBe(1);
  });

  it('VULNERABILITY PROOF 4: useCreateClinicalOrderMutation leaves stranded optimistic order if initial cache is unpopulated', async () => {
    const patientId = 99;
    // Cache has NOT been loaded yet (undefined)
    expect(queryClient.getQueryData(['patient', patientId, 'care-events'])).toBeUndefined();

    vi.mocked(api.createClinicalOrder).mockRejectedValueOnce(new Error('Network disconnected'));

    const { result } = renderHook(() => ({
      createOrder: useCreateClinicalOrderMutation(patientId),
    }), { wrapper: createWrapper() });

    let errorCaught: any = null;
    try {
      await act(async () => {
        await result.current.createOrder.mutateAsync({
          patient_id: patientId,
          order_type: 'MEDICATION',
          title: 'STAT IV Epinephrine',
          notes: 'Anaphylaxis protocol',
        });
      });
    } catch (err) {
      errorCaught = err;
    }

    expect(errorCaught).toBeDefined();

    // Cache should be rolled back to undefined (or empty), NOT left with stranded optimistic event!
    const cacheAfterRollback = queryClient.getQueryData<any>(['patient', patientId, 'care-events']);
    expect(cacheAfterRollback).toBeUndefined();
  });

  it('VULNERABILITY PROOF 5: Concurrent mutations race condition where earlier failure wipes out concurrent optimistic state', async () => {
    const patientId = 77;
    const initialFeed = {
      events: [
        {
          id: 1,
          patient_id: patientId,
          event_type: 'ADMISSION',
          severity: 'INFO' as const,
          title: 'Initial Admission',
          summary: 'Patient admitted',
          created_at: '2026-09-01T10:00:00Z',
        },
      ],
      next_after_id: null,
    };
    queryClient.setQueryData(['patient', patientId, 'care-events'], initialFeed);

    let rejectOrder1: (reason?: any) => void = () => {};
    let resolveOrder2: (value: any) => void = () => {};

    const promise1 = new Promise((_resolve, reject) => {
      rejectOrder1 = reject;
    });
    const promise2 = new Promise((resolve) => {
      resolveOrder2 = resolve;
    });

    vi.mocked(api.createClinicalOrder)
      .mockImplementationOnce(() => promise1 as any)
      .mockImplementationOnce(() => promise2 as any);

    const { result: hook1 } = renderHook(() => useCreateClinicalOrderMutation(patientId), { wrapper: createWrapper() });
    const { result: hook2 } = renderHook(() => useCreateClinicalOrderMutation(patientId), { wrapper: createWrapper() });

    // Trigger mutation 1 on hook1 (slow, will fail)
    act(() => {
      hook1.current.mutate({
        patient_id: patientId,
        order_type: 'LABORATORY',
        title: 'Order 1: CBC with Differential',
        notes: 'Routine blood work',
      });
    });

    // Trigger mutation 2 on hook2 concurrently
    act(() => {
      hook2.current.mutate({
        patient_id: patientId,
        order_type: 'IMAGING',
        title: 'Order 2: STAT Chest X-Ray',
        notes: 'Evaluate pulmonary infiltrates',
      });
    });

    // Both optimistic updates should now be present in the UI
    await waitFor(() => {
      const midState = queryClient.getQueryData<any>(['patient', patientId, 'care-events']);
      expect(midState?.events).toBeDefined();
      const hasOrder1Mid = midState?.events?.some((e: any) => e.title.includes('Order 1'));
      const hasOrder2Mid = midState?.events?.some((e: any) => e.title.includes('Order 2'));
      expect(hasOrder1Mid).toBe(true);
      expect(hasOrder2Mid).toBe(true);
    });

    // Now Order 1 fails!
    await act(async () => {
      rejectOrder1(new Error('Network error on Order 1'));
    });

    // What happened to Order 2? Order 1's rollback should NOT wipe out Order 2!
    const stateAfterOrder1Fail = queryClient.getQueryData<any>(['patient', patientId, 'care-events']);
    const hasOrder2AfterRollback = stateAfterOrder1Fail?.events.some((e: any) => e.title.includes('Order 2'));

    // Check if Order 2 was wiped out by Order 1's naive whole-cache rollback!
    expect(hasOrder2AfterRollback).toBe(true);

    // Resolve Order 2
    await act(async () => {
      resolveOrder2({
        id: 888,
        patient_id: patientId,
        order_type: 'IMAGING',
        title: 'Order 2: STAT Chest X-Ray',
        priority: 'STAT',
        status: 'PLACED',
        created_at: new Date().toISOString(),
      });
    });
  });
});
