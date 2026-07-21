/**
 * AI Healthcare System — Lazy-loaded Telemetry Load History Chart
 *
 * Wraps the recharts AreaChart for the Telemetry page so the ~300KB
 * recharts+d3 bundle is only loaded when this chart renders.
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface HistoryEntry {
  time: string;
  cpu: number;
  ram: number;
  latency: number;
}

interface LazyTelemetryChartProps {
  data: HistoryEntry[];
}

/**
 * Self-contained telemetry load history chart for lazy-loading.
 */
export default function LazyTelemetryChart({ data }: LazyTelemetryChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent-purple)" stopOpacity={0.2} />
            <stop offset="95%" stopColor="var(--accent-purple)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="time"
          tick={{ fill: "var(--text-dim)", fontSize: 8, fontFamily: "monospace" }}
          stroke="rgba(255,255,255,0.03)"
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "var(--text-dim)", fontSize: 8, fontFamily: "monospace" }}
          stroke="rgba(255,255,255,0.03)"
          tickLine={false}
          domain={[0, 100]}
        />
        <Tooltip
          contentStyle={{
            background: "rgba(12,12,14,0.95)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 12,
            fontSize: 10,
            fontFamily: "monospace",
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
          }}
          labelStyle={{ color: "var(--text-dim)", textTransform: "uppercase", fontSize: 8, fontWeight: "bold" }}
        />
        <Area
          type="monotone"
          dataKey="cpu"
          stroke="var(--accent)"
          strokeWidth={2}
          fill="url(#cpuGrad)"
          name="CPU Load %"
        />
        <Area
          type="monotone"
          dataKey="ram"
          stroke="var(--accent-purple)"
          strokeWidth={2}
          fill="url(#ramGrad)"
          name="RAM Util %"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
