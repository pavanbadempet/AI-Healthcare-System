import { act, render, screen, waitFor } from '@testing-library/react';
import OperationsCockpit from '@/components/operations/OperationsCockpit';
import { getAdminOperationsCockpit } from '@/lib/api';
import { ApiConnectionError } from '@/lib/apiErrors';

let mockAuthUser = { username: 'admin_user', full_name: 'Admin User', role: 'admin' };

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

vi.mock('@/lib/api', () => ({
  getAdminOperationsCockpit: vi.fn(() => Promise.resolve({
    hospital: { open_encounters: 5, active_admissions: 2, open_orders: 8, total_beds: 20, occupied_beds: 12 },
    monitoring: { open_signals: 3, total_vital_observations: 15 },
    diagnostics: { pending_review: 4, abnormal_results: 1, total_results: 7 },
    pharmacy: { low_stock_items: 2, active_prescriptions: 6, total_inventory_items: 10 },
    billing: { outstanding_balance: 12500, total_collected: 34000, total_invoices: 9 },
    discharge: { draft_summaries: 3, finalized_summaries: 5 },
    nursing: { assigned_tasks: 6, overdue_tasks: 1, completed_tasks: 12 },
    events: { total_events: 18, events_by_severity: { info: 9, warning: 6, critical: 3 } },
    interoperability: { total_exports: 2, active_consents: 4, total_resources_exported: 11 },
  })),
}));

beforeEach(() => {
  vi.clearAllMocks();
  for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { username: 'admin_user', full_name: 'Admin User', role: 'admin' });
});

async function renderCockpit() {
  const result = render(<OperationsCockpit />);
  await act(async () => {
    await Promise.resolve();
  });
  return result;
}

describe('OperationsCockpit', () => {
  it('renders admin hospital operations metrics from the backend aggregation', async () => {
    await renderCockpit();

    await waitFor(() => {
      expect(screen.getByText('Operational Dashboard Cockpit')).toBeInTheDocument();
    });
    expect(getAdminOperationsCockpit).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Admin Command Console')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Open encounters')).toBeInTheDocument();
    expect(screen.getByText('INR 12,500')).toBeInTheDocument();
    expect(screen.getByText('Outstanding balance')).toBeInTheDocument();
    expect(screen.getAllByText('4').length).toBeGreaterThan(0);
    expect(screen.getByText('Active consents')).toBeInTheDocument();
  });

  it('shows a doctor care-team cockpit without calling admin-only endpoints', async () => {
    for (const key in mockAuthUser) delete (mockAuthUser as any)[key];
    Object.assign(mockAuthUser, { username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' });

    await renderCockpit();

    expect(getAdminOperationsCockpit).not.toHaveBeenCalled();
    expect(screen.getByText('Doctor Care-Team Interface')).toBeInTheDocument();
    expect(screen.getByText('Patient panel')).toBeInTheDocument();
    expect(screen.getByText(/does not prescribe, diagnose, or override/i)).toBeInTheDocument();
  });

  it('shows buyer-safe degraded copy when operations metrics are unavailable', async () => {
    (getAdminOperationsCockpit as vi.Mock).mockRejectedValueOnce(
      new ApiConnectionError('/admin/operations-cockpit')
    );

    await renderCockpit();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Backend connection unavailable. Demo data may be incomplete.'
    );
    expect(screen.queryByText('/admin/operations-cockpit')).not.toBeInTheDocument();
  });
});
