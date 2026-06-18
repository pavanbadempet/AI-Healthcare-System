import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import HospitalSetupPanel from '@/components/operations/HospitalSetupPanel';
import { createBed, createDepartment, getDepartments } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  getDepartments: vi.fn(() => Promise.resolve([
    { id: 1, name: 'Cardiology', department_type: 'OPD', location: 'First Floor', status: 'active', created_at: '2026-05-26T10:00:00Z' },
  ])),
  createDepartment: vi.fn(() => Promise.resolve({ id: 2, name: 'Emergency', department_type: 'Emergency', location: 'Ground', status: 'active', created_at: '2026-05-26T10:01:00Z' })),
  createBed: vi.fn(() => Promise.resolve({ id: 4, department_id: 1, bed_number: 'ICU-01', ward: 'ICU', status: 'available', current_patient_id: null, created_at: '2026-05-26T10:02:00Z' })),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

async function renderPanel() {
  const result = render(<HospitalSetupPanel />);
  await act(async () => {
    await Promise.resolve();
  });
  return result;
}

describe('HospitalSetupPanel', () => {
  it('loads departments and creates a new department', async () => {
    await renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Cardiology')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Department name'), { target: { value: 'Emergency' } });
    fireEvent.change(screen.getByLabelText('Department type'), { target: { value: 'Emergency' } });
    fireEvent.change(screen.getByLabelText('Department location'), { target: { value: 'Ground' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register Division' }));

    await waitFor(() => {
      expect(createDepartment).toHaveBeenCalledWith({
        name: 'Emergency',
        department_type: 'Emergency',
        location: 'Ground',
      });
      expect(screen.getByText('Department created successfully.')).toBeInTheDocument();
      expect(screen.getAllByText('Emergency').length).toBeGreaterThan(0);
    });
  });

  it('creates a bed for the selected department', async () => {
    await renderPanel();

    await waitFor(() => {
      expect(screen.getByText('Cardiology')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Bed department'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Bed number'), { target: { value: 'ICU-01' } });
    fireEvent.change(screen.getByLabelText('Ward'), { target: { value: 'ICU' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register Bed Node' }));

    await waitFor(() => {
      expect(createBed).toHaveBeenCalledWith({
        department_id: 1,
        bed_number: 'ICU-01',
        ward: 'ICU',
        status: 'available',
      });
      expect(screen.getByText('Bed registered successfully.')).toBeInTheDocument();
    });
  });
});
