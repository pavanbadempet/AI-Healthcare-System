import { apiFetch, setTokenGetter } from '@/lib/api';
import { ApiConnectionError } from '@/lib/apiErrors';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  localStorage.clear();
  setTokenGetter(() => null);
});

function mockJsonResponse(body: unknown, ok = false, status = 500) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('core API fetch wrapper', () => {
  it('wraps network failures as connection errors', async () => {
    fetchMock.mockRejectedValueOnce(new Error('network down'));

    await expect(apiFetch('/healthz')).rejects.toBeInstanceOf(ApiConnectionError);
  });

  it('formats validation error arrays from the backend', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      detail: [
        { msg: 'Field required' },
        { msg: 'Value must be positive' },
      ],
    }, false, 422));

    await expect(apiFetch('/predict/diabetes')).rejects.toThrow('Field required, Value must be positive');
  });

  it('formats object error details from the backend', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      detail: { reason: 'invalid payload' },
    }, false, 400));

    await expect(apiFetch('/records')).rejects.toThrow('{"reason":"invalid payload"}');
  });

  it('clears stored auth on unauthorized responses', async () => {
    localStorage.setItem('healthcare-auth', 'stale-token');
    fetchMock.mockReturnValueOnce(mockJsonResponse({ detail: 'Could not validate credentials' }, false, 401));

    await expect(apiFetch('/profile')).rejects.toThrow('Could not validate credentials');

    expect(localStorage.getItem('healthcare-auth')).toBeNull();
    expect(window.location.pathname).toBe('/login');
  });

  it('uses the backend dev server when no API URL is configured', async () => {
    vi.stubEnv('VITE_PUBLIC_API_URL', '');
    vi.stubEnv('NEXT_PUBLIC_API_URL', '');
    vi.resetModules();

    try {
      const { API_BASE } = await import('@/lib/apiCore');
      expect(API_BASE).toBe('http://127.0.0.1:8000/v1');
    } finally {
      vi.stubEnv('VITE_PUBLIC_API_URL', 'http://127.0.0.1:8000');
    }
  });
});
