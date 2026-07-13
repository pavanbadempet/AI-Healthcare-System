import { render, screen, waitFor } from '@testing-library/react';
import PatientDiagnosticResults from '@/components/operations/PatientDiagnosticResults';
import { getPatientDiagnosticResults } from '@/lib/api';

let mockAuthUser = {
  id: 42,
  username: 'patient_user',
  email: 'patient@example.com',
  full_name: 'Patient User',
  role: 'patient',
};

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('@/lib/api', () => ({
  getPatientDiagnosticResults: vi.fn(),
}));

describe('PatientDiagnosticResults', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient User',
      role: 'patient',
    });
    (getPatientDiagnosticResults as vi.Mock).mockResolvedValue([
      {
        id: 10,
        order_id: 4,
        patient_id: 42,
        result_type: 'lab',
        title: 'Metabolic Panel',
        summary: 'Released metabolic panel summary.',
        abnormal_flag: false,
        status: 'final',
        review_status: 'reviewed',
        review_note: 'Reviewed and released.',
        reviewed_by_id: 7,
        reviewed_at: '2026-05-27T10:05:00Z',
        created_at: '2026-05-27T10:00:00Z',
      },
      {
        id: 11,
        order_id: 5,
        patient_id: 42,
        result_type: 'radiology',
        title: 'Chest X-Ray',
        summary: 'Follow-up advised by clinician.',
        abnormal_flag: true,
        status: 'final',
        review_status: 'needs_follow_up',
        review_note: 'Book follow-up with pulmonology.',
        reviewed_by_id: 7,
        reviewed_at: '2026-05-27T10:15:00Z',
        created_at: '2026-05-27T10:10:00Z',
      },
      {
        id: 12,
        order_id: 6,
        patient_id: 42,
        result_type: 'lab',
        title: 'Pending CBC',
        summary: 'Should not render before release.',
        abnormal_flag: true,
        status: 'final',
        review_status: 'pending_review',
        created_at: '2026-05-27T10:20:00Z',
      },
    ]);
  });

  it('shows only clinician-released diagnostic results to the owning patient', async () => {
    render(<PatientDiagnosticResults patientId={42} refreshIntervalMs={0} />);

    expect(await screen.findByRole('heading', { name: /Metabolic Panel/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Chest X-Ray/i })).toBeInTheDocument();
    expect(screen.getByText(/Book follow-up with pulmonology/i)).toBeInTheDocument();
    expect(screen.getByText(/Patients should consult a qualified clinician/i)).toBeInTheDocument();
    expect(screen.queryByText(/Pending CBC/i)).not.toBeInTheDocument();
    await waitFor(() => {
      expect(getPatientDiagnosticResults).toHaveBeenCalledTimes(1);
    });
  });

  it('does not render patient diagnostic results for staff users', () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    });

    const { container } = render(<PatientDiagnosticResults patientId={42} refreshIntervalMs={0} />);

    expect(container).toBeEmptyDOMElement();
    expect(getPatientDiagnosticResults).not.toHaveBeenCalled();
  });
});
