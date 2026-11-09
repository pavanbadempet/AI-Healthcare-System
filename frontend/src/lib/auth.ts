/**
 * AI Healthcare System — Auth Store (Zustand)
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { setTokenGetter, type UserProfile } from './api';

export const DEFAULT_DEMO_CLINICIAN: UserProfile = {
  id: 4,
  username: "staff_clinician",
  full_name: "Staff Clinician",
  email: "clinician@healthcare-system.local",
  role: "doctor",
};

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  setAuth: (token: string, user: UserProfile) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

const memoryStore = new Map<string, string>();

const safeStorage = createJSONStorage(() => {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.getItem('test');
      return window.localStorage;
    }
  } catch {
    // Storage restricted (e.g. iframe partitioning)
  }
  return {
    getItem: (key: string) => memoryStore.get(key) ?? null,
    setItem: (key: string, value: string) => memoryStore.set(key, value),
    removeItem: (key: string) => memoryStore.delete(key),
  };
});

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: "demo-clinician-session-token",
      user: DEFAULT_DEMO_CLINICIAN,
      setAuth: (token, user) => set({ token, user }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'healthcare-auth',
      storage: safeStorage,
    }
  )
);

// Wire up the API client to read the token from the store
if (typeof window !== 'undefined') {
  setTokenGetter(() => useAuthStore.getState().token);
}
