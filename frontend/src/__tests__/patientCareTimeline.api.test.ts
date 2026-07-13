import { getAdminPatientCareEventFeed, getDoctorPatientCareEventFeed, getPatientCareEventFeed, setTokenGetter } from '@/lib/api';

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

describe('patient care timeline API adapter', () => {
  it('fetches role-scoped care event feeds with auth headers and limit cursors', async () => {
    const doctorFeed = {
      patient_id: 42,
      clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
      next_after_id: 12,
      events: [
        {
          id: 12,
          patient_id: 42,
          actor_user_id: 7,
          encounter_id: 9,
          department_id: 1,
          event_type: 'CLINICAL_ORDER_CREATED',
          title: 'CBC panel ordered',
          summary: 'Lab order was placed for clinician review.',
          severity: 'info',
          created_at: '2026-05-26T10:06:00Z',
        },
      ],
    };
    const adminFeed = {
      patient_id: 42,
      clinical_safety_note: 'Care events are operational records and do not replace clinician review.',
      next_after_id: 14,
      events: [
        {
          id: 14,
          patient_id: 42,
          actor_user_id: 1,
          event_type: 'ADMIN_PATIENT_EVENT',
          title: 'Admin patient event reviewed',
          summary: 'Admin-scoped patient feed returned the requested timeline.',
          severity: 'info',
          created_at: '2026-05-26T10:08:00Z',
        },
      ],
    };
    const patientFeed = {
      next_after_id: 3,
      events: [
        {
          id: 3,
          patient_id: 42,
          event_type: 'PRESCRIPTION_CREATED',
          title: 'Prescription prepared',
          summary: 'Medication request is pending pharmacy review.',
          severity: 'warning',
          created_at: '2026-05-26T09:00:00Z',
        },
      ],
    };
    fetchMock
      .mockReturnValueOnce(mockJsonResponse(doctorFeed))
      .mockReturnValueOnce(mockJsonResponse(adminFeed))
      .mockReturnValueOnce(mockJsonResponse(patientFeed));

    await expect(getDoctorPatientCareEventFeed(42, 25)).resolves.toEqual(doctorFeed);
    await expect(getAdminPatientCareEventFeed(42, 25)).resolves.toEqual(adminFeed);
    await expect(getPatientCareEventFeed(10)).resolves.toEqual(patientFeed);

    expect(fetchMock.mock.calls).toEqual([
      [
        'http://127.0.0.1:8000/v1/events/doctor/patients/42/feed?limit=25',
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
      [
        'http://127.0.0.1:8000/v1/events/admin/patients/42/feed?limit=25',
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
      [
        'http://127.0.0.1:8000/v1/events/patient/feed?limit=10',
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer doctor-token',
          },
        },
      ],
    ]);
  });
});
