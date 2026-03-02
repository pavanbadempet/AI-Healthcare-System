/**
 * AI Healthcare System — Auth Store (Zustand)
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { setTokenGetter, type UserProfile } from './api';

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  setAuth: (token: string, user: UserProfile) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
      isAuthenticated: () => !!get().token,
    }),
    { name: 'healthcare-auth' }
  )
);

// Wire up the API client to read the token from the store
if (typeof window !== 'undefined') {
  setTokenGetter(() => useAuthStore.getState().token);
}
