import { describe, expect, test, afterAll } from 'bun:test';
import {
  calculatePercentiles,
  startMockServer,
  benchmarkEndpoint,
  runBenchmarkSuite,
  formatBenchmarkCard,
} from './benchmark_system';

describe('benchmark_system.ts Unit Tests', () => {
  describe('calculatePercentiles', () => {
    test('handles empty array safely', () => {
      const p = calculatePercentiles([]);
      expect(p.min).toBe(0);
      expect(p.max).toBe(0);
      expect(p.mean).toBe(0);
      expect(p.p50).toBe(0);
      expect(p.p75).toBe(0);
      expect(p.p90).toBe(0);
      expect(p.p95).toBe(0);
      expect(p.p99).toBe(0);
      expect(p.stdDev).toBe(0);
    });

    test('handles single value correctly', () => {
      const p = calculatePercentiles([42.5]);
      expect(p.min).toBe(42.5);
      expect(p.max).toBe(42.5);
      expect(p.mean).toBe(42.5);
      expect(p.p50).toBe(42.5);
      expect(p.p95).toBe(42.5);
      expect(p.p99).toBe(42.5);
      expect(p.stdDev).toBe(0);
    });

    test('computes accurate percentiles, mean and stdDev for standard distribution', () => {
      // 100 values from 1 to 100
      const values = Array.from({ length: 100 }, (_, i) => i + 1);
      const p = calculatePercentiles(values);

      expect(p.min).toBe(1);
      expect(p.max).toBe(100);
      expect(p.mean).toBe(50.5);
      expect(p.p50).toBe(51); // index 50 -> 51
      expect(p.p75).toBe(76);
      expect(p.p90).toBe(91);
      expect(p.p95).toBe(96);
      expect(p.p99).toBe(100);
      expect(p.stdDev).toBeGreaterThan(28);
      expect(p.stdDev).toBeLessThan(30);
    });
  });

  describe('HTTP Benchmark Engine with Mock Server', () => {
    const mock = startMockServer(0);

    afterAll(() => {
      mock.stop();
    });

    test('benchmarks mock /healthz/live with 100% success rate', async () => {
      const result = await benchmarkEndpoint(mock.url, '/healthz/live', 30, 5, 2000);

      expect(result.totalRequests).toBe(30);
      expect(result.successfulRequests).toBe(30);
      expect(result.failedRequests).toBe(0);
      expect(result.requestsPerSecond).toBeGreaterThan(100);
      expect(result.latenciesMs.p50).toBeGreaterThan(0);
      expect(result.latenciesMs.min).toBeLessThanOrEqual(result.latenciesMs.max);
      expect(result.endpoint).toBe(`${mock.url}/healthz/live`);
    });

    test('benchmarks mock /healthz/aggregate returning multi-tier status', async () => {
      const result = await benchmarkEndpoint(mock.url, '/healthz/aggregate', 20, 4, 2000);

      expect(result.totalRequests).toBe(20);
      expect(result.successfulRequests).toBe(20);
      expect(result.failedRequests).toBe(0);
      expect(result.latenciesMs.p95).toBeGreaterThan(0);
    });

    test('benchmarks mock /metrics/prometheus text endpoint', async () => {
      const result = await benchmarkEndpoint(mock.url, '/metrics/prometheus', 25, 5, 2000);

      expect(result.totalRequests).toBe(25);
      expect(result.successfulRequests).toBe(25);
      expect(result.failedRequests).toBe(0);
    });

    test('tracks network failures when endpoint is unreachable', async () => {
      // Unreachable port
      const result = await benchmarkEndpoint('http://127.0.0.1:59999', '/nonexistent', 10, 2, 500);

      expect(result.totalRequests).toBe(10);
      expect(result.successfulRequests).toBe(0);
      expect(result.failedRequests).toBe(10);
    });

    test('formats benchmark card string with metrics', async () => {
      const result = await benchmarkEndpoint(mock.url, '/healthz/live', 10, 2, 1000);
      const card = formatBenchmarkCard(result);

      expect(card).toContain('Endpoint:');
      expect(card).toContain('Throughput:');
      expect(card).toContain('Percentiles:');
      expect(card).toContain('p50:');
      expect(card).toContain('p95:');
      expect(card).toContain('p99:');
    });
  });

  describe('runBenchmarkSuite', () => {
    test('executes multi-endpoint benchmark suite in mock mode', async () => {
      const suite = await runBenchmarkSuite({
        concurrency: 4,
        requests: 15,
        forceMock: true,
        timeoutMs: 1500,
      });

      expect(suite.isMock).toBe(true);
      expect(suite.runtime).toContain('bun');
      expect(suite.results.length).toBe(5);

      for (const res of suite.results) {
        expect(res.totalRequests).toBe(15);
        expect(res.successfulRequests).toBe(15);
        expect(res.failedRequests).toBe(0);
        expect(res.latenciesMs.p50).toBeGreaterThan(0);
      }
    });

    test('benchmarks custom URL directly', async () => {
      const mock = startMockServer(0);
      try {
        const suite = await runBenchmarkSuite({
          customUrl: `${mock.url}/healthz`,
          concurrency: 2,
          requests: 10,
          timeoutMs: 1000,
        });

        expect(suite.results.length).toBe(1);
        expect(suite.results[0].totalRequests).toBe(10);
        expect(suite.results[0].successfulRequests).toBe(10);
      } finally {
        mock.stop();
      }
    });
  });
});
