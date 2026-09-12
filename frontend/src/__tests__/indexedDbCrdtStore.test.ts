import { describe, it, expect } from 'vitest';
import {
  saveLocalCrdtChart,
  getLocalCrdtChart,
  queueOfflineMutation,
  getUnsyncedMutations,
  clearSyncedMutation,
  type LocalCrdtChart,
  type OfflineMutation,
} from '@/lib/indexedDbCrdtStore';

describe('IndexedDB CRDT Store', () => {
  it('saves and retrieves patient chart in local store', async () => {
    const chart: LocalCrdtChart = {
      patientId: 'PT-OFFLINE-99',
      allergies: ['Penicillin', 'Sulfa'],
      medications: ['Aspirin 81mg'],
      vitals: {
        heart_rate: { value: 72, timestamp_us: 1000000, node_id: 'LOCAL-NODE' },
      },
      vectorClock: { 'LOCAL-NODE': 3 },
      updatedAt: Date.now(),
    };

    await saveLocalCrdtChart(chart);
    const retrieved = await getLocalCrdtChart('PT-OFFLINE-99');

    expect(retrieved).not.toBeNull();
    expect(retrieved?.patientId).toBe('PT-OFFLINE-99');
    expect(retrieved?.allergies).toContain('Penicillin');
    expect(retrieved?.vitals.heart_rate.value).toBe(72);
  });

  it('queues offline mutations and clears upon sync', async () => {
    const mutation: OfflineMutation = {
      id: 'mut-1001',
      patientId: 'PT-OFFLINE-99',
      nodeId: 'LOCAL-AMB',
      operation: 'add_allergy',
      entity: 'Latex',
      timestampUs: Date.now() * 1000,
      synced: false,
    };

    await queueOfflineMutation(mutation);
    const pending = await getUnsyncedMutations();

    const match = pending.find((m) => m.id === 'mut-1001');
    expect(match).toBeDefined();
    expect(match?.entity).toBe('Latex');

    await clearSyncedMutation('mut-1001');
    const remaining = await getUnsyncedMutations();
    expect(remaining.find((m) => m.id === 'mut-1001')).toBeUndefined();
  });
});
