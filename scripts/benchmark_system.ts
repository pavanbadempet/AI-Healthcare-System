#!/usr/bin/env bun
/**
 * AI Healthcare System - High-Concurrency System Benchmark Harness (Bun TypeScript)
 * Measures real-time p50, p75, p90, p95, p99 latency percentiles and RPS across Edge Gateway & System services.
 * Zero external dependencies.
 */

export interface LatencyMetrics {
  min: number;
  max: number;
  mean: number;
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
  stdDev: number;
}

export interface BenchmarkResult {
  endpoint: string;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  elapsedSeconds: number;
  requestsPerSecond: number;
  latenciesMs: LatencyMetrics;
}

export interface BenchmarkSuiteResult {
  timestamp: string;
  runtime: string;
  isMock: boolean;
  concurrency: number;
  requestsPerEndpoint: number;
  results: BenchmarkResult[];
}

/**
 * Computes exact statistical percentiles, min, max, mean, and standard deviation.
 */
export function calculatePercentiles(latencies: number[]): LatencyMetrics {
  if (latencies.length === 0) {
    return { min: 0, max: 0, mean: 0, p50: 0, p75: 0, p90: 0, p95: 0, p99: 0, stdDev: 0 };
  }

  const sorted = [...latencies].sort((a, b) => a - b);
  const n = sorted.length;
  const sum = sorted.reduce((acc, v) => acc + v, 0);
  const mean = sum / n;
  const variance = sorted.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / n;
  const stdDev = Math.sqrt(variance);

  const getP = (p: number) => {
    const idx = Math.min(Math.floor((p / 100) * n), n - 1);
    return sorted[idx];
  };

  return {
    min: parseFloat(sorted[0].toFixed(3)),
    max: parseFloat(sorted[n - 1].toFixed(3)),
    mean: parseFloat(mean.toFixed(3)),
    p50: parseFloat(getP(50).toFixed(3)),
    p75: parseFloat(getP(75).toFixed(3)),
    p90: parseFloat(getP(90).toFixed(3)),
    p95: parseFloat(getP(95).toFixed(3)),
    p99: parseFloat(getP(99).toFixed(3)),
    stdDev: parseFloat(stdDev.toFixed(3)),
  };
}

/**
 * Starts an in-process mock HTTP server for zero-configuration testing and CI pipelines.
 */
export function startMockServer(port = 0) {
  const server = Bun.serve({
    port,
    fetch(req) {
      const url = new URL(req.url);
      const path = url.pathname;

      if (path === '/healthz' || path === '/healthz/live') {
        return new Response(JSON.stringify({ status: 'ok', uptime: 120.4, timestamp: new Date().toISOString() }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (path === '/healthz/aggregate') {
        return new Response(
          JSON.stringify({
            status: 'healthy',
            services: {
              rust_core: { status: 'healthy', port: 8001, latencyMs: 0.15 },
              python_brain: { status: 'healthy', port: 8002, latencyMs: 0.42 },
            },
            timestamp: new Date().toISOString(),
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }

      if (path === '/metrics/prometheus') {
        const prometheusBody = [
          '# HELP http_requests_total Total number of HTTP requests processed.',
          '# TYPE http_requests_total counter',
          'http_requests_total{handler="healthz",code="200"} 4520',
          '# HELP http_request_duration_seconds Latency histogram.',
          '# TYPE http_request_duration_seconds histogram',
          'http_request_duration_seconds_bucket{le="0.001"} 3800',
          'http_request_duration_seconds_bucket{le="0.005"} 4450',
          'http_request_duration_seconds_bucket{le="+Inf"} 4520',
        ].join('\n');

        return new Response(prometheusBody, {
          status: 200,
          headers: { 'Content-Type': 'text/plain; version=0.0.4' },
        });
      }

      return new Response(JSON.stringify({ status: 'ok', path }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    },
  });

  return {
    server,
    port: server.port,
    url: `http://127.0.0.1:${server.port}`,
    stop: () => server.stop(true),
  };
}

/**
 * Executes a high-concurrency async HTTP benchmark against an endpoint.
 */
export async function benchmarkEndpoint(
  baseUrl: string,
  endpoint: string,
  iterations: number,
  concurrency: number,
  timeoutMs = 5000
): Promise<BenchmarkResult> {
  let fullUrl: string;
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    fullUrl = endpoint;
  } else {
    const cleanBase = baseUrl.replace(/\/+$/, '');
    const cleanEp = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    fullUrl = `${cleanBase}${cleanEp}`;
  }

  const latencies: number[] = [];
  let successful = 0;
  let failed = 0;
  let nextIndex = 0;

  const startTime = performance.now();

  async function worker() {
    while (true) {
      const idx = nextIndex++;
      if (idx >= iterations) break;

      const reqStart = performance.now();
      try {
        const res = await fetch(fullUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Bun-Benchmark-Harness/2.0',
          },
          signal: AbortSignal.timeout(timeoutMs),
        });

        await res.text();
        const durationMs = performance.now() - reqStart;
        latencies.push(durationMs);

        if (res.ok) {
          successful++;
        } else {
          failed++;
        }
      } catch {
        const durationMs = performance.now() - reqStart;
        latencies.push(durationMs);
        failed++;
      }
    }
  }

  const workerCount = Math.max(1, Math.min(concurrency, iterations));
  const workers = Array.from({ length: workerCount }, () => worker());
  await Promise.all(workers);

  const elapsedMs = performance.now() - startTime;
  const elapsedSeconds = parseFloat((elapsedMs / 1000).toFixed(3));
  const requestsPerSecond = parseFloat((iterations / Math.max(elapsedSeconds, 0.0001)).toFixed(1));

  return {
    endpoint: fullUrl,
    totalRequests: iterations,
    successfulRequests: successful,
    failedRequests: failed,
    elapsedSeconds,
    requestsPerSecond,
    latenciesMs: calculatePercentiles(latencies),
  };
}

/**
 * Formats a BenchmarkResult into a structured ASCII console card.
 */
export function formatBenchmarkCard(result: BenchmarkResult): string {
  const successPct = result.totalRequests > 0
    ? ((result.successfulRequests / result.totalRequests) * 100).toFixed(1)
    : '0.0';

  const lines = [
    `  Endpoint:    ${result.endpoint}`,
    `  Requests:    ${result.successfulRequests}/${result.totalRequests} OK (${result.failedRequests} errors, ${successPct}% success)`,
    `  Throughput:  ${result.requestsPerSecond.toLocaleString()} req/sec in ${result.elapsedSeconds}s`,
    `  Percentiles: p50: ${result.latenciesMs.p50}ms | p75: ${result.latenciesMs.p75}ms | p90: ${result.latenciesMs.p90}ms | p95: ${result.latenciesMs.p95}ms | p99: ${result.latenciesMs.p99}ms`,
    `  Range:       min: ${result.latenciesMs.min}ms | mean: ${result.latenciesMs.mean}ms ± ${result.latenciesMs.stdDev}ms | max: ${result.latenciesMs.max}ms`,
  ];
  return lines.join('\n');
}

/**
 * Runs the multi-tier benchmark suite across Edge Gateway, Rust Core, and Python Brain.
 */
export async function runBenchmarkSuite(options: {
  concurrency?: number;
  requests?: number;
  customUrl?: string;
  forceMock?: boolean;
  timeoutMs?: number;
}): Promise<BenchmarkSuiteResult> {
  const concurrency = options.concurrency || 20;
  const requests = options.requests || 100;
  const timeoutMs = options.timeoutMs || 5000;

  let isMock = options.forceMock || false;
  let mockServerInstance: ReturnType<typeof startMockServer> | null = null;

  // If a custom URL is provided, benchmark that endpoint directly
  if (options.customUrl) {
    const res = await benchmarkEndpoint('', options.customUrl, requests, concurrency, timeoutMs);
    return {
      timestamp: new Date().toISOString(),
      runtime: `bun ${Bun.version} (${process.arch})`,
      isMock: false,
      concurrency,
      requestsPerEndpoint: requests,
      results: [res],
    };
  }

  // Standard multi-endpoint target list
  const targets: { name: string; url: string; path: string }[] = [
    { name: 'Bun Edge Gateway (Live)', url: 'http://127.0.0.1:8000', path: '/healthz/live' },
    { name: 'Bun Edge Gateway (Aggregate)', url: 'http://127.0.0.1:8000', path: '/healthz/aggregate' },
    { name: 'Bun Edge Gateway (Prometheus)', url: 'http://127.0.0.1:8000', path: '/metrics/prometheus' },
    { name: 'Rust Systems Core (8001)', url: 'http://127.0.0.1:8001', path: '/healthz' },
    { name: 'Python Deliberation Core (8002)', url: 'http://127.0.0.1:8002', path: '/healthz' },
  ];

  // Auto-detect if live servers are responding or fallback to mock
  if (!isMock) {
    try {
      const probe = await fetch('http://127.0.0.1:8000/healthz/live', {
        signal: AbortSignal.timeout(600),
      });
      if (!probe.ok) isMock = true;
    } catch {
      isMock = true;
    }
  }

  if (isMock) {
    mockServerInstance = startMockServer();
  }

  const results: BenchmarkResult[] = [];

  try {
    for (const target of targets) {
      const baseUrl = isMock ? mockServerInstance!.url : target.url;
      const res = await benchmarkEndpoint(baseUrl, target.path, requests, concurrency, timeoutMs);
      // Retain display name for report
      results.push({
        ...res,
        endpoint: `${target.name} [${isMock ? 'Mock' : target.url}${target.path}]`,
      });
    }
  } finally {
    if (mockServerInstance) {
      mockServerInstance.stop();
    }
  }

  return {
    timestamp: new Date().toISOString(),
    runtime: `bun ${Bun.version} (${process.arch})`,
    isMock,
    concurrency,
    requestsPerEndpoint: requests,
    results,
  };
}

// CLI Execution
if (import.meta.main) {
  const args = process.argv.slice(2);
  let requests = 500;
  let concurrency = 20;
  let customUrl: string | undefined = undefined;
  let jsonOutput = false;
  let forceMock = false;
  let quiet = false;
  let outputPath: string | undefined = undefined;
  let timeoutMs = 5000;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if ((arg === '--requests' || arg === '-n' || arg === '--iterations') && args[i + 1]) {
      requests = parseInt(args[++i], 10);
    } else if ((arg === '--concurrency' || arg === '-c') && args[i + 1]) {
      concurrency = parseInt(args[++i], 10);
    } else if (arg === '--url' && args[i + 1]) {
      customUrl = args[++i];
    } else if (arg === '--json') {
      jsonOutput = true;
    } else if (arg === '--mock') {
      forceMock = true;
    } else if (arg === '--quiet' || arg === '-q') {
      quiet = true;
    } else if ((arg === '--output' || arg === '-o') && args[i + 1]) {
      outputPath = args[++i];
    } else if (arg === '--timeout' && args[i + 1]) {
      timeoutMs = parseInt(args[++i], 10);
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: bun scripts/benchmark_system.ts [options]

High-concurrency async HTTP benchmark harness measuring p50, p75, p90, p95, p99 percentiles.

Options:
  -n, --requests <N>     Total requests per endpoint (default: 500)
  -c, --concurrency <N>  Concurrent worker count (default: 20)
  --url <URL>            Benchmark a specific custom URL
  --mock                 Force using self-contained in-memory mock server (CI mode)
  --json                 Output machine-readable JSON
  -o, --output <path>    Write JSON benchmark report to file
  --timeout <ms>         Per-request timeout in milliseconds (default: 5000)
  -q, --quiet            Suppress non-essential progress output
  -h, --help             Show this help message
`);
      process.exit(0);
    }
  }

  (async () => {
    if (!jsonOutput && !quiet) {
      console.log(`================================================================================`);
      console.log(`  AI HEALTHCARE SYSTEM — HIGH-CONCURRENCY HTTP BENCHMARK (BUN RUNTIME)`);
      console.log(`================================================================================`);
      console.log(`  Concurrency: ${concurrency} parallel workers | Requests: ${requests} req/endpoint`);
      console.log(`  Runtime:     Bun v${Bun.version} (${process.arch})`);
      if (customUrl) console.log(`  Target URL:  ${customUrl}`);
      if (forceMock) console.log(`  Mode:        Standalone In-Memory Mock Server (--mock)`);
      console.log(`================================================================================\n`);
    }

    const suiteResult = await runBenchmarkSuite({
      concurrency,
      requests,
      customUrl,
      forceMock,
      timeoutMs,
    });

    if (jsonOutput) {
      const jsonStr = JSON.stringify(suiteResult, null, 2);
      console.log(jsonStr);
      if (outputPath) {
        await Bun.write(outputPath, jsonStr);
      }
    } else {
      if (!quiet) {
        if (suiteResult.isMock) {
          console.log(`[INFO] Operating in standalone mock fallback mode (services offline or --mock)\n`);
        }
        for (const res of suiteResult.results) {
          console.log(formatBenchmarkCard(res));
          console.log('--------------------------------------------------------------------------------');
        }
        console.log(`\n================================================================================`);
        console.log(`  BENCHMARK SUMMARY (${suiteResult.results.length} endpoints tested)`);
        console.log(`================================================================================`);
        for (const res of suiteResult.results) {
          const epShort = res.endpoint.length > 35 ? res.endpoint.slice(0, 32) + '...' : res.endpoint.padEnd(35);
          console.log(`  ${epShort} | ${String(res.requestsPerSecond).padStart(8)} req/s | p50: ${res.latenciesMs.p50}ms | p95: ${res.latenciesMs.p95}ms | p99: ${res.latenciesMs.p99}ms`);
        }
        console.log(`================================================================================\n`);
      }

      if (outputPath) {
        await Bun.write(outputPath, JSON.stringify(suiteResult, null, 2));
        if (!quiet) console.log(`Report written to ${outputPath}`);
      }
    }
  })();
}
