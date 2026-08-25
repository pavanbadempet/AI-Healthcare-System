/**
 * Edge Proxy Latency Overhead Benchmark
 * Measures round-trip latency through Edge Gateway vs. Direct Upstream to prove <5ms overhead.
 */

import { createApp } from './index';

async function runBenchmark() {
  console.log('=== Starting Edge Gateway Overhead Benchmark ===');

  // 1. Start mock Rust upstream server
  const mockUpstreamPort = 8991;
  const mockServer = Bun.serve({
    port: mockUpstreamPort,
    hostname: '127.0.0.1',
    fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === '/v1/ping') {
        return new Response(JSON.stringify({ pong: true, time: Date.now() }), {
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response('Not Found', { status: 404 });
    },
  });

  // 2. Start Edge Gateway pointing to mock upstream
  const edgePort = 8992;
  const edgeApp = createApp({
    configOverride: {
      port: edgePort,
      host: '127.0.0.1',
      rustBackendUrl: `http://127.0.0.1:${mockUpstreamPort}`,
      rustWsUrl: `ws://127.0.0.1:${mockUpstreamPort}`,
      rateLimitPerMinute: 10000,
      rateLimitBurst: 5000,
    },
  });

  const edgeServer = edgeApp.listen({ port: edgePort, hostname: '127.0.0.1' });

  // Warmup requests
  console.log('Warming up connections...');
  for (let i = 0; i < 50; i++) {
    await fetch(`http://127.0.0.1:${mockUpstreamPort}/v1/ping`);
    await fetch(`http://127.0.0.1:${edgePort}/v1/ping`);
  }

  const iterations = 500;
  const directLatencies: number[] = [];
  const proxiedLatencies: number[] = [];

  console.log(`Executing ${iterations} benchmark requests...`);

  for (let i = 0; i < iterations; i++) {
    // Direct
    const t0 = performance.now();
    const directRes = await fetch(`http://127.0.0.1:${mockUpstreamPort}/v1/ping`);
    await directRes.json();
    const t1 = performance.now();
    directLatencies.push(t1 - t0);

    // Proxied
    const t2 = performance.now();
    const proxiedRes = await fetch(`http://127.0.0.1:${edgePort}/v1/ping`);
    await proxiedRes.json();
    const t3 = performance.now();
    proxiedLatencies.push(t3 - t2);
  }

  const avgDirect = directLatencies.reduce((a, b) => a + b, 0) / directLatencies.length;
  const avgProxied = proxiedLatencies.reduce((a, b) => a + b, 0) / proxiedLatencies.length;
  const overhead = Math.max(0, avgProxied - avgDirect);

  // Percentiles
  proxiedLatencies.sort((a, b) => a - b);
  const p50 = proxiedLatencies[Math.floor(iterations * 0.5)];
  const p95 = proxiedLatencies[Math.floor(iterations * 0.95)];
  const p99 = proxiedLatencies[Math.floor(iterations * 0.99)];

  console.log('====================================================');
  console.log(` Direct Latency (Avg):      ${avgDirect.toFixed(3)} ms`);
  console.log(` Proxied Latency (Avg):     ${avgProxied.toFixed(3)} ms`);
  console.log(` Edge Proxy Overhead (Avg): ${overhead.toFixed(3)} ms`);
  console.log(` Proxied P50:               ${p50.toFixed(3)} ms`);
  console.log(` Proxied P95:               ${p95.toFixed(3)} ms`);
  console.log(` Proxied P99:               ${p99.toFixed(3)} ms`);
  console.log('====================================================');

  if (overhead < 5.0) {
    console.log(`✅ SUCCESS: Edge proxy overhead (${overhead.toFixed(3)} ms) is well below the <5.0ms requirement!`);
  } else {
    console.warn(`⚠️ WARNING: Edge proxy overhead is ${overhead.toFixed(3)} ms`);
  }

  // Cleanup
  mockServer.stop();
  edgeServer.stop();
}

if (import.meta.main) {
  runBenchmark().then(() => process.exit(0)).catch(err => {
    console.error(err);
    process.exit(1);
  });
}
