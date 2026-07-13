import React from "react";
import { XAxis, YAxis, Tooltip, AreaChart, Area, ResponsiveContainer } from "recharts";

interface RiskTrajectoryChartProps {
  data: any[];
}

export default function RiskTrajectoryChart({ data }: RiskTrajectoryChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
        <defs>
          <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.25} />
            <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="name"
          stroke="var(--border-focus)"
          fontSize={9}
          tickLine={false}
          axisLine={false}
          dy={5}
          tick={{ fill: "var(--text-dim)" }}
        />
        <YAxis
          stroke="var(--border-focus)"
          fontSize={9}
          tickLine={false}
          axisLine={false}
          dx={-5}
          tick={{ fill: "var(--text-dim)" }}
        />
        <Tooltip
          cursor={{ stroke: "var(--border-focus)", strokeWidth: 1 }}
          contentStyle={{
            background: "rgba(24,24,27,0.95)",
            border: "1px solid var(--border-focus)",
            borderRadius: "6px",
            fontSize: "11px",
            fontFamily: "var(--font-mono)",
            backdropFilter: "blur(12px)",
          }}
          itemStyle={{ color: "var(--accent)", fontWeight: "700" }}
        />
        <Area
          type="monotone"
          dataKey="riskScore"
          stroke="var(--accent)"
          strokeWidth={1.5}
          fillOpacity={1}
          fill="url(#colorRisk)"
          activeDot={{ r: 4, fill: "var(--bg-primary)", stroke: "var(--accent)", strokeWidth: 1.5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
