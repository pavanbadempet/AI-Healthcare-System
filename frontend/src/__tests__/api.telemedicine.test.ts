import { bookAppointment, getAppointments, getDoctors, setTokenGetter } from '@/lib/api';

const fetchMock = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => 'test-token');
});

function mockJsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('telemedicine API adapter', () => {
  it('maps frontend booking data to the backend appointment schema', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      id: 7,
      user_id: 3,
      doctor_id: 2,
      specialist: 'General Physician',
      date_time: '2026-06-01T09:30:00',
      reason: 'Follow-up visit',
      status: 'Scheduled',
    }));

    const result = await bookAppointment({
      doctor_id: 2,
      appointment_date: '2026-06-01T09:30:00',
      notes: 'Follow-up visit',
    });

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/appointments/', {
      method: 'POST',
      body: JSON.stringify({
        doctor_id: 2,
        specialist: 'General Physician',
        date: '2026-06-01',
        time: '09:30',
        reason: 'Follow-up visit',
      }),
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer test-token',
      },
    });
    expect(result).toMatchObject({
      id: 7,
      doctor_id: 2,
      appointment_date: '2026-06-01T09:30:00',
      notes: 'Follow-up visit',
      status: 'Scheduled',
    });
  });

  it('normalizes backend appointment list fields for the telemedicine page', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse([
      {
        id: 10,
        user_id: 5,
        doctor_id: 4,
        specialist: 'Cardiology',
        date_time: '2026-07-10T14:00:00',
        reason: 'Cardiac follow-up',
        status: 'Scheduled',
      },
    ]));

    const result = await getAppointments();

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/appointments/', {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer test-token',
      },
    });
    expect(result).toEqual([
      {
        id: 10,
        doctor_id: 4,
        appointment_date: '2026-07-10T14:00:00',
        notes: 'Cardiac follow-up',
        status: 'Scheduled',
        doctor: { name: 'Cardiology', specialization: 'Cardiology' },
      },
    ]);
  });

  it('normalizes backend doctor fields for the telemedicine selector', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse([
      {
        id: 12,
        full_name: 'Dr. Mira Rao',
        specialization: 'General Physician',
        consultation_fee: 800,
        profile_picture: null,
      },
    ]));

    const result = await getDoctors();

    expect(result).toEqual([
      {
        id: 12,
        name: 'Dr. Mira Rao',
        specialization: 'General Physician',
      },
    ]);
  });
});
