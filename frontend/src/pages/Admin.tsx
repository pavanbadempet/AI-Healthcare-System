import { useState, useEffect, useMemo } from "react";
import { getAdminStats, getAdminUsers, getAdminAuditLogs, type UserProfile, type AuditLogEntry } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Activity, FileText, Database, ShieldAlert, CheckCircle2, ShieldCheck, Search, Calendar, Terminal } from "lucide-react";
import HospitalSetupPanel from "@/components/operations/HospitalSetupPanel";

export default function AdminPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"users" | "hospital" | "audit">("users");

  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditSearch, setAuditSearch] = useState("");

  const fetchAuditLogs = () => {
    setAuditLoading(true);
    getAdminAuditLogs()
      .then(setAuditLogs)
      .catch((err) => console.error("Failed to load audit logs", err))
      .finally(() => setAuditLoading(false));
  };

  useEffect(() => {
    if (activeTab === "audit") {
      fetchAuditLogs();
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
    </div>
  );
}
