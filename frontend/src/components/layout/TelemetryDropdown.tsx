/**
 * TelemetryDropdown – Live system status widget.
 * Extracted from TopNav.tsx for maintainability.
 */
import { useState, useEffect, useRef } from "react";
import { ChevronDown, Cpu, Network, Database, Server } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Tooltip from "./Tooltip";

export default function TelemetryDropdown() {
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const telemetryRef = useRef<HTMLDivElement>(null);
  const [telemetryStats, setTelemetryStats] = useState({ cpu: 12, latency: 22 });

  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetryStats({
        cpu: Math.floor(Math.random() * 8) + 8,
        latency: Math.floor(Math.random() * 6) + 19,
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (telemetryOpen && telemetryRef.current && !telemetryRef.current.contains(event.target as Node)) {
        setTelemetryOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [telemetryOpen]);

  return (
    <div ref={telemetryRef} className="relative">
      <Tooltip content="System Telemetry & Load Status" position="bottom">
        <button
          onClick={() => setTelemetryOpen(!telemetryOpen)}
          className="status-badge status-badge-success flex items-center gap-1 px-2.5 py-1 rounded-full text-[9px] cursor-pointer hover:bg-[var(--success-muted)] border-[var(--success-border)] transition-colors font-bold uppercase"
          aria-label="Toggle system telemetry details"
        >
          <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" />
          <span className="hidden sm:inline">Telemetry</span>
          <ChevronDown
            size={9}
            className={`transition-transform duration-200 ${telemetryOpen ? "rotate-180" : ""}`}
          />
        </button>
      </Tooltip>

      <AnimatePresence>
        {telemetryOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-[38px] w-64 pt-1 z-50"
          >
            <div className="glass-card p-3.5 bg-[rgba(15,15,18,0.95)] border border-[var(--border-focus)] rounded-xl shadow-[var(--shadow-lg)]">
              <h3 className="section-label text-[var(--success)] mb-2.5 flex items-center gap-1">
                <Cpu size={10} /> Live System Status
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase text-[var(--text-secondary)] mb-1">
                    <span>CPU Core Load</span>
                    <span className="text-[var(--text-primary)]">{telemetryStats.cpu}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden border border-white/[0.02]">
                    <motion.div
                      className="h-full bg-[var(--success)] rounded-full"
                      animate={{ width: `${telemetryStats.cpu}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                  <span className="text-[var(--text-secondary)] flex items-center gap-1">
                    <Network size={10} className="text-sky-400" /> API Latency
                  </span>
                  <span className="text-sky-400 font-bold">{telemetryStats.latency} ms</span>
                </div>

                <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                  <span className="text-[var(--text-secondary)] flex items-center gap-1">
                    <Database size={10} className="text-amber-400" /> FHIR Broker
                  </span>
                  <span className="text-[var(--success)] font-bold">Synced</span>
                </div>

                <div className="flex justify-between items-center text-[10px] font-bold font-mono uppercase border-t border-white/[0.03] pt-2">
                  <span className="text-[var(--text-secondary)] flex items-center gap-1">
                    <Server size={10} className="text-purple-400" /> SQLite Store
                  </span>
                  <span className="text-[var(--text-primary)] font-bold">0.5 MB</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
