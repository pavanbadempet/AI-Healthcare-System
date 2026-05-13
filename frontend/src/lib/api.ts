/**
 * AI Healthcare System — API Client
 * 
 * Typed wrapper around all backend endpoints.
 * Auto-injects auth token from Zustand store.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// ── Auth Store Access ────────────────────────────────────────────
let getToken: (() => string | null) | null = null;

export function setTokenGetter(fn: () => string | null) {
  getToken = fn;
}

function authHeaders(): Record<string, string> {
  const token = getToken?.();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

// ── Generic Fetch Wrapper ────────────────────────────────────────
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    let errorMessage = `API Error: ${res.status}`;
    if (body.detail) {
      if (typeof body.detail === 'string') {
        errorMessage = body.detail;
      } else if (Array.isArray(body.detail)) {
        errorMessage = body.detail.map((e: { msg: string; loc?: string[]; type?: string }) => e.msg).join(", ");
      } else {
        errorMessage = JSON.stringify(body.detail);
      }
    }
    throw new Error(errorMessage);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Login failed');
  }
  return res.json();
}

export async function signup(data: {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ username: string }> {
  return apiFetch('/signup', { method: 'POST', body: JSON.stringify(data) });
}

// ── Profile ──────────────────────────────────────────────────────
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  gender?: string;
  dob?: string;
  blood_type?: string;
  height?: string;
  weight?: string;
  about_me?: string;
  profile_picture?: string;
  plan_tier?: string;
}

export async function fetchProfile(): Promise<UserProfile> {
  return apiFetch('/profile');
}

export async function updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
  return apiFetch('/profile', { method: 'PUT', body: JSON.stringify(data) });
}

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

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, history, model, rag_scope: ragScope }),
    signal: controller.signal,
  })
    .then(async (res) => {
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
              onChunk(data);
              if (data.status === 'complete') { onDone(); return; }
              if (data.status === 'error') { onError(data.error || 'Unknown error'); return; }
            } catch { /* skip malformed */ }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message);
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

// ── Predictions ──────────────────────────────────────────────────
export interface PredictionResult {
  prediction: string;
  probability?: number;
  advice?: string[];
  explanation?: string;
}

export async function predictDiabetes(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/diabetes', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictHeart(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/heart', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLiver(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/liver', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictKidney(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/kidney', { method: 'POST', body: JSON.stringify(data) });
}

export async function predictLungs(data: Record<string, number>): Promise<PredictionResult> {
  return apiFetch('/predict/lungs', { method: 'POST', body: JSON.stringify(data) });
}

// ── Admin ────────────────────────────────────────────────────────
export async function getAdminStats(): Promise<Record<string, unknown>> {
  return apiFetch('/admin/stats');
}

export async function getAdminUsers(): Promise<UserProfile[]> {
  return apiFetch('/admin/users');
}

// ── Payments ─────────────────────────────────────────────────────
export interface PaymentOrder {
  id: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentVerification {
  success: boolean;
  message?: string;
  plan_tier?: string;
}

export async function createPaymentOrder(planId: string): Promise<PaymentOrder> {
  return apiFetch('/payments/create-order', { method: 'POST', body: JSON.stringify({ plan_id: planId }) });
}

export async function verifyPayment(data: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }): Promise<PaymentVerification> {
  return apiFetch('/payments/verify', { method: 'POST', body: JSON.stringify(data) });
}

// ── Telemedicine ─────────────────────────────────────────────────
export interface Appointment {
  id: number;
  doctor_id: number;
  appointment_date: string;
  status: string;
  notes?: string;
  doctor?: { name: string; specialization: string };
}

export async function getAppointments(): Promise<Appointment[]> {
  return apiFetch('/appointments/');
}

export async function bookAppointment(data: { doctor_id: number; appointment_date: string; notes?: string }): Promise<Appointment> {
  return apiFetch('/appointments/', { method: 'POST', body: JSON.stringify(data) });
}

export async function getDoctors(): Promise<{ id: number; name: string; specialization: string }[]> {
  return apiFetch('/appointments/doctors');
}
