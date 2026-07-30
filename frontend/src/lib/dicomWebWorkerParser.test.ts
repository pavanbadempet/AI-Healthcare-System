import { describe, expect, it } from 'vitest';
import { DicomWorkerThreadManager } from './dicomWebWorkerParser';

describe('DicomWorkerThreadManager', () => {
  it('parses DICOM volume slices off main thread asynchronously', async () => {
    const manager = new DicomWorkerThreadManager();
    const buffer = new ArrayBuffer(1024);
    const slices = await manager.parseDicomVolumeAsync(buffer, 64, 64, 4);

    expect(slices.length).toBe(4);
    expect(slices[0].width).toBe(64);
    expect(slices[0].height).toBe(64);
    expect(slices[0].pixelData.length).toBe(4096);
  });
});
