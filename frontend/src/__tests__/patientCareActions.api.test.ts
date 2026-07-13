import { createAdmission, createClinicalOrder, createEncounter, setTokenGetter } from '@/lib/api';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => 'doctor-token');
});

function mockJsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('patient care action API adapter', () => {
  it('creates encounters, admissions, and clinical orders with hospital workflow schemas', async () => {
    fetchMock
      .mockReturnValueOnce(mockJsonResponse({ id: 9, patient_id: 42, department_id: 1, encounter_type: 'OPD', priority: 'routine', status: 'open', started_at: '2026-05-26T10:00:00Z' }, true, 201))
      .mockReturnValueOnce(mockJsonResponse({ id: 3, encounter_id: 9, patient_id: 42, department_id: 1, status: 'active', admitted_at: '2026-05-26T10:05:00Z' }, true, 201))
      .mockReturnValueOnce(mockJsonResponse({ id: 11, encounter_id: 9, patient_id: 42, department_id: 1, order_type: 'lab', title: 'CBC panel', priority: 'routine', status: 'ordered', created_at: '2026-05-26T10:06:00Z' }, true, 201));

    await createEncounter({
      patient_id: 42,
      department_id: 1,
      encounter_type: 'OPD',
      reason: 'Chest pain review',
      priority: 'routine',
    });
    await createAdmission({
      encounter_id: 9,
      patient_id: 42,
      department_id: 1,
      reason: 'Observation admission',
    });
    await createClinicalOrder({
      encounter_id: 9,
      patient_id: 42,
      department_id: 1,
      order_type: 'lab',
      title: 'CBC panel',
      priority: 'routine',
    });

    expect(fetchMock.mock.calls).toEqual([
      [
        'http://127.0.0.1:8000/v1/hospital/encounters',
        {
          method: 'POST',
          body: JSON.stringify({
            patient_id: 42,
            department_id: 1,
            encounter_type: 'OPD',
            reason: 'Chest pain review',
            priority: 'routine',
          }),
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
      [
        'http://127.0.0.1:8000/v1/hospital/admissions',
        {
          method: 'POST',
          body: JSON.stringify({
            encounter_id: 9,
            patient_id: 42,
            department_id: 1,
            reason: 'Observation admission',
          }),
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
      [
        'http://127.0.0.1:8000/v1/hospital/orders',
        {
          method: 'POST',
          body: JSON.stringify({
            encounter_id: 9,
            patient_id: 42,
            department_id: 1,
            order_type: 'lab',
            title: 'CBC panel',
            priority: 'routine',
          }),
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
    ]);
  });
});
