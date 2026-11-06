import React, { Suspense } from "react";
import { Activity } from "lucide-react";
import { Link } from "react-router-dom";
import { prefetchRoute } from "@/lib/prefetch";

interface HealthRecordLike {
  id: number | string;
  prediction?: string;
  timestamp?: string;
  created_at?: string;
  record_type?: string;
  model_type?: string;
}

interface DiagnosticTrajectorySectionProps {
  telemetry: any;
  triggerRipple: (e: React.MouseEvent<HTMLElement>) => void;
  displayChartData: any[];
  RiskTrajectoryChart: React.ComponentType<{ data: any[] }>;
  recentRecords: HealthRecordLike[];
  loading: boolean;
}

export function DiagnosticTrajectorySection({
  telemetry,
  triggerRipple,
  displayChartData,
  RiskTrajectoryChart,
  recentRecords,
  loading,
}: DiagnosticTrajectorySectionProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Risk Trajectory Chart */}
      <div className="lg:col-span-2 panel flex flex-col overflow-hidden">
        <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
          <div>
            <h2 className="section-title">Population Risk Trajectory</h2>
            <p className="mono-meta mt-0.5">
              AGGREGATED PREDICTIVE MODELING (N=
              {telemetry?.active_census != null
                ? telemetry.active_census.toLocaleString()
                : "1,248"}
              )
            </p>
          </div>
          <div className="flex gap-1" role="group" aria-label="Time range selector">
            {["7D", "30D", "90D"].map((range) => (
              <button
                key={range}
                onClick={triggerRipple}
                className={`px-2 py-0.5 border text-[9px] font-bold tracking-wider rounded transition-colors ${
                  range === "30D"
                    ? "bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]"
                    : "bg-[var(--bg-card)] border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text-primary)]"
                }`}
                aria-label={`${range} view`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 flex-1">
          <div className="h-64 w-full overflow-hidden flex items-center justify-center">
            <Suspense
              fallback={
                <div className="flex flex-col items-center gap-3">
                  <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                  <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono">
                    Initializing Telemetry Engine...
                  </p>
                </div>
              }
            >
              <RiskTrajectoryChart data={displayChartData} />
            </Suspense>
          </div>
        </div>
      </div>

      {/* Live Diagnostic Stream */}
      <div className="panel flex flex-col overflow-hidden">
        <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
          <h2 className="section-title flex items-center gap-2">
            <Activity size={12} className="text-[var(--success)]" aria-hidden="true" /> Diagnostic
            Stream
          </h2>
          <span className="text-[9px] font-mono text-[var(--success)] font-bold flex items-center gap-1 uppercase">
            <span
              className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse"
              aria-hidden="true"
            />{" "}
            Live
          </span>
        </div>

        <div
          className="flex-1 overflow-y-auto divide-y divide-[var(--border-subtle)] max-h-64 lg:max-h-none"
          role="log"
          aria-label="Live diagnostic stream"
        >
          {recentRecords.length > 0 ? (
            recentRecords.map((r) => {
              const pred = (r.prediction || "").toLowerCase();
              const isHigh = pred.includes("high") || pred.includes("positive");
              const recordTime = r.timestamp || r.created_at || new Date().toISOString();
              return (
                <div
                  key={r.id}
                  className="p-3 hover:bg-[rgba(255,255,255,0.01)] transition-colors group cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isHigh ? "bg-[var(--danger)]" : "bg-[var(--success)]"
                        }`}
                        aria-hidden="true"
                      />
                      <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">
                        {r.record_type || r.model_type || "DIAGNOSTIC"}
                      </span>
                    </div>
                    <span className="mono-meta text-[10px]">
                      {new Date(recordTime).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[10px] font-mono text-[var(--text-secondary)]">
                    <span>ID: #{r.id}</span>
                    <span
                      className={`px-2 py-0.5 rounded-sm border ${
                        isHigh
                          ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
                          : "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                      }`}
                    >
                      {r.prediction ? String(r.prediction).substring(0, 18) : "NEGATIVE / STABLE"}
                      ...
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-wide">
              {loading ? "Syncing Diagnostic Streams..." : "No stream logs recorded"}
            </div>
          )}
        </div>

        <div className="p-2 border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)]">
          <Link
            to="/patients"
            onMouseEnter={() => prefetchRoute("/patients")}
            className="w-full block text-center text-[10px] text-[var(--text-secondary)] hover:text-[var(--accent)] font-bold tracking-wider uppercase transition-colors"
          >
            View Log History
          </Link>
        </div>
      </div>
    </div>
  );
}
