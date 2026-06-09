import { useState, useEffect } from "react";
import { 
  getAdminStats, 
  getAdminUsers, 
  type UserProfile, 
} from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Activity, FileText, Database, ShieldAlert } from "lucide-react";
import HospitalSetupPanel from "@/components/operations/HospitalSetupPanel";
import UsersPanel from "@/components/admin/UsersPanel";
import AuditPanel from "@/components/admin/AuditPanel";
import DataEngineeringPanel from "@/components/admin/DataEngineeringPanel";
import AnalyticsPanel from "@/components/admin/AnalyticsPanel";

type AdminTab = "users" | "hospital" | "audit" | "data-engineering" | "analytics";

const TAB_CONFIG: { key: AdminTab; label: string; icon: React.ElementType }[] = [
  { key: "users", label: "Registered Nodes", icon: Users },
  { key: "hospital", label: "Hospital Setup", icon: Database },
  { key: "audit", label: "Audit Trail", icon: null as any }, // ShieldCheck imported below
  { key: "data-engineering", label: "Data Pipeline & Quality", icon: null as any }, // Network
  { key: "analytics", label: "Analytics Cockpit", icon: null as any }, // BarChart3
];

export default function AdminPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<AdminTab>("users");

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
        {([
          { key: "users", label: "Registered Nodes", icon: Users },
          { key: "hospital", label: "Hospital Setup", icon: Database },
          { key: "audit", label: "Audit Trail", icon: () => null },
          { key: "data-engineering", label: "Data Pipeline & Quality", icon: () => null },
          { key: "analytics", label: "Analytics Cockpit", icon: () => null },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as AdminTab)}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider transition-all border-b-2 cursor-pointer flex items-center gap-2 ${
              activeTab === tab.key
                ? "border-[var(--accent)] text-[var(--accent)] bg-white/[0.01]"
                : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <tab.icon size={12} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {activeTab === "users" && <UsersPanel users={users} />}
      {activeTab === "hospital" && <HospitalSetupPanel />}
      {activeTab === "audit" && <AuditPanel />}
      {activeTab === "data-engineering" && <DataEngineeringPanel stats={stats} />}
      {activeTab === "analytics" && <AnalyticsPanel />}
    </div>
  );
}
