/**
 * AI Healthcare System — Chat & Records API
 */
import { apiFetch, API_BASE, authHeaders, redirectToLogin } from './apiCore';

// ── Chat ─────────────────────────────────────────────────────────
export interface ChatMessage {
  role: string;
  content: string;
  timestamp?: string;
}

export async function sendChat(message: string): Promise<{ reply: string }> {
  return apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message }) });
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  return apiFetch('/chat/history');
}

export async function clearChatHistory(): Promise<void> {
  await apiFetch('/chat/history', { method: 'DELETE' });
}

export async function getChatSuggestions(): Promise<{ suggestions: string[] }> {
  return apiFetch('/chat/suggestions');
}

export async function getChatContext(query: string): Promise<{ context: string; sources: any[] }> {
  return apiFetch(`/chat/context?q=${encodeURIComponent(query)}`);
}

// ── SSE Streaming Chat ───────────────────────────────────────────
export function streamChat(
  message: string,
  history: { role: string; content: string }[],
  onChunk: (data: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (err: string) => void,
  ragScope: string = "patient",
  cloudProvider?: string,
  cloudApiKey?: string,
  model?: string
) {
  const controller = new AbortController();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  };

  if (cloudProvider) headers['x-ai-provider'] = cloudProvider;
  if (cloudApiKey) headers['x-ai-api-key'] = cloudApiKey;

  let receivedContent = false;

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, history, model, rag_scope: ragScope }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (res.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('healthcare-auth');
          redirectToLogin();
        }
        throw new Error('Unauthorized');
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No stream');
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.reply) {
                receivedContent = true;
              }
              onChunk(data);
              if (data.status === 'complete') { onDone(); return; }
              if (data.status === 'error') { onError(data.error || 'Unknown error'); return; }
            } catch { /* skip malformed */ }
          }
        }
      }
      onDone();
    })
    .catch(async (err) => {
      if (err.name === 'AbortError') return;

      if (!receivedContent) {
        try {
          const syncRes = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ message, history }),
          });
          if (syncRes.status === 401) {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('healthcare-auth');
              redirectToLogin();
            }
            throw new Error('Unauthorized');
          }
          if (!syncRes.ok) throw new Error(`HTTP ${syncRes.status}`);
          const syncData = await syncRes.json();
          const replyText = syncData.response || syncData.reply || "";
          onChunk({ reply: replyText });
          onDone();
          return;
        } catch (fallbackErr: any) {
          onError(fallbackErr.message || "Connection interrupted.");
          return;
        }
      }

      onError(err.message || "Connection interrupted.");
    });

  return () => controller.abort();
}

// ── Health Records ───────────────────────────────────────────────
export interface HealthRecord {
  id: number;
  record_type: string;
  data: Record<string, unknown>;
  prediction: string;
  timestamp: string;
}

export async function getRecords(): Promise<HealthRecord[]> {
  return apiFetch('/records');
}

export async function createRecord(data: {
  record_type: string;
  data: Record<string, unknown>;
  prediction: string;
}): Promise<HealthRecord> {
  return apiFetch('/records', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteRecord(id: number): Promise<void> {
  await apiFetch(`/records/${id}`, { method: 'DELETE' });
}
