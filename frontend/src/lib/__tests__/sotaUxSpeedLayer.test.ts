import { SOTAUXSpeedLayerEngine } from '../sotaUxSpeedLayer';

describe('SOTAUXSpeedLayerEngine', () => {
  it('should generate skeleton placeholder state for instant perceived load', () => {
    const engine = new SOTAUXSpeedLayerEngine();
    const skeleton = engine.generateSkeletonState(8);

    expect(skeleton.isLoading).toBe(true);
    expect(skeleton.itemCount).toBe(8);
    expect(skeleton.shimmerClass).toContain('animate-pulse');
  });

  it('should evaluate search input debounce timing correctly', () => {
    const engine = new SOTAUXSpeedLayerEngine();
    const now = Date.now();

    // 100ms ago: debounce required (300ms window)
    expect(engine.isDebounceRequired(now - 100, 300)).toBe(true);

    // 400ms ago: debounce complete
    expect(engine.isDebounceRequired(now - 400, 300)).toBe(false);
  });
});
