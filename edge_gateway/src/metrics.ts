/**
 * Prometheus Metrics Exporter & Real-Time Telemetry Tracker
 * Tracks request counts, upstream target distributions, and calculates p50/p90/p95/p99 latency quantiles.
 */

export interface LatencyQuantiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  count: number;
  sum: number;
  mean: number;
}

class MetricsRegistry {
  private requestCounts = new Map<string, number>();
  private durations: number[] = []; // In seconds, max 2000 samples
  private maxSamples = 2000;
  private totalSum = 0;
  private totalCount = 0;

  public recordRequest(target: string, method: string, status: number, durationSeconds: number): void {
    const key = `${target}:${method}:${status}`;
    this.requestCounts.set(key, (this.requestCounts.get(key) || 0) + 1);

    this.durations.push(durationSeconds);
    this.totalSum += durationSeconds;
    this.totalCount++;

    if (this.durations.length > this.maxSamples) {
      const removed = this.durations.shift();
      if (removed !== undefined) {
        // Keep moving window
      }
    }
  }

  public getQuantiles(): LatencyQuantiles {
    if (this.durations.length === 0) {
      return { p50: 0, p90: 0, p95: 0, p99: 0, count: 0, sum: 0, mean: 0 };
    }

    const sorted = [...this.durations].sort((a, b) => a - b);
    const n = sorted.length;

    const getQ = (q: number) => {
      const idx = Math.min(Math.floor(q * n), n - 1);
      return sorted[idx];
    };

    return {
      p50: parseFloat(getQ(0.5).toFixed(6)),
      p90: parseFloat(getQ(0.9).toFixed(6)),
      p95: parseFloat(getQ(0.95).toFixed(6)),
      p99: parseFloat(getQ(0.99).toFixed(6)),
      count: this.totalCount,
      sum: parseFloat(this.totalSum.toFixed(6)),
      mean: parseFloat((this.totalSum / this.totalCount).toFixed(6)),
    };
  }

  public toPrometheusText(): string {
    const lines: string[] = [];
    const mem = process.memoryUsage();
    const uptime = Math.floor(process.uptime());

    lines.push('# HELP http_requests_total Total number of HTTP requests processed by Edge Gateway.');
    lines.push('# TYPE http_requests_total counter');

    if (this.requestCounts.size === 0) {
      lines.push('http_requests_total{target="edge",method="GET",status="200"} 0');
    } else {
      for (const [key, count] of this.requestCounts.entries()) {
        const [target, method, status] = key.split(':');
        lines.push(`http_requests_total{target="${target}",method="${method}",status="${status}"} ${count}`);
      }
    }

    const q = this.getQuantiles();
    lines.push('');
    lines.push('# HELP http_request_duration_seconds HTTP request latencies in seconds.');
    lines.push('# TYPE http_request_duration_seconds summary');
    lines.push(`http_request_duration_seconds{quantile="0.5"} ${q.p50}`);
    lines.push(`http_request_duration_seconds{quantile="0.9"} ${q.p90}`);
    lines.push(`http_request_duration_seconds{quantile="0.95"} ${q.p95}`);
    lines.push(`http_request_duration_seconds{quantile="0.99"} ${q.p99}`);
    lines.push(`http_request_duration_seconds_sum ${q.sum}`);
    lines.push(`http_request_duration_seconds_count ${q.count}`);

    lines.push('');
    lines.push('# HELP edge_gateway_uptime_seconds Edge Gateway runtime uptime in seconds.');
    lines.push('# TYPE edge_gateway_uptime_seconds gauge');
    lines.push(`edge_gateway_uptime_seconds ${uptime}`);

    lines.push('');
    lines.push('# HELP edge_gateway_memory_rss_bytes Edge Gateway resident set size in bytes.');
    lines.push('# TYPE edge_gateway_memory_rss_bytes gauge');
    lines.push(`edge_gateway_memory_rss_bytes ${mem.rss}`);

    lines.push('');
    lines.push('# HELP edge_gateway_memory_heap_used_bytes Edge Gateway V8/JavaScriptCore heap used.');
    lines.push('# TYPE edge_gateway_memory_heap_used_bytes gauge');
    lines.push(`edge_gateway_memory_heap_used_bytes ${mem.heapUsed}`);

    return lines.join('\n') + '\n';
  }

  public reset(): void {
    this.requestCounts.clear();
    this.durations = [];
    this.totalSum = 0;
    this.totalCount = 0;
  }
}

export const metricsRegistry = new MetricsRegistry();
