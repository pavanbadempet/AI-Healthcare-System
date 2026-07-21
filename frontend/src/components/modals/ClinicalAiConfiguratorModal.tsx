import React, { useState } from "react";
import { motion } from "framer-motion";
import { X, Sparkles, Sliders, Bot, ShieldCheck, CheckCircle2, Zap, Save, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";

interface ClinicalAiConfiguratorModalProps {
  onClose: () => void;
  onConfigSaved?: (config: ClinicalAiConfig) => void;
}

export interface ClinicalAiConfig {
  persona: string;
  temperature: number;
  topP: number;
  maxTokens: number;
  enforceDisclaimer: boolean;
  enableRagCitations: boolean;
}

export const ClinicalAiConfiguratorModal: React.FC<ClinicalAiConfiguratorModalProps> = ({
  onClose,
  onConfigSaved,
}) => {
  const [persona, setPersona] = useState("cardiology");
  const [temperature, setTemperature] = useState(0.2);
  const [topP, setTopP] = useState(0.95);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [enforceDisclaimer, setEnforceDisclaimer] = useState(true);
  const [enableRagCitations, setEnableRagCitations] = useState(true);

  const personas: Record<string, { title: string; desc: string; prompt: string }> = {
    cardiology: {
      title: "Cardiology & Critical Care Specialist",
      desc: "Focuses on ECG waveforms, troponin elevation trends, GRACE risk scores, and hemodynamics.",
      prompt: "You are an expert Chief of Cardiology AI assistant. Analyze ECGs, vital trends, and lab values with rigorous clinical accuracy.",
    },
    auditor: {
      title: "ICD-10 / CPT Coding & SOAP Auditor",
      desc: "Audits clinical documentation for denial risks, unbundled CPT codes, and missing medical necessity elements.",
      prompt: "You are a Senior Healthcare Compliance & Billing Auditor. Review SOAP notes for coding accuracy and denial prevention.",
    },
    triage: {
      title: "Emergency Triage & SOAP Summarizer",
      desc: "Synthesizes chief complaints into rapid SBAR/SOAP notes with ESI triage level categorization.",
      prompt: "You are an Emergency Medicine Triage AI Specialist. Rapidly summarize patient telemetry and complaints into structured SOAP format.",
    },
    pharma: {
      title: "Pharmacogenomic Contraindications Inspector",
      desc: "Evaluates CYP2D6/CYP2C19 gene variants against drug metabolism and Black Box warning contraindications.",
      prompt: "You are a Clinical Pharmacogenomics Specialist. Cross-reference patient genetic markers with medication safety guidelines.",
    },
  };

  const handleSaveConfig = () => {
    const config: ClinicalAiConfig = {
      persona,
      temperature,
      topP,
      maxTokens,
      enforceDisclaimer,
      enableRagCitations,
    };

    localStorage.setItem("clinical_ai_config", JSON.stringify(config));
    toast.success(`Clinical AI Configured: ${personas[persona].title} (Temp: ${temperature})`);
    if (onConfigSaved) onConfigSaved(config);
    onClose();
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
        aria-labelledby="ai-config-title"
      >
        {/* Header */}
        <div className="bg-white/[0.02] border-b border-white/10 p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 id="ai-config-title" className="text-sm font-bold text-white uppercase tracking-wider">
                Clinical AI Hyperparameters & Prompt Configurator
              </h2>
              <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">
                Tune LLM Temperature, Token Limits, System Prompts & Guardrails
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
          {/* Persona Selection */}
          <div className="space-y-2 font-sans">
            <span className="text-[10px] text-zinc-400 font-bold uppercase block font-mono">Select Clinical System Prompt Persona</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {Object.entries(personas).map(([key, item]) => (
                <div
                  key={key}
                  onClick={() => setPersona(key)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                    persona === key
                      ? "bg-purple-500/10 border-purple-500/50 shadow-md"
                      : "bg-white/[0.02] border-white/5 hover:border-white/10"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-white uppercase">{item.title}</div>
                    <div className="text-[10px] text-zinc-400 font-mono leading-relaxed">{item.desc}</div>
                  </div>
                  <span className="text-[9px] text-purple-400 font-mono font-bold mt-2 block">
                    {persona === key ? "✓ ACTIVE PERSONA" : "SELECT"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Hyperparameters Sliders */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-3 font-sans">
            <span className="text-xs font-bold text-white uppercase tracking-wider block flex items-center gap-1.5 font-mono">
              <Sliders size={14} className="text-purple-400" /> LLM Generation Hyperparameters
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Temperature ($T$)</label>
                <input
                  type="range"
                  min={0.0}
                  max={1.0}
                  step={0.05}
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full accent-purple-500 bg-zinc-800 h-1.5 rounded-lg cursor-pointer"
                />
                <span className="text-[10px] text-purple-400 font-mono font-bold mt-1 block">$T = {temperature}$ ({temperature < 0.3 ? "Deterministic" : "Creative"})</span>
              </div>

              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Top-P Sampling ($p$)</label>
                <input
                  type="range"
                  min={0.1}
                  max={1.0}
                  step={0.05}
                  value={topP}
                  onChange={(e) => setTopP(Number(e.target.value))}
                  className="w-full accent-purple-500 bg-zinc-800 h-1.5 rounded-lg cursor-pointer"
                />
                <span className="text-[10px] text-purple-400 font-mono font-bold mt-1 block">$p = {topP}$</span>
              </div>

              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-bold block mb-1">Max Output Tokens</label>
                <select
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold"
                >
                  <option value={512}>512 Tokens (Concise)</option>
                  <option value={1024}>1024 Tokens (Standard)</option>
                  <option value={2048}>2048 Tokens (Detailed SOAP)</option>
                  <option value={4096}>4096 Tokens (Full Audit Report)</option>
                </select>
              </div>
            </div>

            {/* Guardrails Toggles */}
            <div className="pt-2 border-t border-white/5 space-y-2 font-mono text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-zinc-300 flex items-center gap-1">
                  <ShieldCheck size={12} className="text-emerald-400" /> Mandatory Clinical Medical Disclaimer
                </span>
                <input
                  type="checkbox"
                  checked={enforceDisclaimer}
                  onChange={(e) => setEnforceDisclaimer(e.target.checked)}
                  className="accent-purple-500 cursor-pointer w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-zinc-300 flex items-center gap-1">
                  <Bot size={12} className="text-purple-400" /> RAG Citation Verification (PubMed & Clinical Guidelines)
                </span>
                <input
                  type="checkbox"
                  checked={enableRagCitations}
                  onChange={(e) => setEnableRagCitations(e.target.checked)}
                  className="accent-purple-500 cursor-pointer w-4 h-4"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-white/[0.02] border-t border-white/10 p-4 flex items-center justify-between font-sans">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs uppercase font-bold tracking-wide py-2.5 px-4"
          >
            Cancel
          </button>
          <button
            onClick={handleSaveConfig}
            className="btn bg-purple-600 hover:bg-purple-500 text-white text-xs uppercase font-bold tracking-wide py-2.5 px-5 flex items-center gap-2 rounded-xl shadow-lg shadow-purple-600/20"
          >
            <Save size={14} /> Save AI Configuration
          </button>
        </div>
      </motion.div>
    </div>
  );
};
