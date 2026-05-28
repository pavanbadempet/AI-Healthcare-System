"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
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
} from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import { getAdminOperationsCockpit, type AdminOperationsCockpitData } from "@/lib/api";

type RoleProfile = {
  title: string;
  description: string;
  actions: { label: string; href: string }[];
};

const roleProfiles: Record<string, RoleProfile> = {
  admin: {
    title: "Admin command view",
    description: "Hospital-wide throughput, department queues, consent-led exchange, and finance visibility.",
    actions: [
      { label: "Operations summary", href: "/dashboard" },
      { label: "Patient registry", href: "/patients" },
      { label: "Capacity board", href: "/capacity" },
    ],
  },
  doctor: {
    title: "Doctor care-team view",
    description: "Assigned patient panel, clinician-reviewed signals, orders, diagnostics, and discharge context.",
    actions: [
      { label: "Assigned patient panel", href: "/patients" },
      { label: "AI copilot", href: "/chat" },
      { label: "Diagnostics", href: "/predict" },
    ],
  },
  nurse: {
    title: "Nursing coordination view",
    description: "Task worklists, care timeline events, bedside observations, and overdue care coordination.",
    actions: [
      { label: "Patient registry", href: "/patients" },
      { label: "Capacity board", href: "/capacity" },
      { label: "Care timeline", href: "/dashboard" },
    ],
  },
  pharmacist: {
    title: "Pharmacy operations view",
    description: "Prescription queues, low-stock visibility, dispense status, and medication workflow handoffs.",
    actions: [
      { label: "Prescription queues", href: "/dashboard" },
      { label: "Patient medication view", href: "/patients" },
      { label: "Inventory signals", href: "/dashboard" },
    ],
  },
  billing: {
    title: "Billing operations view",
    description: "Invoices, cashier payments, outstanding balances, and encounter-linked revenue workflow.",
    actions: [
      { label: "Invoice queue", href: "/dashboard" },
      { label: "Patient billing view", href: "/patients" },
      { label: "Admin revenue metrics", href: "/admin" },
    ],
  },
  patient: {
    title: "Patient record view",
    description: "Own timeline, appointments, reports, AI-assisted education, and export consent controls.",
    actions: [
      { label: "My dashboard", href: "/dashboard" },
      { label: "Appointments", href: "/telemedicine" },
      { label: "Health assistant", href: "/chat" },
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
      detail: `${numberValue(data.hospital.active_admissions)} active admissions`,
    },
    {
      label: "Open clinical orders",
      value: numberValue(data.hospital.open_orders),
      icon: ClipboardList,
      tone: "text-[var(--warning)]",
      detail: `${numberValue(data.hospital.occupied_beds)} occupied beds`,
    },
    {
      label: "Monitoring signals",
      value: numberValue(data.monitoring.open_signals),
      icon: HeartPulse,
      tone: "text-[var(--danger)]",
      detail: `${numberValue(data.monitoring.total_vital_observations)} observations`,
    },
    {
      label: "Diagnostics pending review",
      value: numberValue(data.diagnostics.pending_review),
      icon: FlaskConical,
      tone: "text-[var(--accent-blue)]",
      detail: `${numberValue(data.diagnostics.abnormal_results)} abnormal results`,
    },
    {
      label: "Low stock items",
      value: numberValue(data.pharmacy.low_stock_items),
      icon: Pill,
      tone: "text-[var(--warning)]",
      detail: `${numberValue(data.pharmacy.active_prescriptions)} active prescriptions`,
    },
    {
      label: "Outstanding balance",
      value: moneyValue(data.billing.outstanding_balance),
      icon: CreditCard,
      tone: "text-[var(--accent)]",
      detail: `${moneyValue(data.billing.total_collected)} collected`,
    },
    {
      label: "Discharge drafts",
      value: numberValue(data.discharge.draft_summaries),
      icon: FileCheck2,
      tone: "text-[var(--success)]",
      detail: `${numberValue(data.discharge.finalized_summaries)} finalized`,
    },
    {
      label: "Nursing overdue",
      value: numberValue(data.nursing.overdue_tasks),
      icon: Activity,
      tone: "text-[var(--danger)]",
      detail: `${numberValue(data.nursing.assigned_tasks)} assigned tasks`,
    },
    {
      label: "Active consents",
      value: numberValue(data.interoperability.active_consents),
      icon: ShieldCheck,
      tone: "text-[var(--success)]",
      detail: `${numberValue(data.interoperability.total_exports)} exports logged`,
    },
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
      .catch((err) => setError(err.message || "Failed to load operations cockpit"))
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
          <div className="section-label mb-2 flex items-center gap-2 text-[var(--accent)]">
            <Radio size={13} aria-hidden="true" />
            Live hospital workflow layer
          </div>
          <h2 id="operations-cockpit-title" className="text-2xl font-semibold tracking-tight text-[var(--text-primary)]">
            Hospital Operations Cockpit
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
            Role-scoped operational visibility across OPD, IPD, monitoring, diagnostics, pharmacy, billing, discharge,
            nursing, care events, and interoperability.
          </p>
        </div>
        <div className="glass-card min-w-full p-4 lg:min-w-[320px]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)]">
              {isAdmin ? <Users size={17} aria-hidden="true" /> : <Stethoscope size={17} aria-hidden="true" />}
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--text-primary)]">{roleProfile.title}</p>
              <p className="text-xs leading-5 text-[var(--text-dim)]">{roleProfile.description}</p>
            </div>
          </div>
        </div>
      </div>

      {isAdmin ? (
        <div className="p-5">
          {loading && (
            <div className="rounded-md border border-[var(--border)] bg-[var(--bg-card)] p-5 text-sm text-[var(--text-secondary)]" role="status">
              Loading hospital operations metrics...
            </div>
          )}
          {error && (
            <div className="rounded-md border border-[var(--danger-border)] bg-[var(--danger-muted)] p-5 text-sm text-[var(--danger)]" role="alert">
              {error}
            </div>
          )}
          {adminData && (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {cards.map((card) => (
                <div key={card.label} className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4">
                  <div className="mb-5 flex items-start justify-between">
                    <div>
                      <p className="section-label">{card.label}</p>
                      <p className="mt-2 text-2xl font-semibold tracking-tight text-[var(--text-primary)]">{card.value}</p>
                    </div>
                    <card.icon className={card.tone} size={18} aria-hidden="true" />
                  </div>
                  <p className="mono-meta">{card.detail}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 p-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <h3 className="section-title mb-4">Role workflow access</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              {roleProfile.actions.map((action) => (
                <Link
                  key={action.label}
                  href={action.href}
                  className="rounded-md border border-[var(--border)] bg-[rgba(255,244,230,0.025)] p-3 text-sm font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--border-focus)] hover:bg-[rgba(255,244,230,0.045)]"
                >
                  {action.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-[var(--accent-border)] bg-[var(--accent-muted)] p-5">
            <div className="mb-3 flex items-center gap-2 text-[var(--accent)]">
              <AlertTriangle size={16} aria-hidden="true" />
              <h3 className="text-sm font-semibold">Clinical boundary</h3>
            </div>
            <p className="text-sm leading-6 text-[var(--text-secondary)]">
              Clinician review remains required for every AI-assisted signal.
            </p>
            <p className="mt-3 text-xs leading-5 text-[var(--text-dim)]">
              The cockpit organizes operational data and does not diagnose, prescribe, or replace licensed staff decisions.
            </p>
          </div>
        </div>
      )}

      <div className="border-t border-[var(--border)] bg-[var(--bg-primary)] px-5 py-3">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] font-mono uppercase tracking-[0.14em] text-[var(--text-dim)]">
          <span className="flex items-center gap-2 text-[var(--success)]">
            <FileText size={12} aria-hidden="true" />
            Workflow coverage online
          </span>
          <span>OPD/IPD</span>
          <span>Monitoring</span>
          <span>Diagnostics</span>
          <span>Pharmacy</span>
          <span>Billing</span>
          <span>Discharge</span>
          <span>Nursing</span>
          <span>Interop</span>
        </div>
      </div>
    </section>
  );
}
