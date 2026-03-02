"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, AlertTriangle, FileText, CheckCircle2, ChevronDown, Cpu, Sparkles } from "lucide-react";
import type { PredictionResult } from "@/lib/api";

interface Field {
  name: string;
  label: string;
  type: "number" | "select";
  options?: { label: string; value: number }[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  tooltip?: string;
}

interface PredictionFormProps {
  title: string;
  description: string;
  fields: Field[];
  onSubmit: (data: Record<string, number>) => Promise<PredictionResult>;
}

export default function PredictionForm({ title, description, fields, onSubmit }: PredictionFormProps) {
  const [formData, setFormData] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result && window.innerWidth < 1024) {
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const parsedData: Record<string, number> = {};
    for (const field of fields) {
      const val = formData[field.name];
      if (val === undefined || isNaN(val)) {
        setError(`Please provide a valid value for ${field.label}`);
        setLoading(false);
        return;
      }
      parsedData[field.name] = Number(val);
    }

    try {
      const res = await onSubmit(parsedData);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to generate prediction");
    } finally {
      setLoading(false);
    }
  };

  const isHighRisk = result?.prediction.toLowerCase().includes("positive") || result?.prediction.toLowerCase().includes("disease") || result?.prediction.toLowerCase().includes("high");

  // Custom Select Component to override native ugly OS dropdowns
  const CustomSelect = ({ field, value, onChange }: { field: Field, value: number | undefined, onChange: (val: number) => void }) => {
    const [open, setOpen] = useState(false);
    const selectRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
          setOpen(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const selectedOption = field.options?.find(o => o.value === value);

    return (
      <div className="relative w-full" ref={selectRef}>
        <div 
          onClick={() => setOpen(!open)}
          className={`w-full bg-[var(--bg-card)] border ${open ? 'border-[var(--accent)] ring-2 ring-[var(--accent-border)]' : 'border-[var(--border)] hover:bg-[var(--bg-card-hover)]'} px-3 py-2 text-[var(--text-secondary)] text-xs cursor-pointer transition-all flex justify-between items-center`}
          role="combobox"
          aria-expanded={open}
          aria-haspopup="listbox"
          aria-label={`Select ${field.label}`}
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(!open); } }}
        >
          <span className={selectedOption ? "text-[var(--text-primary)] font-medium" : "text-[var(--text-muted)]"}>
            {selectedOption ? selectedOption.label : `Select ${field.label}`}
          </span>
          <ChevronDown size={14} className={`text-[var(--text-dim)] transition-transform ${open ? "rotate-180 text-[var(--accent)]" : ""}`} aria-hidden="true" />
        </div>
        
        <AnimatePresence>
          {open && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 bg-[var(--bg-card)] border border-[var(--border-focus)] overflow-hidden z-50 shadow-[var(--shadow-lg)]"
              role="listbox"
              aria-label={`Options for ${field.label}`}
            >
              <div className="max-h-60 overflow-y-auto py-1">
                {field.options?.map((opt) => (
                  <div 
                    key={opt.value}
                    onClick={() => {
                      onChange(opt.value);
                      setOpen(false);
                    }}
                    className={`px-3 py-2.5 hover:bg-[var(--accent-muted)] hover:text-[var(--accent)] text-xs cursor-pointer transition-colors ${value === opt.value ? 'text-[var(--accent)] bg-[var(--accent-muted)]' : 'text-[var(--text-secondary)]'}`}
                    role="option"
                    aria-selected={value === opt.value}
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter') { onChange(opt.value); setOpen(false); } }}
                  >
                    {opt.label}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 w-full">
      
      {/* Left Column: Form */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.3 }}
        className="lg:col-span-7 space-y-6"
      >
        <div className="panel p-6 md:p-8 relative">
          <div className="absolute top-0 right-0 p-2 mono-meta border-b border-l border-[var(--border)] bg-[var(--bg-primary)]">
            INPUT VECTORS
          </div>
          
          <div className="mb-8 mt-2">
            <div className="status-badge status-badge-accent mb-4">
              <span className="w-1.5 h-1.5 rounded-sm bg-[var(--accent)] animate-pulse" aria-hidden="true"></span>
              DIAGNOSTIC SUBSYSTEM
            </div>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] uppercase tracking-wider mb-2">{title}</h2>
            <p className="text-[var(--text-secondary)] text-[11px] font-mono tracking-wide max-w-xl">{description}</p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: "auto" }} 
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mb-6"
              >
                <div className="p-3 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] flex items-start gap-2" role="alert">
                  <AlertTriangle size={14} className="shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-[11px] font-mono uppercase tracking-wider">{error}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-5">
              {fields.map((field, i) => (
                <div key={field.name} className="space-y-1.5">
                  <label className="section-label flex items-center gap-1.5 mb-1" htmlFor={`field-${field.name}`}>
                    {field.label} 
                    {field.tooltip && <span title={field.tooltip} className="cursor-help text-[var(--border-focus)] hover:text-[var(--text-primary)] transition-colors"><Activity size={10} aria-hidden="true" /></span>}
                  </label>
                  
                  <div className="relative">
                    {field.type === "select" ? (
                      <CustomSelect 
                        field={field} 
                        value={formData[field.name]} 
                        onChange={(val) => setFormData({ ...formData, [field.name]: val })} 
                      />
                    ) : (
                      <input
                        id={`field-${field.name}`}
                        type="number"
                        min={field.min}
                        max={field.max}
                        step={field.step || 1}
                        value={formData[field.name] ?? ""}
                        onChange={(e) => setFormData({ ...formData, [field.name]: Number(e.target.value) })}
                        placeholder={field.placeholder}
                        required
                        className="input-clinical"
                        aria-label={field.label}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>

            <button 
              type="submit" 
              disabled={loading} 
              className="w-full mt-6 relative overflow-hidden group"
              aria-label={loading ? "Running clinical assessment" : "Execute clinical assessment"}
            >
              <div className={`absolute inset-0 transition-all duration-300 ${loading ? 'bg-[var(--bg-card)]' : 'bg-[var(--accent)] group-hover:bg-[var(--accent-hover)]'}`} />
              
              {/* Button Progress Bar (Hidden when not loading) */}
              {loading && (
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 2, ease: "linear" }}
                  className="absolute bottom-0 left-0 h-0.5 bg-[var(--success)] z-20"
                  aria-hidden="true"
                />
              )}

              <span className="relative z-10 flex items-center justify-center gap-3 py-3 px-4 text-[var(--text-primary)] font-bold uppercase tracking-[0.3em] text-[11px]">
                {loading ? (
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                  >
                    <Activity size={14} className="text-[var(--success)]" aria-hidden="true" />
                  </motion.div>
                ) : (
                  <Sparkles size={14} className="opacity-50" aria-hidden="true" />
                )}
                {loading ? "INITIALIZING NEURAL COMPUTE..." : "EXECUTE CLINICAL ASSESSMENT"}
              </span>
            </button>
          </form>
        </div>
      </motion.div>

      {/* Right Column: Results */}
      <motion.div 
        ref={resultRef} 
        initial={{ opacity: 0, y: 10 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.3, delay: 0.1 }}
        className="lg:col-span-5 h-full"
      >
        <AnimatePresence mode="wait">
          {!result ? (
            <motion.div 
              key="awaiting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full min-h-[500px] panel flex flex-col items-center justify-center text-center p-8 relative"
            >
              <div className="absolute top-0 left-0 p-2 mono-meta border-b border-r border-[var(--border)] bg-[var(--bg-primary)]">
                ANALYSIS OUTPUT
              </div>
              
              {loading ? (
                <div className="space-y-6 w-full max-w-xs" role="status" aria-label="Processing diagnostic analysis">
                  <div className="flex flex-col items-center gap-4">
                    <div className="relative">
                      <motion.div 
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
                        className="w-16 h-16 border-2 border-dashed border-[var(--accent-border)] rounded-full"
                        aria-hidden="true"
                      />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Activity className="text-[var(--accent)] animate-pulse" size={24} aria-hidden="true" />
                      </div>
                    </div>
                    <div className="text-center">
                      <p className="text-[11px] font-mono text-[var(--accent)] animate-pulse uppercase tracking-[0.2em] mb-1">Processing Telemetry</p>
                      <p className="text-[11px] font-mono text-[var(--border-focus)] uppercase">Neural Net Inversion: v4.2</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-[1px] w-full bg-[var(--border-subtle)] relative overflow-hidden" aria-hidden="true">
                        <motion.div 
                          animate={{ x: ["-100%", "100%"] }}
                          transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.3 }}
                          className="absolute inset-0 w-1/3 bg-gradient-to-r from-transparent via-[var(--accent-border)] to-transparent"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 bg-[var(--bg-card)] border border-[var(--border)] flex items-center justify-center mb-6">
                    <Cpu size={24} className="text-[var(--border-focus)]" aria-hidden="true" />
                  </div>
                  <h3 className="text-[13px] font-bold text-[var(--text-primary)] mb-2 uppercase tracking-widest">Awaiting Telemetry</h3>
                  <p className="text-[11px] font-mono text-[var(--text-dim)] max-w-sm uppercase leading-relaxed">Enter patient metrics into the diagnostic subsystem to generate a clinical assessment matrix.</p>
                </>
              )}
            </motion.div>
          ) : (
            <motion.div 
              key="result"
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              className={`panel p-8 h-full flex flex-col ${isHighRisk ? 'border-[var(--danger)]' : 'border-[var(--success)]'}`}
              role="region"
              aria-label="Diagnostic results"
            >
              <div className="flex items-start gap-4 mb-8">
                <div className={`p-3 border ${isHighRisk ? 'bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]' : 'bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]'}`}>
                  {isHighRisk ? <AlertTriangle size={20} aria-hidden="true" /> : <CheckCircle2 size={20} aria-hidden="true" />}
                </div>
                <div>
                  <h3 className="section-label mb-1">Diagnostic Classification</h3>
                  <p className={`text-xl font-bold uppercase tracking-wider ${isHighRisk ? 'text-[var(--danger)]' : 'text-[var(--success)]'}`}>
                    {result.prediction.split('.')[0]}
                  </p>
                </div>
              </div>

              {result.probability !== undefined && (
                <div className="mb-8 p-4 bg-[var(--bg-card)] border border-[var(--border)]">
                  <div className="flex justify-between items-end mb-3">
                    <span className="section-label">Confidence Interval</span>
                    <span className="text-xl font-mono font-semibold text-[var(--text-primary)]">{(result.probability * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1 w-full bg-[var(--border)] overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }} 
                      animate={{ width: `${result.probability * 100}%` }} 
                      transition={{ duration: 0.8 }}
                      className={`h-full ${isHighRisk ? 'bg-[var(--danger)]' : 'bg-[var(--success)]'}`}
                      role="progressbar"
                      aria-valuenow={Math.round(result.probability * 100)}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`Confidence: ${(result.probability * 100).toFixed(1)}%`}
                    />
                  </div>
                </div>
              )}

              {result.advice && result.advice.length > 0 && (
                <div className="flex-1">
                  <h4 className="section-label mb-4 flex items-center gap-2 border-b border-[var(--border)] pb-2">
                    <FileText size={12} className="text-[var(--accent)]" aria-hidden="true" /> Recommended Protocol
                  </h4>
                  <ul className="space-y-2">
                    {result.advice.map((item, i) => (
                      <li 
                        key={i} 
                        className="text-[11px] font-mono leading-relaxed flex items-start gap-3 p-3 bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)]"
                      >
                        <span className="text-[var(--accent)]" aria-hidden="true">{`>`}</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="mt-8 pt-4 border-t border-[var(--border)] text-center">
                <p className="text-[11px] text-[var(--text-dim)] font-bold uppercase tracking-widest">
                  AI Prediction • Not for Official Diagnostic Use
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
