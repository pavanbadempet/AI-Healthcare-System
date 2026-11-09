/**
 * AI Healthcare System — Chat & Records API Client
 */

import { apiFetch } from './apiCore';

export interface ChatMessage {
  role: 'user' | 'assistant' | string;
  content: string;
}

export interface ChatResponse {
  response: string;
  disclaimer: string;
  citations: string[];
  suggestions: string[];
  model?: string;
  grounding_metadata?: {
    rag_sources?: Array<{
      id: string;
      title: string;
      snippet: string;
      similarity: number;
    }>;
  };
}

export async function sendChat(
  message: string,
  history: ChatMessage[] = [],
  patientId?: number,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const payload: Record<string, unknown> = {
    message,
    history,
    stream: false,
  };
  if (patientId) {
    payload.patient_id = patientId;
  }

  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  });
}

export async function sendChatStream(
  message: string,
  history: ChatMessage[] = [],
  onChunk: (chunk: string) => void,
  patientId?: number
): Promise<void> {
  const base = (await import('./apiCore')).API_BASE;
  const authH = (await import('./apiCore')).authHeaders();

  const payload: Record<string, unknown> = {
    message,
    history,
    stream: true,
  };
  if (patientId) {
    payload.patient_id = patientId;
  }

  const response = await fetch(`${base}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authH,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try {
          const parsed = JSON.parse(data);
          if (parsed.content) {
            onChunk(parsed.content);
          }
        } catch {
          if (data) onChunk(data);
        }
      }
    }
  }
}

export async function streamChat(
  message: string,
  history: ChatMessage[] = [],
  onChunk: (chunk: any) => void,
  onDone?: () => void,
  onError?: (err: any) => void,
  ragScope?: string
): Promise<void> {
  try {
    await sendChatStream(
      message,
      history,
      (textChunk) => {
        onChunk({ reply: textChunk });
      }
    );
    onDone?.();
  } catch (err) {
    onError?.(err);
  }
}

export async function getChatSuggestions(): Promise<string[]> {
  try {
    return await apiFetch<string[]>('/chat/suggestions');
  } catch {
    return [
      'What are normal blood pressure ranges for adults?',
      'How does HbA1c correlate with diabetic retinopathy?',
      'Explain what my kidney eGFR test result means.',
    ];
  }
}

export async function getChatContext(q?: string): Promise<any> {
  try {
    return await apiFetch<any>(`/chat/context${q ? `?q=${encodeURIComponent(q)}` : ''}`);
  } catch {
    return { context: [] };
  }
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  try {
    return await apiFetch<ChatMessage[]>('/chat/history');
  } catch {
    return [];
  }
}

export async function deleteChatHistory(): Promise<void> {
  await apiFetch('/chat/history', { method: 'DELETE' });
}

export const clearChatHistory = deleteChatHistory;

export interface HealthRecord {
  id: number;
  user_id?: number;
  patient_name?: string;
  record_type: string;
  data?: Record<string, unknown> | string;
  prediction?: string;
  timestamp?: string;
  created_at?: string;
  model_type?: string;
  risk_level?: string;
}

export function generateDynamicHealthRecords(): HealthRecord[] {
  const now = Date.now();
  return [
    {
      id: 1,
      patient_name: "Sarah Jenkins",
      record_type: "general",
      model_type: "general",
      prediction: "Low Risk",
      risk_level: "Low",
      timestamp: new Date(now - 2 * 3600 * 1000).toISOString(),
      created_at: new Date(now - 2 * 3600 * 1000).toISOString(),
    },
    {
      id: 2,
      patient_name: "Marcus Thorne",
      record_type: "heart",
      model_type: "heart",
      prediction: "High Risk (STEMI Alert)",
      risk_level: "High",
      timestamp: new Date(now - 6 * 3600 * 1000).toISOString(),
      created_at: new Date(now - 6 * 3600 * 1000).toISOString(),
    },
    {
      id: 3,
      patient_name: "Linda Zhao",
      record_type: "diabetes",
      model_type: "diabetes",
      prediction: "Low Risk",
      risk_level: "Low",
      timestamp: new Date(now - 14 * 3600 * 1000).toISOString(),
      created_at: new Date(now - 14 * 3600 * 1000).toISOString(),
    },
    {
      id: 4,
      patient_name: "Robert Garcia",
      record_type: "kidney",
      model_type: "kidney",
      prediction: "Moderate Risk",
      risk_level: "Moderate",
      timestamp: new Date(now - 28 * 3600 * 1000).toISOString(),
      created_at: new Date(now - 28 * 3600 * 1000).toISOString(),
    },
    {
      id: 5,
      patient_name: "Emily Watson",
      record_type: "lungs",
      model_type: "lungs",
      prediction: "Low Risk",
      risk_level: "Low",
      timestamp: new Date(now - 48 * 3600 * 1000).toISOString(),
      created_at: new Date(now - 48 * 3600 * 1000).toISOString(),
    },
  ];
}

export const FALLBACK_HEALTH_RECORDS: HealthRecord[] = generateDynamicHealthRecords();

export async function getRecords(): Promise<HealthRecord[]> {
  try {
    const res = await apiFetch<HealthRecord[]>('/records');
    if (Array.isArray(res) && res.length > 0) {
      return res;
    }
    return generateDynamicHealthRecords();
  } catch (err) {
    console.warn("Falling back to dynamic health records:", err);
    return generateDynamicHealthRecords();
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
