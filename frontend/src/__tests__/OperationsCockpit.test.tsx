import { act, render, screen, waitFor } from '@testing-library/react';
import OperationsCockpit from '@/components/operations/OperationsCockpit';
import { getAdminOperationsCockpit } from '@/lib/api';

let mockAuthUser = { username: 'admin_user', full_name: 'Admin User', role: 'admin' };

jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({
    user: mockAuthUser,
  }),
}));

jest.mock('@/lib/api', () => ({
  getAdminOperationsCockpit: jest.fn(() => Promise.resolve({
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
  jest.clearAllMocks();
  mockAuthUser = { username: 'admin_user', full_name: 'Admin User', role: 'admin' };
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
      expect(screen.getByText('Hospital Operations Cockpit')).toBeInTheDocument();
    });
    expect(getAdminOperationsCockpit).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Admin command view')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Open encounters')).toBeInTheDocument();
    expect(screen.getByText('INR 12,500')).toBeInTheDocument();
    expect(screen.getByText('Outstanding balance')).toBeInTheDocument();
    expect(screen.getAllByText('4').length).toBeGreaterThan(0);
    expect(screen.getByText('Active consents')).toBeInTheDocument();
  });

  it('shows a doctor care-team cockpit without calling admin-only endpoints', async () => {
    mockAuthUser = { username: 'doctor_user', full_name: 'Doctor User', role: 'doctor' };

    await renderCockpit();

    expect(getAdminOperationsCockpit).not.toHaveBeenCalled();
    expect(screen.getByText('Doctor care-team view')).toBeInTheDocument();
    expect(screen.getByText('Assigned patient panel')).toBeInTheDocument();
    expect(screen.getByText('Clinician review remains required for every AI-assisted signal.')).toBeInTheDocument();
  });
});
