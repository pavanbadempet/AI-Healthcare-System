
import { useState, useRef, useEffect, useId } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, AlertTriangle, FileText, CheckCircle2, ChevronDown, Cpu, Sparkles } from "lucide-react";
import type { PredictionResult } from "@/lib/api";
import Tooltip from "../layout/Tooltip";

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

const FRIENDLY_FEATURE_LABELS: Record<string, string> = {
  // Diabetes (BRFSS)
  bmi: "Body Mass Index (BMI)",
  hypertension: "High Blood Pressure",
  high_chol: "High Cholesterol",
  smoking_history: "Smoking History",
  heart_disease: "Heart Disease History",
  physical_activity: "Physical Activity",
  general_health: "General Health Rating",
  gender: "Biological Gender",
  age: "Age",
  age_bucket: "Age Group",
  // Heart (Cleveland)
  sex: "Gender",
  cp: "Chest Pain Type",
  trestbps: "Resting Blood Pressure",
  chol: "Serum Cholesterol",
  fbs: "Fasting Blood Sugar",
  restecg: "Resting ECG Results",
  thalach: "Max Heart Rate",
  exang: "Exercise Induced Angina",
  oldpeak: "ST Depression",
  slope: "ST Slope",
  ca: "Major Vessels Count",
  thal: "Thalassemia Type",
  // Kidney (Renal)
  bp: "Blood Pressure",
  sg: "Specific Gravity",
  al: "Albumin",
  su: "Sugar",
  rbc: "Red Blood Cells",
  pc: "Pus Cell",
  pcc: "Pus Cell Clumps",
  ba: "Bacteria",
  bgr: "Blood Glucose Random",
  bu: "Blood Urea",
  sc: "Serum Creatinine",
  sod: "Sodium",
  pot: "Potassium",
  hemo: "Hemoglobin",
  pcv: "Packed Cell Volume",
  wc: "White Blood Cell Count",
  rc: "Red Blood Cell Count",
  htn: "Hypertension",
  dm: "Diabetes Mellitus",
  cad: "Coronary Artery Disease",
  appet: "Appetite",
  pe: "Pedal Edema",
  ane: "Anemia",
  // Liver (ILPD)
  Age: "Age",
  Gender: "Biological Gender",
  Total_Bilirubin: "Total Bilirubin",
  Direct_Bilirubin: "Direct Bilirubin",
  Total_Proteins: "Total Proteins",
  Albumin: "Albumin",
  Albumin_and_Globulin_Ratio: "Albumin/Globulin Ratio",
  Alamine_Aminotransferase: "ALT Enzyme Level",
  Aspartate_Aminotransferase: "AST Enzyme Level",
  Alkaline_Phosphotase: "Alkaline Phosphatase",
  // Lungs (Pulmonary)
  GENDER: "Biological Gender",
  AGE: "Age",
  SMOKING: "Smoking History",
  YELLOW_FINGERS: "Yellow Fingers",
  ANXIETY: "Anxiety",
  PEER_PRESSURE: "Peer Pressure",
  CHRONIC_DISEASE: "Chronic Disease",
  FATIGUE: "Fatigue Level",
  ALLERGY: "Allergy History",
  WHEEZING: "Wheezing Symptoms",
  ALCOHOL_CONSUMING: "Alcohol Consumption",
  COUGHING: "Coughing Symptoms",
  SHORTNESS_OF_BREATH: "Shortness of Breath",
  SWALLOWING_DIFFICULTY: "Difficulty Swallowing",
  CHEST_PAIN: "Chest Pain"
};

interface PredictionFormProps {
  title: string;
  description: string;
  fields: Field[];
  onSubmit: (data: Record<string, number>, computeMode?: 'local' | 'remote') => Promise<PredictionResult>;
}

export default function PredictionForm({ title, description, fields, onSubmit }: PredictionFormProps) {
  const [formData, setFormData] = useState<Record<string, number>>({});
  const [computeMode, setComputeMode] = useState<'local' | 'remote'>('remote');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result && window.innerWidth < 1024) {
      resultRef.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
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
      const res = await onSubmit(parsedData, computeMode);
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
    const listboxId = useId();

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
          className={`w-full bg-[rgba(255,255,255,0.02)] border ${open ? 'border-[var(--accent)] ring-1 ring-[var(--accent)]' : 'border-[var(--border)] hover:bg-[rgba(255,255,255,0.04)]'} px-3 py-2 text-[var(--text-secondary)] text-xs rounded cursor-pointer transition-all flex justify-between items-center`}
          role="combobox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-haspopup="listbox"
          aria-label={`Select ${field.label}`}
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(!open); } }}
        >
          <span className={selectedOption ? "text-[var(--text-primary)] font-medium uppercase font-mono" : "text-[var(--text-muted)] font-mono uppercase"}>
            {selectedOption ? selectedOption.label : `-- SELECT ${field.label} --`}
          </span>
          <ChevronDown size={13} className={`text-[var(--text-dim)] transition-transform ${open ? "rotate-180 text-[var(--accent)]" : ""}`} aria-hidden="true" />
        </div>
        
        <AnimatePresence>
          {open && (
            <motion.div 
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.1 }}
              className="absolute top-full left-0 right-0 mt-1 bg-[#18181b] border border-[var(--border-focus)] rounded overflow-hidden z-50 shadow-[var(--shadow-lg)]"
              id={listboxId}
              role="listbox"
              aria-label={`Options for ${field.label}`}
            >
              <div className="max-h-52 overflow-y-auto py-1">
                {field.options?.map((opt) => (
                  <div 
                    key={opt.value}
                    onClick={() => {
                      onChange(opt.value);
                      setOpen(false);
                    }}
                    className={`px-3 py-2 hover:bg-[var(--accent-muted)] hover:text-[var(--accent)] text-xs font-mono uppercase cursor-pointer transition-colors ${value === opt.value ? 'text-[var(--accent)] bg-[var(--accent-muted)] font-bold' : 'text-[var(--text-secondary)]'}`}
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
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 w-full">
      
      {/* Left Column: Form */}
      <motion.div 
        initial={{ opacity: 0, y: 8 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.25 }}
        className="lg:col-span-7 space-y-6"
      >
        <div className="panel p-5 relative">
          <div className="absolute top-0 right-0 p-2 text-[9px] font-mono border-b border-l border-[var(--border)] bg-[#09090b] text-[var(--text-dim)] uppercase">
            Input Vector Map
          </div>
          
          <div className="mb-6 mt-2">
            <div className="status-badge status-badge-accent mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" aria-hidden="true"></span>
              DIAGNOSTIC PIPELINE
            </div>
            <h2 className="text-md font-bold text-[var(--text-primary)] uppercase tracking-wider mb-1">{title}</h2>
            <p className="text-[var(--text-secondary)] text-xs font-mono uppercase tracking-wide max-w-xl">{description}</p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: "auto" }} 
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mb-4"
              >
                <div className="p-3 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] flex items-start gap-2" role="alert">
                  <AlertTriangle size={14} className="shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-[10px] font-mono uppercase tracking-wider">{error}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
            {/* Compute Enclave Selector Switch */}
            <div className="mb-5 p-3 bg-zinc-950/60 border border-[var(--border)] rounded flex flex-col sm:flex-row justify-between sm:items-center gap-3 text-xs font-mono">
              <div>
                <span className="text-white font-bold block uppercase tracking-wider">Compute Enclave Mode</span>
                <span className="text-[9px] text-[var(--text-dim)] uppercase">Select execution environment target</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setComputeMode("local")}
                  className={`px-3 py-1.5 border text-[10px] font-bold uppercase tracking-wider rounded transition-all cursor-pointer ${
                    computeMode === "local"
                      ? "text-[var(--accent)] border-[var(--accent)] bg-[var(--accent-muted)]"
                      : "text-[var(--text-dim)] border-[var(--border)] hover:text-white hover:bg-zinc-900"
                  }`}
                >
                  Local Edge (WASM)
                </button>
                <button
                  type="button"
                  onClick={() => setComputeMode("remote")}
                  className={`px-3 py-1.5 border text-[10px] font-bold uppercase tracking-wider rounded transition-all cursor-pointer ${
                    computeMode === "remote"
                      ? "text-[var(--accent)] border-[var(--accent)] bg-[var(--accent-muted)]"
                      : "text-[var(--text-dim)] border-[var(--border)] hover:text-white hover:bg-zinc-900"
                  }`}
                >
                  Remote AI (SHAP)
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {fields.map((field) => (
                <div key={field.name} className="space-y-1.5">
                  <label className="section-label flex items-center gap-1 mb-1" htmlFor={`field-${field.name}`}>
                    {field.label} 
                    {field.tooltip && (
                      <Tooltip content={field.tooltip} position="top">
                        <span className="cursor-help text-[var(--text-dim)] hover:text-[var(--text-primary)] transition-colors">
                          <Activity size={10} aria-hidden="true" />
                        </span>
                      </Tooltip>
                    )}
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
                        placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
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
              className="w-full mt-4 btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-2"
              aria-label={loading ? "Running diagnostic pipeline" : "Execute diagnostics compute"}
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  INVERTING NEURAL GRAPH...
                </>
              ) : (
                <>
                  <Sparkles size={13} aria-hidden="true" />
                  EXECUTE COMPUTE
                </>
              )}
            </button>
          </form>
        </div>
      </motion.div>

      {/* Right Column: Results */}
      <motion.div 
        ref={resultRef} 
        initial={{ opacity: 0, y: 8 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.25, delay: 0.05 }}
        className="lg:col-span-5 h-full"
      >
        <AnimatePresence mode="wait">
          {!result ? (
            <motion.div 
              key="awaiting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full min-h-[420px] panel flex flex-col items-center justify-center text-center p-8 relative bg-[rgba(24,24,27,0.4)]"
            >
              <div className="absolute top-0 left-0 p-2 text-[9px] font-mono border-b border-r border-[var(--border)] bg-[#09090b] text-[var(--text-dim)] uppercase">
                Analysis Matrix
              </div>
              
              {loading ? (
                <div className="space-y-4 w-full max-w-xs" role="status" aria-label="Processing diagnostic analysis">
                  <div className="flex flex-col items-center gap-3">
                    <div className="relative w-12 h-12 flex items-center justify-center">
                      <span className="w-10 h-10 border-2 border-dashed border-[var(--accent)] rounded-full animate-spin absolute" />
                      <Activity className="text-[var(--accent)]" size={18} aria-hidden="true" />
                    </div>
                    <div className="text-center font-mono text-[10px] uppercase">
                      <p className="text-[var(--accent)] animate-pulse tracking-widest font-bold">Computing Vectors</p>
                      <p className="text-[var(--text-dim)] mt-0.5">Neural Graph: v3.2</p>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="w-12 h-12 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] rounded flex items-center justify-center mb-4">
                    <Cpu size={20} className="text-[var(--text-dim)]" aria-hidden="true" />
                  </div>
                  <h3 className="text-xs font-bold text-[var(--text-primary)] mb-1 uppercase tracking-widest">Awaiting Telemetry</h3>
                  <p className="text-[10px] font-mono text-[var(--text-dim)] max-w-xs uppercase leading-relaxed">Submit patient metrics to start the secure inference pipeline.</p>
                </>
              )}
            </motion.div>
          ) : (
            <motion.div 
              key="result"
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              className={`panel p-6 h-full flex flex-col justify-between ${isHighRisk ? 'border-[var(--danger)] shadow-[0_0_12px_rgba(239,68,68,0.1)]' : 'border-[var(--success)] shadow-[0_0_12px_rgba(16,185,129,0.1)]'}`}
              role="region"
              aria-label="Diagnostic results"
            >
              <div className="space-y-6">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded border ${isHighRisk ? 'bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]' : 'bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]'}`}>
                    {isHighRisk ? <AlertTriangle size={18} aria-hidden="true" /> : <CheckCircle2 size={18} aria-hidden="true" />}
                  </div>
                  <div>
                    <h3 className="section-label mb-0.5">Classification Output</h3>
                    <p className={`text-md font-bold uppercase tracking-wider ${isHighRisk ? 'text-[var(--danger)]' : 'text-[var(--success)]'}`}>
                      {result.prediction.split('.')[0]}
                    </p>
                  </div>
                </div>

                {(result.confidence !== undefined || result.probability !== undefined) && (
                  <div className="p-3 bg-[rgba(255,255,255,0.015)] border border-[var(--border)] rounded">
                    <div className="flex justify-between items-end mb-2">
                      <span className="section-label">Confidence Probability</span>
                      <span className="text-sm font-mono font-bold text-[var(--text-primary)]">
                        {result.confidence !== undefined ? `${result.confidence}%` : `${((result.probability ?? 0) * 100).toFixed(1)}%`}
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-[var(--border)] overflow-hidden rounded-full">
                      <motion.div 
                        initial={{ width: 0 }} 
                        animate={{ width: `${result.confidence ?? ((result.probability ?? 0) * 100)}%` }} 
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className={`h-full ${
                          (result.confidence ?? ((result.probability ?? 0) * 100)) >= 75 
                            ? 'bg-[var(--danger)]' 
                            : (result.confidence ?? ((result.probability ?? 0) * 100)) >= 40 
                              ? 'bg-[var(--warning)]' 
                              : 'bg-[var(--success)]'
                        }`}
                        role="progressbar"
                        aria-valuenow={Math.round(result.confidence ?? ((result.probability ?? 0) * 100))}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`Confidence: ${result.confidence ?? ((result.probability ?? 0) * 100)}%`}
                      />
                    </div>
                    
                    {result.risk_level && (
                      <div className="flex items-center gap-1.5 mt-2.5">
                        <span className="section-label">Acuity Stratification:</span>
                        <span className={`text-[9px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                          result.risk_level === 'High' 
                            ? 'text-[var(--danger)] bg-[var(--danger-muted)] border-[var(--danger-border)]'
                            : result.risk_level === 'Moderate'
                              ? 'text-[var(--warning)] bg-[var(--warning-muted)] border-[var(--warning-border)]'
                              : 'text-[var(--success)] bg-[var(--success-muted)] border-[var(--success-border)]'
                        }`}>
                          {result.risk_level}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                {result.clinical_indices && (
                  <div className="space-y-4 border border-[var(--border)] rounded p-4 bg-zinc-950/40">
                    <h4 className="text-[11px] font-bold text-white uppercase tracking-wider flex items-center gap-1.5 border-b border-[var(--border)] pb-2">
                      <Sparkles size={12} className="text-[var(--accent)]" aria-hidden="true" /> Advanced Conformal & Recourse Analytics
                    </h4>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[10px] font-mono uppercase">
                      <div>
                        <span className="text-[var(--text-dim)] font-bold block mb-0.5">Prediction Set</span>
                        <span className="text-white bg-zinc-900 border border-white/[0.05] px-1.5 py-0.5 rounded">
                          {`[${(result.clinical_indices.conformal_prediction_set || []).join(", ")}]`}
                        </span>
                      </div>
                      <div>
                        <span className="text-[var(--text-dim)] font-bold block mb-0.5">Uncertainty Status</span>
                        <span className={`font-bold ${
                          (result.clinical_indices.uncertainty_status || "").includes("Low") 
                            ? "text-[var(--success)]" 
                            : "text-[var(--danger)]"
                        }`}>
                          {result.clinical_indices.uncertainty_status || "N/A"}
                        </span>
                      </div>
                      <div className="sm:col-span-2">
                        <span className="text-[var(--text-dim)] font-bold block mb-0.5">Significance Level (Adaptive α)</span>
                        <span className="text-white">
                          {result.clinical_indices.significance_level !== undefined 
                            ? `${(result.clinical_indices.significance_level * 100).toFixed(2)}%` 
                            : "N/A"}
                        </span>
                      </div>
                    </div>

                    {result.clinical_indices.clinical_recourse && (
                      <div className="space-y-1.5 pt-2 border-t border-[var(--border)]/40 text-[10px] font-mono uppercase">
                        <span className="text-[var(--text-dim)] font-bold block animate-pulse">Lifestyle Action Recourse</span>
                        <p className="text-amber-500 leading-normal bg-amber-500/5 border border-amber-500/10 p-2.5 rounded">
                          {result.clinical_indices.clinical_recourse}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Patient Explainable AI (XAI) Panel */}
                {((result.attributions && Object.keys(result.attributions).length > 0) || result.patient_explanation) && (
                  <div className="space-y-4 border border-[var(--border)] rounded p-4 bg-zinc-950/40">
                    <h4 className="text-[11px] font-bold text-white uppercase tracking-wider flex items-center gap-1.5 border-b border-[var(--border)] pb-2">
                      <Sparkles size={12} className="text-[var(--accent)]" aria-hidden="true" /> Patient-Friendly Explainable AI (XAI)
                    </h4>

                    {result.attributions && Object.keys(result.attributions).length > 0 && (
                      <div className="space-y-2.5">
                        <span className="section-label block">Key Health Drivers Impact</span>
                        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                          {Object.entries(result.attributions)
                            .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                            .filter(([_, val]) => Math.abs(val) > 0.0001)
                            .map(([feat, val]) => {
                              const friendlyName = FRIENDLY_FEATURE_LABELS[feat] || feat;
                              const isPositive = val > 0;
                              const absPercent = Math.min(100, Math.round(Math.abs(val) * 100));
                              return (
                                <div key={feat} className="text-[10px] font-mono uppercase space-y-1">
                                  <div className="flex justify-between text-[9px]">
                                    <span className="text-[var(--text-primary)] font-bold">{friendlyName}</span>
                                    <span className={isPositive ? "text-[var(--danger)]" : "text-[var(--success)]"}>
                                      {isPositive ? `+${absPercent}% Risk Amplifier` : `-${absPercent}% Risk Mitigator`}
                                    </span>
                                  </div>
                                  <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden flex">
                                    {isPositive ? (
                                      <>
                                        <div className="w-1/2 bg-zinc-900" />
                                        <div 
                                          className="bg-[var(--danger)] rounded-r-full" 
                                          style={{ width: `${absPercent / 2}%` }}
                                        />
                                      </>
                                    ) : (
                                      <>
                                        <div className="flex-1 flex justify-end">
                                          <div 
                                            className="bg-[var(--success)] rounded-l-full" 
                                            style={{ width: `${absPercent / 2}%` }}
                                          />
                                        </div>
                                        <div className="w-1/2 bg-zinc-900" />
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}

                    {result.patient_explanation && (
                      <div className="space-y-1.5 pt-2 border-t border-[var(--border)]/40 text-[10px] font-mono uppercase">
                        <span className="text-[var(--text-dim)] font-bold block">Empathetic Layperson Narrative</span>
                        <p className="text-[var(--text-primary)] leading-relaxed bg-[rgba(255,255,255,0.01)] border border-[var(--border)] p-3 rounded text-[10px] font-mono normal-case">
                          {result.patient_explanation}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {result.advice && result.advice.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="section-label flex items-center gap-1.5 border-b border-[var(--border)] pb-1.5">
                      <FileText size={12} className="text-[var(--accent)]" aria-hidden="true" /> Recommended Protocol
                    </h4>
                    <div className="space-y-2">
                      {result.advice.map((item, i) => (
                        <div 
                          key={i} 
                          className="text-[10px] font-mono uppercase leading-normal flex items-start gap-2 p-2.5 bg-[rgba(255,255,255,0.01)] border border-[var(--border)] rounded text-[var(--text-primary)]"
                        >
                          <span className="text-[var(--accent)] font-bold">{`>`}</span>
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 pt-4 border-t border-[var(--border)]">
                <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase leading-normal mb-2">
                  {result.disclaimer || "AI-assisted screening tool, not a medical diagnosis. Consult a qualified professional."}
                </p>
                <p className="text-[9px] text-[var(--text-dim)] font-bold uppercase tracking-wider text-center border border-[var(--border)] py-1 bg-[rgba(255,255,255,0.01)] font-mono">
                  Clinical Support Feed • Not Diagnostic
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
