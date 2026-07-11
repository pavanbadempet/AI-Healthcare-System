import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, FileText, Activity, Heart, Droplets, Wind, Clipboard, Brain,
  CheckCircle, AlertCircle, Play, Sparkles, HelpCircle, Loader2, ArrowRight
} from "lucide-react";
import { uploadLabReportImage, predictMultiOrgan } from "../lib/apiIntelligence";

interface OrganResult {
  prediction: string;
  raw: number;
  confidence: number;
  risk_level: string;
  disclaimer: string;
  clinical_indices?: Record<string, any>;
  attributions?: Record<string, number>;
  error?: string;
}

export default function UnifiedHub() {
  // File Upload State
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Form Parameters (Unified Profile)
  const [params, setParams] = useState({
    gender: 1, // 1: Male, 0: Female
    age: 45,
    glucose: 90.0,
    hba1c: 5.4,
    smoking: 0,
    physical_activity: 1,
    alcohol: 0,
    general_health: 2,
    bmi: 24.5,
    hypertension: 0,
    heart_disease: 0,
    cp: 0,
    trestbps: 120,
    chol: 195,
    fbs: 0,
    restecg: 0,
    thalach: 150,
    exang: 0,
    oldpeak: 0.0,
    slope: 1,
    ca: 0,
    thal: 2,
    hdl: 50.0,
    hyp_treatment: 0,
    total_bilirubin: 0.8,
    direct_bilirubin: 0.2,
    alkaline_phosphotase: 85.0,
    alamine_aminotransferase: 25.0,
    aspartate_aminotransferase: 22.0,
    total_proteins: 7.2,
    albumin: 4.2,
    albumin_and_globulin_ratio: 1.4,
    platelets: 250.0,
    bp: 120.0,
    sg: 1.020,
    al: 0,
    su: 0,
    rbc: 0,
    pc: 0,
    pcc: 0,
    ba: 0,
    bgr: 90.0,
    bu: 35.0,
    sc: 0.9,
    sod: 138.0,
    pot: 4.2,
    hemo: 15.2,
    pcv: 45.0,
    wc: 7500.0,
    rc: 4.8,
    htn: 0,
    dm: 0,
    cad: 0,
    appet: 0,
    pe: 0,
    ane: 0,
    yellow_fingers: 0,
    anxiety: 0,
    peer_pressure: 0,
    chronic_disease: 0,
    fatigue: 0,
    allergy: 0,
    wheezing: 0,
    coughing: 0,
    shortness_of_breath: 0,
    swallowing_difficulty: 0,
    chest_pain: 0,
  });

  // Diagnostics State
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<Record<string, OrganResult> | null>(null);
  const [clinicalNarrative, setClinicalNarrative] = useState("");
  const [auditSummary, setAuditSummary] = useState("");

  // Handle Drag & Drop
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (
        droppedFile.type === "application/pdf" || 
        droppedFile.type.startsWith("image/")
      ) {
        setFile(droppedFile);
        setUploadError("");
        setUploadSuccess(false);
      } else {
        setUploadError("Invalid file type. Please upload a PDF or an Image.");
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadError("");
      setUploadSuccess(false);
    }
  };

  // Upload & Parse Report
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError("");
    setUploadSuccess(false);

    try {
      const parsed = await uploadLabReportImage(file);
      setUploadSuccess(true);
      
      // Auto-fill extracted values into parameter state
      if (parsed.extracted_data) {
        const ext = parsed.extracted_data;
        setParams(prev => ({
          ...prev,
          glucose: ext.glucose || prev.bgr || 90.0,
          bgr: ext.glucose || prev.bgr || 90.0,
          hba1c: ext.hba1c || prev.hba1c || 5.4,
          chol: ext.cholesterol || ext.chol || prev.chol || 195,
          total_bilirubin: ext.total_bilirubin || prev.total_bilirubin || 0.8,
          trestbps: ext.trestbps || ext.bp || prev.trestbps || 120,
          bp: ext.bp || ext.trestbps || prev.bp || 120.0,
          thalach: ext.thalach || prev.thalach || 150,
        }));
      }
      
      if (parsed.summary) {
        setAuditSummary(parsed.summary);
      }
    } catch (err: any) {
      setUploadError(err.message || "Failed to analyze document.");
    } finally {
      setUploading(false);
    }
  };

  // Execute Multi-Organ Enclave Audit
  const handleRunAudit = async () => {
    setRunning(true);
    try {
      const response = await predictMultiOrgan(params);
      setResults(response.report);
      setClinicalNarrative(response.clinical_narrative || "");
    } catch (err: any) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  // Color mappings for Risk Level
  const getRiskColor = (level: string) => {
    const lvl = level.toLowerCase();
    if (lvl.includes("high") || lvl.includes("detected") || lvl.includes("respiratory issue")) return "var(--danger)";
    if (lvl.includes("moderate") || lvl.includes("borderline")) return "var(--warning)";
    return "var(--success)";
  };

  return (
    <div className="py-6 space-y-8">
      {/* Header */}
      <header className="space-y-1.5 border-l-2 border-[var(--accent)] pl-4">
        <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">
          Unified Health Hub
        </h1>
        <p className="text-[var(--text-dim)] text-xs font-mono tracking-wide max-w-xl uppercase">
          Frictionless lab report ingestion & concurrent multi-organ predictive diagnostics.
        </p>
      </header>

      {/* Top Section: Upload & Actionable Intake */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Column */}
        <div className="lg:col-span-1 panel p-6 flex flex-col justify-between space-y-4 border-[var(--border)] bg-[rgba(24,24,27,0.3)]">
          <div className="space-y-2">
            <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
              <Upload size={14} className="text-[var(--accent)]" /> Ingest Lab Report
            </h2>
            <p className="text-[var(--text-dim)] text-[10px] uppercase font-mono leading-relaxed">
              Upload clinical PDF reports or lab result images. The enclave extracts metrics automatically.
            </p>
          </div>

          {/* Drag & Drop Area */}
          <div
            onDragOver={onDragOver}
            onDrop={onDrop}
            className={`border border-dashed rounded p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
              file ? "border-[var(--accent)] bg-[rgba(14,165,233,0.02)]" : "border-[var(--border)] hover:border-[var(--border-focus)] bg-[rgba(255,255,255,0.01)]"
            }`}
          >
            <input
              type="file"
              id="file-input"
              className="hidden"
              accept=".pdf,image/jpeg,image/png,image/jpg"
              onChange={handleFileChange}
            />
            <label htmlFor="file-input" className="cursor-pointer flex flex-col items-center space-y-2">
              <FileText size={28} className={file ? "text-[var(--accent)] animate-pulse" : "text-[var(--text-dim)]"} />
              <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase text-center">
                {file ? file.name : "Drag & Drop or Select File"}
              </span>
              <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">
                PDF, PNG, JPG (Max 5MB)
              </span>
            </label>
          </div>

          {/* Action buttons */}
          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn btn-primary w-full flex items-center justify-center gap-2 py-2 text-[10px]"
            >
              {uploading ? (
                <>
                  <Loader2 size={12} className="animate-spin" /> Ingesting Document...
                </>
              ) : (
                <>
                  <Sparkles size={12} /> Auto-Extract Markers
                </>
              )}
            </button>
          )}

          {/* Success / Error Feedback */}
          {uploadSuccess && (
            <div className="flex items-start gap-2 p-3 rounded bg-[rgba(16,185,129,0.05)] border border-[var(--success)]/20">
              <CheckCircle size={14} className="text-[var(--success)] mt-0.5" />
              <div>
                <h4 className="text-[10px] font-bold text-[var(--success)] uppercase">Report Analyzed</h4>
                <p className="text-[9px] text-[var(--text-secondary)] uppercase font-mono mt-0.5 leading-normal">
                  Identified metrics successfully loaded into enclaves. Review parameters below.
                </p>
              </div>
            </div>
          )}

          {uploadError && (
            <div className="flex items-start gap-2 p-3 rounded bg-[rgba(239,68,68,0.05)] border border-[var(--danger)]/20">
              <AlertCircle size={14} className="text-[var(--danger)] mt-0.5" />
              <div>
                <h4 className="text-[10px] font-bold text-[var(--danger)] uppercase">Analysis Failed</h4>
                <p className="text-[9px] text-[var(--text-secondary)] font-mono mt-0.5">
                  {uploadError}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Clinical Summary & Parameters Preview */}
        <div className="lg:col-span-2 panel p-6 flex flex-col justify-between space-y-6 border-[var(--border)] bg-[rgba(24,24,27,0.3)]">
          <div className="space-y-4">
            <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
              <Clipboard size={14} className="text-[var(--accent)]" /> Intake Parameter Review
            </h2>
            
            {auditSummary && (
              <div className="p-3 bg-[rgba(255,255,255,0.02)] border border-[var(--border)] rounded">
                <h3 className="text-[9px] font-bold text-[var(--text-primary)] uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Sparkles size={10} className="text-[var(--accent)]" /> Extracted Document Summary:
                </h3>
                <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed font-mono uppercase">
                  {auditSummary}
                </p>
              </div>
            )}

            {/* Quick-Adjust Parameters */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Age (Years)</label>
                <input
                  type="number"
                  value={params.age}
                  onChange={(e) => setParams({ ...params, age: parseFloat(e.target.value) || 0 })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Gender</label>
                <select
                  value={params.gender}
                  onChange={(e) => setParams({ ...params, gender: parseInt(e.target.value) })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                >
                  <option value={1}>Male</option>
                  <option value={0}>Female</option>
                </select>
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Systolic BP (mmHg)</label>
                <input
                  type="number"
                  value={params.trestbps}
                  onChange={(e) => setParams({ 
                    ...params, 
                    trestbps: parseFloat(e.target.value) || 0,
                    bp: parseFloat(e.target.value) || 0
                  })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Serum Chol (mg/dL)</label>
                <input
                  type="number"
                  value={params.chol}
                  onChange={(e) => setParams({ ...params, chol: parseFloat(e.target.value) || 0 })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Fast Blood Sugar (mg/dL)</label>
                <input
                  type="number"
                  value={params.bgr}
                  onChange={(e) => setParams({ 
                    ...params, 
                    bgr: parseFloat(e.target.value) || 0,
                    fbs: parseFloat(e.target.value) > 120 ? 1 : 0
                  })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Body Mass Index (BMI)</label>
                <input
                  type="number"
                  step="0.1"
                  value={params.bmi}
                  onChange={(e) => setParams({ ...params, bmi: parseFloat(e.target.value) || 0 })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Bilirubin (mg/dL)</label>
                <input
                  type="number"
                  step="0.1"
                  value={params.total_bilirubin}
                  onChange={(e) => setParams({ ...params, total_bilirubin: parseFloat(e.target.value) || 0 })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
              <div>
                <label className="block text-[8px] font-mono text-[var(--text-dim)] uppercase mb-1">Serum Creatinine (sc)</label>
                <input
                  type="number"
                  step="0.01"
                  value={params.sc}
                  onChange={(e) => setParams({ ...params, sc: parseFloat(e.target.value) || 0 })}
                  className="input-text text-xs py-1 px-2 w-full bg-[rgba(0,0,0,0.2)] border-[var(--border)]"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleRunAudit}
            disabled={running}
            className="btn btn-primary w-full flex items-center justify-center gap-2 py-3 text-xs uppercase tracking-wider font-bold"
            style={{ backgroundColor: "var(--accent)" }}
          >
            {running ? (
              <>
                <Loader2 size={14} className="animate-spin" /> Running Multi-Organ AI Enclaves...
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" /> Run Unified Health Audit
              </>
            )}
          </button>
        </div>
      </div>

      {/* Audit Results Dashboard */}
      <AnimatePresence>
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            className="space-y-6"
          >
            {clinicalNarrative && (
              <div className="panel p-6 border-[var(--border)] bg-[rgba(24,24,27,0.455)] space-y-3 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-[var(--accent)]" />
                <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={14} className="text-[var(--accent)]" /> Unified Generative Clinical Narrative Note
                </h3>
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed max-w-4xl italic font-mono uppercase">
                  {clinicalNarrative}
                </p>
              </div>
            )}

            <div className="section-label">Organ Risk Panels</div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Individual Organ System Cards */}
              {Object.entries(results).map(([organ, data]) => {
                const isError = !!data.error;
                const riskColor = getRiskColor(data.risk_level);
                
                // Select Icon
                let OrganIcon = Activity;
                if (organ === "heart") OrganIcon = Heart;
                if (organ === "diabetes") OrganIcon = Droplets;
                if (organ === "kidney") OrganIcon = Clipboard;
                if (organ === "lungs") OrganIcon = Wind;
                if (organ === "stroke") OrganIcon = Brain;

                return (
                  <motion.div
                    key={organ}
                    whileHover={{ y: -2 }}
                    className="panel p-6 flex flex-col justify-between border-[var(--border)] bg-[rgba(24,24,27,0.45)] hover:border-[var(--border-focus)] transition-all overflow-hidden relative"
                  >
                    {/* Top Right colored glow */}
                    <div 
                      className="absolute -top-16 -right-16 w-32 h-32 rounded-full blur-[45px] opacity-10 pointer-events-none"
                      style={{ backgroundColor: riskColor }}
                    />

                    <div className="space-y-4">
                      {/* Header */}
                      <div className="flex justify-between items-center">
                        <span 
                          className="p-1.5 rounded bg-[rgba(255,255,255,0.02)] border border-[var(--border)] flex items-center justify-center"
                          style={{ color: riskColor }}
                        >
                          <OrganIcon size={16} />
                        </span>
                        <span 
                          className="text-[9px] font-mono uppercase px-2 py-0.5 rounded border"
                          style={{ borderColor: riskColor, color: riskColor, backgroundColor: "rgba(255, 255, 255, 0.05)" }}
                        >
                          {data.risk_level}
                        </span>
                      </div>

                      {/* Title & Status */}
                      <div>
                        <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                          {organ === "heart" ? "Cardiovascular Panel" : 
                           organ === "diabetes" ? "Metabolic Panel (Diabetes)" : 
                           organ === "kidney" ? "Renal Panel (Kidney)" : 
                           organ === "lungs" ? "Pulmonary Panel (Lungs)" : 
                           organ === "stroke" ? "Cerebrovascular Panel (Stroke)" :
                           "Hepatic Panel (Liver)"}
                        </h3>
                        <p className="text-[10px] text-[var(--text-dim)] uppercase font-mono mt-0.5">
                          Enclave output: {data.prediction}
                        </p>
                      </div>

                      {/* Confidence bar */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-[8px] font-mono text-[var(--text-dim)] uppercase">
                          <span>Diagnostic Confidence</span>
                          <span>{data.confidence}%</span>
                        </div>
                        <div className="h-1 bg-[rgba(255,255,255,0.04)] rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${data.confidence}%`, backgroundColor: riskColor }}
                          />
                        </div>
                      </div>

                      {/* Conformal Uncertainty Bounds */}
                      {data.clinical_indices?.uncertainty_status && (
                        <div className="p-2 bg-[rgba(255,255,255,0.01)] border border-[var(--border)] rounded space-y-0.5">
                          <div className="text-[8px] font-mono text-[var(--text-dim)] uppercase">Conformal Calibration Bounds</div>
                          <div className="text-[9px] font-mono uppercase flex items-center gap-1">
                            <span 
                              className="w-1.5 h-1.5 rounded-full" 
                              style={{ backgroundColor: data.clinical_indices.uncertainty_status.includes("High") ? "var(--danger)" : "var(--success)" }}
                            />
                            {data.clinical_indices.uncertainty_status}
                          </div>
                        </div>
                      )}

                      {/* Recourse ( lifestyle counterpart ) */}
                      {data.clinical_indices?.clinical_recourse && (
                        <div className="p-2 bg-[rgba(14,165,233,0.02)] border border-[rgba(14,165,233,0.1)] rounded space-y-0.5">
                          <div className="text-[8px] font-mono text-[var(--accent)] uppercase">Target Recourse Recommendation</div>
                          <div className="text-[9px] font-mono text-[var(--text-secondary)] uppercase leading-relaxed">
                            {data.clinical_indices.clinical_recourse}
                          </div>
                        </div>
                      )}

                      {/* Attributions (SHAP drivers) */}
                      {data.clinical_indices?.top_risk_factors && (
                        <div className="space-y-1">
                          <div className="text-[8px] font-mono text-[var(--text-dim)] uppercase">Primary Risk Drivers</div>
                          <div className="space-y-1">
                            {data.clinical_indices.top_risk_factors.map((factor: string, idx: number) => (
                              <div key={idx} className="text-[9px] font-mono text-[var(--text-secondary)] uppercase flex items-center gap-1">
                                <span className="text-[var(--accent)]">•</span> {factor}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
