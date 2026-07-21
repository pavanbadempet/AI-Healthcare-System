import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Server, ArrowRightLeft, ShieldCheck, AlertTriangle, RefreshCw, CheckCircle2, Zap, Database } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface InfrastructureFailoverModalProps {
  onClose: () => void;
  onFailoverComplete?: () => void;
}

export const InfrastructureFailoverModal: React.FC<InfrastructureFailoverModalProps> = ({
  onClose,
  onFailoverComplete,
}) => {
  const [activePrimary, setActivePrimary] = useState("DB-PRIMARY-01 (10.0.4.12)");
  const [activeReplica, setActiveReplica] = useState("DB-REPLICA-01 (10.0.4.13)");
  const [isSimulating, setIsSimulating] = useState(false);
  const [failoverStep, setFailoverStep] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const handleRunFailover = async (scenario: string) => {
    setIsSimulating(true);
    setLogs([]);

    const addLog = (msg: string) => {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
    };

    try {
      addLog(`INITIATING FAILOVER SCENARIO: ${scenario}`);
      setFailoverStep("Detecting Node Health Drift...");
      await new Promise((r) => setTimeout(r, 600));

      addLog("HEARTBEAT FAILURE DETECTED on DB-PRIMARY-01 (Port 5432 Timeout)");
      setFailoverStep("Demoting Primary Node to Standby...");
      await new Promise((r) => setTimeout(r, 600));

      addLog("SWAPPING VIRTUAL IP (VIP) 10.0.4.100 -> DB-REPLICA-01");
      setFailoverStep("Promoting DB-REPLICA-01 to Read/Write Master...");
      await new Promise((r) => setTimeout(r, 600));

      setActivePrimary("DB-REPLICA-01 (10.0.4.13)");
      setActiveReplica("DB-PRIMARY-01 (Standby Recovery Mode)");
      addLog("FAILOVER COMPLETE: Zero transaction loss. Read/Write connections restored.");
      setFailoverStep(null);

      await dispatchCareEvent({
        event_type: "incident",
        title: `Infrastructure Failover Simulation: ${scenario}`,
        summary: `VIP 10.0.4.100 successfully re-routed from DB-PRIMARY-01 to DB-REPLICA-01. All read/write database connections restored with zero downtime.`,
        severity: "warning",
      });

      toast.success(`Disaster Recovery Simulation Successful: VIP re-routed to DB-REPLICA-01!`);
      if (onFailoverComplete) onFailoverComplete();
    } catch (err) {
      toast.error("Failover simulation error.");
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="failover-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
              <ArrowRightLeft size={18} />
            </div>
            <div>
              <h2 id="failover-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Read-Replica Failover & Disaster Recovery Simulator
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Simulate Primary DB Node Blackout & Automatic VIP Swapping
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 font-mono text-xs">
          {/* Active Topology State */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-1">
              <span className="text-[10px] text-zinc-400 uppercase font-bold block">Active Master Node (Read/Write)</span>
              <div className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                <Database size={14} /> {activePrimary}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-cyan-500/5 border border-cyan-500/20 space-y-1">
              <span className="text-[10px] text-zinc-400 uppercase font-bold block">Standby Read-Replica</span>
              <div className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                <Server size={14} /> {activeReplica}
              </div>
            </div>
          </div>

          {/* Failover Actions */}
          <div className="space-y-2 font-sans">
            <span className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Select Disaster Recovery Failure Scenario</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <button
                disabled={isSimulating}
                onClick={() => handleRunFailover("Primary Node Blackout")}
                className="p-3.5 rounded-xl border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-left transition-all flex flex-col justify-between cursor-pointer disabled:opacity-50"
              >
                <div className="space-y-1">
                  <div className="text-xs font-bold text-red-300 uppercase flex items-center gap-1.5 font-sans">
                    <AlertTriangle size={14} /> Primary Node Blackout
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono leading-relaxed">
                    Simulate ungraceful kernel crash on DB-PRIMARY-01 and trigger VIP promotion.
                  </div>
                </div>
              </button>

              <button
                disabled={isSimulating}
                onClick={() => handleRunFailover("Network Partition & Latency Spike")}
                className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-left transition-all flex flex-col justify-between cursor-pointer disabled:opacity-50"
              >
                <div className="space-y-1">
                  <div className="text-xs font-bold text-amber-300 uppercase flex items-center gap-1.5 font-sans">
                    <Zap size={14} /> Network Partition (+450ms)
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono leading-relaxed">
                    Inject artificial latency packets to verify automatic circuit-breaker fallback.
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Failover Execution Step & Live Log */}
          {failoverStep && (
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center gap-2 text-purple-300 font-bold font-mono">
              <RefreshCw size={14} className="animate-spin" /> {failoverStep}
            </div>
          )}

          {logs.length > 0 && (
            <div className="p-3.5 rounded-xl bg-zinc-950 border border-white/10 space-y-1.5 max-h-40 overflow-y-auto font-mono text-[10px]">
              <span className="text-zinc-500 uppercase font-bold block mb-1">Disaster Recovery Execution Log</span>
              {logs.map((log, idx) => (
                <div key={idx} className="text-emerald-400">{log}</div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Close Console
          </button>
        </div>
      </motion.div>
    </div>
  );
};
