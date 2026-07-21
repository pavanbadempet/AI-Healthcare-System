import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Activity, Thermometer, Clock, X } from "lucide-react";
import LiveECGMonitor from "./LiveECGMonitor";

export interface ClinicalBed {
  bed: string;
  name: string;
  status: "Stable" | "Alert";
  hr: number;
  spo2: number;
  bp: string;
  rr: number;
  ecgD: string;
}

interface BedCardProps {
  bed: ClinicalBed;
  isExpanded: boolean;
  onToggleExpand: () => void;
  patientDbId: number;
  isNurseCallActive: boolean;
  onToggleNurseCall: (active: boolean) => void;
  isCodeBlueActive: boolean;
  onTriggerCodeBlue: () => void;
  onRunAICheck: () => void;
  onNavigateToPatient: () => void;
  onPrefetchPatient: () => void;
  triggerRipple: (e: React.MouseEvent<HTMLElement>) => void;
}

const BedCard = memo(function BedCard({
  bed,
  isExpanded,
  onToggleExpand,
  patientDbId,
  isNurseCallActive,
  onToggleNurseCall,
  isCodeBlueActive,
  onTriggerCodeBlue,
  onRunAICheck,
  onNavigateToPatient,
  onPrefetchPatient,
  triggerRipple,
}: BedCardProps) {
  const isAlert = bed.status === "Alert";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onToggleExpand}
      className={`glass-card rounded-2xl p-5 relative overflow-hidden group transition-colors duration-300 cursor-pointer h-fit content-visibility-auto gpu-accelerated ${
        isAlert
          ? "ring-1 ring-[var(--danger)]/30 bg-[var(--danger-muted)]/40 hover:bg-[var(--danger-muted)]/60"
          : isExpanded
            ? "border-[var(--accent)] bg-white/[0.03] shadow-glow-indigo"
            : "hover:border-[var(--accent)]/30"
      }`}
    >
      {/* Header: Bed and Status */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className={`font-bold text-xs tracking-widest uppercase ${isAlert ? "text-[var(--danger)]" : "text-[var(--accent)]"}`}>
            {bed.bed}
          </span>
          <h4
            onClick={(e) => {
              e.stopPropagation();
              onNavigateToPatient();
            }}
            onMouseEnter={onPrefetchPatient}
            className="text-base font-bold text-[var(--text-primary)] hover:text-[var(--accent)] hover:underline uppercase tracking-wide mt-0.5 cursor-pointer block"
            title="Click to view full patient EMR profile"
          >
            {bed.name}
          </h4>
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
          isAlert
            ? "bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] status-pulse-ruby"
            : "bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)]"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${isAlert ? "bg-[var(--danger)] animate-ping" : "bg-[var(--success)]"}`} />
          {bed.status}
        </div>
      </div>

      {/* Animated ECG Waveform */}
      <div className="h-20 w-full mb-5 relative bg-black/20 rounded-lg p-1 border border-white/[0.02] overflow-hidden">
        <LiveECGMonitor hr={bed.hr} status={bed.status} />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[var(--bg-card)]/40 pointer-events-none" />
      </div>

      {/* Vitals Readings Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Heart Rate */}
        <div className={`rounded-xl p-2.5 border flex flex-col justify-between ${
          isAlert
            ? "bg-[var(--danger-muted)]/50 border-[var(--danger-border)]"
            : "bg-white/[0.02] border-white/[0.04] group-hover:border-white/[0.08]"
        }`}>
          <span className={`text-[9px] font-bold uppercase tracking-wider ${isAlert ? "text-[var(--danger)]" : "text-[var(--text-secondary)]"}`}>
            Heart Rate
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <Heart size={12} className={`shrink-0 self-center ${isAlert ? "text-[var(--danger)] animate-bounce" : "text-[var(--accent)]"}`} />
            <span className={`font-mono text-2xl font-black ${isAlert ? "text-[var(--danger)]" : "text-[var(--text-primary)]"}`}>
              {bed.hr}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] uppercase">BPM</span>
          </div>
        </div>

        {/* SpO2 */}
        <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">SpO2</span>
          <div className="flex items-baseline gap-1 mt-1">
            <Activity size={12} className="text-[var(--success)] shrink-0 self-center" />
            <span className="font-mono text-2xl font-black text-[var(--success)]">
              {bed.spo2}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] uppercase">%</span>
          </div>
        </div>

        {/* Blood Pressure */}
        <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">Blood Pressure</span>
          <div className="flex flex-col mt-1">
            <span className="font-mono text-base font-black text-[var(--text-primary)]">
              {bed.bp}
            </span>
            <span className="text-[8px] text-[var(--text-dim)] font-mono uppercase tracking-wider">
              MAP: {Math.round((Number(bed.bp.split('/')[0]) + 2 * Number(bed.bp.split('/')[1])) / 3)} mmHg
            </span>
          </div>
        </div>

        {/* Respiration */}
        <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
          <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">Respiration</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="font-mono text-lg font-black text-[var(--text-primary)]">
              {bed.rr}
            </span>
            <span className="text-[10px] text-[var(--text-dim)] uppercase">RPM</span>
          </div>
        </div>
      </div>

      {/* Expandable Details Area */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden mt-4 pt-4 border-t border-white/[0.04] space-y-3 text-xs"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] text-[var(--text-dim)] uppercase font-mono block">Patient EHR Status</span>
                <p className="text-[var(--text-secondary)] mt-0.5">Admitted: 48 hours ago</p>
                <p className="text-[var(--text-secondary)]">Condition: {isAlert ? "Decompensating" : "Stable / Recovery"}</p>
              </div>
              <div>
                <span className="text-[10px] text-[var(--text-dim)] uppercase font-mono block">Clinical Diagnostics</span>
                <div className="flex items-center gap-1.5 mt-0.5 text-[var(--text-secondary)]">
                  <Thermometer size={12} className="text-[var(--accent-purple)]" />
                  <span>Temp: {isAlert ? "101.4 °F" : "98.6 °F"}</span>
                </div>
                <div className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                  <Clock size={12} className="text-[var(--accent-blue)]" />
                  <span>Last Scan: 14 mins ago</span>
                </div>
              </div>
            </div>

            {/* Expanded Waveform Monitors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 pt-3 border-t border-white/[0.04]">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[9px] text-[var(--success)] font-bold uppercase tracking-wider">SpO2 Pleth Waveform</span>
                  <span className="text-[10px] text-[var(--success)] font-mono font-bold">{bed.spo2}%</span>
                </div>
                <div className="h-12 w-full relative bg-black/25 rounded-lg p-1 border border-white/[0.01] overflow-hidden">
                  <LiveECGMonitor hr={bed.hr} status={bed.status} mode="spo2" />
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[var(--bg-card)]/45 pointer-events-none" />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[9px] text-[#8656f5] font-bold uppercase tracking-wider">Respiration (Resp) Waveform</span>
                  <span className="text-[10px] text-[#8656f5] font-mono font-bold">{bed.rr} RPM</span>
                </div>
                <div className="h-12 w-full relative bg-black/25 rounded-lg p-1 border border-white/[0.01] overflow-hidden">
                  <LiveECGMonitor hr={bed.hr} status={bed.status} mode="resp" />
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[var(--bg-card)]/45 pointer-events-none" />
                </div>
              </div>
            </div>

            <div className="bg-white/[0.01] border border-white/[0.03] p-2.5 rounded-lg font-mono text-[10px] text-[var(--text-dim)] space-y-1">
              <div className="flex justify-between">
                <span>HL7 MESSAGE:</span>
                <span className="text-[var(--text-secondary)]">ADT^A08 EVENT</span>
              </div>
              <div className="flex justify-between">
                <span>ALARM CODE:</span>
                <span className={isAlert ? "text-[var(--danger)] font-bold animate-pulse" : "text-[var(--success)]"}>
                  {isAlert ? "SYS_ALARM_TACHY" : "SYS_NORMAL"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>TELEMETRY CHANNEL:</span>
                <span className="text-[var(--text-secondary)]">CH_ECG_II_PRIMARY</span>
              </div>
            </div>

            <div className="flex gap-2">
              {isNurseCallActive ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleNurseCall(false);
                  }}
                  className="btn btn-primary flex-1 py-1 text-[10px] font-bold uppercase tracking-wider bg-[var(--danger)] hover:bg-[var(--danger)]/80 text-white animate-pulse"
                >
                  Cancel Call
                </button>
              ) : (
                <>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRunAICheck();
                    }}
                    className="btn btn-secondary flex-1 py-1 text-[10px] font-bold uppercase tracking-wider border-white/[0.06] hover:border-[var(--accent-blue)]/50"
                  >
                    🔬 Run AI Check
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleNurseCall(true);
                    }}
                    className="btn btn-primary flex-1 py-1 text-[10px] font-bold uppercase tracking-wider bg-[var(--accent)] hover:bg-[var(--accent-hover)]"
                  >
                    📞 Call Nurse
                  </button>
                </>
              )}

              {isCodeBlueActive ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Custom resolving internally
                  }}
                  className="btn btn-danger flex-1 py-1 text-[10px] font-bold uppercase tracking-wider animate-pulse bg-red-600 hover:bg-red-700 text-white border-red-700"
                >
                  CODE BLUE ACTIVE
                </button>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    triggerRipple(e);
                    onTriggerCodeBlue();
                  }}
                  className="btn btn-cyber-danger flex-1 py-1 text-[10px] font-bold uppercase tracking-wider bg-red-950/40 border border-red-500/20 text-red-500 hover:bg-red-500 hover:text-white transition-all"
                >
                  🚨 Code Blue
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
});

export default BedCard;
