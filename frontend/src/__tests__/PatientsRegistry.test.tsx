import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  type ReactNode,
  type Ref,
} from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientsPage from '@/pages/Patients';
import { getAdminPatients, getAdminUsers, getDoctorPatients } from '@/lib/api';

let mockAuthUser = { id: 7, username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' };

vi.mock('framer-motion', () => {
  const omittedMotionProps = new Set([
    'initial',
    'animate',
    'exit',
    'transition',
    'whileInView',
    'viewport',
    'whileHover',
    'whileTap',
    'layout',
  ]);

  return {
    motion: new Proxy(
      {},
      {
        get: (_target, element) => {
          const tagName = String(element);
          const MotionComponent = mockForwardRef(
            ({ children, ...props }: { children?: ReactNode; [key: string]: unknown }, ref: Ref<HTMLElement>) => {
              const domProps = Object.fromEntries(
                Object.entries(props).filter(([key]) => !omittedMotionProps.has(key))
              );
              return mockCreateElement(tagName, { ...domProps, ref }, children);
            }
          );
          MotionComponent.displayName = `MockMotion.${tagName}`;
          return MotionComponent;
        },
      }
    ),
  };
});

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('@/lib/api', () => ({
  getAdminPatients: vi.fn(() => Promise.resolve([
    {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient One',
      role: 'patient',
    },
  ])),
  getAdminUsers: vi.fn(() => Promise.resolve([
    {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient One',
      role: 'patient',
    },
    {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    },
    {
      id: 8,
      username: 'nurse_user',
      email: 'nurse@example.com',
      full_name: 'Nurse User',
      role: 'nurse',
    },
    {
      id: 9,
      username: 'billing_user',
      email: 'billing@example.com',
      full_name: 'Billing User',
      role: 'billing',
    },
    {
      id: 1,
      username: 'admin_user',
      email: 'admin@example.com',
      full_name: 'Admin User',
      role: 'admin',
    },
  ])),
  getDoctorPatients: vi.fn(() => Promise.resolve([
    {
      patient_id: 42,
      username: 'assigned_patient',
      full_name: 'Assigned Patient',
      latest_encounter_id: 9,
      latest_encounter_type: 'OPD',
      latest_status: 'open',
      open_orders: 2,
      active_admissions: 1,
    },
  ])),
}));

describe('PatientsPage registry filtering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 7, username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' });
  });

  it('uses the doctor-scoped patient panel for doctor users', async () => {
    render(<PatientsPage />);

    await waitFor(() => {
      expect(getDoctorPatients).toHaveBeenCalledTimes(1);
    });
    expect(getAdminUsers).not.toHaveBeenCalled();
    await screen.findByText('Assigned Patient');

    expect(screen.getByText('Assigned Patient')).toBeInTheDocument();
    expect(screen.getByText(/census: 1/i)).toBeInTheDocument();
  });

  it('lists patient accounts only, never staff accounts as patient records for admins', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { id: 1, username: 'admin_user', full_name: 'Admin User', role: 'admin' });

    render(<PatientsPage />);

    await waitFor(() => {
      expect(getAdminPatients).toHaveBeenCalledTimes(1);
    });
    expect(getAdminUsers).not.toHaveBeenCalled();
    expect(getDoctorPatients).not.toHaveBeenCalled();
    await screen.findByText('Patient One');

    expect(screen.getByText('Patient One')).toBeInTheDocument();
    expect(screen.getByText(/census: 1/i)).toBeInTheDocument();
    expect(screen.queryByText('Doctor User')).not.toBeInTheDocument();
    expect(screen.queryByText('Nurse User')).not.toBeInTheDocument();
    expect(screen.queryByText('Billing User')).not.toBeInTheDocument();
    expect(screen.queryByText('Admin User')).not.toBeInTheDocument();
  });

  it('opens a new admission patient-selection worklist from the registry action', async () => {
    render(<PatientsPage />);
    await screen.findByText('Assigned Patient');

    fireEvent.click(screen.getByRole('button', { name: /New patient admission/i }));

    expect(screen.getByRole('region', { name: /New admission patient selection/i })).toBeInTheDocument();
    const admissionLink = screen.getByRole('link', { name: /Start admission for Assigned Patient/i });
    expect(admissionLink).toHaveAttribute('href', '/patients/42?intent=admission');
    expect(screen.getByText(/admissions: 1/i)).toBeInTheDocument();
  });

  it('does not fabricate unavailable clinical facts while keeping registry sync time stable', async () => {
    const randomSpy = vi.spyOn(Math, 'random')
      .mockReturnValueOnce(0.1)
      .mockReturnValueOnce(0.1)
      .mockReturnValue(0.9);
    const timeSpy = vi.spyOn(Date.prototype, 'toLocaleTimeString')
      .mockReturnValueOnce('10:00:00')
      .mockReturnValue('10:01:00');

    try {
      render(<PatientsPage />);
      await screen.findByText('Assigned Patient');

      const syncBefore = screen.getByText(/LAST SYNC:/).textContent;
      const visibleTextBefore = document.body.textContent ?? '';

      expect(visibleTextBefore).toMatch(/DOB: Not recorded/i);
      expect(visibleTextBefore).toMatch(/Sex: None \| Blood: None/i);
      expect(visibleTextBefore).toMatch(/Primary diagnosis not recorded/i);
      expect(visibleTextBefore).toMatch(/No verified telemetry/i);
      expect(visibleTextBefore).toMatch(/Attending: Not recorded/i);
      expect(visibleTextBefore).toMatch(/REVIEW/i);
      expect(visibleTextBefore).not.toMatch(/1985-04-12/i);
      expect(visibleTextBefore).not.toMatch(/I50\.9/i);
      expect(visibleTextBefore).not.toMatch(/Dr\. Smith/i);

      fireEvent.change(screen.getByLabelText('Search patient records'), {
        target: { value: 'Assigned' },
      });

      expect(screen.getByText('Assigned Patient')).toBeInTheDocument();
      expect(screen.getByText(/LAST SYNC:/).textContent).toBe(syncBefore);
      expect(document.body.textContent ?? '').toMatch(/Primary diagnosis not recorded/i);
    } finally {
      randomSpy.mockRestore();
      timeSpy.mockRestore();
    }
  });

  it('matches patient registry search by visible MRN and operational status', async () => {
    render(<PatientsPage />);
    await screen.findByText('Assigned Patient');

    fireEvent.change(screen.getByLabelText('Search patient records'), {
      target: { value: 'MRN-143008' },
    });

    expect(screen.getByText('Assigned Patient')).toBeInTheDocument();
    expect(screen.getByText(/census: 1/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search patient records'), {
      target: { value: 'open' },
    });

    expect(screen.getByText('Assigned Patient')).toBeInTheDocument();
    expect(screen.getByText(/census: 1/i)).toBeInTheDocument();
  });

  it('filters patient registry rows by risk level', async () => {
    render(<PatientsPage />);
    await screen.findByText('Assigned Patient');

    fireEvent.click(screen.getByLabelText('Filter patients'));
    fireEvent.click(screen.getByRole('button', { name: 'HIGH' }));

    expect(screen.queryByText('Assigned Patient')).not.toBeInTheDocument();
    expect(screen.getByText(/no matching patient records/i)).toBeInTheDocument();
    expect(screen.getByText(/census: 0/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'REVIEW' }));

    expect(screen.getByText('Assigned Patient')).toBeInTheDocument();
    expect(screen.getByText(/census: 1/i)).toBeInTheDocument();
  });
});
