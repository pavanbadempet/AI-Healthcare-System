/**
 * UsersPanel – Registered user nodes table for the Admin page.
 * Extracted from Admin.tsx for maintainability.
 */
import { CheckCircle2 } from "lucide-react";
import type { UserProfile } from "@/lib/api";

interface UsersPanelProps {
  users: UserProfile[];
}

export default function UsersPanel({ users }: UsersPanelProps) {
  return (
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
  );
}
