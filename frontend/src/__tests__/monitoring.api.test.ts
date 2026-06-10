import { getDoctorPatientMonitoringSignals, resolveMonitoringSignal, setTokenGetter } from '@/lib/api';

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

describe('monitoring API adapter', () => {
  it('loads doctor-scoped patient monitoring signals', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      patient_id: 42,
      latest_vitals: [],
      open_signals: [],
      clinical_safety_note: 'Signals highlight patterns for clinician review and are not final clinical conclusions.',
    }));

    const result = await getDoctorPatientMonitoringSignals(42);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/monitoring/doctor/patients/42/signals',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer doctor-token',
        },
      }),
    );
    expect(result.patient_id).toBe(42);
  });

  it('resolves monitoring signals with doctor auth headers', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      id: 7,
      patient_id: 42,
      signal_type: 'oxygen_saturation',
      severity: 'warning',
      title: 'Oxygen saturation needs review',
      summary: 'Recent oxygen saturation is outside the review range and needs clinician review.',
      status: 'resolved',
      created_at: '2026-05-27T10:00:00Z',
    }));

    const result = await resolveMonitoringSignal(7);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/monitoring/signals/7/resolve',
      expect.objectContaining({
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer doctor-token',
        },
      }),
    );
    expect(result.status).toBe('resolved');
  });
});
