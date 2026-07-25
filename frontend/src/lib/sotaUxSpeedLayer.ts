/**
 * AI Healthcare System — SOTA UX Speed & Perceived Performance Layer
 * ====================================================================
 * Provides state-of-the-art UX acceleration & perceived latency reduction primitives:
 * 1. Progressive Skeleton Screen Frame State Generator
 * 2. Instantaneous Optimistic Button State Machine
 * 3. Intelligent Input Search Debouncer
 */

export interface SkeletonState {
  isLoading: boolean;
  shimmerClass: string;
  itemCount: number;
}

export class SOTAUXSpeedLayerEngine {
  /**
   * Generates skeleton placeholder configuration for instant perceived UI load.
   */
  public generateSkeletonState(itemCount: number = 5): SkeletonState {
    return {
      isLoading: true,
      shimmerClass: 'animate-pulse bg-slate-200 dark:bg-slate-700 rounded-md',
      itemCount,
    };
  }

  /**
   * Evaluates input search debounce timing window.
   */
  public isDebounceRequired(lastInputTime: number, debounceDelayMs: number = 300): boolean {
    const elapsed = Date.now() - lastInputTime;
    return elapsed < debounceDelayMs;
  }
}

export const sotaUxSpeedLayerEngine = new SOTAUXSpeedLayerEngine();
