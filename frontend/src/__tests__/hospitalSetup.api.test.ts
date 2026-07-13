import { createBed, createDepartment, getBeds, getDepartments, setTokenGetter } from '@/lib/api';

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

describe('hospital setup API adapter', () => {
  it('loads departments with auth headers', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse([
      { id: 1, name: 'Cardiology', department_type: 'OPD', location: 'First Floor', status: 'active', created_at: '2026-05-26T10:00:00Z' },
    ]));

    const departments = await getDepartments();

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/hospital/departments', {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer admin-token',
      },
    });
    expect(departments[0]).toMatchObject({ id: 1, name: 'Cardiology', department_type: 'OPD' });
  });

  it('creates departments and beds using backend hospital setup schemas', async () => {
    fetchMock
      .mockReturnValueOnce(mockJsonResponse({ id: 2, name: 'Emergency', department_type: 'Emergency', location: 'Ground', status: 'active', created_at: '2026-05-26T10:00:00Z' }, true, 201))
      .mockReturnValueOnce(mockJsonResponse({ id: 7, department_id: 2, bed_number: 'ER-01', ward: 'Resus', status: 'available', current_patient_id: null, created_at: '2026-05-26T10:01:00Z' }, true, 201));

    await createDepartment({ name: 'Emergency', department_type: 'Emergency', location: 'Ground' });
    await createBed({ department_id: 2, bed_number: 'ER-01', ward: 'Resus', status: 'available' });

    expect(fetchMock.mock.calls[0]).toEqual([
        'http://127.0.0.1:8000/v1/hospital/departments',
      {
        method: 'POST',
        body: JSON.stringify({ name: 'Emergency', department_type: 'Emergency', location: 'Ground' }),
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer admin-token',
        },
      },
    ]);
    expect(fetchMock.mock.calls[1]).toEqual([
        'http://127.0.0.1:8000/v1/hospital/beds',
      {
        method: 'POST',
        body: JSON.stringify({ department_id: 2, bed_number: 'ER-01', ward: 'Resus', status: 'available' }),
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer admin-token',
        },
      },
    ]);
  });

  it('loads beds with and without status filters', async () => {
    fetchMock
      .mockReturnValueOnce(mockJsonResponse([]))
      .mockReturnValueOnce(mockJsonResponse([]));

    await getBeds();
    await getBeds('available');

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      'http://127.0.0.1:8000/v1/hospital/beds',
      'http://127.0.0.1:8000/v1/hospital/beds?status=available',
    ]);
  });
});
