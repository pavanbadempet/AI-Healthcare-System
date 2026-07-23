/**
 * Frontend Code-Level Hyper-Optimization Utilities
 * =================================================
 * Provides:
 * - FastDomBatcher: Batches DOM reads and writes via requestAnimationFrame to eliminate layout thrashing.
 * - ZeroAllocationArrayPool: Object pool for arrays in continuous canvas/ECG rendering loops.
 */

export class FastDomBatcher {
  private readQueue: Array<() => void> = [];
  private writeQueue: Array<() => void> = [];
  private isScheduled: boolean = false;

  public read(fn: () => void): void {
    this.readQueue.push(fn);
    this.scheduleFlush();
  }

  public write(fn: () => void): void {
    this.writeQueue.push(fn);
    this.scheduleFlush();
  }

  private scheduleFlush(): void {
    if (!this.isScheduled) {
      this.isScheduled = true;
      requestAnimationFrame(() => this.flush());
    }
  }

  private flush(): void {
    // 1. Execute all layout reads first
    const reads = this.readQueue.splice(0, this.readQueue.length);
    for (const readFn of reads) {
      try {
        readFn();
      } catch (e) {
        console.error("FastDomBatcher read error:", e);
      }
    }

    // 2. Execute all DOM writes second (prevents layout thrashing/reflow loops)
    const writes = this.writeQueue.splice(0, this.writeQueue.length);
    for (const writeFn of writes) {
      try {
        writeFn();
      } catch (e) {
        console.error("FastDomBatcher write error:", e);
      }
    }

    this.isScheduled = false;
  }
}

export class ZeroAllocationArrayPool<T = number> {
  private pool: Array<Array<T>> = [];

  constructor(private defaultCapacity: number = 512, poolSize: number = 16) {
    for (let i = 0; i < poolSize; i++) {
      this.pool.push(new Array<T>(defaultCapacity));
    }
  }

  public acquire(): Array<T> {
    const arr = this.pool.pop();
    if (arr) {
      arr.length = 0;
      return arr;
    }
    return new Array<T>(this.defaultCapacity);
  }

  public release(arr: Array<T>): void {
    if (this.pool.length < 16) {
      arr.length = 0;
      this.pool.push(arr);
    }
  }
}

export const fastDomBatcher = new FastDomBatcher();
export const zeroAllocationArrayPool = new ZeroAllocationArrayPool();
