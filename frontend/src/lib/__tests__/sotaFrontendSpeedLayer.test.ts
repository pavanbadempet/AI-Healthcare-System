import { describe, expect, it } from 'bun:test';
import { SOTAFrontendSpeedLayerEngine } from '../sotaFrontendSpeedLayer';

describe('SOTAFrontendSpeedLayerEngine', () => {
  it('should calculate correct virtual window DOM bounds', () => {
    const engine = new SOTAFrontendSpeedLayerEngine();

    const windowResult = engine.calculateVirtualWindow({
      totalItems: 1000,
      itemHeight: 50,
      containerHeight: 500,
      scrollTop: 1000,
      overscan: 2,
    });

    // 1000 / 50 = item 20. startIndex with overscan 2 = 18.
    expect(windowResult.startIndex).toBe(18);
    expect(windowResult.totalPaddingTop).toBe(18 * 50); // 900px
    expect(windowResult.endIndex).toBeGreaterThan(windowResult.startIndex);
  });

  it('should prefetch routes without duplicate loads', () => {
    const engine = new SOTAFrontendSpeedLayerEngine();

    expect(engine.prefetchRoute('/patients/1001')).toBe(true);
    expect(engine.prefetchRoute('/patients/1001')).toBe(false); // Second prefetch is cached
  });
});
