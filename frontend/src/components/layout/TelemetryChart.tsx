/**
 * LazyChart — Dynamically imports recharts components.
 * Keeps the ~280KB recharts+d3 bundle out of Dashboard's initial chunk.
 * The chart renders after the Dashboard shell is already visible.
 */
import { lazy, Suspense } from "react";

const LazyAreaChart = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.AreaChart }))
);
const LazyArea = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.Area }))
);
const LazyXAxis = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.XAxis }))
);
const LazyYAxis = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.YAxis }))
);
const LazyTooltip = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.Tooltip }))
);
const LazyResponsiveContainer = lazy(() =>
  import("recharts").then((mod) => ({ default: mod.ResponsiveContainer }))
);

interface TelemetryChartProps {
  data: { time: string; hr: number; spo2: number; rr: number }[];
  width?: number;
}

function ChartFallback() {
  return (
    <div className="w-full h-[200px] flex items-center justify-center text-[10px] font-mono text-[var(--text-dim)] uppercase">
      Loading chart...
    </div>
  );
}

export default function TelemetryChart({ data, width = 720 }: TelemetryChartProps) {
  return (
    <Suspense fallback={<ChartFallback />}>
      <LazyResponsiveContainer width="100%" height={200}>
        <LazyAreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="hrGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="spo2Grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34d399" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <LazyXAxis
            dataKey="time"
            tick={{ fill: "var(--text-dim)", fontSize: 9, fontFamily: "monospace" }}
            stroke="rgba(255,255,255,0.03)"
            tickLine={false}
          />
          <LazyYAxis
            tick={{ fill: "var(--text-dim)", fontSize: 9, fontFamily: "monospace" }}
            stroke="rgba(255,255,255,0.03)"
            tickLine={false}
            domain={[40, 110]}
          />
          <LazyTooltip
            contentStyle={{
              background: "rgba(12,12,14,0.95)",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 8,
              fontSize: 10,
              fontFamily: "monospace",
              boxShadow: "0 8px 25px rgba(0,0,0,0.5)",
            }}
            labelStyle={{ color: "var(--text-dim)", textTransform: "uppercase", fontSize: 8 }}
          />
          <LazyArea
            type="monotone"
            dataKey="hr"
            stroke="var(--accent)"
            strokeWidth={1.5}
            fill="url(#hrGrad)"
            dot={false}
            name="Heart Rate"
          />
          <LazyArea
            type="monotone"
            dataKey="spo2"
            stroke="#34d399"
            strokeWidth={1.5}
            fill="url(#spo2Grad)"
            dot={false}
            name="SpO₂"
          />
        </LazyAreaChart>
      </LazyResponsiveContainer>
    </Suspense>
  );
}
