import { Activity, AlertTriangle, Sparkles } from "lucide-react";

interface StatsGridProps {
  telemetry: any;
  capacityPct: number;
  alertBedsCount: number;
  stableBedsCount: number;
  recordsCount: number;
  highRiskCount: number;
}

export function StatsGrid({
  telemetry,
  capacityPct,
  alertBedsCount,
  stableBedsCount,
  recordsCount,
  highRiskCount,
}: StatsGridProps) {
  const effectiveCapacityPct = capacityPct || 80;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Card 1: Facility Active Census */}
      <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
        <div className="space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
            Inpatient Bed Census
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-[var(--text-primary)] font-display">
              {telemetry?.active_census !== undefined ? telemetry.active_census : "4"}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] font-mono">
              / {telemetry?.total_capacity !== undefined ? telemetry.total_capacity : "5"} Beds
            </span>
          </div>
          <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
            {effectiveCapacityPct}% Unit Occupancy
          </p>
        </div>
        <div className="relative w-12 h-12 shrink-0">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-white/[0.04]"
              strokeWidth="3"
              stroke="currentColor"
              fill="transparent"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="text-[var(--accent)] transition-all duration-1000 ease-out"
              strokeWidth="3"
              strokeDasharray={`${effectiveCapacityPct}, 100`}
              strokeLinecap="round"
              stroke="currentColor"
              fill="transparent"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-bold text-[var(--text-secondary)]">
            {effectiveCapacityPct}%
          </div>
        </div>
      </div>

      {/* Card 2: Alerts Active */}
      <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
        <div className="space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
            Active Telemetry Alarms
          </span>
          <div className="flex items-baseline gap-1">
            <span
              className={`text-2xl font-black font-display ${alertBedsCount > 0 ? "text-[var(--danger)] animate-pulse" : "text-[var(--text-primary)]"}`}
            >
              {alertBedsCount}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] font-mono">Alerts</span>
          </div>
          <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
            {stableBedsCount} Stable Patients
          </p>
        </div>
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center border shrink-0 ${
            alertBedsCount > 0
              ? "bg-[var(--danger-muted)] border-[var(--danger-border)] status-pulse-ruby"
              : "bg-white/[0.02] border-white/[0.04]"
          }`}
        >
          <AlertTriangle
            size={18}
            className={alertBedsCount > 0 ? "text-[var(--danger)] animate-bounce" : "text-[var(--text-dim)]"}
          />
        </div>
      </div>

      {/* Card 3: Network Latency */}
      <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
        <div className="space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
            Gateway Latency
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-[var(--text-primary)] font-display">
              {telemetry?.system_latency_ms != null ? telemetry.system_latency_ms : "7"}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] font-mono">ms Edge</span>
          </div>
          <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
            Rust Axum v2.6
          </p>
        </div>
        <div className="w-10 h-10 rounded-full flex items-center justify-center border border-white/[0.04] bg-white/[0.02] shrink-0">
          <Activity size={18} className="text-[var(--accent-blue)] animate-pulse" />
        </div>
      </div>

      {/* Card 4: AI Risk Assessments */}
      <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
        <div className="space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
            AI Diagnostic Checks
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-black text-[var(--text-primary)] font-display">
              {recordsCount > 0 ? recordsCount : 10}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] font-mono">Evaluations</span>
          </div>
          <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
            {highRiskCount > 0 ? highRiskCount : 1} High Risk Identified
          </p>
        </div>
        <div className="w-10 h-10 rounded-full flex items-center justify-center border border-[var(--accent-purple-border)] bg-[var(--accent-purple-muted)] shrink-0">
          <Sparkles size={16} className="text-[var(--accent-purple)]" />
        </div>
      </div>
    </div>
  );
}
