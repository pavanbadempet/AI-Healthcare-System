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

export async function sendChat(message: string, model?: string): Promise<{ reply: string }> {
  const language = typeof window !== 'undefined' ? localStorage.getItem('app-language') || 'en' : 'en';
  return apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message, model, language }) });
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

  let p = cloudProvider || (typeof window !== 'undefined' ? localStorage.getItem('ai_cloud_provider') : null);
  let k = cloudApiKey || (typeof window !== 'undefined' ? localStorage.getItem('ai_cloud_api_key') : null);

  if (!p) {
    p = "custom";
    k = "cloudflare";
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  };

  if (p) headers['x-ai-provider'] = p;
  if (k) headers['x-ai-api-key'] = k;

  let receivedContent = false;

  const language = typeof window !== 'undefined' ? localStorage.getItem('app-language') || 'en' : 'en';

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, history, model, rag_scope: ragScope, language }),
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
            body: JSON.stringify({ message, history, language }),
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
  record_type?: string;
  patient_name?: string;
  data?: Record<string, unknown> | string;
  prediction: string;
  timestamp: string;
  created_at?: string;
  model_type?: string;
  risk_level?: string;
}

export const FALLBACK_HEALTH_RECORDS: HealthRecord[] = [
  {
    id: 1,
    patient_name: "Sarah Jenkins",
    model_type: "general",
    prediction: "Low Risk",
    risk_level: "Low",
    timestamp: "2026-09-17T10:00:00Z",
    created_at: "2026-09-17T10:00:00Z",
  },
  {
    id: 2,
    patient_name: "Marcus Thorne",
    model_type: "heart",
    prediction: "High Risk (STEMI Alert)",
    risk_level: "High",
    timestamp: "2026-09-17T11:30:00Z",
    created_at: "2026-09-17T11:30:00Z",
  },
  {
    id: 3,
    patient_name: "Linda Zhao",
    model_type: "diabetes",
    prediction: "Low Risk",
    risk_level: "Low",
    timestamp: "2026-09-17T12:15:00Z",
    created_at: "2026-09-17T12:15:00Z",
  },
  {
    id: 4,
    patient_name: "Robert Garcia",
    model_type: "kidney",
    prediction: "Moderate Risk",
    risk_level: "Moderate",
    timestamp: "2026-09-17T13:45:00Z",
    created_at: "2026-09-17T13:45:00Z",
  },
  {
    id: 5,
    patient_name: "Emily Watson",
    model_type: "lungs",
    prediction: "Low Risk",
    risk_level: "Low",
    timestamp: "2026-09-17T14:20:00Z",
    created_at: "2026-09-17T14:20:00Z",
  },
];

export async function getRecords(): Promise<HealthRecord[]> {
  try {
    return await apiFetch('/records');
  } catch (err) {
    console.warn("Falling back to demo health records:", err);
    return FALLBACK_HEALTH_RECORDS;
  }
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
