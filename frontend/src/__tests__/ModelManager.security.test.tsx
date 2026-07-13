import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ModelManager } from '@/components/chat/ModelManager';

const fetchMock = vi.fn();
let authState = {
  token: 'admin-token',
  user: { username: 'admin_user', role: 'admin' },
};

vi.mock('@/lib/auth', () => ({
  useAuthStore: () => authState,
}));

vi.mock('@/lib/webllm', () => ({
  isWebGPUSupported: () => false,
  WEBLLM_MODELS: [],
  loadModel: vi.fn(),
}));

function renderModelManager() {
  return render(
    <ModelManager
      onClose={vi.fn()}
      onOllamaSelect={vi.fn()}
      onWebLLMSelect={vi.fn()}
      onWebLLMUnload={vi.fn()}
      onWebLLMLoad={vi.fn()}
      currentOllamaModel=""
      currentWebLLMModel={null}
      webllmActive={false}
      webllmLoading={null}
      webllmProgress={null}
    />
  );
}

function mockInitialModelFetches() {
  fetchMock
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        catalog: [
          {
            name: 'llama3.2',
            label: 'Llama 3.2',
            size: '2.0GB',
            speed: 'fast',
            quality: 'great',
            description: 'General chat model',
          },
        ],
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ available: true, models: [] }),
    });
}

function mockDownloadedModelFetches() {
  fetchMock
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ catalog: [] }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        available: true,
        models: [
          {
            name: 'llama3.2',
            size: '2.0GB',
            size_bytes: 2000000000,
            parameter_size: '3B',
            family: 'llama',
            quantization: 'Q4',
          },
        ],
      }),
    });
}

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock as unknown as typeof fetch;
  authState = {
    token: 'admin-token',
    user: { username: 'admin_user', role: 'admin' },
  };
});

describe('ModelManager admin model actions', () => {
  it('sends the bearer token when an admin pulls an Ollama model', async () => {
    mockInitialModelFetches();
    fetchMock.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ detail: 'Ollama unavailable' }),
    });

    renderModelManager();

    fireEvent.click(await screen.findByRole('button', { name: /download to local hub/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/ai/models/pull',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer admin-token',
          },
          body: JSON.stringify({ name: 'llama3.2' }),
        })
      );
    });
  });

  it('does not render Ollama download controls for non-admin users', async () => {
    authState = {
      token: 'patient-token',
      user: { username: 'patient_user', role: 'patient' },
    };
    mockInitialModelFetches();

    renderModelManager();

    expect(await screen.findByText('Llama 3.2')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /download to local hub/i })).not.toBeInTheDocument();
    expect(screen.getByText(/admin access required/i)).toBeInTheDocument();
  });

  it('sends the bearer token when an admin deletes an installed Ollama model', async () => {
    mockDownloadedModelFetches();
    fetchMock.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ success: true }) });
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);

    renderModelManager();

    fireEvent.click(await screen.findByRole('button', { name: /installed \(1\)/i }));
    fireEvent.click(await screen.findByRole('button', { name: /delete llama3\.2/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/ai/models',
        expect.objectContaining({
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            Authorization: 'Bearer admin-token',
          },
          body: JSON.stringify({ name: 'llama3.2' }),
        })
      );
    });
  });
});
