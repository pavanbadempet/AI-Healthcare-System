import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  Suspense,
  type ReactNode,
  type Ref,
} from 'react';
import { act, render, screen } from '@testing-library/react';
import LoginPage from '@/app/login/page';
import SignupPage from '@/app/signup/page';
import DashboardPage from '@/app/(p)/dashboard/page';
import TelemedicinePage from '@/app/(p)/telemedicine/page';
import AboutPage from '@/app/(p)/about/page';
import PatientDetailPage from '@/app/(p)/patients/[id]/page';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/',
}));

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
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AreaChart: () => <div />,
  LineChart: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  Area: () => <div />,
  Line: () => <div />,
}));

jest.mock('@/components/operations/PatientCareActions', () => function MockPatientCareActions() {
  return <div>Care actions</div>;
});

jest.mock('@/components/operations/PatientCareTimeline', () => function MockPatientCareTimeline() {
  return <div>Care timeline</div>;
});

jest.mock('@/lib/auth', () => {
  const setAuth = jest.fn();
  const logout = jest.fn();
  const user = { id: 7, username: 'clinician', full_name: 'Test Clinician', role: 'doctor' };
  const useAuthStore = () => ({
    user,
    setAuth,
    logout,
  });
  useAuthStore.getState = () => ({ setAuth, logout });

  return { useAuthStore };
});

jest.mock('@/lib/useTelemetry', () => ({
  useTelemetry: () => ({
    status: 'connected',
    data: {
      active_census: 10,
      total_capacity: 20,
      ed_boarding: 1,
      system_latency_ms: 8,
      ai_nodes_active: 2,
      department_loads: [{ dept: 'Cardiology', load: 50, status: 'Stable' }],
    },
  }),
}));

jest.mock('@/lib/api', () => ({
  login: jest.fn(),
  signup: jest.fn(),
  fetchProfile: jest.fn(),
  getRecords: jest.fn(() => Promise.resolve([])),
  getAdminOperationsCockpit: jest.fn(() => Promise.resolve({
    hospital: {},
    monitoring: {},
    diagnostics: {},
    pharmacy: {},
    billing: {},
    discharge: {},
    nursing: {},
    events: {},
    interoperability: {},
  })),
  getAppointments: jest.fn(() => Promise.resolve([])),
  getDoctors: jest.fn(() => Promise.resolve([])),
  bookAppointment: jest.fn(),
  getDepartments: jest.fn(() => Promise.resolve([])),
  getDoctorPatients: jest.fn(() => Promise.resolve([
    {
      patient_id: 42,
      username: 'patient_42',
      full_name: 'Patient 42',
      latest_encounter_id: 9,
      latest_encounter_type: 'OPD',
      latest_status: 'open',
    },
  ])),
  getAdminUsers: jest.fn(() => Promise.resolve([])),
  exportDoctorPatientFhirBundle: jest.fn(),
  createEncounter: jest.fn(),
  createAdmission: jest.fn(),
  createClinicalOrder: jest.fn(),
  getDoctorPatientCareEventFeed: jest.fn(() => Promise.resolve({ events: [], next_after_id: null })),
  getPatientCareEventFeed: jest.fn(() => Promise.resolve({ events: [], next_after_id: null })),
}));

const unverifiedClaims = [
  /\bHIPAA\b/i,
  /\bSOC\s*2\b/i,
  /\bAES-256(?:-GCM)?\b/i,
  /\bend-to-end encryption\b/i,
  /\bfull\s+HIPAA\s+compliance\b/i,
  /\bPHI\b.*\bnever leaves\b/i,
];

const surfaces = [
  ['login page', <LoginPage key="login" />],
  ['signup page', <SignupPage key="signup" />],
  ['dashboard page', <DashboardPage key="dashboard" />],
  ['telemedicine page', <TelemedicinePage key="telemedicine" />],
  ['about page', <AboutPage key="about" />],
] as const;

describe('healthcare compliance copy', () => {
  it.each(surfaces)('does not render unverified security/compliance guarantees on the %s', async (_name, element) => {
    const { container } = render(element);
    await act(async () => {
      await Promise.resolve();
    });
    const visibleText = container.textContent ?? '';

    for (const claim of unverifiedClaims) {
      expect(visibleText).not.toMatch(claim);
    }
  });

  it('renders patient AI synthesis as clinician-reviewed decision support, not autonomous treatment advice', async () => {
    let view: ReturnType<typeof render> | undefined;
    await act(async () => {
      view = render(
        <Suspense fallback={<div>Loading patient record</div>}>
          <PatientDetailPage params={Promise.resolve({ id: '42' })} />
        </Suspense>
      );
    });
    await screen.findByText(/Clinical AI Synthesis/i);
    const visibleText = view?.container.textContent ?? '';

    expect(visibleText).toMatch(/decision support only/i);
    expect(visibleText).toMatch(/not a diagnosis or treatment plan/i);
    expect(visibleText).toMatch(/consult a qualified clinician/i);
    expect(visibleText).toMatch(/emergency/i);
    expect(visibleText).not.toMatch(/recommended actions/i);
    expect(visibleText).not.toMatch(/administer 30cc\/kg/i);
    expect(visibleText).not.toMatch(/initiate broad-spectrum IV antibiotics/i);
    expect(visibleText).not.toMatch(/run ai diagnostic/i);
  });
});
