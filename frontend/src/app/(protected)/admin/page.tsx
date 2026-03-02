"use client";

import { useState, useEffect } from "react";
import { getAdminStats, getAdminUsers, type UserProfile } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Activity, FileText, Database, ShieldAlert, CheckCircle2 } from "lucide-react";

export default function AdminPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto text-center mt-20" role="alert">
        <ShieldAlert size={64} className="mx-auto mb-6 opacity-50 text-[var(--danger)]" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Access Denied</h1>
        <p className="text-[var(--text-secondary)]">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full flex justify-center mt-20" role="status" aria-label="Loading admin data">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent)]" />
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-2 tracking-tight">System Administration</h1>
        <p className="text-[var(--text-secondary)] text-sm">Global oversight of the AI Healthcare platform.</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" role="region" aria-label="System statistics">
        {[
          { label: "Total Users", value: stats?.total_users || 0, icon: Users, color: "text-[var(--accent)]", bg: "bg-[var(--accent-muted)]", border: "border-[var(--accent-border)]" },
          { label: "Assessments Run", value: stats?.total_records || 0, icon: FileText, color: "text-[var(--accent-purple)]", bg: "bg-[var(--accent-purple-muted)]", border: "border-[var(--accent-purple-border)]" },
          { label: "AI Chats", value: stats?.total_chats || 0, icon: Activity, color: "text-[var(--success)]", bg: "bg-[var(--success-muted)]", border: "border-[var(--success-border)]" },
          { label: "Database Size", value: "24.5 MB", icon: Database, color: "text-[var(--warning)]", bg: "bg-[var(--warning-muted)]", border: "border-[var(--warning)]/20" },
        ].map((stat, i) => (
          <div key={i} className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-5 flex items-center gap-4 hover:border-[var(--border-focus)] transition-colors">
            <div className={`p-3 rounded-md border ${stat.bg} ${stat.color} ${stat.border}`}>
              <stat.icon size={20} aria-hidden="true" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--text-primary)] tracking-tight">{stat.value}</p>
              <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Users Table */}
      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg overflow-hidden">
        <div className="p-5 border-b border-[var(--border)] flex justify-between items-center bg-[var(--bg-secondary)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Registered Users</h2>
          <span className="px-2.5 py-1 text-[11px] font-medium rounded-md bg-[var(--border)] text-[var(--text-primary)]">{users.length} Total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left" aria-label="Registered users table">
            <thead className="text-[11px] uppercase tracking-wider bg-[var(--bg-card-hover)] text-[var(--text-dim)] border-b border-[var(--border)]">
              <tr>
                <th className="px-5 py-3 font-medium" scope="col">User</th>
                <th className="px-5 py-3 font-medium" scope="col">Email</th>
                <th className="px-5 py-3 font-medium" scope="col">Role</th>
                <th className="px-5 py-3 font-medium" scope="col">Tier</th>
                <th className="px-5 py-3 font-medium text-right" scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-card-hover)]/50 transition-colors">
                  <td className="px-5 py-3.5 font-medium text-[var(--text-primary)] flex items-center gap-3">
                    <div className="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-bold bg-[var(--accent-muted)] border border-[var(--accent-border)] text-[var(--accent)]">
                      {u.full_name?.[0]?.toUpperCase() || u.username[0].toUpperCase()}
                    </div>
                    {u.full_name || u.username}
                  </td>
                  <td className="px-5 py-3.5 text-[var(--text-secondary)]">{u.email}</td>
                  <td className="px-5 py-3.5">
                    <span className={`px-2 py-1 rounded-[4px] text-[11px] font-semibold uppercase tracking-wider border ${u.role === "admin" ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]" : "bg-[var(--accent-purple-muted)] text-[var(--accent-purple)] border-[var(--accent-purple-border)]"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-[12px] font-medium text-[var(--accent)]">{u.plan_tier || "Standard"}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--success)]">
                      <CheckCircle2 size={14} aria-hidden="true" /> Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
