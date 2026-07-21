/**
 * AI Healthcare System — Lazy-loaded Recharts Radar Chart
 *
 * Wraps the recharts Radar chart components so the ~300KB recharts+d3
 * bundle is only loaded when the chart is actually rendered.
 * Used as the default export for React.lazy().
 */

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

interface RadarDataPoint {
  subject: string;
  A: number;
  fullMark: number;
}

interface LazyRadarChartProps {
  /** Chart data points */
  data: RadarDataPoint[];
  /** Display name for the radar series */
  seriesName: string;
  /** Stroke color (CSS variable or hex) */
  strokeColor?: string;
  /** Fill color (CSS variable or hex) */
  fillColor?: string;
  /** Fill opacity (0-1) */
  fillOpacity?: number;
}

/**
 * Self-contained Radar chart component designed for lazy-loading.
 * Encapsulates all recharts imports so the parent page doesn't need them.
 */
export default function LazyRadarChart({
  data,
  seriesName,
  strokeColor = "var(--accent)",
  fillColor = "var(--accent)",
  fillOpacity = 0.25,
}: LazyRadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.06)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 8, fontFamily: "monospace" }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fill: "rgba(255,255,255,0.2)", fontSize: 6 }}
          stroke="transparent"
        />
        <Radar
          name={seriesName}
          dataKey="A"
          stroke={strokeColor}
          fill={fillColor}
          fillOpacity={fillOpacity}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
