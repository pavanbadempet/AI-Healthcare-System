import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientCareTimeline from '@/components/operations/PatientCareTimeline';
import { getAdminPatientCareEventFeed, getDoctorPatientCareEventFeed, getPatientCareEventFeed } from '@/lib/api';

let mockAuthUser = { id: 7, username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' };

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({ user: mockAuthUser }),
}));

vi.mock('@/lib/api', () => ({
  getAdminPatientCareEventFeed: vi.fn(() => Promise.resolve({
    patient_id: 42,
    clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
    next_after_id: 14,
    events: [
      {
        id: 14,
        patient_id: 42,
        actor_user_id: 1,
        event_type: 'ADMIN_PATIENT_EVENT',
        title: 'Admin patient event reviewed',
        summary: 'Admin-scoped patient feed returned the requested timeline.',
        severity: 'info',
        created_at: '2026-05-26T10:08:00Z',
      },
    ],
  })),
  getDoctorPatientCareEventFeed: vi.fn(() => Promise.resolve({
    patient_id: 42,
    clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
    next_after_id: 12,
    events: [
      {
        id: 12,
        patient_id: 42,
        actor_user_id: 7,
        encounter_id: 9,
        department_id: 1,
        event_type: 'CLINICAL_ORDER_CREATED',
        title: 'CBC panel ordered',
        summary: 'Lab order was placed for clinician review.',
        severity: 'info',
        created_at: '2026-05-26T10:06:00Z',
      },
    ],
  })),
  getPatientCareEventFeed: vi.fn(() => Promise.resolve({
    next_after_id: 3,
    events: [
      {
        id: 3,
        patient_id: 42,
        event_type: 'PRESCRIPTION_CREATED',
        title: 'Prescription prepared',
        summary: 'Medication request is pending pharmacy review.',
        severity: 'warning',
        created_at: '2026-05-26T09:00:00Z',
      },
    ],
  })),
}));

beforeEach(() => {
  vi.clearAllMocks();
  for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 7, username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' });
});

async function renderTimeline() {
  const result = render(<PatientCareTimeline patientId={42} refreshIntervalMs={0} />);
  await act(async () => {
    await Promise.resolve();
  });
  return result;
}

describe('PatientCareTimeline', () => {
  it('renders a doctor-scoped operational event feed and refreshes it on demand', async () => {
    await renderTimeline();

    await waitFor(() => {
      expect(getDoctorPatientCareEventFeed).toHaveBeenCalledWith(42, 25);
    });
    expect(screen.getByText('Live Care Timeline')).toBeInTheDocument();
    expect(screen.getByText('CBC panel ordered')).toBeInTheDocument();
    expect(screen.getByText('Lab order was placed for clinician review.')).toBeInTheDocument();
    expect(screen.getByText('Care events are operational records and do not replace clinician review.')).toBeInTheDocument();
    expect(screen.getByText('Synced Event ID: #12')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Refresh timeline' }));

    await waitFor(() => {
      expect(getDoctorPatientCareEventFeed).toHaveBeenCalledTimes(2);
    });
  });

  it('refreshes when care workflow actions announce a matching patient update', async () => {
    (getDoctorPatientCareEventFeed as vi.Mock)
      .mockResolvedValueOnce({
        patient_id: 42,
        clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
        next_after_id: 12,
        events: [
          {
            id: 12,
            patient_id: 42,
            actor_user_id: 7,
            encounter_id: 9,
            department_id: 1,
            event_type: 'CLINICAL_ORDER_CREATED',
            title: 'CBC panel ordered',
            summary: 'Lab order was placed for clinician review.',
            severity: 'info',
            created_at: '2026-05-26T10:06:00Z',
          },
        ],
      })
      .mockResolvedValueOnce({
        patient_id: 42,
        clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
        next_after_id: 13,
        events: [
          {
            id: 13,
            patient_id: 42,
            actor_user_id: 7,
            encounter_id: 9,
            department_id: 1,
            event_type: 'ADMISSION_CREATED',
            title: 'Admission created',
            summary: 'Admission workflow was started from the patient record.',
            severity: 'success',
            created_at: '2026-05-26T10:07:00Z',
          },
        ],
      });
    await renderTimeline();

    await waitFor(() => {
      expect(screen.getByText('CBC panel ordered')).toBeInTheDocument();
    });

    await act(async () => {
      window.dispatchEvent(new CustomEvent('patient-care-events-updated', {
        detail: { patientId: 42 },
      }));
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(getDoctorPatientCareEventFeed).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByText('Admission created')).toBeInTheDocument();
    expect(screen.getByText('Synced Event ID: #13')).toBeInTheDocument();
  });

  it('uses the admin-scoped patient feed for admin users', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 1, username: 'admin_user', full_name: 'Admin User', role: 'admin' });

    await renderTimeline();

    await waitFor(() => {
      expect(getAdminPatientCareEventFeed).toHaveBeenCalledWith(42, 25);
    });
    expect(getDoctorPatientCareEventFeed).not.toHaveBeenCalled();
    expect(getPatientCareEventFeed).not.toHaveBeenCalled();
    expect(screen.getByText('Admin patient event reviewed')).toBeInTheDocument();
    expect(screen.getByText('Synced Event ID: #14')).toBeInTheDocument();
  });

  it('uses the patient-scoped feed for patient users', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 42, username: 'patient_user', full_name: 'Patient User', role: 'patient' });

    await renderTimeline();

    await waitFor(() => {
      expect(getPatientCareEventFeed).toHaveBeenCalledWith(25);
    });
    expect(getDoctorPatientCareEventFeed).not.toHaveBeenCalled();
    expect(screen.getByText('Prescription prepared')).toBeInTheDocument();
    expect(screen.getByText('Care events are operational records for review and do not replace clinician judgment.')).toBeInTheDocument();
  });

  it('does not request timeline data for unsupported roles', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 12, username: 'billing_user', full_name: 'Billing User', role: 'billing' });

    await renderTimeline();

    expect(screen.getByText('Care timeline unavailable')).toBeInTheDocument();
    expect(getAdminPatientCareEventFeed).not.toHaveBeenCalled();
    expect(getDoctorPatientCareEventFeed).not.toHaveBeenCalled();
    expect(getPatientCareEventFeed).not.toHaveBeenCalled();
  });
});
