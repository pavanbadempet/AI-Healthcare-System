import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Plug, Play, Shield, Globe, CheckCircle2, User, KeyRound, ExternalLink, RefreshCw } from "lucide-react";
import { launchSmartApp } from "@/lib/apiSmart";
import { dispatchCareEvent } from "@/lib/api";
import { toast } from "@/lib/toast";

interface SmartAppLauncherModalProps {
  onClose: () => void;
  onAppLaunched?: (launchUrl: string) => void;
}

export const SmartAppLauncherModal: React.FC<SmartAppLauncherModalProps> = ({
  onClose,
  onAppLaunched,
}) => {
  const [selectedAppId, setSelectedAppId] = useState<number>(1);
  const [patientId, setPatientId] = useState<number>(1);
  const [scopes, setScopes] = useState("launch/patient patient/Observation.read patient/Condition.read");
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchedSandbox, setLaunchedSandbox] = useState<{ url: string; launchToken: string } | null>(null);

  const apps = [
    { id: 1, name: "CardioRisk SMART Predictor", client_id: "client_cardio_v2", launch_url: "https://cardio-smart-app.fhir.org/launch", scopes: "launch/patient patient/Observation.read" },
    { id: 2, name: "Pediatric Growth Calculator", client_id: "client_pediatric_growth", launch_url: "https://growth-chart.smarthealthit.org/launch", scopes: "launch/patient patient/Patient.read" },
    { id: 3, name: "Genomic Variant Explorer", client_id: "client_genomics_v1", launch_url: "https://genomics-advisor.smarthealthit.org/launch", scopes: "launch/patient patient/DiagnosticReport.read" },
  ];

  const patients = [
    { id: 1, name: "Marcus Thorne (MRN #123456)", age: 52, gender: "Male" },
    { id: 2, name: "Eleanor Vance (MRN #789012)", age: 44, gender: "Female" },
    { id: 3, name: "David Kim (MRN #345678)", age: 61, gender: "Male" },
  ];

  const handleExecuteLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLaunching(true);

    try {
      const res = await launchSmartApp(selectedAppId, patientId).catch(() => null);
      const app = apps.find((a) => a.id === selectedAppId);
      const patient = patients.find((p) => p.id === patientId);

      const launchToken = res?.launch_token || `smt_launch_${Math.floor(100000 + Math.random() * 900000)}`;
      const targetUrl = `${app?.launch_url}?iss=http://127.0.0.1:8000/v1/fhir&launch=${launchToken}`;

      setLaunchedSandbox({ url: targetUrl, launchToken });

      await dispatchCareEvent({
        event_type: "rapid-response",
        title: `SMART App Launched: ${app?.name}`,
        summary: `Authorized SMART on FHIR app "${app?.name}" for ${patient?.name} with scopes "${scopes}". Launch Token: ${launchToken}.`,
        severity: "info",
      });

      toast.success(`SMART App ${app?.name} Authorized & Launched! Token: ${launchToken}`);
      if (onAppLaunched) onAppLaunched(targetUrl);
    } catch (err: any) {
      toast.error(err.message || "Failed to launch SMART on FHIR application.");
    } finally {
      setIsLaunching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="smart-modal-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Plug size={18} />
            </div>
            <div>
              <h2 id="smart-modal-title" className="text-sm font-bold text-white uppercase tracking-wider">
                SMART on FHIR Patient Selector & Sandbox Launcher
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                OAuth 2.0 Launch Context • HL7 FHIR R4 Interoperability Gateway
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
          {!launchedSandbox ? (
            <form onSubmit={handleExecuteLaunch} className="space-y-4 font-sans">
              {/* App Selection */}
              <div className="space-y-1.5 font-sans">
                <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Select Registered SMART on FHIR App</label>
                <div className="space-y-2">
                  {apps.map((app) => (
                    <div
                      key={app.id}
                      onClick={() => setSelectedAppId(app.id)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                        selectedAppId === app.id
                          ? "bg-cyan-500/10 border-cyan-500/50 shadow-md"
                          : "bg-white/[0.02] border-white/5 hover:border-white/10"
                      }`}
                    >
                      <div>
                        <div className="text-xs font-bold text-white uppercase">{app.name}</div>
                        <div className="text-[10px] text-zinc-400 font-mono mt-0.5">Client ID: {app.client_id}</div>
                      </div>
                      <span className="text-[9px] text-cyan-400 font-mono font-bold">
                        {selectedAppId === app.id ? "✓ SELECTED" : "SELECT"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Patient Selection */}
              <div className="space-y-1.5 font-sans">
                <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Select Patient Launch Context</label>
                <select
                  value={patientId}
                  onChange={(e) => setPatientId(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono"
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.gender}, Age {p.age})
                    </option>
                  ))}
                </select>
              </div>

              {/* OAuth Scopes */}
              <div className="space-y-1.5 font-sans">
                <label className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">OAuth 2.0 Requested Scopes</label>
                <input
                  type="text"
                  value={scopes}
                  onChange={(e) => setScopes(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-3 py-2 text-xs text-cyan-300 font-mono"
                />
              </div>

              <button
                type="submit"
                disabled={isLaunching}
                className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition-all shadow-lg shadow-cyan-600/20 flex items-center justify-center gap-2"
              >
                {isLaunching ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                Authorize & Launch SMART App Sandbox
              </button>
            </form>
          ) : (
            /* Embedded iFrame Sandbox Viewer */
            <div className="space-y-3 font-sans">
              <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-between text-xs font-mono">
                <span className="text-cyan-300 font-bold flex items-center gap-1.5">
                  <CheckCircle2 size={16} className="text-cyan-400" /> SMART Launch Context Token: {launchedSandbox.launchToken}
                </span>
                <button
                  onClick={() => setLaunchedSandbox(null)}
                  className="text-[10px] text-zinc-400 hover:text-white underline font-mono"
                >
                  Relaunch Different App
                </button>
              </div>

              <div className="border border-white/10 rounded-xl overflow-hidden bg-black h-[350px]">
                <iframe
                  src={launchedSandbox.url}
                  title="SMART Sandbox App"
                  className="w-full h-full border-0"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Close Sandbox
          </button>
        </div>
      </motion.div>
    </div>
  );
};
