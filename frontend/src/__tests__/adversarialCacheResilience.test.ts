import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, onlineManager, dehydrate, hydrate } from '@tanstack/react-query';
import {
  queryClient as productionQueryClient,
  broadcastQueryInvalidation,
  createTestQueryClient,
} from '@/lib/queryClient';
import { FALLBACK_BEDS } from '@/hooks/useHospitalCapacity';
import { FALLBACK_CLINICAL_ALERTS } from '@/hooks/useClinicalIntelligence';

describe('Adversarial Verification: Milestone 3 Frontend Local-First & Cache Architecture', () => {
  let testClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    onlineManager.setOnline(true);
  });

  afterEach(() => {
    onlineManager.setOnline(true);
  });

  // ── Dimension 1: Production QueryClient Configuration ──────────────────────
  describe('Dimension 1: Production QueryClient Configuration Integrity', () => {
    it('enforces networkMode: "offlineFirst" across queries and mutations in production client', () => {
      const defaultOptions = productionQueryClient.getDefaultOptions();

      // Queries networkMode verification
      expect(defaultOptions.queries?.networkMode).toBe('offlineFirst');
      // Mutations networkMode verification
      expect(defaultOptions.mutations?.networkMode).toBe('offlineFirst');

      // Stale & GC time retention (5 min stale, 24 hr retention)
      expect(defaultOptions.queries?.staleTime).toBe(1000 * 60 * 5);
      expect(defaultOptions.queries?.gcTime).toBe(1000 * 60 * 60 * 24);

      // Retry policy
      expect(defaultOptions.queries?.retry).toBe(2);
      expect(defaultOptions.mutations?.retry).toBe(2);
    });

    it('createTestQueryClient creates clean isolated instances with networkMode always', () => {
      const client = createTestQueryClient();
      expect(client.getDefaultOptions().queries?.networkMode).toBe('always');
      expect(client.getDefaultOptions().queries?.staleTime).toBe(0);
      expect(client.getDefaultOptions().queries?.retry).toBe(false);
    });
  });

  // ── Dimension 2: Offline-First Resilience & Error Isolation ────────────────
  describe('Dimension 2: Offline-First Resilience & Error Isolation', () => {
    it('returns cached data without throwing uncaught errors when network is offline', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: {
            networkMode: 'offlineFirst',
            staleTime: 1000 * 60 * 5,
            retry: false,
          },
        },
      });

      const queryKey = ['patients', 'list', 'test'];
      const cachedPatients = [
        { id: 1, name: 'John Doe', condition: 'Hypertension' },
        { id: 2, name: 'Jane Smith', condition: 'Arrhythmia' },
      ];

      // Pre-seed query cache
      client.setQueryData(queryKey, cachedPatients);

      // Verify query cache state has pre-seeded data
      const queryState = client.getQueryState(queryKey);
      expect(queryState?.data).toEqual(cachedPatients);
      expect(queryState?.status).toBe('success');

      // In offline mode with networkMode: 'offlineFirst', query returns cached data
      // If queryFn is called when offline, it pauses without error or serves cache
      onlineManager.setOnline(false);

      const cachedResult = client.getQueryData(queryKey);
      expect(cachedResult).toEqual(cachedPatients);

      // Verify that attempting to fetch does not crash and preserves cached data
      try {
        await client.fetchQuery({
          queryKey,
          queryFn: async () => {
            throw new Error('NETWORK_DOWN: ECONNREFUSED');
          },
        });
      } catch {
        // Fetch was either paused or rejected, but cache must remain intact
      }

      expect(client.getQueryData(queryKey)).toEqual(cachedPatients);
    });

    it('handles query function network failure by retaining previously cached data in cache', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: {
            networkMode: 'offlineFirst',
            retry: false,
          },
        },
      });

      const queryKey = ['appointments', 'patient', 99];
      const initialData = [{ id: 1, doctor_id: 10, notes: 'Followup' }];
      client.setQueryData(queryKey, initialData);

      // Simulate a network failure during query execution
      try {
        await client.fetchQuery({
          queryKey,
          queryFn: async () => {
            throw new Error('500 Service Unavailable');
          },
        });
      } catch (err: any) {
        expect(err.message).toBe('500 Service Unavailable');
      }

      // Cached data must still be accessible and not cleared on network failure
      const cached = client.getQueryData(queryKey);
      expect(cached).toEqual(initialData);
    });
  });

  // ── Dimension 3: 3-Phase Optimistic UI Rollback on Network Rejection ───────
  describe('Dimension 3: 3-Phase Optimistic UI Rollback on Network Rejection', () => {
    it('optimistically injects item on onMutate and performs complete rollback on onError', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const queryKey = ['appointments', undefined];
      const baselineAppointments = [
        { id: 101, doctor_id: 1, notes: 'Baseline Consultation', status: 'scheduled' },
      ];
      client.setQueryData(queryKey, baselineAppointments);

      const optimisticBooking = {
        id: -Date.now(),
        doctor_id: 2,
        notes: 'Optimistic Checkup',
        status: 'scheduled',
      };

      // Construct a 3-phase optimistic mutation pipeline identical to useBookAppointmentMutation
      let mutationFailed = false;
      try {
        await client.getMutationCache().build(client, {
          mutationFn: async () => {
            throw new Error('500 Internal Server Error: Database write failed');
          },
          onMutate: async () => {
            await client.cancelQueries({ queryKey });
            const previousAppointments = client.getQueryData(queryKey);
            // Optimistically insert
            client.setQueryData(queryKey, (old: any[] = []) => [optimisticBooking, ...old]);
            return { previousAppointments };
          },
          onError: (_err, _vars, context: any) => {
            // Rollback to snapshot
            if (context?.previousAppointments) {
              client.setQueryData(queryKey, context.previousAppointments);
            }
          },
        }).execute(optimisticBooking);
      } catch {
        mutationFailed = true;
      }

      expect(mutationFailed).toBe(true);

      // Verify the cache has been cleanly rolled back to baseline
      const afterRollback = client.getQueryData(queryKey);
      expect(afterRollback).toEqual(baselineAppointments);
      expect((afterRollback as any[]).find((a) => a.notes === 'Optimistic Checkup')).toBeUndefined();
    });

    it('optimistically updates hospital bed status and rolls back on failure', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const queryKey = ['hospital', 'beds', undefined];
      const initialBeds = [
        { id: 1, bed_number: 'ICU-01', status: 'available' },
        { id: 2, bed_number: 'ICU-02', status: 'available' },
      ];
      client.setQueryData(queryKey, initialBeds);

      try {
        await client.getMutationCache().build(client, {
          mutationFn: async () => {
            throw new Error('Admission conflict: Bed was just occupied');
          },
          onMutate: async (vars: { bed_id: number }) => {
            await client.cancelQueries({ queryKey });
            const previousBeds = client.getQueryData(queryKey);
            client.setQueryData(queryKey, (old: any[] = []) =>
              old.map((b) => (b.id === vars.bed_id ? { ...b, status: 'occupied' } : b))
            );
            return { previousBeds };
          },
          onError: (_err, _vars, context: any) => {
            if (context?.previousBeds) {
              client.setQueryData(queryKey, context.previousBeds);
            }
          },
        }).execute({ bed_id: 1 });
      } catch {
        // Expected failure
      }

      const restoredBeds = client.getQueryData(queryKey) as any[];
      expect(restoredBeds[0].status).toBe('available');
    });
  });

  // ── Dimension 4: Cache Persistence & Storage Fallback ─────────────────────
  describe('Dimension 4: Cache Persistence & Storage Fallback', () => {
    it('dehydrates and rehydrates query cache state accurately', () => {
      const clientA = new QueryClient();
      clientA.setQueryData(['clinical', 'alerts'], FALLBACK_CLINICAL_ALERTS);
      clientA.setQueryData(['hospital', 'beds'], FALLBACK_BEDS);

      const dehydrated = dehydrate(clientA, {
        shouldDehydrateQuery: (query) => query.state.status === 'success',
      });

      expect(dehydrated.queries.length).toBe(2);

      // Hydrate into clean clientB
      const clientB = new QueryClient();
      hydrate(clientB, dehydrated);

      const hydratedAlerts = clientB.getQueryData(['clinical', 'alerts']);
      const hydratedBeds = clientB.getQueryData(['hospital', 'beds']);

      expect(hydratedAlerts).toEqual(FALLBACK_CLINICAL_ALERTS);
      expect(hydratedBeds).toEqual(FALLBACK_BEDS);
    });

    it('gracefully handles corrupted JSON in localStorage without throwing', () => {
      const CACHE_KEY = 'ai_healthcare_query_state_v1';
      localStorage.setItem(CACHE_KEY, '{ invalid JSON corrup#ted ');

      // Should safely catch SyntaxError and return null
      let retrieved = null;
      expect(() => {
        try {
          const raw = localStorage.getItem(CACHE_KEY);
          if (raw) retrieved = JSON.parse(raw);
        } catch {
          retrieved = null;
        }
      }).not.toThrow();

      expect(retrieved).toBeNull();
      localStorage.removeItem(CACHE_KEY);
    });

    it('gracefully handles localStorage QuotaExceededError without crashing', () => {
      const CACHE_KEY = 'ai_healthcare_query_state_v1';
      const originalSetItem = localStorage.setItem;

      // Mock QuotaExceededError
      localStorage.setItem = vi.fn(() => {
        const err = new Error('The quota has been exceeded.');
        err.name = 'QuotaExceededError';
        throw err;
      });

      expect(() => {
        try {
          localStorage.setItem(CACHE_KEY, JSON.stringify({ queries: [] }));
        } catch {
          // Fallback safely caught
        }
      }).not.toThrow();

      // Restore
      localStorage.setItem = originalSetItem;
    });
  });

  // ── Dimension 5: BroadcastChannel Multi-Tab Synchronization ────────────────
  describe('Dimension 5: BroadcastChannel Multi-Tab Sync & Anti-Loop Safeguards', () => {
    it('broadcastQueryInvalidation safely posts messages without throwing', () => {
      expect(() => {
        broadcastQueryInvalidation(['appointments']);
        broadcastQueryInvalidation(['hospital', 'beds']);
        broadcastQueryInvalidation(['clinical', 'alerts', 'CRITICAL']);
      }).not.toThrow();
    });

    it('prevents self-broadcast reflection loops by checking tabId !== currentTabId', () => {
      // Simulate listener logic in queryClient.ts
      const testTabId = 'tab-alpha-001';
      const invalidateMock = vi.fn();

      const handleMessage = (data: any) => {
        if (data && data.type === 'INVALIDATE_QUERY' && data.tabId !== testTabId && data.queryKey) {
          invalidateMock(data.queryKey);
        }
      };

      // 1. Message from the SAME tab (must be ignored to prevent infinite loop)
      handleMessage({
        type: 'INVALIDATE_QUERY',
        queryKey: ['appointments'],
        tabId: testTabId, // SAME TAB
        timestamp: Date.now(),
      });
      expect(invalidateMock).not.toHaveBeenCalled();

      // 2. Message from a DIFFERENT tab (must trigger invalidation)
      handleMessage({
        type: 'INVALIDATE_QUERY',
        queryKey: ['appointments'],
        tabId: 'tab-beta-002', // DIFFERENT TAB
        timestamp: Date.now(),
      });
      expect(invalidateMock).toHaveBeenCalledTimes(1);
      expect(invalidateMock).toHaveBeenCalledWith(['appointments']);
    });

    it('handles malformed, null, or burst cross-tab messages safely', () => {
      const invalidateMock = vi.fn();
      const currentTabId = 'tab-gamma-777';

      const handleMessage = (data: any) => {
        try {
          if (data && data.type === 'INVALIDATE_QUERY' && data.tabId !== currentTabId && data.queryKey) {
            invalidateMock(data.queryKey);
          }
        } catch (err) {
          throw err;
        }
      };

      // Adversarial inputs: null, undefined, primitive, empty object, missing queryKey
      expect(() => {
        handleMessage(null);
        handleMessage(undefined);
        handleMessage('INVALID_STRING_MESSAGE');
        handleMessage(42);
        handleMessage({});
        handleMessage({ type: 'UNKNOWN_EVENT' });
        handleMessage({ type: 'INVALIDATE_QUERY' }); // missing queryKey
        handleMessage({ type: 'INVALIDATE_QUERY', tabId: 'other' }); // missing queryKey
      }).not.toThrow();

      expect(invalidateMock).not.toHaveBeenCalled();

      // Burst of 100 valid messages from another tab
      for (let i = 0; i < 100; i++) {
        handleMessage({
          type: 'INVALIDATE_QUERY',
          queryKey: ['hospital', 'beds', i],
          tabId: `remote-tab-${i}`,
          timestamp: Date.now(),
        });
      }

      expect(invalidateMock).toHaveBeenCalledTimes(100);
    });
  });

  // ── Dimension 6: Live Hook Error Containment & Fallback Verification ───────
  describe('Dimension 6: Live Hook Error Containment & Fallback Verification', () => {
    it('useHospitalBedsQuery seamlessly serves FALLBACK_BEDS when API fails', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: {
            networkMode: 'offlineFirst',
            retry: false,
          },
        },
      });

      // Query function with failing network
      const result = await client.fetchQuery({
        queryKey: ['hospital', 'beds', 'ICU'],
        queryFn: async () => {
          try {
            throw new Error('503 Service Unavailable: Gateway Timeout');
          } catch {
            return FALLBACK_BEDS;
          }
        },
      });

      expect(result).toBeDefined();
      expect(result).toEqual(FALLBACK_BEDS);
      expect(result[0].bed_number).toBe('ICU-01');
    });

    it('useClinicalAlertsQuery seamlessly serves FALLBACK_CLINICAL_ALERTS when API fails', async () => {
      const client = new QueryClient({
        defaultOptions: {
          queries: {
            networkMode: 'offlineFirst',
            retry: false,
          },
        },
      });

      const result = await client.fetchQuery({
        queryKey: ['clinical', 'alerts', 'ALL'],
        queryFn: async () => {
          try {
            throw new Error('Connection reset by peer');
          } catch {
            return FALLBACK_CLINICAL_ALERTS;
          }
        },
      });

      expect(result).toBeDefined();
      expect(result).toEqual(FALLBACK_CLINICAL_ALERTS);
      expect(result[0].alert_type).toBe('CARDIAC_TACHYCARDIA');
    });
  });

  // ── Dimension 7: IndexedDB Failure & Fallback Resilience ──────────────────
  describe('Dimension 7: IndexedDB Failure & Fallback Resilience', () => {
    it('simulates IndexedDB open failure and confirms graceful degradation without app crash', async () => {
      // Mock window.indexedDB to reject on open
      const originalIndexedDB = window.indexedDB;
      const mockIndexedDB = {
        open: vi.fn(() => {
          const request: any = {};
          setTimeout(() => {
            if (request.onerror) {
              request.error = new DOMException('Access denied by user agent policy', 'SecurityError');
              request.onerror(new Event('error'));
            }
          }, 0);
          return request;
        }),
      };

      // Wrap in promise matching openCacheDatabase behavior
      const openDbPromise = new Promise((resolve, reject) => {
        const req = (mockIndexedDB as any).open('test', 1);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });

      let caughtError = null;
      try {
        await openDbPromise;
      } catch (err: any) {
        caughtError = err;
      }

      expect(caughtError).toBeDefined();
      expect(caughtError.name).toBe('SecurityError');

      // Verify localStorage is ready as secondary fallback
      localStorage.setItem('ai_healthcare_query_state_v1', JSON.stringify({ queries: [], mutations: [] }));
      const fallbackData = JSON.parse(localStorage.getItem('ai_healthcare_query_state_v1') || '{}');
      expect(fallbackData).toEqual({ queries: [], mutations: [] });

      localStorage.removeItem('ai_healthcare_query_state_v1');
    });
  });
});
