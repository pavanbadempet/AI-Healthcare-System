import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  Suspense,
  type ReactNode,
  type Ref,
} from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PatientDetailPage from '@/app/(p)/patients/[id]/page';
import { exportDoctorPatientFhirBundle, getAdminPatient, getAdminUsers, getDoctorPatients } from '@/lib/api';

interface MockAuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  dob?: string;
  gender?: string;
  blood_type?: string;
}

let mockAuthUser: MockAuthUser = {
  id: 7,
  username: 'doctor_user',
  email: 'doctor@example.com',
  full_name: 'Doctor User',
  role: 'doctor',
};

jest.mock('framer-motion', () => {
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

jest.mock('recharts', () => ({
  LineChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Line: () => <div />,
}));

jest.mock('@/components/operations/PatientCareActions', () => function MockPatientCareActions() {
  return <div>Care actions</div>;
});

jest.mock('@/components/operations/PatientCareTimeline', () => function MockPatientCareTimeline() {
  return <div>Care timeline</div>;
});

jest.mock('@/components/operations/PatientMonitoringSignals', () => function MockPatientMonitoringSignals() {
  return <div>Monitoring signals</div>;
});

jest.mock('@/components/operations/PatientDiagnosticsReview', () => function MockPatientDiagnosticsReview() {
  return <div>Diagnostic review</div>;
});

jest.mock('@/components/operations/PatientDiagnosticResults', () => function MockPatientDiagnosticResults() {
  return <div>Patient diagnostic results</div>;
});

jest.mock('@/components/operations/PatientMedicationsPanel', () => function MockPatientMedicationsPanel() {
  return <div>No active medication data loaded from source systems for this patient record.</div>;
});

jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

jest.mock('@/lib/api', () => ({
  getAdminPatient: jest.fn(() => Promise.resolve({
    id: 42,
    username: 'admin_patient',
    email: 'admin-patient@example.com',
    full_name: 'Admin Patient',
    role: 'patient',
  })),
  getAdminUsers: jest.fn(() => Promise.resolve([])),
  getDoctorPatients: jest.fn(() => Promise.resolve([
    {
      patient_id: 42,
      username: 'assigned_patient',
      full_name: 'Assigned Patient',
      latest_encounter_id: 9,
      latest_encounter_type: 'OPD',
      latest_status: 'open',
    },
  ])),
  exportDoctorPatientFhirBundle: jest.fn(() => Promise.resolve({
    export: { id: 12, resource_count: 4 },
    manifest: { signature_algorithm: 'HMAC-SHA256' },
    standards_note: 'FHIR-style bundle for integration mapping; local validation and approvals are still required.',
  })),
}));

describe('Patient detail identity', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthUser = {
      id: 7,
      username: 'doctor_user',
      email: 'doctor@example.com',
      full_name: 'Doctor User',
      role: 'doctor',
    };
  });

  it('resolves a doctor patient detail header from the doctor-scoped patient list', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('heading', { name: /Assigned Patient/ })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Doe, John/ })).not.toBeInTheDocument();
    expect(getDoctorPatients).toHaveBeenCalledTimes(1);
    expect(getAdminUsers).not.toHaveBeenCalled();
  });

  it('does not render an unassigned patient shell for doctor users', async () => {
    (getDoctorPatients as jest.Mock).mockResolvedValueOnce([]);

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '43' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(/This patient record is not available for the current account/i);
    expect(screen.queryByRole('heading', { name: /Patient #43/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Export FHIR Bundle/i })).not.toBeInTheDocument();
  });

  it('prepares a doctor-scoped FHIR bundle export from the patient detail action', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Assigned Patient/ });
    fireEvent.click(screen.getByRole('button', { name: /Export FHIR Bundle/i }));

    await waitFor(() => {
      expect(exportDoctorPatientFhirBundle).toHaveBeenCalledWith(42);
    });
    expect(await screen.findByText(/FHIR bundle export #12 prepared/i)).toBeInTheDocument();
    expect(screen.getByText(/HMAC-SHA256/i)).toBeInTheDocument();
  });

  it('resolves a patient user from their own profile without doctor or admin lookups', async () => {
    mockAuthUser = {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient Self',
      role: 'patient',
      dob: '1990-01-01',
      gender: 'female',
      blood_type: 'B+',
    };

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('heading', { name: /Patient Self/ })).toBeInTheDocument();
    expect(screen.getByText(/DOB: 1990-01-01/i)).toBeInTheDocument();
    expect(screen.getByText(/SEX: FEMALE/i)).toBeInTheDocument();
    expect(screen.getByText(/BLOOD: B\+/i)).toBeInTheDocument();
    expect(getDoctorPatients).not.toHaveBeenCalled();
    expect(getAdminUsers).not.toHaveBeenCalled();
  });

  it('hides doctor-scoped export and AI preparation actions for patient users', async () => {
    mockAuthUser = {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient Self',
      role: 'patient',
    };

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Patient Self/ });
    expect(screen.queryByRole('button', { name: /Export FHIR Bundle/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Prepare clinician-reviewed AI analysis/i })).not.toBeInTheDocument();
    expect(exportDoctorPatientFhirBundle).not.toHaveBeenCalled();
  });

  it('does not render another patient record shell for patient users', async () => {
    mockAuthUser = {
      id: 42,
      username: 'patient_user',
      email: 'patient@example.com',
      full_name: 'Patient Self',
      role: 'patient',
    };

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '43' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(/This patient record is not available for the current account/i);
    expect(screen.queryByRole('heading', { name: /Patient #43/ })).not.toBeInTheDocument();
    expect(getDoctorPatients).not.toHaveBeenCalled();
    expect(getAdminUsers).not.toHaveBeenCalled();
  });

  it('resolves an admin patient detail header from the patient-specific admin lookup', async () => {
    mockAuthUser = {
      id: 1,
      username: 'admin_user',
      email: 'admin@example.com',
      full_name: 'Admin User',
      role: 'admin',
    };
    (getAdminPatient as jest.Mock).mockResolvedValueOnce(
      {
        id: 42,
        username: 'admin_patient',
        email: 'admin-patient@example.com',
        full_name: 'Admin Patient',
        role: 'patient',
        dob: '1988-04-15',
        gender: 'male',
        blood_type: 'O+',
      }
    );

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('heading', { name: /Admin Patient/ })).toBeInTheDocument();
    expect(screen.getByText(/DOB: 1988-04-15/i)).toBeInTheDocument();
    expect(screen.getByText(/SEX: MALE/i)).toBeInTheDocument();
    expect(screen.getByText(/BLOOD: O\+/i)).toBeInTheDocument();
    expect(getAdminPatient).toHaveBeenCalledWith(42);
    expect(getAdminUsers).not.toHaveBeenCalled();
    expect(getDoctorPatients).not.toHaveBeenCalled();
  });

  it('hides doctor-scoped export and AI preparation actions for admin users', async () => {
    mockAuthUser = {
      id: 1,
      username: 'admin_user',
      email: 'admin@example.com',
      full_name: 'Admin User',
      role: 'admin',
    };
    (getAdminPatient as jest.Mock).mockResolvedValueOnce(
      {
        id: 42,
        username: 'admin_patient',
        email: 'admin-patient@example.com',
        full_name: 'Admin Patient',
        role: 'patient',
      }
    );

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Admin Patient/ });
    expect(screen.queryByRole('button', { name: /Export FHIR Bundle/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Prepare clinician-reviewed AI analysis/i })).not.toBeInTheDocument();
    expect(exportDoctorPatientFhirBundle).not.toHaveBeenCalled();
  });

  it('does not render a staff account shell as a patient record for admin users', async () => {
    mockAuthUser = {
      id: 1,
      username: 'admin_user',
      email: 'admin@example.com',
      full_name: 'Admin User',
      role: 'admin',
    };
    (getAdminPatient as jest.Mock).mockRejectedValueOnce(new Error('Patient not found'));

    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '7' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(/This patient record is not available for the current account/i);
    expect(screen.queryByRole('heading', { name: /Patient #7/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Export FHIR Bundle/i })).not.toBeInTheDocument();
    expect(getAdminPatient).toHaveBeenCalledWith(7);
    expect(getAdminUsers).not.toHaveBeenCalled();
    expect(getDoctorPatients).not.toHaveBeenCalled();
  });

  it('does not fabricate critical status, allergies, or anthropometrics without source data', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Assigned Patient/ });
    const visibleText = document.body.textContent ?? '';

    expect(visibleText).not.toMatch(/CRITICAL PRIORITY LEVEL 1/i);
    expect(visibleText).not.toMatch(/ICU-A BED 04/i);
    expect(visibleText).not.toMatch(/ALLERGIES: PENICILLIN/i);
    expect(visibleText).not.toMatch(/WT: 82\.5 KG/i);
    expect(visibleText).not.toMatch(/HT: 180 CM/i);
    expect(visibleText).toMatch(/ACUITY: Review source systems/i);
    expect(visibleText).toMatch(/ALLERGIES: Not recorded/i);
    expect(visibleText).toMatch(/BLOOD: Not recorded/i);
  });

  it('does not render fabricated clinical findings when source clinical data is unavailable', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Assigned Patient/ });
    const visibleText = document.body.textContent ?? '';

    expect(visibleText).not.toMatch(/A41\.9 Sepsis/i);
    expect(visibleText).not.toMatch(/WBC\s*14\.2/i);
    expect(visibleText).not.toMatch(/Lactate\s*3\.1/i);
    expect(visibleText).not.toMatch(/Vancomycin/i);
    expect(visibleText).not.toMatch(/CT CHEST/i);
    expect(visibleText).not.toMatch(/elevated WBC/i);
    expect(visibleText).not.toMatch(/sinus tachycardia/i);
    expect(visibleText).toMatch(/No verified live telemetry loaded/i);
    expect(visibleText).toMatch(/No verified laboratory results loaded/i);
    expect(visibleText).toMatch(/No verified active problems loaded/i);
    expect(visibleText).toMatch(/No clinician-reviewed AI synthesis prepared/i);
    expect(visibleText).toMatch(/No imaging study loaded/i);
    expect(visibleText).toMatch(/No active medication data loaded/i);
  });

  it('requires verified source data before preparing an AI review', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Assigned Patient/ });
    fireEvent.click(screen.getByRole('button', { name: /Prepare clinician-reviewed AI analysis/i }));

    expect(screen.getByText(/Verified source data is required before clinician-reviewed AI synthesis can be prepared/i)).toBeInTheDocument();
  });

  it('acknowledges admission intent links from the registry', async () => {
    await act(async () => {
      render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage
            params={Promise.resolve({ id: '42' })}
            searchParams={Promise.resolve({ intent: 'admission' })}
          />
        </Suspense>
      );
      await Promise.resolve();
    });

    await screen.findByRole('heading', { name: /Assigned Patient/ });
    expect(screen.getByText(/Admission workflow selected/i)).toBeInTheDocument();
    expect(screen.getByText(/Open a clinician-reviewed encounter before creating an admission/i)).toBeInTheDocument();
  });
});
