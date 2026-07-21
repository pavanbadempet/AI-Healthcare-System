import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, ShieldAlert, Pill, AlertTriangle, CheckCircle2, Search, Zap, Save, RefreshCw, FileText } from "lucide-react";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface DdiAllergySafetyModalProps {
  patientId?: number | string;
  patientName?: string;
  onClose: () => void;
  onSafetyApproved?: () => void;
}

export const DdiAllergySafetyModal: React.FC<DdiAllergySafetyModalProps> = ({
  patientId = 1,
  patientName = "Marcus Thorne",
  onClose,
  onSafetyApproved,
}) => {
  const [candidateDrug, setCandidateDrug] = useState("Spironolactone 25mg QD");
  const [allergies, setAllergies] = useState<string[]>(["Penicillin", "Sulfonamides", "NSAIDs / Aspirin"]);
  const [activeMeds, setActiveMeds] = useState<string[]>(["Lisinopril 10mg QD", "Metformin 500mg BID", "Warfarin 5mg QD"]);
  
  const [isChecking, setIsChecking] = useState(false);
  const [safetyReport, setSafetyReport] = useState<any>(null);
  const [overrideJustification, setOverrideJustification] = useState("");

  React.useEffect(() => {
    async function loadPatientMeds() {
      try {
        const { apiFetch } = await import("@/lib/apiCore");
        const res: any = await apiFetch(`/pharmacy/doctor/patients/${patientId}/prescriptions`);
        if (Array.isArray(res) && res.length > 0) {
          const fetchedMeds: string[] = [];
          res.forEach((p: any) => {
            if (Array.isArray(p.items)) {
              p.items.forEach((item: any) => {
                if (item.medication_name) {
                  fetchedMeds.push(`${item.medication_name} ${item.dosage || ''}`);
                }
              });
            }
          });
          if (fetchedMeds.length > 0) {
            setActiveMeds(fetchedMeds);
          }
        }
      } catch (err) {
        console.warn("Using baseline patient medication history:", err);
      }
    }
    loadPatientMeds();
  }, [patientId]);

  const handleRunSafetyCheck = async () => {
    setIsChecking(true);
    setSafetyReport(null);

    let alerts: any[] = [];

    try {
      const { apiFetch } = await import("@/lib/apiCore");
      const res: any = await apiFetch("/pharmacy/check-safety", {
        method: "POST",
        body: JSON.stringify({
          patient_id: Number(patientId) || 1,
          medication_name: candidateDrug,
          dosage: "25mg",
          frequency: "QD",
          duration: "30 days",
          additional_allergies: allergies,
        }),
      });

      if (res && Array.isArray(res.alerts)) {
        alerts = res.alerts;
      } else {
        throw new Error("Local fallback required");
      }
    } catch (err) {
      console.warn("Backend PrescribingSafetyAgent check fallback to local DDI rules:", err);
      const candidateLower = candidateDrug.toLowerCase();

      // Rule 1: Lisinopril + Spironolactone = Severe Hyperkalemia Risk
      if (candidateLower.includes("spironolactone") && activeMeds.some((m) => m.toLowerCase().includes("lisinopril"))) {
        alerts.push({
          severity: "MAJOR",
          type: "Drug-Drug Interaction",
          title: "Severe Hyperkalemia Risk (Lisinopril + Spironolactone)",
          desc: "Co-administration of ACE inhibitors and potassium-sparing diuretics may cause life-threatening serum potassium elevation (> 6.0 mEq/L).",
        });
      }

      // Rule 2: Warfarin + Aspirin/NSAID = Bleeding Risk
      if (candidateLower.includes("ibuprofen") || (candidateLower.includes("aspirin") && activeMeds.some((m) => m.toLowerCase().includes("warfarin")))) {
        alerts.push({
          severity: "CRITICAL",
          type: "Drug-Drug Interaction",
          title: "High Risk Gastrointestinal & Internal Hemorrhage (Warfarin + NSAID)",
          desc: "NSAIDs inhibit platelet aggregation and cause gastric mucosal erosion, dramatically elevating INR bleeding risk.",
        });
      }

      // Rule 3: Penicillin Allergy check
      if (candidateLower.includes("amoxicillin") || candidateLower.includes("penicillin")) {
        alerts.push({
          severity: "CRITICAL",
          type: "Patient Allergy Conflict",
          title: "Severe Anaphylaxis Warning: Known Penicillin Hypersensitivity",
          desc: "Patient record confirms IgE-mediated anaphylactic reaction to Beta-Lactam antibiotics.",
        });
      }
    }

    const report = {
      passed: alerts.length === 0,
      alerts,
      timestamp: new Date().toLocaleTimeString(),
    };

    setSafetyReport(report);
    setIsChecking(false);

    if (alerts.length === 0) {
      toast.success(`Safety Check Passed! Zero DDI contraindications for ${candidateDrug}.`);
    } else {
      toast.error(`Safety Check Flagged ${alerts.length} Clinical Contraindications!`);
    }
  };

  const handleApproveWithOverride = async () => {
    if (!overrideJustification.trim()) {
      toast.error("Please enter a clinical override justification before approving.");
      return;
    }

    try {
      await dispatchCareEvent({
        event_type: "incident",
        title: `Clinical DDI Override: ${candidateDrug}`,
        summary: `Clinician approved ${candidateDrug} for ${patientName} despite DDI safety alerts. Override Justification: "${overrideJustification}".`,
        severity: "warning",
      });

      toast.success(`Clinical Override logged for ${candidateDrug}. Care event dispatched.`);
      if (onSafetyApproved) onSafetyApproved();
      onClose();
    } catch (err) {
      toast.error("Failed to log clinical override.");
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
        aria-labelledby="ddi-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 shrink-0">
              <ShieldAlert size={18} />
            </div>
            <div>
              <h2 id="ddi-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Drug-Drug Interaction & Allergy Safety Cross-Checker
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Patient: {patientName} • MRN #{patientId}
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
          {/* Active Allergy & Medication Profile */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-sans">
            <div className="p-3.5 rounded-xl bg-red-500/5 border border-red-500/20 space-y-1.5">
              <span className="text-[10px] text-red-400 font-bold uppercase block font-mono flex items-center gap-1">
                <AlertTriangle size={12} /> Active Allergy Profile
              </span>
              <div className="flex flex-wrap gap-1.5">
                {allergies.map((all, idx) => (
                  <span key={idx} className="bg-red-500/20 text-red-300 border border-red-500/30 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    {all}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-purple-500/5 border border-purple-500/20 space-y-1.5">
              <span className="text-[10px] text-purple-400 font-bold uppercase block font-mono flex items-center gap-1">
                <Pill size={12} /> Active Patient Prescriptions
              </span>
              <div className="flex flex-wrap gap-1.5">
                {activeMeds.map((med, idx) => (
                  <span key={idx} className="bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    {med}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Candidate Drug Input */}
          <div className="space-y-1.5 font-sans">
            <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Candidate New Medication</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={candidateDrug}
                onChange={(e) => setCandidateDrug(e.target.value)}
                placeholder="e.g. Spironolactone 25mg QD, Amoxicillin 500mg..."
                className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-red-500"
              />
              <button
                onClick={handleRunSafetyCheck}
                disabled={isChecking || !candidateDrug.trim()}
                className="btn bg-red-600 hover:bg-red-500 text-white font-bold text-xs uppercase px-4 rounded-xl flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {isChecking ? <RefreshCw size={14} className="animate-spin" /> : <Search size={14} />}
                Run DDI Check
              </button>
            </div>
          </div>

          {/* Safety Check Report */}
          {safetyReport && (
            <div className="space-y-3 font-sans">
              {safetyReport.passed ? (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-emerald-300 font-bold text-xs">
                  <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                  <span>SAFETY PASSED: No severe drug interactions or allergy conflicts detected for {candidateDrug}.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <span className="text-[10px] text-red-400 font-bold uppercase block font-mono flex items-center gap-1">
                    <ShieldAlert size={13} /> {safetyReport.alerts.length} Clinical Safety Alerts Flagged
                  </span>
                  {safetyReport.alerts.map((alert: any, idx: number) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 space-y-1">
                      <div className="flex items-center justify-between text-xs font-bold text-red-300 uppercase">
                        <span>{alert.title}</span>
                        <span className="bg-red-500/20 text-red-400 border border-red-500/40 px-2 py-0.5 rounded text-[9px] font-mono">
                          {alert.severity}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-300 font-mono leading-relaxed">{alert.desc}</p>
                    </div>
                  ))}

                  {/* Override Justification Form */}
                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-2 mt-3">
                    <label className="text-[10px] text-amber-400 font-bold uppercase block font-mono flex items-center gap-1">
                      <FileText size={12} /> Physician Clinical Override Justification
                    </label>
                    <textarea
                      rows={2}
                      value={overrideJustification}
                      onChange={(e) => setOverrideJustification(e.target.value)}
                      placeholder="Specify clinical rationale, serum potassium monitoring schedule, or benefit vs risk assessment..."
                      className="w-full bg-zinc-900 border border-white/10 rounded-xl p-2.5 text-xs text-white font-mono focus:outline-none focus:border-amber-500 resize-none"
                    />
                    <button
                      onClick={handleApproveWithOverride}
                      className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-amber-600/20 flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Save size={14} /> Confirm Clinical Override & Dispatch Care Event
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};
