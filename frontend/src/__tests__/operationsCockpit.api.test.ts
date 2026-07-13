import { getAdminOperationsCockpit, setTokenGetter } from '@/lib/api';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => 'admin-token');
});

function mockJsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('operations cockpit API adapter', () => {
  it('aggregates the hospital admin operations endpoints with auth headers', async () => {
    const responses = [
      { open_encounters: 5, active_admissions: 2, open_orders: 8, total_beds: 20, occupied_beds: 12 },
      { open_signals: 3, total_vital_observations: 15 },
      { pending_review: 4, abnormal_results: 1, total_results: 7 },
      { low_stock_items: 2, active_prescriptions: 6, total_inventory_items: 10 },
      { outstanding_balance: 12500, total_collected: 34000, total_invoices: 9 },
      { draft_summaries: 3, finalized_summaries: 5 },
      { assigned_tasks: 6, overdue_tasks: 1, completed_tasks: 12 },
      { total_events: 18, events_by_severity: { info: 9, warning: 6, critical: 3 } },
      { total_exports: 2, active_consents: 4, total_resources_exported: 11 },
    ];
    responses.forEach((body) => fetchMock.mockReturnValueOnce(mockJsonResponse(body)));

    const result = await getAdminOperationsCockpit();

    expect(fetchMock).toHaveBeenCalledTimes(9);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      'http://127.0.0.1:8000/v1/hospital/admin/operations',
      'http://127.0.0.1:8000/v1/monitoring/admin/patterns',
      'http://127.0.0.1:8000/v1/diagnostics/admin/metrics',
      'http://127.0.0.1:8000/v1/pharmacy/admin/metrics',
      'http://127.0.0.1:8000/v1/billing/admin/metrics',
      'http://127.0.0.1:8000/v1/discharge/admin/metrics',
      'http://127.0.0.1:8000/v1/nursing/admin/metrics',
      'http://127.0.0.1:8000/v1/events/admin/metrics',
      'http://127.0.0.1:8000/v1/interop/admin/metrics',
    ]);
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer admin-token',
      },
    });
    expect(result.hospital.open_encounters).toBe(5);
    expect(result.billing.outstanding_balance).toBe(12500);
    expect(result.interoperability.active_consents).toBe(4);
  });
});
