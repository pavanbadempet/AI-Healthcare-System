import React from "react";
import { Activity, BrainCircuit, Sparkles, Users } from "lucide-react";

interface GuidedConsoleProps {
  navigate: (path: string) => void;
  triggerRipple: (e: React.MouseEvent<HTMLElement>) => void;
  toast: {
    info: (msg: string) => void;
    success: (msg: string) => void;
    error: (msg: string) => void;
  };
  apiBase: string;
  authHeaders: () => Record<string, string>;
}

export function GuidedConsole({
  navigate,
  triggerRipple,
  toast,
}: GuidedConsoleProps) {
  return (
    <section className="glass-card p-5 rounded-2xl border border-[var(--border)] bg-gradient-to-br from-indigo-950/20 to-black/40 backdrop-blur-xl relative overflow-hidden">
      {/* Subtle ambient corner glow */}
      <div
        className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent)] opacity-10 rounded-full filter blur-2xl pointer-events-none"
        style={{ pointerEvents: "none" }}
      />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-1.5">
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--accent)] flex items-center gap-1.5">
            <Sparkles size={12} className="text-[var(--accent)]" /> ICU Clinical Operations Console
          </span>
          <h2 className="text-base font-bold text-[var(--text-primary)] uppercase tracking-wide">
            Rapid Triage & Clinical Shift Actions
          </h2>
          <p className="text-xs text-[var(--text-secondary)] leading-relaxed max-w-xl">
            Access active inpatient encounters, review bedside vitals telemetry, compile structured
            SBAR shift handoffs, and engage the clinical AI decision copilot.
          </p>
        </div>

        {/* Rapid-action clinical buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full lg:w-auto shrink-0">
          <button
            onClick={(e) => {
              triggerRipple(e);
              navigate("/patients");
              toast.info("Viewing registered inpatients and historical telemetry.");
            }}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide flex items-center justify-center gap-2 py-2.5 px-4 hover:border-[var(--accent)] hover:text-white"
          >
            <Users size={14} className="text-[var(--accent)]" />
            Patient Registry
          </button>
          <button
            onClick={(e) => {
              triggerRipple(e);
              navigate("/chat");
              toast.info("Clinical Copilot ready for differential diagnoses and medication safety.");
            }}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide flex items-center justify-center gap-2 py-2.5 px-4 hover:border-[var(--accent-purple)] hover:text-white"
          >
            <BrainCircuit size={14} className="text-[var(--accent-purple)]" />
            Clinical Copilot
          </button>
          <button
            onClick={(e) => {
              triggerRipple(e);
              navigate("/capacity");
              toast.info("Opening Acute Care Bed Capacity and Admission Intake.");
            }}
            className="btn btn-primary text-xs uppercase font-bold tracking-wide flex items-center justify-center gap-2 py-2.5 px-4"
          >
            <Activity size={14} />
            Unit Capacity
          </button>
        </div>
      </div>

      {/* Clinical Workflow Modules */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-5 pt-4 border-t border-white/[0.04]">
        <div className="p-3 rounded-lg bg-white/[0.015] border border-white/[0.03] flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-[var(--accent-muted)] border border-[var(--accent-border)] flex items-center justify-center text-[var(--accent)] font-mono text-xs font-bold shrink-0">
            1
          </div>
          <div>
            <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">Inpatient Triage</h3>
            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">
              Real-time monitoring of bed census, alarms, and patient acuity levels.
            </p>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-white/[0.015] border border-white/[0.03] flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-[var(--accent-purple-muted)] border border-[var(--accent-purple-border)] flex items-center justify-center text-[var(--accent-purple)] font-mono text-xs font-bold shrink-0">
            2
          </div>
          <div>
            <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">Bedside Telemetry</h3>
            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">
              Hemodynamic wave tracing, continuous SpO2, and automated arrhythmia flags.
            </p>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-white/[0.015] border border-white/[0.03] flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-[var(--accent-blue-muted)] border border-[var(--accent-blue-border)] flex items-center justify-center text-[var(--accent-blue)] font-mono text-xs font-bold shrink-0">
            3
          </div>
          <div>
            <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">Shift Handoff</h3>
            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">
              Automated SBAR generation and continuity of care documentation.
            </p>
          </div>
        </div>
        <div className="p-3 rounded-lg bg-white/[0.015] border border-white/[0.03] flex items-start gap-3">
          <div className="w-6 h-6 rounded-full bg-[var(--success-muted)] border border-[var(--success-border)] flex items-center justify-center text-[var(--success)] font-mono text-xs font-bold shrink-0">
            4
          </div>
          <div>
            <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">Safety & Coding Audit</h3>
            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 leading-relaxed">
              Conformal confidence sets, clinical documentation integrity, and billing audits.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
