import { exportDoctorPatientFhirBundle, setTokenGetter } from '@/lib/api';

describe('interoperability API helpers', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    global.fetch = fetchMock;
    setTokenGetter(() => 'doctor-token');
  });

  it('exports a doctor-scoped patient FHIR bundle with auth headers', async () => {
    const payload = {
      bundle: { resourceType: 'Bundle', entry: [] },
      export: { id: 12, resource_count: 4 },
      manifest: { signature_algorithm: 'HMAC-SHA256' },
      standards_note: 'FHIR-style bundle for integration mapping; local validation and approvals are still required.',
    };
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => payload,
    });

    await expect(exportDoctorPatientFhirBundle(42)).resolves.toEqual(payload);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/v1/interop/doctor/patients/42/fhir-bundle',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer doctor-token',
          'Content-Type': 'application/json',
        }),
      })
    );
  });
});
