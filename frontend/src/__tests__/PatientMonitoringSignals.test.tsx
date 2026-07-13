import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientMonitoringSignals from '@/components/operations/PatientMonitoringSignals';
import { getDoctorPatientMonitoringSignals, resolveMonitoringSignal } from '@/lib/api';

let mockAuthUser = {
  id: 7,
  username: 'doctor_user',
  email: 'doctor@example.com',
  full_name: 'Doctor User',
  role: 'doctor',
};

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('@/lib/api', () => ({
  getDoctorPatientMonitoringSignals: vi.fn(),
  resolveMonitoringSignal: vi.fn(),
}));

describe('PatientMonitoringSignals', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(mockAuthUser, {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    });
    (getDoctorPatientMonitoringSignals as vi.Mock)
      .mockResolvedValueOnce({
        patient_id: 42,
        latest_vitals: [],
        open_signals: [
          {
            id: 11,
            patient_id: 42,
            signal_type: 'oxygen_saturation',
            severity: 'warning',
            title: 'Oxygen saturation needs review',
            summary: 'Recent oxygen saturation is outside the review range and needs clinician review.',
            status: 'open',
            created_at: '2026-05-27T10:00:00Z',
          },
        ],
        clinical_safety_note: 'Signals highlight patterns for clinician review and are not final clinical conclusions.',
      })
      .mockResolvedValueOnce({
        patient_id: 42,
        latest_vitals: [],
        open_signals: [],
        clinical_safety_note: 'Signals highlight patterns for clinician review and are not final clinical conclusions.',
      });
    (resolveMonitoringSignal as vi.Mock).mockResolvedValue({
      id: 11,
      patient_id: 42,
      signal_type: 'oxygen_saturation',
      severity: 'warning',
      title: 'Oxygen saturation needs review',
      summary: 'Recent oxygen saturation is outside the review range and needs clinician review.',
      status: 'resolved',
      created_at: '2026-05-27T10:00:00Z',
    });
  });

  it('lets assigned doctors resolve open monitoring signals', async () => {
    render(<PatientMonitoringSignals patientId={42} refreshIntervalMs={0} />);

    expect(await screen.findByText(/Oxygen saturation needs review/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Resolve monitoring signal Oxygen saturation needs review/i }));

    await waitFor(() => {
      expect(resolveMonitoringSignal).toHaveBeenCalledWith(11);
    });
    await waitFor(() => {
      expect(getDoctorPatientMonitoringSignals).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText(/No active alarm flags/i)).toBeInTheDocument();
  });

  it('does not render the doctor signal panel for patient users', () => {
    // Clear properties to prevent leftovers, then assign
    for (const key in mockAuthUser) {
      delete (mockAuthUser as any)[key];
    }
    Object.assign(mockAuthUser, {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient User',
      role: 'patient',
    });

    const { container } = render(<PatientMonitoringSignals patientId={42} refreshIntervalMs={0} />);

    expect(container).toBeEmptyDOMElement();
    expect(getDoctorPatientMonitoringSignals).not.toHaveBeenCalled();
  });
});
