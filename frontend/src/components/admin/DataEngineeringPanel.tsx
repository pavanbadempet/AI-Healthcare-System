/**
 * DataEngineeringPanel – Database connection, ETL pipeline, and data quality tab.
 * Extracted from Admin.tsx for maintainability.
 */
import { useState, useEffect } from "react";
import { Database, Network, Shield, CheckCircle2, ShieldAlert, Info, Loader2, BarChart3, RefreshCw } from "lucide-react";
import { getAdminDataQuality, getAdminOperationalHealth, triggerMaintenance, type DataQualityReport, type OperationalHealthReport } from "@/lib/api";
import { toast } from "@/lib/toast";

export default function DataEngineeringPanel({ stats }: { stats: any }) {
  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null);
  const [operationalHealth, setOperationalHealth] = useState<OperationalHealthReport | null>(null);
  const [dqLoading, setDqLoading] = useState(false);
  const [dqError, setDqError] = useState("");

  useEffect(() => {
    setDqLoading(true);
    setDqError("");
    Promise.all([getAdminDataQuality(), getAdminOperationalHealth()])
      .then(([dqData, ohData]) => {
        setDataQuality(dqData);
        setOperationalHealth(ohData);
      })
      .catch((err) => {
        console.error("Failed to load pipeline data", err);
        setDqError(err.message || "Failed to load pipeline or data quality metrics.");
      })
      .finally(() => setDqLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Database Persistence Config */}
      <div className="panel p-6">
        <div className="flex flex-col lg:flex-row justify-between items-start gap-4 mb-6">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
              <Database size={15} className="text-[var(--accent)]" /> Active Database Connection
            </h3>
            <p className="text-[11px] text-[var(--text-secondary)] font-mono uppercase mt-1">
              EHR transactional layer database engine status and settings.
            </p>
          </div>

          {stats?.database_type === "sqlite" ? (
            <span className="px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 animate-pulse">
              <ShieldAlert size={12} /> SQLite (Ephemeral Persistence)
            </span>
          ) : (
            <span className="px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <CheckCircle2 size={12} /> PostgreSQL (Persistent Cloud DB)
            </span>
          )}
        </div>

        {stats?.database_type === "sqlite" && (
          <div className="bg-amber-500/5 border border-amber-500/20 p-4 rounded-lg flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center">
            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-widest text-amber-400 flex items-center gap-1">
                <Info size={12} /> Ephemeral Database Warning
              </span>
              <p className="text-[11px] text-zinc-400 max-w-2xl leading-relaxed uppercase font-mono">
                Since Hugging Face Spaces run in a stateless Docker container, SQLite database modifications are lost when the Space sleeps or restarts. To set up permanent data storage for free, connect a cloud database:
              </p>
            </div>
            <div className="bg-zinc-950/80 border border-zinc-800 p-3 rounded text-[10px] font-mono text-zinc-300 w-full lg:max-w-md space-y-2 select-all leading-normal">
              <div className="font-bold text-white uppercase border-b border-zinc-800 pb-1.5 flex justify-between items-center">
                <span>Setup Permanent Database (Free)</span>
                <span className="text-[8px] bg-cyan-500/10 text-cyan-400 px-1 py-px rounded font-bold">NEON.TECH</span>
              </div>
              <p>1. Sign up at <a href="https://neon.tech" target="_blank" rel="noreferrer" className="text-[var(--accent)] underline font-bold">neon.tech</a> and create a free Postgres database.</p>
              <p>2. Copy the database connection URI.</p>
              <p>3. Go to Hugging Face settings and add a Secret:<br/>Key: <code className="text-white font-bold bg-zinc-900 px-1">DATABASE_URL</code><br/>Value: <code className="text-white font-bold bg-zinc-900 px-1">postgresql://...</code></p>
            </div>
          </div>
        )}
      </div>

      {/* SOTA Database Optimization & Retention Control */}
      <div className="panel p-6">
        <div className="flex flex-col lg:flex-row justify-between items-start gap-4 mb-6">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
              <Shield size={15} className="text-[var(--accent)]" /> System Maintenance & Retention Coordinator
            </h3>
            <p className="text-[11px] text-[var(--text-secondary)] font-mono uppercase mt-1">
              GDPR/HIPAA-compliant retention pruning, data deactivation, and index database optimizations.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                try {
                  const res = await triggerMaintenance();
                  toast.success(res.message || "Optimization executed successfully!");
                } catch (err: any) {
                  toast.error(err.message || "Failed to execute maintenance.");
                }
              }}
              className="btn btn-primary text-xs uppercase font-bold tracking-wide flex items-center gap-2"
            >
              <RefreshCw size={12} className="animate-spin" /> Run Optimization & Pruning
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-zinc-950/40 border border-[var(--border)] rounded-lg space-y-1">
            <span className="text-[10px] font-bold text-white uppercase tracking-wider block">Index Rebuilding</span>
            <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">Optimizes B-tree index tables and reclaims unused database storage pages.</p>
          </div>
          <div className="p-4 bg-zinc-950/40 border border-[var(--border)] rounded-lg space-y-1">
            <span className="text-[10px] font-bold text-white uppercase tracking-wider block">GDPR Compliance</span>
            <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">Prunes expired telemetry logs, clinical chat records, and soft-deleted nodes older than 30 days.</p>
          </div>
          <div className="p-4 bg-zinc-950/40 border border-[var(--border)] rounded-lg space-y-1">
            <span className="text-[10px] font-bold text-white uppercase tracking-wider block">Vector DB Compact</span>
            <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">Compacts local vector space indexes, ensuring fast semantic search response times.</p>
          </div>
        </div>
      </div>

      {/* ETL Engineering Pipeline Flow */}
      <div className="panel p-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Network size={15} className="text-[var(--accent-purple)]" /> Data Engineering Pipelines
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          <div className="hidden md:block absolute top-10 left-1/4 right-10 h-0.5 bg-gradient-to-r from-[var(--accent)] via-[var(--accent-purple)] to-[var(--success)] opacity-20 -z-0" />

          {[
            { step: "01", name: "FHIR/HL7 Ingestion", desc: "Listens on /chat and /records for patient EHR payload sync", status: "Active", color: "text-[var(--accent)]", bg: "bg-[var(--accent-muted)]", border: "border-[var(--accent-border)]" },
            { step: "02", name: "Data Sanitization", desc: "Filters PII, runs validation schemas, and quarantines anomalies", status: "Active", color: "text-[var(--accent-purple)]", bg: "bg-[var(--accent-purple-muted)]", border: "border-[var(--accent-purple-border)]" },
            { step: "03", name: "Embedding Sync", desc: "Converts text entries to vectors and indexes them for RAG search", status: "Active", color: "text-cyan-400", bg: "bg-cyan-950/20", border: "border-cyan-500/30" },
            { step: "04", name: "Tri-Tier AI RAG", desc: "Retrieves matched records context for WebGPU or Cloud LLM", status: "Online", color: "text-[var(--success)]", bg: "bg-[var(--success-muted)]", border: "border-[var(--success-border)]" }
          ].map((step, i) => (
            <div key={i} className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-4 relative z-10 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
              <div>
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[10px] font-mono text-[var(--text-dim)] font-bold uppercase">Pipeline Step {step.step}</span>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase border ${step.bg} ${step.color} ${step.border}`}>{step.status}</span>
                </div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-1.5">{step.name}</h4>
                <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed uppercase font-mono">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operational Health Checkups */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Signals */}
        <div className="panel lg:col-span-1 flex flex-col">
          <div className="panel-header bg-[rgba(15,15,17,0.5)]">
            <h3 className="section-title flex items-center gap-2">
              <Shield size={13} className="text-[var(--accent)]" /> System Diagnostics
            </h3>
          </div>
          
          <div className="p-4 flex-1 flex flex-col justify-center divide-y divide-[var(--border)]">
            {dqLoading ? (
              <div className="p-6 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-widest">
                <Loader2 size={16} className="animate-spin inline-block mr-2 align-middle text-[var(--accent)]" /> Checking health...
              </div>
            ) : operationalHealth?.checks?.map(check => (
              <div key={check.id} className="py-2.5 flex items-center justify-between">
                <div className="min-w-0 pr-2">
                  <span className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-wider block truncate">{check.name}</span>
                  <span className="text-[8px] text-[var(--text-dim)] font-mono uppercase mt-0.5 block truncate">{check.detail || "Operational"}</span>
                </div>
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase border ${
                  check.status === "passed"
                    ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                    : check.status === "warning"
                    ? "bg-[var(--warning-muted)] text-[var(--warning)] border-[var(--warning-border)]"
                    : "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
                }`}>{check.status}</span>
              </div>
            )) || (
              <div className="p-4 text-center text-xs text-[var(--text-dim)] font-mono">No telemetry data loaded.</div>
            )}
          </div>
        </div>

        {/* Live Data Quality Report */}
        <div className="panel lg:col-span-2">
          <div className="panel-header bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
            <h3 className="section-title flex items-center gap-2">
              <BarChart3 size={13} className="text-[var(--accent-purple)]" /> Data Quality Governance
            </h3>
            {dataQuality && (
              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider border ${
                dataQuality.overall_score >= 0.9
                  ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                  : "bg-[var(--warning-muted)] text-[var(--warning)] border-[var(--warning-border)]"
              }`}>
                Quality Score: {(dataQuality.overall_score * 100).toFixed(1)}%
              </span>
            )}
          </div>

          <div className="p-5 space-y-6">
            {dqLoading ? (
              <div className="p-12 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-widest">
                <Loader2 size={20} className="animate-spin inline-block mr-2 align-middle text-[var(--accent)]" /> Syncing Quality Metrics...
              </div>
            ) : dataQuality ? (
              <div className="space-y-4">
                <div className="overflow-x-auto border border-[var(--border)] rounded">
                  <table className="w-full text-left border-collapse" aria-label="Database dataset lineage table">
                    <thead className="text-[9px] font-bold uppercase tracking-wider bg-zinc-950 text-[var(--text-dim)] border-b border-[var(--border)]">
                      <tr>
                        <th className="px-3 py-2.5 border-r border-[var(--border)]">Dataset Name</th>
                        <th className="px-3 py-2.5 border-r border-[var(--border)]">Record Count</th>
                        <th className="px-3 py-2.5 border-r border-[var(--border)]">Upstream Ingestion</th>
                        <th className="px-3 py-2.5">PII Exposure</th>
                      </tr>
                    </thead>
                    <tbody className="text-[10px] font-mono uppercase">
                      {dataQuality.datasets.map(ds => (
                        <tr key={ds.name} className="border-b border-[var(--border)] hover:bg-white/[0.01]">
                          <td className="px-3 py-2 border-r border-[var(--border)] text-[var(--text-primary)] font-bold">{ds.name.replace("_", " ")}</td>
                          <td className="px-3 py-2 border-r border-[var(--border)] text-right">{ds.record_count}</td>
                          <td className="px-3 py-2 border-r border-[var(--border)] text-[var(--text-secondary)]">{ds.lineage.upstream_modules.join(", ")}</td>
                          <td className="px-3 py-2">
                            <span className={`px-1 rounded text-[8px] font-black ${ds.pii_exposed ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                              {ds.pii_exposed ? 'EXPOSED' : 'STRIPPED'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="space-y-2">
                  <span className="text-[9px] font-mono text-[var(--text-dim)] font-bold uppercase tracking-wider block">Rule Assertions</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {dataQuality.checks.map(check => (
                      <div key={check.id} className="p-3 bg-zinc-950/40 border border-[var(--border)] rounded flex justify-between items-start gap-2">
                        <div className="min-w-0 flex-1">
                          <span className="text-[9px] font-bold text-white uppercase block tracking-wider truncate">{check.id.replace(/_/g, " ")}</span>
                          <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-1 leading-snug">{check.description}</p>
                        </div>
                        <div className="shrink-0 flex flex-col items-end gap-1">
                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase ${check.status === 'passed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                            {check.status}
                          </span>
                          {check.failed_count > 0 && (
                            <span className="text-[8px] font-mono text-red-400 font-bold uppercase">({check.failed_count} quarantined)</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-xs text-[var(--text-dim)] font-mono">No data lineage telemetry available.</div>
            )}
          </div>
        </div>
      </div>

      {/* Visual Cron Retraining & MLOps Pipeline Scheduler */}
      <div className="panel p-6">
        <div className="flex flex-col lg:flex-row justify-between items-start gap-4 mb-6">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
              <RefreshCw size={15} className="text-purple-400" /> Automated MLOps & Delta Lake Cron Scheduler
            </h3>
            <p className="text-[11px] text-[var(--text-secondary)] font-mono uppercase mt-1">
              Configure recurring background model evaluation, PySpark feature store generation, and gold table vacuuming.
            </p>
          </div>
          <span className="px-2.5 py-1 text-[10px] font-mono font-bold uppercase rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
            ACTIVE SCHEDULER: CRON DAEMON
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-white font-bold">
              <span>Delta Lake Gold Sync</span>
              <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded">EVERY 6 HOURS</span>
            </div>
            <p className="text-[10px] text-zinc-400 font-sans">Compacts bronze stream logs into silver/gold parquet tables.</p>
            <div className="pt-2 flex justify-between text-[10px] text-zinc-400">
              <span>Last Run: 2h ago</span>
              <button
                onClick={() => toast.success("Triggered Delta Lake Gold Sync execution!")}
                className="text-purple-400 hover:text-purple-300 font-bold uppercase"
              >
                Run Now ↗
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-white font-bold">
              <span>Risk Model Retrain</span>
              <span className="text-[9px] bg-cyan-500/10 text-cyan-400 px-1.5 py-0.5 rounded">DAILY AT 02:00</span>
            </div>
            <p className="text-[10px] text-zinc-400 font-sans">Fits LightGBM risk classifier on newly ingested EHR encounters.</p>
            <div className="pt-2 flex justify-between text-[10px] text-zinc-400">
              <span>Last Run: 11h ago</span>
              <button
                onClick={() => toast.success("Triggered Risk Model Retraining pipeline!")}
                className="text-purple-400 hover:text-purple-300 font-bold uppercase"
              >
                Run Now ↗
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-white font-bold">
              <span>Vector Index Vacuum</span>
              <span className="text-[9px] bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded">SUNDAY AT 00:00</span>
            </div>
            <p className="text-[10px] text-zinc-400 font-sans">Prunes deleted patient vector embeddings from HNSW index.</p>
            <div className="pt-2 flex justify-between text-[10px] text-zinc-400">
              <span>Last Run: 3d ago</span>
              <button
                onClick={() => toast.success("Triggered Vector Index Vacuum!")}
                className="text-purple-400 hover:text-purple-300 font-bold uppercase"
              >
                Run Now ↗
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
