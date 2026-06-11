import { getAdminPatient, getAdminPatients, getDoctorPatients, setTokenGetter } from '@/lib/api';

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

describe('patient registry API adapter', () => {
  it('loads the doctor-scoped patient panel instead of the admin user directory', async () => {
    const panel = [
      {
        patient_id: 42,
        username: 'assigned_patient',
        full_name: 'Assigned Patient',
        latest_encounter_id: 9,
        latest_encounter_type: 'OPD',
        latest_status: 'open',
        open_orders: 2,
        active_admissions: 1,
      },
    ];
    fetchMock.mockReturnValueOnce(mockJsonResponse(panel));

    await expect(getDoctorPatients()).resolves.toEqual(panel);

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/hospital/doctor/patients', {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer doctor-token',
      },
    });
  });

  it('loads a single admin patient profile without fetching the whole user directory', async () => {
    const profile = {
      id: 42,
      username: 'admin_patient',
      email: 'admin-patient@example.com',
      full_name: 'Admin Patient',
      role: 'patient',
      dob: '1988-04-15',
      gender: 'male',
      blood_type: 'O+',
    };
    fetchMock.mockReturnValueOnce(mockJsonResponse(profile));

    await expect(getAdminPatient(42)).resolves.toEqual(profile);

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/admin/patients/42', {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer doctor-token',
      },
    });
  });

  it('loads the admin patient registry from the patient-only endpoint', async () => {
    const patients = [
      {
        id: 42,
        username: 'admin_patient',
        email: 'admin-patient@example.com',
        full_name: 'Admin Patient',
        role: 'patient',
      },
    ];
    fetchMock.mockReturnValueOnce(mockJsonResponse(patients));

    await expect(getAdminPatients()).resolves.toEqual(patients);

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/admin/patients', {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer doctor-token',
      },
    });
  });
});
