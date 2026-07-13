import {
  getDoctorPatientPrescriptions,
  getPatientPrescriptions,
  setTokenGetter,
} from '@/lib/api';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => 'clinical-token');
});

function mockJsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

const prescription = {
  id: 30,
  encounter_id: 9,
  patient_id: 42,
  doctor_id: 7,
  diagnosis_context: 'Clinician-reviewed fever management',
  status: 'active',
  created_at: '2026-05-27T10:00:00Z',
  dispensed_at: null,
  items: [
    {
      id: 31,
      prescription_id: 30,
      inventory_id: 3,
      medication_name: 'Paracetamol',
      dosage: '500mg',
      frequency: 'Twice daily',
      duration: '3 days',
      quantity_prescribed: 6,
      quantity_dispensed: 0,
      instructions: 'After food',
      status: 'pending',
    },
  ],
};

describe('pharmacy API adapter', () => {
  it('loads doctor-scoped patient prescriptions', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      patient_id: 42,
      prescriptions: [prescription],
      clinical_safety_note: 'Prescriptions support clinician and pharmacist workflows.',
    }));

    const result = await getDoctorPatientPrescriptions(42);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/pharmacy/doctor/patients/42/prescriptions',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer clinical-token',
        },
      }),
    );
    expect(result.prescriptions[0].items[0].medication_name).toBe('Paracetamol');
  });

  it('loads patient-scoped prescriptions', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse([prescription]));

    const result = await getPatientPrescriptions();

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/pharmacy/patient/prescriptions',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer clinical-token',
        },
      }),
    );
    expect(result).toHaveLength(1);
  });
});
