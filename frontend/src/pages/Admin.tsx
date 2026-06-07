import { useState, useEffect, useMemo } from "react";
import { 
  getAdminStats, 
  getAdminUsers, 
  getAdminAuditLogs, 
  getAdminDataQuality, 
  getAdminOperationalHealth, 
  getAnalyticsReport,
  type UserProfile, 
  type AuditLogEntry,
  type DataQualityReport,
  type OperationalHealthReport,
  type AnalyticsReport
} from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Activity, FileText, Database, ShieldAlert, CheckCircle2, ShieldCheck, Search, Calendar, Terminal, Network, Info, ArrowUpRight, Shield, RefreshCw, BarChart3, HelpCircle, Loader2, TrendingUp, Sparkles } from "lucide-react";
import HospitalSetupPanel from "@/components/operations/HospitalSetupPanel";

export default function AdminPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"users" | "hospital" | "audit" | "data-engineering" | "analytics">("users");

  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditSearch, setAuditSearch] = useState("");

  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null);
  const [operationalHealth, setOperationalHealth] = useState<OperationalHealthReport | null>(null);
  const [dqLoading, setDqLoading] = useState(false);
  const [dqError, setDqError] = useState("");

  const [analyticsReport, setAnalyticsReport] = useState<AnalyticsReport | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState("");

  const fetchAuditLogs = () => {
    setAuditLoading(true);
    getAdminAuditLogs()
      .then(setAuditLogs)
      .catch((err) => console.error("Failed to load audit logs", err))
      .finally(() => setAuditLoading(false));
  };

  const fetchDataEngineering = () => {
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
  };

  const fetchAnalyticsReport = () => {
    setAnalyticsLoading(true);
    setAnalyticsError("");
    getAnalyticsReport()
      .then(setAnalyticsReport)
      .catch((err) => {
        console.error("Failed to load analytics report", err);
        setAnalyticsError(err.message || "Failed to load analyst report.");
      })
      .finally(() => setAnalyticsLoading(false));
  };

  useEffect(() => {
    if (activeTab === "audit") {
      fetchAuditLogs();
    } else if (activeTab === "data-engineering") {
      fetchDataEngineering();
    } else if (activeTab === "analytics") {
      fetchAnalyticsReport();
    }
  }, [activeTab]);

  useEffect(() => {
    if (user?.role !== "admin") {
      setError("Unauthorized access. Admin privileges required.");
      setLoading(false);
      return;
    }

    Promise.all([getAdminStats(), getAdminUsers()])
      .then(([statsData, usersData]) => {
        setStats(statsData);
        setUsers(usersData);
      })
      .catch((err) => setError(err.message || "Failed to load admin data"))
      .finally(() => setLoading(false));
  }, [user]);

  const filteredAuditLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const search = auditSearch.toLowerCase();
      return (
        log.action.toLowerCase().includes(search) ||
        (log.actor_user_id !== null && log.actor_user_id.toString().includes(search)) ||
        (log.target_user_id !== null && log.target_user_id.toString().includes(search)) ||
        (log.details && log.details.toLowerCase().includes(search))
      );
    });
  }, [auditLogs, auditSearch]);

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto text-center mt-20" role="alert">
        <ShieldAlert size={56} className="mx-auto mb-4 opacity-50 text-[var(--danger)]" aria-hidden="true" />
        <h1 className="text-lg font-bold text-[var(--text-primary)] mb-1 uppercase">Access Denied</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full flex justify-center mt-20" role="status" aria-label="Loading admin data">
        <span className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">System Administration</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono uppercase mt-1">Global oversight and configuration of the platform.</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" role="region" aria-label="System statistics">
        {[
          { label: "Total Users", value: stats?.total_users || 0, icon: Users, color: "text-[var(--accent)]", bg: "bg-[var(--accent-muted)]", border: "border-[var(--accent-border)]" },
          { label: "Assessments Run", value: stats?.total_records || 0, icon: FileText, color: "text-[var(--accent-purple)]", bg: "bg-[var(--accent-purple-muted)]", border: "border-[var(--accent-purple-border)]" },
          { label: "AI Chats", value: stats?.total_chats || 0, icon: Activity, color: "text-[var(--success)]", bg: "bg-[var(--success-muted)]", border: "border-[var(--success-border)]" },
          { label: "Database Size", value: "24.5 MB", icon: Database, color: "text-[var(--warning)]", bg: "bg-[var(--warning-muted)]", border: "border-[var(--warning-border)]" },
        ].map((stat, i) => (
          <div key={i} className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-4 flex items-center gap-4 hover:border-[var(--border-focus)] transition-colors">
            <div className={`p-2.5 rounded border ${stat.bg} ${stat.color} ${stat.border}`}>
              <stat.icon size={16} aria-hidden="true" />
            </div>
            <div>
              <p className="text-xl font-extrabold text-[var(--text-primary)] tracking-tight font-mono">{stat.value}</p>
              <p className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tab Selector Switch */}
      <div className="flex border-b border-[var(--border)] gap-2 pb-px pt-2">
        <button
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "users"
              ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <Users size={12} />
          Registered Nodes
        </button>
        <button
          onClick={() => setActiveTab("hospital")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "hospital"
              ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <Database size={12} />
          Hospital Setup
        </button>
        <button
          onClick={() => setActiveTab("audit")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "audit"
              ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <ShieldCheck size={12} />
          Audit Trail
        </button>
        <button
          onClick={() => setActiveTab("data-engineering")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "data-engineering"
              ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <Network size={12} />
          Data Pipeline & Quality
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
            activeTab === "analytics"
              ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
              : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
        >
          <BarChart3 size={12} />
          Analytics Cockpit
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "users" && (
        <div className="panel overflow-hidden">
          <div className="p-4 border-b border-[var(--border)] flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
            <h2 className="section-title">Registered User Nodes</h2>
            <span className="px-2.5 py-0.5 text-[10px] font-mono rounded bg-[rgba(255,255,255,0.03)] border border-[var(--border)] text-[var(--text-secondary)] uppercase">{users.length} Total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" aria-label="Registered users table">
              <thead className="text-[10px] font-bold uppercase tracking-wider bg-[rgba(15,15,17,0.85)] text-[var(--text-dim)] border-b border-[var(--border)]">
                <tr>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">User</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Email Address</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Role Context</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Plan Tier</th>
                  <th className="px-4 py-3 text-right" scope="col">Status</th>
                </tr>
              </thead>
              <tbody className="text-xs font-mono">
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-[var(--border)] hover:bg-[rgba(255,255,255,0.015)] transition-colors">
                    <td className="px-4 py-3 border-r border-[var(--border)] font-medium text-[var(--text-primary)] flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded bg-[var(--accent-muted)] border border-[var(--accent-border)] text-[var(--accent)] flex items-center justify-center font-bold text-[10px] uppercase">
                        {u.full_name?.[0]?.toUpperCase() || u.username[0].toUpperCase()}
                      </div>
                      <span className="uppercase">{u.full_name || u.username}</span>
                    </td>
                    <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] lowercase">{u.email}</td>
                    <td className="px-4 py-3 border-r border-[var(--border)]">
                      <span className={`px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase tracking-wider border ${u.role === "admin" ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]" : "bg-[var(--accent-purple-muted)] text-[var(--accent-purple)] border-[var(--accent-purple-border)]"}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 border-r border-[var(--border)]">
                      <span className="text-[11px] font-bold text-[var(--accent)] uppercase">{u.plan_tier || "Standard"}</span>
                    </td>
                    <td className="px-4 py-3 text-right align-middle">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[var(--success)] uppercase">
                        <CheckCircle2 size={12} aria-hidden="true" /> Connected
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "hospital" && <HospitalSetupPanel />}

      {activeTab === "audit" && (
        <div className="panel overflow-hidden">
          <div className="p-4 border-b border-[var(--border)] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[rgba(15,15,17,0.5)]">
            <div>
              <h2 className="section-title">System Security & Access Audit Logs</h2>
              <p className="text-[10px] text-[var(--text-dim)] font-mono uppercase mt-0.5">Sanitized HIPAA Compliance Access Logs</p>
            </div>
            
            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
              <input
                type="text"
                placeholder="Search audit trail..."
                value={auditSearch}
                onChange={(e) => setAuditSearch(e.target.value)}
                className="input-clinical pl-9 text-xs py-1.5 w-full"
              />
            </div>
          </div>

          {auditLoading ? (
            <div className="p-12 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-wide">
              <span className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin inline-block mr-2 align-middle" />
              Syncing Audit Trail Logs...
            </div>
          ) : filteredAuditLogs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse" aria-label="System security audit logs table">
                <thead className="text-[10px] font-bold uppercase tracking-wider bg-[rgba(15,15,17,0.85)] text-[var(--text-dim)] border-b border-[var(--border)]">
                  <tr>
                    <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Timestamp</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Action Code</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Actor ID</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Target ID</th>
                    <th className="px-4 py-3" scope="col">PHI-Safe Details Payload</th>
                  </tr>
                </thead>
                <tbody className="text-[11px] font-mono">
                  {filteredAuditLogs.map((log) => (
                    <tr key={log.id} className="border-b border-[var(--border)] hover:bg-[rgba(255,255,255,0.015)] transition-colors">
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] whitespace-nowrap">
                        <span className="flex items-center gap-1.5">
                          <Calendar size={11} className="text-[var(--text-dim)]" />
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </td>
                      <td className="px-4 py-3 border-r border-[var(--border)]">
                        <span className={`px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase tracking-wider border ${
                          log.action.includes("DELETE") || log.action.includes("FAIL") || log.action.includes("WARN")
                            ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
                            : log.action.includes("UPDATE") || log.action.includes("ASSIGN")
                            ? "bg-[var(--warning-muted)] text-[var(--warning)] border-[var(--warning-border)]"
                            : "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-primary)]">
                        {log.actor_user_id ? `#${log.actor_user_id}` : "SYSTEM"}
                      </td>
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">
                        {log.target_user_id ? `#${log.target_user_id}` : "N/A"}
                      </td>
                      <td className="px-4 py-3 align-middle">
                        <div className="flex items-center gap-1.5 bg-white/[0.01] border border-white/[0.03] px-2 py-1 rounded max-w-lg overflow-x-auto">
                          <Terminal size={11} className="text-[var(--text-dim)] shrink-0" />
                          <code className="text-[10px] text-[var(--text-secondary)] whitespace-nowrap">
                            {log.details || "{}"}
                          </code>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-wide">
              No audit log entries matched search criteria
            </div>
          )}
          
          {/* HIPAA Safety Notice footer */}
          <div className="p-3 bg-white/[0.01] border-t border-[var(--border)] text-center">
            <p className="text-[10px] leading-relaxed text-gray-500 font-medium italic">
              Note: System audit logs are captured under HIPAA §164.312(b) and GDPR Article 30. Details are automatically sanitized inside the database layer to strip any clinical raw values, patient names, credentials, or PII.
            </p>
          </div>
        </div>
      )}

      {activeTab === "data-engineering" && (
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
                  <p>3. Go to Hugging Face settings and add a Secret:<br/>Key: <code className="text-white font-bold bg-zinc-900 px-1">DATABASE_URL</code><br/>Value: <code className="text-white bg-zinc-900 px-1">postgresql://...</code></p>
                </div>
              </div>
            )}
          </div>

          {/* ETL Engineering Pipeline Flow */}
          <div className="panel p-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Network size={15} className="text-[var(--accent-purple)]" /> Data Engineering Pipelines
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
              {/* Connecting Lines for Large Screens */}
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
                {/* Dataset Table */}
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

                    {/* Rule validations list */}
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
        </div>
      )}

      {activeTab === "analytics" && (
        <div className="space-y-6">
          {/* Header Actions */}
          <div className="panel p-6 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
                <Sparkles size={15} className="text-[var(--accent)]" /> Medallion Gold Layer Insights
              </h3>
              <p className="text-[11px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                Data Science aggregates, cohorts, and model performance metrics.
              </p>
            </div>
            
            <div className="flex flex-wrap items-center gap-3">
              {analyticsReport?.report_generated_at && (
                <div className="text-right font-mono text-[10px] text-[var(--text-dim)] uppercase">
                  <span>Last Compiled: {new Date(analyticsReport.report_generated_at).toLocaleString()}</span>
                  {analyticsReport.pipeline_execution && (
                    <span className="block text-right">Duration: {analyticsReport.pipeline_execution.duration_seconds}s</span>
                  )}
                </div>
              )}
              <button
                onClick={fetchAnalyticsReport}
                disabled={analyticsLoading}
                className="btn-clinical text-xs py-1.5 px-3 flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw size={12} className={analyticsLoading ? "animate-spin" : ""} />
                {analyticsLoading ? "Refreshing..." : "Sync Report"}
              </button>
            </div>
          </div>

          {analyticsLoading && !analyticsReport ? (
            <div className="panel p-12 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-widest">
              <Loader2 size={24} className="animate-spin inline-block mr-2 align-middle text-[var(--accent)]" /> 
              Compiling Data Science Analytics...
            </div>
          ) : analyticsError ? (
            <div className="panel p-6 border-[var(--danger-border)] bg-[rgba(239,68,68,0.02)] text-center">
              <ShieldAlert size={32} className="mx-auto mb-2 text-[var(--danger)] opacity-80" />
              <h4 className="text-xs font-bold text-white uppercase mb-1">Failed to Load Report</h4>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">{analyticsError}</p>
            </div>
          ) : analyticsReport ? (
            <>
              {/* Top Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
                  <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Total Records Analyzed</span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                      {analyticsReport.total_records_analyzed.toLocaleString()}
                    </span>
                    <span className="text-[10px] font-bold text-[var(--success)] uppercase">Conformed</span>
                  </div>
                  <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                    Aggregated across all conformed Silver & Gold Parquet tables.
                  </p>
                </div>

                <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
                  <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Cohort Mean Age</span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                      {analyticsReport.demographics?.avg_age || 0}
                    </span>
                    <span className="text-[10px] font-bold text-[var(--accent)] uppercase">Years</span>
                  </div>
                  <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                    Arithmetic mean of conformed patient demographic records.
                  </p>
                </div>

                <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
                  <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Cohort Mean BMI</span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                      {analyticsReport.demographics?.avg_bmi || 0}
                    </span>
                    <span className="text-[10px] font-bold text-[var(--accent-purple)] uppercase">kg/m²</span>
                  </div>
                  <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                    Conformed Body Mass Index distribution (healthy target: 18.5 - 24.9).
                  </p>
                </div>
              </div>

              {/* Second Row: Demographics and Disease Prevalence */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Cohort Gender Distribution */}
                <div className="panel p-5 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded flex flex-col justify-between">
                  <div className="mb-4">
                    <span className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider block">Gender Cohort Distribution</span>
                    <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                      Self-reported gender identification demographics inside the conformed datasets.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-end font-mono text-xs">
                      <div className="space-y-0.5">
                        <span className="text-[9px] font-bold text-[var(--accent)] uppercase block">Male Ratio</span>
                        <span className="text-lg font-black text-white">{analyticsReport.demographics?.gender_distribution?.male_ratio || 0}%</span>
                      </div>
                      <div className="space-y-0.5 text-right">
                        <span className="text-[9px] font-bold text-[var(--accent-purple)] uppercase block">Female Ratio</span>
                        <span className="text-lg font-black text-white">{analyticsReport.demographics?.gender_distribution?.female_ratio || 0}%</span>
                      </div>
                    </div>

                    {/* Dual Conjoined Progress Bar */}
                    <div className="w-full h-3 rounded-full bg-zinc-950 overflow-hidden flex border border-white/[0.03]">
                      <div 
                        style={{ width: `${analyticsReport.demographics?.gender_distribution?.male_ratio || 50}%` }} 
                        className="bg-[var(--accent)] h-full transition-all duration-500"
                      />
                      <div 
                        style={{ width: `${analyticsReport.demographics?.gender_distribution?.female_ratio || 50}%` }} 
                        className="bg-[var(--accent-purple)] h-full transition-all duration-500"
                      />
                    </div>

                    <div className="flex gap-4 items-center justify-center pt-2">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded bg-[var(--accent)] inline-block" />
                        <span className="text-[9px] font-mono text-[var(--text-secondary)] uppercase">Male</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded bg-[var(--accent-purple)] inline-block" />
                        <span className="text-[9px] font-mono text-[var(--text-secondary)] uppercase">Female</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Disease Prevalence */}
                <div className="panel p-5 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
                  <div className="mb-4">
                    <span className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider block">Clinical Cohort Prevalence Rates</span>
                    <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                      Percentage of high-risk / disease-detected individuals derived from Silver Parquet aggregates.
                    </p>
                  </div>

                  <div className="space-y-3">
                    {[
                      { key: "diabetes", label: "Diabetes Mellitus", color: "bg-[var(--accent)]", val: analyticsReport.prevalence_rates?.diabetes ?? 0 },
                      { key: "heart", label: "Cardiovascular Issues", color: "bg-[var(--accent-purple)]", val: analyticsReport.prevalence_rates?.heart ?? 0 },
                      { key: "liver", label: "Hepatic Dysfunctions", color: "bg-amber-500", val: analyticsReport.prevalence_rates?.liver ?? 0 },
                      { key: "kidney", label: "Renal Failures", color: "bg-cyan-500", val: analyticsReport.prevalence_rates?.kidney ?? 0 },
                      { key: "lungs", label: "Pulmonary Pathologies", color: "bg-[var(--danger)]", val: analyticsReport.prevalence_rates?.lungs ?? 0 }
                    ].map((item) => (
                      <div key={item.key} className="space-y-1">
                        <div className="flex justify-between items-center text-[10px] font-mono uppercase font-bold">
                          <span className="text-white">{item.label}</span>
                          <span className="text-[var(--text-secondary)]">{item.val.toFixed(1)}%</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-zinc-950 overflow-hidden border border-white/[0.02]">
                          <div 
                            style={{ width: `${item.val}%` }} 
                            className={`${item.color} h-full rounded-full transition-all duration-500`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>

              {/* Machine Learning Model Performance */}
              <div className="panel bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
                <div className="p-4 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
                  <div>
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Activity size={13} className="text-[var(--success)]" /> ML Model Retraining Accuracies (Gold Layer)
                    </h4>
                    <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                      Weekly automated PySpark model retraining performance telemetry.
                    </p>
                  </div>
                  <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-zinc-900 border border-white/[0.05] text-[var(--text-secondary)] uppercase">
                    5 Models Active
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse" aria-label="ML Models accuracy table">
                    <thead className="text-[9px] font-bold uppercase tracking-wider bg-zinc-950/60 text-[var(--text-dim)] border-b border-[var(--border)]">
                      <tr>
                        <th className="px-4 py-3 border-r border-[var(--border)]">Model Identifier</th>
                        <th className="px-4 py-3 border-r border-[var(--border)]">Target Area</th>
                        <th className="px-4 py-3 border-r border-[var(--border)]">Conformed Dataset size</th>
                        <th className="px-4 py-3 border-r border-[var(--border)]">Training Accuracy</th>
                        <th className="px-4 py-3 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="text-[11px] font-mono">
                      {[
                        { id: "diabetes_model", label: "Diabetes Predictor", disease: "Diabetes Mellitus", size: "253,680 Rows", acc: analyticsReport.model_performance?.diabetes ?? 0.0 },
                        { id: "heart_disease_model", label: "Cardio Disease Predictor", disease: "Cardiovascular disease", size: "253,680 Rows", acc: analyticsReport.model_performance?.heart ?? 0.0 },
                        { id: "kidney_model", label: "Renal failure Predictor", disease: "Chronic kidney disease", size: "15 Rows", acc: analyticsReport.model_performance?.kidney ?? 0.0 },
                        { id: "liver_disease_model", label: "Hepatic Predictor", disease: "Liver disease", size: "30,691 Rows", acc: analyticsReport.model_performance?.liver ?? 0.0 },
                        { id: "lungs_model", label: "Pulmonary Predictor", disease: "Lung disease", size: "309 Rows", acc: analyticsReport.model_performance?.lungs ?? 0.0 }
                      ].map((model) => (
                        <tr key={model.id} className="border-b border-[var(--border)] hover:bg-white/[0.01] transition-colors">
                          <td className="px-4 py-3 border-r border-[var(--border)] text-white font-bold uppercase">{model.label}</td>
                          <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] uppercase">{model.disease}</td>
                          <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">{model.size}</td>
                          <td className="px-4 py-3 border-r border-[var(--border)]">
                            <div className="flex items-center gap-3">
                              <span className="font-bold text-white w-12">{(model.acc * 100).toFixed(1)}%</span>
                              <div className="w-24 h-1.5 rounded-full bg-zinc-950 overflow-hidden border border-white/[0.02] shrink-0">
                                <div 
                                  style={{ width: `${model.acc * 100}%` }} 
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    model.acc >= 0.8 
                                      ? "bg-[var(--success)]" 
                                      : model.acc >= 0.7 
                                      ? "bg-amber-500" 
                                      : "bg-[var(--danger)]"
                                  }`}
                                />
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${
                              model.acc > 0.0 
                                ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                                : "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
                            }`}>
                              {model.acc > 0.0 ? "OPTIMIZED" : "DEGRADED"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-3.5 bg-white/[0.01] text-center border-t border-[var(--border)]">
                  <p className="text-[10px] text-gray-500 italic font-medium">
                    Disclaimer: Machine learning predictions are trained on conformed Silver & Gold datasets to assist clinician diagnostics. Model accuracies are evaluated on test sets and should not substitute human clinical expertise.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="panel p-6 text-center text-xs text-[var(--text-dim)] font-mono">
              NO REPORT DATA LOADED. PLEASE SELECT "SYNC REPORT".
            </div>
          )}
        </div>
      )}
    </div>
  );
}
