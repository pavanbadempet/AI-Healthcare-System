import { render, screen, waitFor } from '@testing-library/react';
import PatientMedicationsPanel from '@/components/operations/PatientMedicationsPanel';
import { getDoctorPatientPrescriptions, getPatientPrescriptions } from '@/lib/api';

let mockAuthUser = {
  id: 7,
  username: 'doctor_user',
  email: 'doctor@example.com',
  full_name: 'Doctor User',
  role: 'doctor',
};

const prescription = {
  id: 30,
  encounter_id: 9,
  patient_id: 42,
  doctor_id: 7,
  diagnosis_context: 'Clinician-reviewed fever management',
  status: 'active',
  created_at: '2026-05-27T10:00:00Z',
  dispensed_at: null,
  items: [
    {
      id: 31,
      prescription_id: 30,
      inventory_id: 3,
      medication_name: 'Paracetamol',
      dosage: '500mg',
      frequency: 'Twice daily',
      duration: '3 days',
      quantity_prescribed: 6,
      quantity_dispensed: 0,
      instructions: 'After food',
      status: 'pending',
    },
  ],
};

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('@/lib/api', () => ({
  getDoctorPatientPrescriptions: vi.fn(),
  getPatientPrescriptions: vi.fn(),
}));

describe('PatientMedicationsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    });
    (getDoctorPatientPrescriptions as vi.Mock).mockResolvedValue({
      patient_id: 42,
      prescriptions: [prescription],
      clinical_safety_note: 'Prescriptions support clinician and pharmacist workflows; clinicians remain responsible for treatment decisions.',
    });
    (getPatientPrescriptions as vi.Mock).mockResolvedValue([prescription]);
  });

  it('shows doctor-scoped medication orders for assigned patients', async () => {
    render(<PatientMedicationsPanel patientId={42} refreshIntervalMs={0} />);

    expect(await screen.findByRole('heading', { name: /Active Medications/i })).toBeInTheDocument();
    expect(await screen.findByText(/Paracetamol/i)).toBeInTheDocument();
    expect(screen.getByText(/500mg/i)).toBeInTheDocument();
    expect(screen.getByText(/Twice daily/i)).toBeInTheDocument();
    expect(screen.getByText(/6 units prescribed/i)).toBeInTheDocument();
    expect(screen.getByText(/0 dispensed/i)).toBeInTheDocument();
    expect(screen.getByText(/clinicians remain responsible/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(getDoctorPatientPrescriptions).toHaveBeenCalledWith(42);
    });
    expect(getPatientPrescriptions).not.toHaveBeenCalled();
  });

  it('shows patient-scoped prescriptions to the owning patient', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient User',
      role: 'patient',
    });

    render(<PatientMedicationsPanel patientId={42} refreshIntervalMs={0} />);

    expect(await screen.findByText(/Paracetamol/i)).toBeInTheDocument();
    expect(screen.getByText(/Medication details are for review/i)).toBeInTheDocument();
    expect(screen.getByText(/Consult your provider before changes/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(getPatientPrescriptions).toHaveBeenCalledTimes(1);
    });
    expect(getDoctorPatientPrescriptions).not.toHaveBeenCalled();
  });
});
