import {
  createElement as mockCreateElement,
  forwardRef as mockForwardRef,
  Suspense,
  type ReactNode,
  type Ref,
} from 'react';
import { act, render, screen } from '@testing-library/react';
import LoginPage from '@/pages/Login';
import SignupPage from '@/pages/Signup';
import DashboardPage from '@/pages/Dashboard';
import TelemedicinePage from '@/pages/Telemedicine';
import AboutPage from '@/pages/About';
import PatientDetailPage from '@/pages/PatientDetail';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/',
}));

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
    AnimatePresence: ({ children }: { children?: ReactNode }) => <>{children}</>,
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

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AreaChart: () => <div />,
  LineChart: () => <div />,
  RadarChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  PolarGrid: () => <div />,
  PolarAngleAxis: () => <div />,
  PolarRadiusAxis: () => <div />,
  Radar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  Area: () => <div />,
  Line: () => <div />,
}));

vi.mock('@/components/operations/PatientCareActions', () => ({
  default: function MockPatientCareActions() {
    return <div>Care actions</div>;
  }
}));

vi.mock('@/components/operations/PatientCareTimeline', () => ({
  default: function MockPatientCareTimeline() {
    return <div>Care timeline</div>;
  }
}));

vi.mock('@/components/operations/PatientMonitoringSignals', () => ({
  default: function MockPatientMonitoringSignals() {
    return <div>Monitoring signals</div>;
  }
}));

vi.mock('@/components/operations/PatientDiagnosticsReview', () => ({
  default: function MockPatientDiagnosticsReview() {
    return <div>Diagnostic review</div>;
  }
}));

vi.mock('@/components/operations/PatientDiagnosticResults', () => ({
  default: function MockPatientDiagnosticResults() {
    return <div>Patient diagnostic results</div>;
  }
}));

vi.mock('@/components/operations/PatientMedicationsPanel', () => ({
  default: function MockPatientMedicationsPanel() {
    return <div>No active medication data loaded from source systems for this patient record.</div>;
  }
}));

vi.mock('@/lib/auth', () => {
  const setAuth = vi.fn();
  const logout = vi.fn();
  const user = { id: 7, username: 'clinician', full_name: 'Test Clinician', role: 'doctor' };
  const useAuthStore = () => ({
    user,
    setAuth,
    logout,
  });
  useAuthStore.getState = () => ({ setAuth, logout });

  return { useAuthStore };
});

vi.mock('@/lib/useTelemetry', () => ({
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

vi.mock('@/lib/api', () => ({
  login: vi.fn(),
  signup: vi.fn(),
  fetchProfile: vi.fn(),
  getRecords: vi.fn(() => Promise.resolve([])),
  getDemoReadiness: vi.fn(() => Promise.resolve({
    status: 'demo-ready',
    demo_mode: true,
    environment: 'demo',
    required: {},
    optional: {},
    missing_required: [],
    capabilities: { synthetic_demo: true },
    source: 'backend.demo_readiness',
  })),
  getAdminOperationsCockpit: vi.fn(() => Promise.resolve({
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
  getAppointments: vi.fn(() => Promise.resolve([])),
  getDoctors: vi.fn(() => Promise.resolve([])),
  bookAppointment: vi.fn(),
  getDepartments: vi.fn(() => Promise.resolve([])),
  getDoctorPatients: vi.fn(() => Promise.resolve([
    {
      patient_id: 42,
      username: 'patient_42',
      full_name: 'Patient 42',
      latest_encounter_id: 9,
      latest_encounter_type: 'OPD',
      latest_status: 'open',
    },
  ])),
  getAdminUsers: vi.fn(() => Promise.resolve([])),
  exportDoctorPatientFhirBundle: vi.fn(),
  createEncounter: vi.fn(),
  createAdmission: vi.fn(),
  createClinicalOrder: vi.fn(),
  getDoctorPatientCareEventFeed: vi.fn(() => Promise.resolve({ events: [], next_after_id: null })),
  getPatientCareEventFeed: vi.fn(() => Promise.resolve({ events: [], next_after_id: null })),
  getPatientOrganHealth: vi.fn(() => Promise.resolve({
    patient_id: 42,
    patient_name: 'Patient 42',
    age: 45,
    gender: 'female',
    vitals_source: 'baseline_fallback',
    vitals: {
      heart_rate: 72,
      systolic_bp: 120,
      diastolic_bp: 80,
      spo2: 98,
      temperature_c: 36.8,
      respiratory_rate: 14,
    },
    organ_risks: {
      heart: { risk_probability: 0.1, status: 'Stable' },
      lungs: { risk_probability: 0.1, status: 'Stable' },
      kidney: { risk_probability: 0.1, status: 'Stable' },
      diabetes: { risk_probability: 0.1, status: 'Stable' },
      liver: { risk_probability: 0.1, status: 'Stable' },
    },
    labs_source: 'baseline_fallback',
    labs: {
      serum_creatinine: 1.0,
      blood_urea: 40.0,
      total_bilirubin: 1.0,
      direct_bilirubin: 0.3,
      alt: 30.0,
      ast: 30.0,
    },
    recommended_orders: [],
    ai_clinical_synthesis: 'Mock AI Clinical Synthesis',
    disclaimer: 'Mock disclaimer',
  })),
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
