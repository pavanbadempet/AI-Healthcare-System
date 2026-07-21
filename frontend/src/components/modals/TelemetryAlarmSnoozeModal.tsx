import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, BellOff, Clock, CheckCircle2, AlertTriangle, ShieldCheck, Save } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface TelemetryAlarmSnoozeModalProps {
  bedCode: string;
  patientName?: string;
  alarmTitle: string;
  onClose: () => void;
  onSnoozeComplete: (snoozeMinutes: number, reason: string) => void;
}

export const TelemetryAlarmSnoozeModal: React.FC<TelemetryAlarmSnoozeModalProps> = ({
  bedCode,
  patientName = "Patient",
  alarmTitle,
  onClose,
  onSnoozeComplete,
}) => {
  const [snoozeMinutes, setSnoozeMinutes] = useState(15);
  const [reason, setReason] = useState("Artifact / Patient Motion");
  const [customNotes, setCustomNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const fullReason = customNotes.trim() ? `${reason} — ${customNotes.trim()}` : reason;

    try {
      await dispatchCareEvent({
        event_type: "rapid-response",
        title: `Telemetry alarm acknowledged & snoozed for ${bedCode}`,
        summary: `Alarm '${alarmTitle}' for bed ${bedCode} (${patientName}) snoozed for ${snoozeMinutes}m. Clinical Reason: ${fullReason}.`,
        severity: "info",
      });
      toast.success(`Alarm for ${bedCode} snoozed for ${snoozeMinutes} min.`);
      onSnoozeComplete(snoozeMinutes, fullReason);
      onClose();
    } catch (err) {
      toast.error("Failed to persist alarm resolution event.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-md overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alarm-snooze-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
              <BellOff size={18} />
            </div>
            <div>
              <h2 id="alarm-snooze-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Acknowledge Telemetry Alarm
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                {bedCode} • {patientName}
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4 font-mono text-xs">
          {/* Active Alarm Badge */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center gap-2 text-amber-300 font-sans">
            <AlertTriangle size={16} className="shrink-0" />
            <div>
              <span className="text-[10px] uppercase block font-bold text-amber-400">Triggered Alarm Parameter</span>
              <span className="text-xs font-bold text-white">{alarmTitle}</span>
            </div>
          </div>

          {/* Snooze Duration */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 uppercase font-bold block">Snooze Duration</label>
            <div className="grid grid-cols-4 gap-2 font-mono">
              {[5, 15, 30, 60].map((mins) => (
                <button
                  type="button"
                  key={mins}
                  onClick={() => setSnoozeMinutes(mins)}
                  className={`py-2 text-xs font-bold rounded-lg border transition-all ${
                    snoozeMinutes === mins
                      ? "bg-amber-500/20 border-amber-500 text-amber-300 shadow-md"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                  }`}
                >
                  {mins}m
                </button>
              ))}
            </div>
          </div>

          {/* Clinical Reason */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 uppercase font-bold block">Clinical Resolution Reason</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500 font-mono"
            >
              <option value="Artifact / Patient Motion">Artifact / Patient Motion</option>
              <option value="Lead / Sensor Dislodged">Lead / Sensor Dislodged</option>
              <option value="Physician Notified & Attending">Physician Notified & Attending</option>
              <option value="Patient Ambulating">Patient Ambulating</option>
              <option value="Medication Administered">Medication Administered</option>
              <option value="Other Clinical Reason">Other Clinical Reason</option>
            </select>
          </div>

          {/* Notes */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 uppercase font-bold block">Additional Clinical Notes (Optional)</label>
            <textarea
              rows={2}
              value={customNotes}
              onChange={(e) => setCustomNotes(e.target.value)}
              placeholder="e.g. Lead repositioned by RN..."
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500 font-mono resize-none"
            />
          </div>

          {/* Footer */}
          <div className="pt-2 flex items-center justify-between font-sans border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2 px-4"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn bg-amber-600 hover:bg-amber-500 text-white text-xs uppercase font-bold tracking-wide py-2 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-amber-600/20 disabled:opacity-50"
            >
              <ShieldCheck size={14} /> {isSubmitting ? "Saving..." : "Acknowledge & Snooze"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};
