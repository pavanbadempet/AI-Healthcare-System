/**
 * In-Memory Token Bucket / Sliding Rate Limiter Middleware
 * Protects edge endpoints against DDoS, brute-force, and noisy neighbors with per-IP tracking and burst capacity.
 */

import { Elysia } from 'elysia';
import { config } from '../config';
import { extractClientIp } from './request_context';

interface TokenBucket {
  tokens: number;
  lastRefill: number; // timestamp in ms
}

export class RateLimiter {
  private buckets = new Map<string, TokenBucket>();
  private maxTokens: number;
  private refillRatePerMs: number;
  private burstCapacity: number;
  private cleanupInterval: Timer | null = null;

  constructor(requestsPerMinute: number = 100, burst: number = 20) {
    this.maxTokens = requestsPerMinute;
    this.burstCapacity = requestsPerMinute + burst;
    // Tokens added per millisecond = limit / (60 * 1000)
    this.refillRatePerMs = requestsPerMinute / 60000;

    // Periodic cleanup of inactive IPs every 2 minutes
    this.cleanupInterval = setInterval(() => this.cleanup(), 120000);
  }

  public check(ip: string): {
    allowed: boolean;
    limit: number;
    remaining: number;
    resetSeconds: number;
    retryAfterSeconds: number;
  } {
    const now = Date.now();
    let bucket = this.buckets.get(ip);

    if (!bucket) {
      bucket = {
        tokens: this.burstCapacity,
        lastRefill: now,
      };
      this.buckets.set(ip, bucket);
    } else {
      // Refill tokens based on elapsed time
      const elapsed = now - bucket.lastRefill;
      const tokensToAdd = elapsed * this.refillRatePerMs;
      bucket.tokens = Math.min(this.burstCapacity, bucket.tokens + tokensToAdd);
      bucket.lastRefill = now;
    }

    const resetSeconds = Math.ceil((this.maxTokens - Math.min(this.maxTokens, bucket.tokens)) / (this.refillRatePerMs * 1000));

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return {
        allowed: true,
        limit: this.maxTokens,
        remaining: Math.floor(bucket.tokens),
        resetSeconds: Math.max(1, resetSeconds),
        retryAfterSeconds: 0,
      };
    } else {
      // Rate limit exceeded
      const tokensNeeded = 1 - bucket.tokens;
      const retryAfterSeconds = Math.ceil(tokensNeeded / (this.refillRatePerMs * 1000));

      return {
        allowed: false,
        limit: this.maxTokens,
        remaining: 0,
        resetSeconds: Math.max(1, resetSeconds),
        retryAfterSeconds: Math.max(1, retryAfterSeconds),
      };
    }
  }

  public reset(): void {
    this.buckets.clear();
  }

  private cleanup(): void {
    const now = Date.now();
    const maxInactiveMs = 5 * 60 * 1000; // 5 minutes
    for (const [ip, bucket] of this.buckets.entries()) {
      if (now - bucket.lastRefill > maxInactiveMs) {
        this.buckets.delete(ip);
      }
    }
  }

  public destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }
}

// Global rate limiter instance
export const rateLimiter = new RateLimiter(
  config.rateLimitPerMinute,
  config.rateLimitBurst
);

export function isRateLimitExempt(pathname: string): boolean {
  if (
    pathname.startsWith('/health') ||
    pathname.startsWith('/healthz') ||
    pathname === '/metrics' ||
    pathname === '/docs' ||
    pathname === '/openapi.json' ||
    pathname.startsWith('/assets/') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.js')
  ) {
    return true;
  }
  return false;
}

export const rateLimitMiddleware = new Elysia({ name: 'middleware:rate-limit' })
  .onRequest(({ request, set }) => {
    const url = new URL(request.url);
    if (isRateLimitExempt(url.pathname)) {
      return;
    }

    const clientIp = extractClientIp(request.headers);
    const result = rateLimiter.check(clientIp);

    set.headers['x-ratelimit-limit'] = result.limit.toString();
    set.headers['x-ratelimit-remaining'] = result.remaining.toString();
    set.headers['x-ratelimit-reset'] = result.resetSeconds.toString();

    if (!result.allowed) {
      set.status = 429;
      set.headers['retry-after'] = result.retryAfterSeconds.toString();
      return {
        error: 'Too Many Requests',
        message: 'Rate limit exceeded. Please try again later.',
        retry_after: result.retryAfterSeconds,
      };
    }
  });
