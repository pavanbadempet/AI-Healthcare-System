"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useTelemetry } from "@/lib/useTelemetry";
import { BedDouble, Users, ArrowRight, TrendingUp, Building2, MapPin, Wifi, WifiOff } from "lucide-react";

export default function CapacityPage() {
  const [mounted, setMounted] = useState(false);
  const { data: telemetry, status: wsStatus } = useTelemetry();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Derive values from live telemetry or use defaults
  const totalCensus = telemetry ? telemetry.active_census : 412;
  const totalCapacity = telemetry ? telemetry.total_capacity : 450;
  const occupancyPct = Math.round((totalCensus / totalCapacity) * 100);
  const edBoarding = telemetry ? telemetry.ed_boarding : 18;
  const edAvgWait = telemetry ? telemetry.ed_avg_wait_min : 145;
  const pendingDischarges = telemetry ? telemetry.pending_discharges : 34;
  const confirmedDischarges = telemetry ? telemetry.confirmed_discharges : 12;
  const surgePct = telemetry ? telemetry.surge_prediction_pct : 15;
  const bedUnits = telemetry?.bed_units ?? [
    { unit: "ICU-A", total: 20, occupied: 18, cleaning: 1, available: 1 },
    { unit: "MED-SURG 4B", total: 40, occupied: 35, cleaning: 2, available: 3 },
  ];

  const statusLabel = occupancyPct > 90
    ? "CODE RED"
    : occupancyPct > 80
    ? "CODE YELLOW"
    : "NORMAL OPERATIONS";

  const statusColor = occupancyPct > 90
    ? "text-[var(--danger)]"
    : occupancyPct > 80
    ? "text-[var(--warning)]"
    : "text-[var(--success)]";

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Top Status Bar */}
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[11px] font-mono tracking-widest text-[var(--text-dim)] uppercase" role="status" aria-label="Capacity status bar">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5 text-[var(--accent)]">
            <div className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-pulse" aria-hidden="true" />
            LIVE ADT FEED
          </span>
          <span>CAPACITY COMMAND CENTER</span>
        </div>
        <div className="flex gap-4 items-center">
          <span className={statusColor}>HOSPITAL STATUS: {statusLabel}</span>
          {wsStatus === "connected" ? (
            <span className="flex items-center gap-1 text-[var(--success)]"><Wifi size={10} aria-hidden="true" /> LIVE</span>
          ) : (
            <span className="flex items-center gap-1 text-[var(--danger)]"><WifiOff size={10} aria-hidden="true" /> OFFLINE</span>
          )}
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-1 tracking-tight flex items-center gap-3">
              Bed Board & Capacity
              <span className={`text-[11px] ${occupancyPct > 90 ? "bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]" : "bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]"} border px-2 py-1 rounded uppercase tracking-widest align-middle`}>
                {occupancyPct}% OCCUPANCY
              </span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono mt-1">Real-time throughput, discharge predictions, and hospital census.</p>
          </div>

          <div className="flex gap-3">
            <button className="btn btn-secondary text-xs font-bold uppercase tracking-wider flex items-center gap-2" aria-label="Change facility">
              <Building2 size={14} aria-hidden="true" /> Change Facility
            </button>
            <button className="btn btn-primary text-xs font-bold uppercase tracking-wider flex items-center gap-2" aria-label="Request patient transfer">
              <ArrowRight size={14} aria-hidden="true" /> Request Transfer
            </button>
          </div>
        </motion.div>

        {/* Top KPIs — all driven by telemetry */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4" role="region" aria-label="Capacity key metrics">
          <div className="panel p-4 flex flex-col justify-between">
            <h3 className="section-label mb-4 flex items-center gap-2">
              <BedDouble size={14} aria-hidden="true" /> Total Census
            </h3>
            <div className="flex items-end justify-between">
              <span className="text-4xl font-light text-[var(--text-primary)] font-mono">
                {totalCensus}<span className="text-sm text-[var(--text-dim)]">/{totalCapacity}</span>
              </span>
              <span className="text-[11px] font-mono text-[var(--danger)]">
                {occupancyPct > 85 ? "CRITICAL" : "STABLE"}
              </span>
            </div>
          </div>

          <div className="panel p-4 flex flex-col justify-between">
            <h3 className="section-label mb-4 flex items-center gap-2">
              <Users size={14} aria-hidden="true" /> ED Boarding
            </h3>
            <div className="flex items-end justify-between">
              <span className="text-4xl font-light text-[var(--warning)] font-mono">{edBoarding}</span>
              <span className="text-[11px] font-mono text-[var(--warning)]">Avg {edAvgWait}m Wait</span>
            </div>
          </div>

          <div className="panel p-4 flex flex-col justify-between">
            <h3 className="section-label mb-4 flex items-center gap-2">
              <ArrowRight size={14} aria-hidden="true" /> Pending Discharges
            </h3>
            <div className="flex items-end justify-between">
              <span className="text-4xl font-light text-[var(--success)] font-mono">{pendingDischarges}</span>
              <span className="text-[11px] font-mono text-[var(--text-secondary)]">{confirmedDischarges} Confirmed</span>
            </div>
          </div>

          <div className="bg-[var(--danger-muted)] border border-[var(--danger-border)] p-4 flex flex-col justify-between">
            <h3 className="text-[11px] font-bold uppercase tracking-widest text-[var(--danger)] mb-4 flex items-center gap-2">
              <TrendingUp size={14} aria-hidden="true" /> AI Surge Predictor
            </h3>
            <div className="flex items-end justify-between">
              <span className="text-3xl font-light text-[var(--danger)] font-mono">+{surgePct}%</span>
              <span className="text-[11px] font-mono text-[var(--danger)]">In next 4 hours</span>
            </div>
          </div>
        </div>

        {/* Deep Dive Bed Grid — driven by telemetry bed_units */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="panel">
              <div className="panel-header flex justify-between items-center bg-[var(--bg-card)]">
                <h3 className="section-title">Unit Capacity Matrix</h3>
                <div className="flex gap-3 text-[11px] font-mono text-[var(--text-dim)]">
                  <span className="flex items-center gap-1"><div className="w-2 h-2 bg-[var(--success)]" aria-hidden="true" /> OPEN</span>
                  <span className="flex items-center gap-1"><div className="w-2 h-2 bg-[var(--danger)]" aria-hidden="true" /> OCCUPIED</span>
                  <span className="flex items-center gap-1"><div className="w-2 h-2 bg-[var(--warning)]" aria-hidden="true" /> CLEANING</span>
                </div>
              </div>

              <div className="p-5 space-y-6">
                {bedUnits.map((unit) => {
                  const unitOccPct = Math.round((unit.occupied / unit.total) * 100);
                  return (
                    <div key={unit.unit} role="region" aria-label={`${unit.unit} bed status`}>
                      <div className="flex justify-between items-end mb-3">
                        <h4 className="text-sm font-semibold text-[var(--text-primary)]">{unit.unit}</h4>
                        <span className={`text-xs font-mono font-bold ${unitOccPct > 85 ? "text-[var(--danger)]" : unitOccPct > 70 ? "text-[var(--warning)]" : "text-[var(--success)]"}`}>
                          {unit.occupied}/{unit.total} OCCUPIED ({unitOccPct}%)
                        </span>
                      </div>
                      <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
                        {Array.from({ length: unit.total }).map((_, i) => {
                          let cellType: "occupied" | "cleaning" | "open";
                          if (i < unit.occupied) cellType = "occupied";
                          else if (i < unit.occupied + unit.cleaning) cellType = "cleaning";
                          else cellType = "open";

                          const prefix = unit.unit.substring(0, 1);
                          return (
                            <motion.div
                              key={i}
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: i * 0.01 }}
                              className={`h-10 border flex items-center justify-center text-[11px] font-mono font-bold ${
                                cellType === "occupied"
                                  ? "bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]"
                                  : cellType === "cleaning"
                                  ? "bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]"
                                  : "bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]"
                              }`}
                              aria-label={`Bed ${prefix}${String(i + 1).padStart(2, "0")}: ${cellType}`}
                            >
                              {prefix}{String(i + 1).padStart(2, "0")}
                            </motion.div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="lg:col-span-1 space-y-6">
            <div className="panel h-full flex flex-col">
              <div className="panel-header bg-[var(--bg-card)]">
                <h3 className="section-title">High Acuity Transfers</h3>
              </div>
              <div className="flex-1 p-0 divide-y divide-[var(--border)] overflow-y-auto max-h-[500px]">
                {[1, 2, 3, 4, 5].map((item) => (
                  <div key={item} className="p-4 hover:bg-[var(--bg-card)] transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)] animate-pulse" aria-hidden="true" />
                        <span className="text-xs font-bold text-[var(--text-primary)]">MRN-774{item}2</span>
                      </div>
                      <span className="text-[11px] font-mono text-[var(--warning)] border border-[var(--warning)]/30 px-1.5 py-0.5">PENDING BED</span>
                    </div>
                    <p className="text-[11px] text-[var(--text-secondary)] font-mono mb-2">
                      <MapPin size={10} className="inline mr-1" aria-hidden="true" />
                      ED Trauma Bay {item} → ICU-A
                    </p>
                    <div className="flex justify-between items-center section-label">
                      <span>Dx: STEMI</span>
                      <span>Wait: {15 * item}m</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
