import {
  getDoctorPatientDiagnosticResults,
  getPatientDiagnosticResults,
  reviewDiagnosticResult,
  setTokenGetter,
} from '@/lib/api';

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

describe('diagnostics API adapter', () => {
  it('loads doctor-scoped patient diagnostic results', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      patient_id: 42,
      results: [],
      clinical_safety_note: 'Diagnostic results require clinician review and are not AI diagnoses.',
    }));

    const result = await getDoctorPatientDiagnosticResults(42);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/diagnostics/doctor/patients/42/results',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer doctor-token',
        },
      }),
    );
    expect(result.patient_id).toBe(42);
  });

  it('reviews diagnostic results with doctor auth headers', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      id: 9,
      order_id: 3,
      patient_id: 42,
      result_type: 'lab',
      title: 'CBC Result',
      summary: 'Synthetic result summary.',
      abnormal_flag: true,
      status: 'final',
      review_status: 'reviewed',
      review_note: 'Reviewed with patient.',
      reviewed_by_id: 7,
      reviewed_at: '2026-05-27T10:05:00Z',
      created_at: '2026-05-27T10:00:00Z',
    }));

    const result = await reviewDiagnosticResult(9, {
      review_status: 'reviewed',
      review_note: 'Reviewed with patient.',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/diagnostics/results/9/review',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({
          review_status: 'reviewed',
          review_note: 'Reviewed with patient.',
        }),
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer doctor-token',
        },
      }),
    );
    expect(result.review_status).toBe('reviewed');
  });

  it('loads patient-visible reviewed diagnostic results', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse([
      {
        id: 10,
        order_id: 4,
        patient_id: 42,
        result_type: 'lab',
        title: 'Metabolic Panel',
        summary: 'Released result summary.',
        abnormal_flag: false,
        status: 'final',
        review_status: 'reviewed',
        review_note: 'Reviewed and released.',
        reviewed_by_id: 7,
        reviewed_at: '2026-05-27T10:05:00Z',
        created_at: '2026-05-27T10:00:00Z',
      },
    ]));

    const result = await getPatientDiagnosticResults();

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/diagnostics/patient/results',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer doctor-token',
        },
      }),
    );
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Metabolic Panel');
  });
});
