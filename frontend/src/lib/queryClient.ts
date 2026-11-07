/**
 * AI Healthcare System — Local-First Query Client
 *
 * Implements local-first TanStack Query v5 architecture with:
 * - offlineFirst networkMode for seamless offline operation
 * - 5-minute staleTime and 24-hour gcTime
 * - IndexedDB persistence with localStorage fallback
 * - Multi-tab synchronization via BroadcastChannel ('ai-healthcare-query-sync')
 */

import { QueryClient, dehydrate, hydrate, type DehydratedState } from '@tanstack/react-query';

const DB_NAME = 'AiHealthcareQueryDb';
const DB_VERSION = 1;
const STORE_NAME = 'query_cache';
const CACHE_KEY = 'ai_healthcare_query_state_v1';
const SYNC_CHANNEL_NAME = 'ai-healthcare-query-sync';

// Unique identifier for current tab to prevent self-broadcast reflection loops
const currentTabId = typeof crypto !== 'undefined' && crypto.randomUUID
  ? crypto.randomUUID()
  : Math.random().toString(36).substring(2, 11);

// ── Multi-Tab Sync BroadcastChannel ──────────────────────────────
let syncChannel: BroadcastChannel | null = null;
if (typeof window !== 'undefined' && typeof BroadcastChannel !== 'undefined') {
  try {
    syncChannel = new BroadcastChannel(SYNC_CHANNEL_NAME);
  } catch (err) {
    console.warn('[QuerySync] BroadcastChannel unavailable:', err);
  }
}

/**
 * Broadcast query invalidation across all open browser tabs
 */
export function broadcastQueryInvalidation(queryKey: readonly unknown[] | unknown[]) {
  if (!syncChannel) return;
  try {
    syncChannel.postMessage({
      type: 'INVALIDATE_QUERY',
      queryKey,
      tabId: currentTabId,
      timestamp: Date.now(),
    });
  } catch (err) {
    console.warn('[QuerySync] Failed to post invalidation message:', err);
  }
}

// ── IndexedDB Storage Helpers ─────────────────────────────────────
function isIndexedDbAvailable(): boolean {
  return typeof window !== 'undefined' && 'indexedDB' in window && window.indexedDB !== null;
}

function openCacheDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!isIndexedDbAvailable()) {
      return reject(new Error('IndexedDB not available'));
    }
    const req = window.indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function getStoredState(): Promise<DehydratedState | null> {
  if (isIndexedDbAvailable()) {
    try {
      const db = await openCacheDatabase();
      return await new Promise<DehydratedState | null>((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.get(CACHE_KEY);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch {
      // Fall through to localStorage
    }
  }

  // Fallback to localStorage
  if (typeof window !== 'undefined' && window.localStorage) {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (raw) return JSON.parse(raw);
    } catch {
      // Storage unavailable or quota exceeded
    }
  }
  return null;
}

async function saveStoredState(state: DehydratedState): Promise<void> {
  if (isIndexedDbAvailable()) {
    try {
      const db = await openCacheDatabase();
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.put(state, CACHE_KEY);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
      return;
    } catch {
      // Fall through to localStorage
    }
  }

  if (typeof window !== 'undefined' && window.localStorage) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(state));
    } catch {
      // Quota exceeded or private browsing
    }
  }
}

// ── QueryClient Configuration ────────────────────────────────────
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,          // 5 minutes freshness window
      gcTime: 1000 * 60 * 60 * 24,       // 24 hours retention
      networkMode: 'offlineFirst',       // Local-first: serve cache immediately offline
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
      retry: 2,
      structuralSharing: true,
    },
    mutations: {
      networkMode: 'offlineFirst',       // Local-first: queue mutations if offline
      retry: 2,
    },
  },
});

// ── Multi-Tab Invalidation Listener ──────────────────────────────
if (syncChannel) {
  syncChannel.onmessage = (event) => {
    const data = event.data;
    if (data && data.type === 'INVALIDATE_QUERY' && data.tabId !== currentTabId && data.queryKey) {
      void queryClient.invalidateQueries({ queryKey: data.queryKey });
    }
  };
}

// ── Persistence Setup ────────────────────────────────────────────
let persistenceInitialized = false;

export async function initQueryClientPersistence(): Promise<void> {
  if (persistenceInitialized || typeof window === 'undefined') return;
  persistenceInitialized = true;

  try {
    const savedState = await getStoredState();
    if (savedState) {
      hydrate(queryClient, savedState);
    }
  } catch (err) {
    console.warn('[QueryPersist] Failed to restore cached queries:', err);
  }

  // Debounced cache persistence on successful query/mutation settles
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  const triggerSave = () => {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      try {
        const dehydrated = dehydrate(queryClient, {
          shouldDehydrateQuery: (query) => {
            // Persist queries that have succeeded and have data
            return query.state.status === 'success' && query.state.data !== undefined;
          },
        });
        await saveStoredState(dehydrated);
      } catch (err) {
        console.warn('[QueryPersist] Failed to save queries:', err);
      }
    }, 1000);
  };

  queryClient.getQueryCache().subscribe((event) => {
    if (event.type === 'updated' && event.action.type === 'success') {
      triggerSave();
    }
  });
}

// Automatically initiate persistence in browser environments
if (typeof window !== 'undefined') {
  void initQueryClientPersistence();
}

/**
 * Factory for creating clean isolated QueryClients in test suites
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 0,
        gcTime: 0,
        networkMode: 'always',
        retry: false,
      },
      mutations: {
        networkMode: 'always',
        retry: false,
      },
    },
  });
}
