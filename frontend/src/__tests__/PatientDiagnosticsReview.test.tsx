import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientDiagnosticsReview from '@/components/operations/PatientDiagnosticsReview';
import { getDoctorPatientDiagnosticResults, reviewDiagnosticResult } from '@/lib/api';

let mockAuthUser = {
  id: 7,
  username: 'doctor_user',
  email: 'doctor@example.com',
  full_name: 'Doctor User',
  role: 'doctor',
};

jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

jest.mock('@/lib/api', () => ({
  getDoctorPatientDiagnosticResults: jest.fn(),
  reviewDiagnosticResult: jest.fn(),
}));

describe('PatientDiagnosticsReview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthUser = {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    };
    (getDoctorPatientDiagnosticResults as jest.Mock)
      .mockResolvedValueOnce({
        patient_id: 42,
        results: [
          {
            id: 9,
            order_id: 3,
            patient_id: 42,
            result_type: 'lab',
            title: 'CBC Result',
            summary: 'Synthetic abnormal CBC summary.',
            abnormal_flag: true,
            status: 'final',
            review_status: 'pending_review',
            created_at: '2026-05-27T10:00:00Z',
          },
        ],
        clinical_safety_note: 'Diagnostic results require clinician review and are not AI diagnoses.',
      })
      .mockResolvedValueOnce({
        patient_id: 42,
        results: [
          {
            id: 9,
            order_id: 3,
            patient_id: 42,
            result_type: 'lab',
            title: 'CBC Result',
            summary: 'Synthetic abnormal CBC summary.',
            abnormal_flag: true,
            status: 'final',
            review_status: 'reviewed',
            review_note: 'Reviewed with patient and follow-up scheduled.',
            reviewed_by_id: 7,
            reviewed_at: '2026-05-27T10:05:00Z',
            created_at: '2026-05-27T10:00:00Z',
          },
        ],
        clinical_safety_note: 'Diagnostic results require clinician review and are not AI diagnoses.',
      });
    (reviewDiagnosticResult as jest.Mock).mockResolvedValue({
      id: 9,
      order_id: 3,
      patient_id: 42,
      result_type: 'lab',
      title: 'CBC Result',
      summary: 'Synthetic abnormal CBC summary.',
      abnormal_flag: true,
      status: 'final',
      review_status: 'reviewed',
      review_note: 'Reviewed with patient and follow-up scheduled.',
      reviewed_by_id: 7,
      reviewed_at: '2026-05-27T10:05:00Z',
      created_at: '2026-05-27T10:00:00Z',
    });
  });

  it('lets assigned doctors review pending diagnostic results with a note', async () => {
    render(<PatientDiagnosticsReview patientId={42} refreshIntervalMs={0} />);

    expect(await screen.findByText(/CBC Result/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Review note for CBC Result/i), {
      target: { value: 'Reviewed with patient and follow-up scheduled.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Mark CBC Result as reviewed/i }));

    await waitFor(() => {
      expect(reviewDiagnosticResult).toHaveBeenCalledWith(9, {
        review_status: 'reviewed',
        review_note: 'Reviewed with patient and follow-up scheduled.',
      });
    });
    await waitFor(() => {
      expect(getDoctorPatientDiagnosticResults).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText(/No pending diagnostic results/i)).toBeInTheDocument();
  });

  it('does not render the diagnostic review panel for patient users', () => {
    mockAuthUser = {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient User',
      role: 'patient',
    };

    const { container } = render(<PatientDiagnosticsReview patientId={42} refreshIntervalMs={0} />);

    expect(container).toBeEmptyDOMElement();
    expect(getDoctorPatientDiagnosticResults).not.toHaveBeenCalled();
  });
});
