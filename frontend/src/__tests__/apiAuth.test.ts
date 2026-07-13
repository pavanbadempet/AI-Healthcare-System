import { fetchProfile, login, setTokenGetter, signup, updateProfile } from '@/lib/api';

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  setTokenGetter(() => null);
});

function mockJsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('auth API adapter', () => {
  it('posts login credentials as form data', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({
      access_token: 'jwt-token',
      token_type: 'bearer',
    }));

    const result = await login('doctor_user', 'StrongPassword123!');

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: expect.any(URLSearchParams),
    });
    const body = fetchMock.mock.calls[0][1].body as URLSearchParams;
    expect(body.get('username')).toBe('doctor_user');
    expect(body.get('password')).toBe('StrongPassword123!');
    expect(result.access_token).toBe('jwt-token');
  });

  it('surfaces backend login failures', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({ detail: 'Incorrect username or password' }, false, 401));

    await expect(login('bad_user', 'wrong')).rejects.toThrow('Incorrect username or password');
  });

  it('creates users through the versioned signup endpoint', async () => {
    fetchMock.mockReturnValueOnce(mockJsonResponse({ username: 'new_patient' }));

    const result = await signup({
      username: 'new_patient',
      email: 'new_patient@example.com',
      password: 'StrongPassword123!',
      full_name: 'New Patient',
    });

    expect(fetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/v1/signup', {
      method: 'POST',
      body: JSON.stringify({
        username: 'new_patient',
        email: 'new_patient@example.com',
        password: 'StrongPassword123!',
        full_name: 'New Patient',
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
    expect(result.username).toBe('new_patient');
  });

  it('loads and updates the authenticated profile', async () => {
    setTokenGetter(() => 'profile-token');
    fetchMock
      .mockReturnValueOnce(mockJsonResponse({
        id: 3,
        username: 'profile_user',
        email: 'profile@example.com',
        full_name: 'Profile User',
        role: 'patient',
      }))
      .mockReturnValueOnce(mockJsonResponse({
        id: 3,
        username: 'profile_user',
        email: 'profile@example.com',
        full_name: 'Updated User',
        role: 'patient',
      }));

    const profile = await fetchProfile();
    const updated = await updateProfile({ full_name: 'Updated User' });

    expect(fetchMock.mock.calls[0]).toEqual([
      'http://127.0.0.1:8000/v1/profile',
      {
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer profile-token',
        },
      },
    ]);
    expect(fetchMock.mock.calls[1]).toEqual([
      'http://127.0.0.1:8000/v1/profile',
      {
        method: 'PUT',
        body: JSON.stringify({ full_name: 'Updated User' }),
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer profile-token',
        },
      },
    ]);
    expect(profile.username).toBe('profile_user');
    expect(updated.full_name).toBe('Updated User');
  });
});
