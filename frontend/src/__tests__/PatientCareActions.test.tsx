import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientCareActions from '@/components/operations/PatientCareActions';
import { createAdmission, createClinicalOrder, createEncounter } from '@/lib/api';

let mockAuthUser = { username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' };

jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({ user: mockAuthUser }),
}));

jest.mock('@/lib/api', () => ({
  getDepartments: jest.fn(() => Promise.resolve([
    { id: 1, name: 'Cardiology', department_type: 'OPD', location: 'First Floor', status: 'active', created_at: '2026-05-26T10:00:00Z' },
  ])),
  createEncounter: jest.fn(() => Promise.resolve({ id: 9, patient_id: 42, department_id: 1, encounter_type: 'OPD', priority: 'routine', status: 'open', started_at: '2026-05-26T10:00:00Z' })),
  createAdmission: jest.fn(() => Promise.resolve({ id: 3, encounter_id: 9, patient_id: 42, department_id: 1, status: 'active', admitted_at: '2026-05-26T10:05:00Z' })),
  createClinicalOrder: jest.fn(() => Promise.resolve({ id: 11, encounter_id: 9, patient_id: 42, department_id: 1, order_type: 'lab', title: 'CBC panel', priority: 'routine', status: 'ordered', created_at: '2026-05-26T10:06:00Z' })),
}));

beforeEach(() => {
  jest.clearAllMocks();
  mockAuthUser = { username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' };
});

async function renderActions() {
  const result = render(<PatientCareActions patientId={42} />);
  await act(async () => {
    await Promise.resolve();
  });
  return result;
}

describe('PatientCareActions', () => {
  it('opens an encounter and uses it for admission and order actions', async () => {
    const workflowUpdated = jest.fn();
    window.addEventListener('patient-care-events-updated', workflowUpdated as EventListener);

    await renderActions();

    await waitFor(() => {
      expect(screen.getByText('Care Workflow Actions')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Encounter reason'), { target: { value: 'Chest pain review' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open encounter' }));

    await waitFor(() => {
      expect(createEncounter).toHaveBeenCalledWith({
        patient_id: 42,
        department_id: 1,
        encounter_type: 'OPD',
        reason: 'Chest pain review',
        priority: 'routine',
      });
    });
    expect(screen.getByText('Encounter opened')).toBeInTheDocument();
    expect(screen.getByText('Encounter #9 active')).toBeInTheDocument();
    expect(workflowUpdated).toHaveBeenLastCalledWith(expect.objectContaining({
      detail: { patientId: 42 },
    }));

    fireEvent.change(screen.getByLabelText('Admission reason'), { target: { value: 'Observation admission' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create admission' }));

    await waitFor(() => {
      expect(createAdmission).toHaveBeenCalledWith({
        encounter_id: 9,
        patient_id: 42,
        department_id: 1,
        reason: 'Observation admission',
      });
    });
    expect(screen.getByText('Admission created')).toBeInTheDocument();
    expect(workflowUpdated).toHaveBeenCalledTimes(2);

    fireEvent.change(screen.getByLabelText('Order title'), { target: { value: 'CBC panel' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create order' }));

    await waitFor(() => {
      expect(createClinicalOrder).toHaveBeenCalledWith({
        encounter_id: 9,
        patient_id: 42,
        department_id: 1,
        order_type: 'lab',
        title: 'CBC panel',
        priority: 'routine',
      });
    });
    expect(screen.getByText('Order created')).toBeInTheDocument();
    expect(workflowUpdated).toHaveBeenCalledTimes(3);

    window.removeEventListener('patient-care-events-updated', workflowUpdated as EventListener);
  });

  it('does not expose staff workflow controls to patient users', async () => {
    mockAuthUser = { username: 'patient_user', full_name: 'Patient User', role: 'patient' };

    await renderActions();

    expect(screen.getByText('Medical staff actions unavailable')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open encounter' })).not.toBeInTheDocument();
  });
});
