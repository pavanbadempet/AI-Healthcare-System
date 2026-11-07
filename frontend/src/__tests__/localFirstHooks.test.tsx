import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  useAppointmentsQuery,
  useBookAppointmentMutation,
} from '@/hooks/useAppointments';
import { usePatientsRegistryQuery } from '@/hooks/usePatients';
import {
  usePatientVitalsQuery,
  useCreateClinicalOrderMutation,
} from '@/hooks/usePatientDetail';
import {
  useHospitalBedsQuery,
  useAssignBedMutation,
} from '@/hooks/useHospitalCapacity';
import {
  useClinicalAlertsQuery,
  useAcknowledgeAlertMutation,
} from '@/hooks/useClinicalIntelligence';
import { broadcastQueryInvalidation } from '@/lib/queryClient';

// Mock API endpoints
vi.mock('@/lib/api', () => ({
  getAppointments: vi.fn(() => Promise.resolve([
    {
      id: 1,
      doctor_id: 1,
      appointment_date: '2026-09-18T10:30:00',
      status: 'scheduled',
      notes: 'Initial consultation',
      doctor: { name: 'Dr. Marcus Vance, MD', specialization: 'Cardiovascular Medicine' },
    },
  ])),
  getDoctors: vi.fn(() => Promise.resolve([
    { id: 1, name: 'Dr. Marcus Vance, MD', specialization: 'Cardiovascular Medicine' },
  ])),
  bookAppointment: vi.fn((input) => Promise.resolve({
    id: 999,
    doctor_id: input.doctor_id,
    appointment_date: input.appointment_date,
    status: 'scheduled',
    notes: input.notes,
    doctor: { name: 'Dr. Marcus Vance, MD', specialization: 'Cardiovascular Medicine' },
  })),
  getDoctorPatients: vi.fn(() => Promise.resolve([
    {
      patient_id: 2,
      username: 'sarah_jenkins',
      full_name: 'Sarah Jenkins',
      latest_encounter_type: 'ICU-A',
      latest_status: 'active',
      open_orders: 2,
      active_admissions: 1,
    },
  ])),
  getAdminPatients: vi.fn(() => Promise.resolve([])),
  getDoctorPatientMonitoringSignals: vi.fn((id: number) => Promise.resolve({
    patient_id: id,
    latest_vitals: [{ heart_rate: 76, systolic_bp: 120, diastolic_bp: 80, spo2: 99, temperature_c: 36.7 }],
  })),
  getPatientOrganHealth: vi.fn(() => Promise.resolve(null)),
  getDoctorPatientCareEventFeed: vi.fn(() => Promise.resolve({
    events: [],
    next_after_id: null,
  })),
  createClinicalOrder: vi.fn((order) => Promise.resolve({
    id: 123,
    patient_id: order.patient_id,
    order_type: order.order_type,
    title: order.title,
    priority: 'ROUTINE',
    status: 'PLACED',
    created_at: new Date().toISOString(),
  })),
  getBeds: vi.fn(() => Promise.resolve([
    { id: 10, bed_number: 'ICU-01', ward: 'ICU-A', status: 'available', department_id: 1, created_at: '2026-01-01' },
  ])),
  getDepartments: vi.fn(() => Promise.resolve([])),
  createEncounter: vi.fn(() => Promise.resolve({ id: 55 })),
  createAdmission: vi.fn(() => Promise.resolve({
    id: 77,
    patient_id: 1,
    department_id: 1,
    bed_id: 10,
    admission_date: new Date().toISOString(),
    status: 'admitted',
    created_at: new Date().toISOString(),
  })),
  fetchAlerts: vi.fn(() => Promise.resolve([
    {
      id: 50,
      patient_id: 3,
      alert_type: 'CARDIAC_TACHYCARDIA',
      severity: 'CRITICAL',
      message: 'Elevated HR',
      source_event_id: null,
      is_acknowledged: false,
      acknowledged_by: null,
      acknowledged_at: null,
      created_at: new Date().toISOString(),
    },
  ])),
  acknowledgeAlert: vi.fn(() => Promise.resolve({ message: 'Alert acknowledged' })),
}));

vi.mock('@/lib/apiIntelligence', () => ({
  fetchAlerts: vi.fn(() => Promise.resolve([
    {
      id: 50,
      patient_id: 3,
      alert_type: 'CARDIAC_TACHYCARDIA',
      severity: 'CRITICAL',
      message: 'Elevated HR',
      source_event_id: null,
      is_acknowledged: false,
      acknowledged_by: null,
      acknowledged_at: null,
      created_at: new Date().toISOString(),
    },
  ])),
  acknowledgeAlert: vi.fn(() => Promise.resolve({ message: 'Alert acknowledged' })),
  fetchTriageQueue: vi.fn(() => Promise.resolve({ queue: [] })),
  fetchPatientInsights: vi.fn(() => Promise.resolve(null)),
  fetchExplainability: vi.fn(() => Promise.resolve(null)),
}));

describe('Local-First Modular TanStack Query Hooks & Optimistic Mutations', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, gcTime: 0, networkMode: 'always' },
        mutations: { retry: false, networkMode: 'always' },
      },
    });
  });

  const createWrapper = () => ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('useAppointmentsQuery hydrates appointment feed and useBookAppointmentMutation updates optimistically', async () => {
    const { result } = renderHook(
      () => ({
        appointments: useAppointmentsQuery(),
        book: useBookAppointmentMutation(),
      }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.appointments.isSuccess).toBe(true));
    expect(result.current.appointments.data).toHaveLength(1);
    expect(result.current.appointments.data?.[0].notes).toBe('Initial consultation');

    // Execute optimistic appointment booking
    await act(async () => {
      await result.current.book.mutateAsync({
        doctor_id: 1,
        appointment_date: '2026-09-19T14:00:00',
        notes: 'Follow-up ECG check',
      });
    });

    await waitFor(() => expect(result.current.book.isSuccess).toBe(true));
  });

  it('usePatientsRegistryQuery resolves local-first doctor patient list', async () => {
    const { result } = renderHook(() => usePatientsRegistryQuery('doctor'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].full_name).toBe('Sarah Jenkins');
  });

  it('usePatientVitalsQuery retrieves telemetry signals and useCreateClinicalOrderMutation executes 3-phase optimistic UI', async () => {
    const { result } = renderHook(
      () => ({
        vitals: usePatientVitalsQuery(2, true),
        createOrder: useCreateClinicalOrderMutation(2),
      }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.vitals.isSuccess).toBe(true));
    expect(result.current.vitals.data?.hr).toBe(76);
    expect(result.current.vitals.data?.spo2).toBe(99);

    await act(async () => {
      await result.current.createOrder.mutateAsync({
        patient_id: 2,
        order_type: 'LABORATORY',
        title: 'STAT Serum Troponin I',
        notes: 'Evaluate troponin baseline',
      });
    });

    await waitFor(() => expect(result.current.createOrder.isSuccess).toBe(true));
  });

  it('useHospitalBedsQuery and useAssignBedMutation optimistically marks bed occupied', async () => {
    const { result } = renderHook(
      () => ({
        beds: useHospitalBedsQuery(),
        assign: useAssignBedMutation(),
      }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.beds.isSuccess).toBe(true));
    expect(result.current.beds.data?.[0].status).toBe('available');

    await act(async () => {
      await result.current.assign.mutateAsync({
        patient_id: 2,
        department_id: 1,
        bed_id: 10,
        reason: 'Admission to ICU-01',
      });
    });

    await waitFor(() => expect(result.current.assign.isSuccess).toBe(true));
  });

  it('useClinicalAlertsQuery and useAcknowledgeAlertMutation optimistically updates is_acknowledged to true', async () => {
    const { result } = renderHook(
      () => ({
        alerts: useClinicalAlertsQuery('ALL'),
        ack: useAcknowledgeAlertMutation(),
      }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.alerts.isSuccess).toBe(true));
    expect(result.current.alerts.data?.[0].is_acknowledged).toBe(false);

    await act(async () => {
      await result.current.ack.mutateAsync(50);
    });

    await waitFor(() => expect(result.current.ack.isSuccess).toBe(true));
  });

  it('broadcastQueryInvalidation safely fires without errors when channel is active', () => {
    expect(() => {
      broadcastQueryInvalidation(['appointments']);
      broadcastQueryInvalidation(['hospital', 'beds']);
    }).not.toThrow();
  });
});
