import { describe, it, expect } from 'bun:test';
import { RateLimiter, isRateLimitExempt } from '../src/middleware/rate_limiter';

describe('Token Bucket Rate Limiter', () => {
  it('allows requests within limit and tracks remaining quota', () => {
    const limiter = new RateLimiter(10, 0); // 10 req/min, 0 burst
    const ip = '192.168.1.100';

    const first = limiter.check(ip);
    expect(first.allowed).toBe(true);
    expect(first.limit).toBe(10);
    expect(first.remaining).toBe(9);

    const second = limiter.check(ip);
    expect(second.allowed).toBe(true);
    expect(second.remaining).toBe(8);

    limiter.destroy();
  });

  it('rejects requests when rate limit is exhausted and provides retry-after', () => {
    const limiter = new RateLimiter(3, 0); // 3 req/min
    const ip = '192.168.1.101';

    expect(limiter.check(ip).allowed).toBe(true);
    expect(limiter.check(ip).allowed).toBe(true);
    expect(limiter.check(ip).allowed).toBe(true);

    const blocked = limiter.check(ip);
    expect(blocked.allowed).toBe(false);
    expect(blocked.remaining).toBe(0);
    expect(blocked.retryAfterSeconds).toBeGreaterThan(0);

    limiter.destroy();
  });

  it('allows burst capacity beyond base limit', () => {
    const limiter = new RateLimiter(5, 5); // 5 base + 5 burst = 10 total capacity
    const ip = '192.168.1.102';

    let count = 0;
    for (let i = 0; i < 10; i++) {
      if (limiter.check(ip).allowed) {
        count++;
      }
    }
    expect(count).toBe(10);

    // 11th request is blocked
    expect(limiter.check(ip).allowed).toBe(false);

    limiter.destroy();
  });

  it('identifies exempt paths correctly', () => {
    expect(isRateLimitExempt('/health')).toBe(true);
    expect(isRateLimitExempt('/healthz')).toBe(true);
    expect(isRateLimitExempt('/healthz/live')).toBe(true);
    expect(isRateLimitExempt('/metrics')).toBe(true);
    expect(isRateLimitExempt('/docs')).toBe(true);
    expect(isRateLimitExempt('/openapi.json')).toBe(true);
    expect(isRateLimitExempt('/assets/main.js')).toBe(true);
    expect(isRateLimitExempt('/favicon.ico')).toBe(true);

    expect(isRateLimitExempt('/v1/predict/diabetes')).toBe(false);
    expect(isRateLimitExempt('/v1/token')).toBe(false);
    expect(isRateLimitExempt('/api/patients')).toBe(false);
  });
});
