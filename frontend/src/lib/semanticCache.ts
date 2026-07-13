/**
 * Client-Side Semantic Cache for Clinical Queries
 * Bypasses backend RAG/LLM calls for repeated or highly similar queries asked within a short window.
 * Employs a Jaccard token similarity match with an LRU capacity and safety TTL.
 */

interface CacheEntry {
  query: string;
  tokens: Set<string>;
  reply: string;
  timestamp: number;
}

class ClientSemanticCache {
  private cache: CacheEntry[] = [];
  private maxCapacity: number = 30;
  private ttlMs: number = 45 * 1000; // 45-second lifespan (prevents stale vitals/clinical status readings)
  private similarityThreshold: number = 0.85; // Jaccard similarity index limit

  private tokenize(text: string): Set<string> {
    const clean = text
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    
    const words = clean.split(" ").filter(w => w.length > 1);
    return new Set(words);
  }

  private calculateJaccard(setA: Set<string>, setB: Set<string>): number {
    if (setA.size === 0 || setB.size === 0) return 0;
    
    let intersectionSize = 0;
    for (const item of setA) {
      if (setB.has(item)) {
        intersectionSize++;
      }
    }
    
    const unionSize = setA.size + setB.size - intersectionSize;
    return intersectionSize / unionSize;
  }

  /**
   * Attempts to retrieve a semantically similar cached reply.
   */
  public get(query: string): string | null {
    const now = Date.now();
    const queryTokens = this.tokenize(query);
    if (queryTokens.size === 0) return null;

    // Filter out expired items
    this.cache = this.cache.filter(entry => now - entry.timestamp < this.ttlMs);

    for (let i = 0; i < this.cache.length; i++) {
      const entry = this.cache[i];
      const similarity = this.calculateJaccard(queryTokens, entry.tokens);
      
      if (similarity >= this.similarityThreshold) {
        console.log(`[Semantic Cache] HIT for query: "${query}" (Matched: "${entry.query}", Similarity: ${similarity.toFixed(2)})`);
        // Move to front (MRU)
        this.cache.splice(i, 1);
        entry.timestamp = now; // renew timestamp
        this.cache.unshift(entry);
        return entry.reply;
      }
    }

    return null;
  }

  /**
   * Adds an entry to the cache, evicting the oldest if capacity is exceeded.
   */
  public set(query: string, reply: string): void {
    const queryTokens = this.tokenize(query);
    if (queryTokens.size === 0 || !reply.trim()) return;

    const now = Date.now();
    
    // Remove if already exists to update
    this.cache = this.cache.filter(entry => entry.query.toLowerCase() !== query.toLowerCase());

    const newEntry: CacheEntry = {
      query,
      tokens: queryTokens,
      reply,
      timestamp: now
    };

    this.cache.unshift(newEntry);

    // Evict least recently used if capacity exceeded
    if (this.cache.length > this.maxCapacity) {
      this.cache.pop();
    }

    console.log(`[Semantic Cache] Cached new response for query: "${query}"`);
  }

  /**
   * Clears the entire cache.
   */
  public clear(): void {
    this.cache = [];
    console.log(`[Semantic Cache] Cache cleared.`);
  }
}

export const semanticCache = new ClientSemanticCache();
