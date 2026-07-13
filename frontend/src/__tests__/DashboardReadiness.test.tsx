import { render, screen } from '@testing-library/react';
import DashboardPage from '@/pages/Dashboard';
import { getDemoReadiness, getRecords } from '@/lib/api';
import { ApiConnectionError } from '@/lib/apiErrors';

vi.mock('next/link', () => ({
  default: function MockLink({ href, children }: { href: string; children: React.ReactNode }) {
    return <a href={href}>{children}</a>;
  }
}));

vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: { children?: React.ReactNode }) => <div {...props}>{children}</div>,
  },
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  RadarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PolarGrid: () => <div />,
  PolarAngleAxis: () => <div />,
  PolarRadiusAxis: () => <div />,
  Radar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  Area: () => <div />,
}));

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: { id: 1, username: 'admin', full_name: 'Admin User', role: 'admin' },
  }),
}));

vi.mock('@/lib/useTelemetry', () => ({
  useTelemetry: () => ({
    status: 'error',
    data: null,
  }),
}));

vi.mock('@/components/operations/OperationsCockpit', () => ({
  default: function MockOperationsCockpit() {
    return <div>Operations cockpit</div>;
  }
}));

vi.mock('@/lib/api', () => ({
  getDemoReadiness: vi.fn(() => Promise.resolve({
    status: 'demo-ready',
    demo_mode: true,
    environment: 'demo',
    required: {},
    optional: {},
    missing_required: [],
    capabilities: ['Local demo mode'],
    clinical_safety_note: 'Demo readiness is operational metadata only.',
    privacy_note: 'No patient data is returned.',
    source: 'backend.demo_readiness',
  })),
  getRecords: vi.fn(() => Promise.reject(new ApiConnectionError('/records'))),
}));

describe('Dashboard readiness and degraded states', () => {
  it('shows demo readiness and buyer-safe backend degraded copy', async () => {
    render(<DashboardPage />);

    expect(await screen.findByText('Demo Ready')).toBeInTheDocument();
    expect(screen.getByText('Backend connection unavailable. Demo data may be incomplete.')).toBeInTheDocument();
    expect(screen.queryByText('/records')).not.toBeInTheDocument();
    expect(getDemoReadiness).toHaveBeenCalledTimes(1);
    expect(getRecords).toHaveBeenCalledTimes(1);
  });
});
