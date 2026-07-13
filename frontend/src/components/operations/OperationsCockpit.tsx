import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  ClipboardList,
  CreditCard,
  FileCheck2,
  FileText,
  FlaskConical,
  HeartPulse,
  Pill,
  Radio,
  ShieldCheck,
  Stethoscope,
  Users,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import { getAdminOperationsCockpit, type AdminOperationsCockpitData } from "@/lib/api";
import { safeApiMessage } from "@/lib/apiErrors";

type RoleProfile = {
  title: string;
  description: string;
  actions: { label: string; href: string; detail: string; icon: any }[];
};

const roleProfiles: Record<string, RoleProfile> = {
  admin: {
    title: "Admin Command Console",
    description: "Hospital-wide throughput, department queues, consent exchange, and revenue status.",
    actions: [
      { label: "Operations cockpit", href: "/dashboard", detail: "Real-time clinic throughput overview", icon: Radio },
      { label: "Patient database", href: "/patients", detail: "Longitudinal patient registries", icon: Users },
      { label: "Capacity board", href: "/capacity", detail: "Bed maps & ward metrics", icon: TrendingUp },
    ],
  },
  doctor: {
    title: "Doctor Care-Team Interface",
    description: "Assigned patient panel, clinical signals, diagnostic predictions, and AI copilot RAG.",
    actions: [
      { label: "Patient panel", href: "/patients", detail: "Active patient registry & vitals", icon: Stethoscope },
      { label: "AI Copilot RAG", href: "/chat", detail: "Consult clinical reference guides", icon: ShieldCheck },
      { label: "Model predictors", href: "/predict", detail: "Run clinical risk models", icon: FlaskConical },
    ],
  },
  nurse: {
    title: "Nursing Care Dashboard",
    description: "Bedside observations, medication schedules, and clinical task lists.",
    actions: [
      { label: "Active census", href: "/patients", detail: "Bedside monitoring & logs", icon: HeartPulse },
      { label: "Bed board", href: "/capacity", detail: "ADT ward map & unit occupancy", icon: Activity },
      { label: "Operations timeline", href: "/dashboard", detail: "Care timeline & checklist", icon: ClipboardList },
    ],
  },
  pharmacist: {
    title: "Pharmacy Operations Center",
    description: "Prescription queues, inventory signals, and medication dispensing.",
    actions: [
      { label: "Dispense queue", href: "/dashboard", detail: "Process medication orders", icon: Pill },
      { label: "Patient records", href: "/patients", detail: "View allergy lists & logs", icon: FileText },
      { label: "Supplies tracker", href: "/dashboard", detail: "Check low-stock diagnostics", icon: ClipboardList },
    ],
  },
  billing: {
    title: "Billing Operations Center",
    description: "Invoices, transactions, cashiering, and financial accounts.",
    actions: [
      { label: "Pending invoices", href: "/dashboard", detail: "Outstanding cashier invoices", icon: CreditCard },
      { label: "Patient financials", href: "/patients", detail: "Encounter ledger history", icon: FileText },
      { label: "System logs", href: "/admin", detail: "Database telemetry metrics", icon: Radio },
    ],
  },
  patient: {
    title: "My Health Hub",
    description: "Personal health timeline, upcoming consults, and secure medical records.",
    actions: [
      { label: "My dashboard", href: "/dashboard", detail: "My risk modeling trends", icon: Stethoscope },
      { label: "Telemedicine scheduler", href: "/telemedicine", detail: "Book virtual appointments", icon: Radio },
      { label: "AI assistant", href: "/chat", detail: "Learn about wellness indices", icon: ShieldCheck },
    ],
  },
};

function numberValue(value: number | undefined): string {
  return typeof value === "number" ? value.toLocaleString("en-IN") : "--";
}

function moneyValue(value: number | undefined): string {
  return typeof value === "number" ? `INR ${value.toLocaleString("en-IN")}` : "INR --";
}

function adminMetricCards(data: AdminOperationsCockpitData) {
  return [
    {
      label: "Open encounters",
      value: numberValue(data.hospital.open_encounters),
      icon: Stethoscope,
      tone: "text-[var(--accent)]",
      bg: "bg-[var(--accent-muted)]",
      border: "border-[var(--accent-border)] hover:border-[var(--accent)]",
      detail: `${numberValue(data.hospital.active_admissions)} active admissions`,
    },
    {
      label: "Open clinical orders",
      value: numberValue(data.hospital.open_orders),
      icon: ClipboardList,
      tone: "text-[var(--warning)]",
      bg: "bg-[var(--warning-muted)]",
      border: "border-[var(--warning-border)] hover:border-[var(--warning)]",
      detail: `${numberValue(data.hospital.occupied_beds)} occupied beds`,
    },
    {
      label: "Monitoring signals",
      value: numberValue(data.monitoring.open_signals),
      icon: HeartPulse,
      tone: "text-[var(--danger)]",
      bg: "bg-[var(--danger-muted)]",
      border: "border-[var(--danger-border)] hover:border-[var(--danger)]",
      detail: `${numberValue(data.monitoring.total_vital_observations)} observations`,
    },
    {
      label: "Diagnostics pending",
      value: numberValue(data.diagnostics.pending_review),
      icon: FlaskConical,
      tone: "text-[var(--accent-blue)]",
      bg: "bg-[var(--accent-blue-muted)]",
      border: "border-[var(--accent-blue-border)] hover:border-[var(--accent-blue)]",
      detail: `${numberValue(data.diagnostics.abnormal_results)} abnormal results`,
    },
    {
      label: "Low stock items",
      value: numberValue(data.pharmacy.low_stock_items),
      icon: Pill,
      tone: "text-[var(--warning)]",
      bg: "bg-[var(--warning-muted)]",
      border: "border-[var(--warning-border)] hover:border-[var(--warning)]",
      detail: `${numberValue(data.pharmacy.active_prescriptions)} active prescriptions`,
    },
    {
      label: "Outstanding balance",
      value: moneyValue(data.billing.outstanding_balance),
      icon: CreditCard,
      tone: "text-[var(--accent)]",
      bg: "bg-[var(--accent-muted)]",
      border: "border-[var(--accent-border)] hover:border-[var(--accent)]",
      detail: `${moneyValue(data.billing.total_collected)} collected`,
    },
    {
      label: "Discharge drafts",
      value: numberValue(data.discharge.draft_summaries),
      icon: FileCheck2,
      tone: "text-[var(--success)]",
      bg: "bg-[var(--success-muted)]",
      border: "border-[var(--success-border)] hover:border-[var(--success)]",
      detail: `${numberValue(data.discharge.finalized_summaries)} finalized`,
    },
    {
      label: "Nursing overdue",
      value: numberValue(data.nursing.overdue_tasks),
      icon: Activity,
      tone: "text-[var(--danger)]",
      bg: "bg-[var(--danger-muted)]",
      border: "border-[var(--danger-border)] hover:border-[var(--danger)]",
      detail: `${numberValue(data.nursing.assigned_tasks)} assigned tasks`,
    },
    {
      label: "Active consents",
      value: numberValue(data.interoperability.active_consents),
      icon: ShieldCheck,
      tone: "text-[var(--success)]",
      bg: "bg-[var(--success-muted)]",
      border: "border-[var(--success-border)] hover:border-[var(--success)]",
      detail: `${numberValue(data.interoperability.total_exports)} exports logged`,
    },
    ...(data.monitoring.spark_info?.spark_batch_id !== undefined ? [
      {
        label: "Spark Stream Engine",
        value: `Batch #${data.monitoring.spark_info.spark_batch_id}`,
        icon: Radio,
        tone: "text-[var(--accent-blue)]",
        bg: "bg-[var(--accent-blue-muted)]",
        border: "border-[var(--accent-blue-border)] hover:border-[var(--accent-blue)]",
        detail: `Latency: ${data.monitoring.spark_info.spark_latency_ms.toFixed(1)}ms | ML: ${data.monitoring.spark_info.spark_ml_latency_ms.toFixed(1)}ms | Ingest: ${data.monitoring.spark_info.spark_records_processed} recs`,
      }
    ] : []),
  ];
}

export default function OperationsCockpit() {
  const { user } = useAuthStore();
  const [adminData, setAdminData] = useState<AdminOperationsCockpitData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const role = user?.role || "patient";
  const roleProfile = roleProfiles[role] || roleProfiles.patient;
  const isAdmin = role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setAdminData(null);
      return;
    }
    setLoading(true);
    setError("");
    getAdminOperationsCockpit()
      .then(setAdminData)
      .catch((err) => setError(safeApiMessage(err)))
      .finally(() => setLoading(false));
  }, [isAdmin]);

  const cards = useMemo(() => {
    if (!adminData) return [];
    return adminMetricCards(adminData);
  }, [adminData]);

  return (
    <section className="panel overflow-hidden" aria-labelledby="operations-cockpit-title">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-2 text-[var(--accent)] tracking-wider">
            <Radio size={12} className="text-[var(--accent)] animate-pulse" aria-hidden="true" />
            Live Hospital Workflow Layer
          </div>
          <h2 id="operations-cockpit-title" className="text-lg font-bold text-[var(--text-primary)] uppercase tracking-wide">
            Operational Dashboard Cockpit
          </h2>
          <p className="mt-1 max-w-3xl text-xs text-[var(--text-secondary)] font-mono uppercase leading-relaxed">
            Role-scoped pipeline status spanning OPD/IPD, monitoring signals, predictive diagnostics, pharmacy stock, and consent exchange logs.
          </p>
        </div>
        
        <div className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.4)] p-4 lg:max-w-[340px] w-full flex items-center gap-3 hover:border-[var(--border-focus)] transition-colors">
          <div className="flex h-10 w-10 items-center justify-center rounded border border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)] shrink-0">
            {isAdmin ? <Users size={16} aria-hidden="true" /> : <Stethoscope size={16} aria-hidden="true" />}
          </div>
          <div>
            <p className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">{roleProfile.title}</p>
            <p className="text-[10px] text-[var(--text-secondary)] mt-0.5 leading-snug">{roleProfile.description}</p>
          </div>
        </div>
      </div>

      {isAdmin ? (
        <div className="p-5">
          {loading && (
            <div className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.2)] p-6 text-center text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider" role="status">
              Loading hospital operations metrics...
            </div>
          )}
          {error && (
            <div className="rounded border border-[var(--danger-border)] bg-[var(--danger-muted)] p-4 text-xs font-mono text-[var(--danger)] uppercase tracking-wider" role="alert">
              {error}
            </div>
          )}
          {adminData && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {cards.map((card, idx) => {
                const getCardStyle = (tone: string) => {
                  if (tone.includes("accent-blue")) {
                    return {
                      gradient: "from-cyan-950/20 via-cyan-900/5 to-black/40",
                      glow: "rgba(34, 211, 238, 0.25)"
                    };
                  }
                  if (tone.includes("accent")) {
                    return {
                      gradient: "from-indigo-950/20 via-indigo-900/5 to-black/40",
                      glow: "rgba(99, 102, 241, 0.25)"
                    };
                  }
                  if (tone.includes("warning")) {
                    return {
                      gradient: "from-amber-950/20 via-amber-900/5 to-black/40",
                      glow: "rgba(245, 158, 11, 0.25)"
                    };
                  }
                  if (tone.includes("danger")) {
                    return {
                      gradient: "from-rose-950/20 via-rose-900/5 to-black/40",
                      glow: "rgba(239, 68, 68, 0.25)"
                    };
                  }
                  if (tone.includes("success")) {
                    return {
                      gradient: "from-emerald-950/20 via-emerald-900/5 to-black/40",
                      glow: "rgba(16, 185, 129, 0.25)"
                    };
                  }
                  return {
                    gradient: "from-zinc-900/40 to-black/40",
                    glow: "rgba(255, 255, 255, 0.05)"
                  };
                };

                const style = getCardStyle(card.tone);

                return (
                  <motion.div 
                    key={card.label} 
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    className={`rounded-2xl border border-white/[0.06] bg-gradient-to-br ${style.gradient} hover:border-white/[0.12] p-5 flex flex-col justify-between transition-all duration-300 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.5)]`}
                  >
                    <div className="mb-4 flex items-start justify-between">
                      <div>
                        <p className="section-label text-[9px] tracking-wider">{card.label}</p>
                        <p className="mt-2.5 text-2xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">{card.value}</p>
                      </div>
                      <div 
                        className={`p-2 rounded-xl border border-white/10 ${card.bg} ${card.tone} transition-transform duration-500 hover:scale-110`}
                        style={{ filter: `drop-shadow(0 0 6px ${style.glow})` }}
                      >
                        <card.icon size={15} aria-hidden="true" />
                      </div>
                    </div>
                    <p className="mono-meta text-[9px] border-t border-white/[0.06] pt-2.5 mt-1">{card.detail}</p>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 p-5 lg:grid-cols-[1.2fr_0.8fr]">
          {/* Action List */}
          <div className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.2)] p-5">
            <h3 className="section-title mb-4 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
              <ClipboardList size={13} className="text-[var(--accent)]" />
              Role Workflow Actions
            </h3>
            
            <div className="grid gap-3 sm:grid-cols-2">
              {roleProfile.actions.map((action) => {
                const Icon = action.icon;
                return (
                  <Link
                    key={action.label}
                    to={action.href}
                    className="group rounded border border-[var(--border)] hover:border-[var(--border-focus)] bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.02)] p-4.5 transition-all flex items-start justify-between"
                  >
                    <div className="space-y-1">
                      <p className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide group-hover:text-[var(--accent)] transition-colors">
                        {action.label}
                      </p>
                      <p className="text-[9px] font-mono text-[var(--text-secondary)] uppercase tracking-wide">
                        {action.detail}
                      </p>
                    </div>
                    <div className="p-2 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.02)] text-[var(--text-dim)] group-hover:text-[var(--accent)] group-hover:border-[var(--accent-border)] transition-colors shrink-0">
                      <Icon size={14} aria-hidden="true" />
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
          
          {/* Legal Boundary Notice */}
          <div className="rounded border border-[var(--accent-border)] bg-[var(--accent-muted)] p-5 flex flex-col justify-between hover:border-[var(--accent)] transition-all duration-300">
            <div>
              <div className="mb-3.5 flex items-center gap-2 text-[var(--accent)]">
                <AlertTriangle size={15} aria-hidden="true" />
                <h3 className="text-xs font-bold uppercase tracking-wider">Clinical Safety Guard</h3>
              </div>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] font-mono uppercase">
                Active clinician review and diagnostic sign-off is required for all AI-assisted observations. The inference suite organizes telemetry records and does not prescribe, diagnose, or override qualified provider workflows.
              </p>
            </div>
            <div className="mt-4 text-[9px] font-mono text-[var(--text-dim)] border-t border-[var(--accent-border)] pt-3.5 uppercase">
              Escalate emergency cases to on-call clinical teams immediately.
            </div>
          </div>
        </div>
      )}

      {/* Ribbon bottom */}
      <div className="border-t border-[var(--border)] bg-[rgba(15,15,17,0.3)] px-5 py-3">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[10px] font-mono uppercase tracking-widest text-[var(--text-dim)]">
          <span className="flex items-center gap-1.5 text-[var(--success)] font-semibold">
            <ShieldCheck size={11} aria-hidden="true" />
            ADT / HL7 WORKFLOW COVERAGE ACTIVE
          </span>
          <span>OPD/IPD Admissions</span>
          <span>Monitoring Feed</span>
          <span>Diagnostics Suite</span>
          <span>Pharmacy Handoff</span>
          <span>Billing Records</span>
        </div>
      </div>
    </section>
  );
}
