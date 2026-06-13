/**
 * AuditPanel – System Security & Access Audit Logs tab for the Admin page.
 * Extracted from Admin.tsx for maintainability.
 */
import { useMemo, useState, useEffect } from "react";
import { Search, Calendar, Terminal } from "lucide-react";
import { getAdminAuditLogs, type AuditLogEntry } from "@/lib/api";

export default function AuditPanel() {
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditSearch, setAuditSearch] = useState("");

  useEffect(() => {
    setAuditLoading(true);
    getAdminAuditLogs()
      .then(setAuditLogs)
      .catch((err) => console.error("Failed to load audit logs", err))
      .finally(() => setAuditLoading(false));
  }, []);

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

  return (
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
  );
}
