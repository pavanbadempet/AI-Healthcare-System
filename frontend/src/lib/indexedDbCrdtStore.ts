/**
 * IndexedDB CRDT Store for Zero-Network Offline Clinical Resilience.
 *
 * Provides persistent local storage for decentralized patient charts,
 * delta mutations, and vector clocks, synchronizing transparently with
 * the backend's /v1/resilience/crdt/merge-sync endpoint.
 */

export interface LocalCrdtChart {
  patientId: string;
  allergies: string[];
  medications: string[];
  vitals: Record<string, { value: number | string; timestamp_us: number; node_id: string }>;
  vectorClock: Record<string, number>;
  updatedAt: number;
}

export interface OfflineMutation {
  id: string;
  patientId: string;
  nodeId: string;
  operation: 'add_allergy' | 'remove_allergy' | 'add_medication' | 'remove_medication' | 'record_vital';
  entity: string;
  value?: any;
  timestampUs: number;
  synced: boolean;
}

const DB_NAME = 'ClinicalOfflineDb';
const DB_VERSION = 1;
const STORE_CHARTS = 'patient_charts';
const STORE_MUTATIONS = 'pending_mutations';

// In-memory fallback for SSR/Vitest environments where IndexedDB is mocked or absent
const memoryCharts = new Map<string, LocalCrdtChart>();
const memoryMutations = new Map<string, OfflineMutation>();

function isIndexedDbSupported(): boolean {
  return typeof window !== 'undefined' && 'indexedDB' in window;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!isIndexedDbSupported()) {
      return reject(new Error('IndexedDB not supported in current environment'));
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_CHARTS)) {
        db.createObjectStore(STORE_CHARTS, { keyPath: 'patientId' });
      }
      if (!db.objectStoreNames.contains(STORE_MUTATIONS)) {
        const mutStore = db.createObjectStore(STORE_MUTATIONS, { keyPath: 'id' });
        mutStore.createIndex('patientId', 'patientId', { unique: false });
        mutStore.createIndex('synced', 'synced', { unique: false });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Save or update a patient chart in the local offline store.
 */
export async function saveLocalCrdtChart(chart: LocalCrdtChart): Promise<void> {
  if (!isIndexedDbSupported()) {
    memoryCharts.set(chart.patientId, chart);
    return;
  }

  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_CHARTS, 'readwrite');
      const store = tx.objectStore(STORE_CHARTS);
      const req = store.put(chart);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  } catch {
    memoryCharts.set(chart.patientId, chart);
  }
}

/**
 * Retrieve a patient chart from the local offline store.
 */
export async function getLocalCrdtChart(patientId: string): Promise<LocalCrdtChart | null> {
  if (!isIndexedDbSupported()) {
    return memoryCharts.get(patientId) || null;
  }

  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_CHARTS, 'readonly');
      const store = tx.objectStore(STORE_CHARTS);
      const req = store.get(patientId);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  } catch {
    return memoryCharts.get(patientId) || null;
  }
}

/**
 * Queue a mutation generated while offline for subsequent synchronization.
 */
export async function queueOfflineMutation(mutation: OfflineMutation): Promise<void> {
  if (!isIndexedDbSupported()) {
    memoryMutations.set(mutation.id, mutation);
    return;
  }

  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_MUTATIONS, 'readwrite');
      const store = tx.objectStore(STORE_MUTATIONS);
      const req = store.put(mutation);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  } catch {
    memoryMutations.set(mutation.id, mutation);
  }
}

/**
 * Retrieve all unsynced mutations queued while disconnected.
 */
export async function getUnsyncedMutations(): Promise<OfflineMutation[]> {
  if (!isIndexedDbSupported()) {
    return Array.from(memoryMutations.values()).filter((m) => !m.synced);
  }

  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_MUTATIONS, 'readonly');
      const store = tx.objectStore(STORE_MUTATIONS);
      const req = store.getAll();
      req.onsuccess = () => {
        const all = (req.result as OfflineMutation[]) || [];
        resolve(all.filter((m) => !m.synced));
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    return Array.from(memoryMutations.values()).filter((m) => !m.synced);
  }
}

/**
 * Mark a queued mutation as committed and remove it from the backlog.
 */
export async function clearSyncedMutation(id: string): Promise<void> {
  if (!isIndexedDbSupported()) {
    memoryMutations.delete(id);
    return;
  }

  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_MUTATIONS, 'readwrite');
      const store = tx.objectStore(STORE_MUTATIONS);
      const req = store.delete(id);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  } catch {
    memoryMutations.delete(id);
  }
}
