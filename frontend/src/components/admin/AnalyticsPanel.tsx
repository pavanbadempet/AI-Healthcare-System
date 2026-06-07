/**
 * AnalyticsPanel – Medallion Gold Layer Insights tab for the Admin page.
 * Extracted from Admin.tsx for maintainability.
 */
import { useState } from "react";
import { Activity, Sparkles, RefreshCw, ShieldAlert, Loader2 } from "lucide-react";
import { getAnalyticsReport, type AnalyticsReport } from "@/lib/api";

export default function AnalyticsPanel() {
  const [analyticsReport, setAnalyticsReport] = useState<AnalyticsReport | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState("");

  const fetchAnalyticsReport = () => {
    setAnalyticsLoading(true);
    setAnalyticsError("");
    getAnalyticsReport()
      .then(setAnalyticsReport)
      .catch((err) => {
        console.error("Failed to load analytics report", err);
        setAnalyticsError(err.message || "Failed to load analyst report.");
      })
      .finally(() => setAnalyticsLoading(false));
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="panel p-6 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
            <Sparkles size={15} className="text-[var(--accent)]" /> Medallion Gold Layer Insights
          </h3>
          <p className="text-[11px] text-[var(--text-secondary)] font-mono uppercase mt-1">
            Data Science aggregates, cohorts, and model performance metrics.
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {analyticsReport?.report_generated_at && (
            <div className="text-right font-mono text-[10px] text-[var(--text-dim)] uppercase">
              <span>Last Compiled: {new Date(analyticsReport.report_generated_at).toLocaleString()}</span>
              {analyticsReport.pipeline_execution && (
                <span className="block text-right">Duration: {analyticsReport.pipeline_execution.duration_seconds}s</span>
              )}
            </div>
          )}
          <button
            onClick={fetchAnalyticsReport}
            disabled={analyticsLoading}
            className="btn-clinical text-xs py-1.5 px-3 flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={12} className={analyticsLoading ? "animate-spin" : ""} />
            {analyticsLoading ? "Refreshing..." : "Sync Report"}
          </button>
        </div>
      </div>

      {analyticsLoading && !analyticsReport ? (
        <div className="panel p-12 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-widest">
          <Loader2 size={24} className="animate-spin inline-block mr-2 align-middle text-[var(--accent)]" /> 
          Compiling Data Science Analytics...
        </div>
      ) : analyticsError ? (
        <div className="panel p-6 border-[var(--danger-border)] bg-[rgba(239,68,68,0.02)] text-center">
          <ShieldAlert size={32} className="mx-auto mb-2 text-[var(--danger)] opacity-80" />
          <h4 className="text-xs font-bold text-white uppercase mb-1">Failed to Load Report</h4>
          <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase">{analyticsError}</p>
        </div>
      ) : analyticsReport ? (
        <>
          {/* Top Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
              <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Total Records Analyzed</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                  {analyticsReport.total_records_analyzed.toLocaleString()}
                </span>
                <span className="text-[10px] font-bold text-[var(--success)] uppercase">Conformed</span>
              </div>
              <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                Aggregated across all conformed Silver & Gold Parquet tables.
              </p>
            </div>

            <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
              <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Cohort Mean Age</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                  {analyticsReport.demographics?.avg_age || 0}
                </span>
                <span className="text-[10px] font-bold text-[var(--accent)] uppercase">Years</span>
              </div>
              <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                Arithmetic mean of conformed patient demographic records.
              </p>
            </div>

            <div className="bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors">
              <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider">Cohort Mean BMI</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-white tracking-tight font-mono">
                  {analyticsReport.demographics?.avg_bmi || 0}
                </span>
                <span className="text-[10px] font-bold text-[var(--accent-purple)] uppercase">kg/m²</span>
              </div>
              <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-2">
                Conformed Body Mass Index distribution (healthy target: 18.5 - 24.9).
              </p>
            </div>
          </div>

          {/* Demographics and Disease Prevalence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gender Distribution */}
            <div className="panel p-5 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded flex flex-col justify-between">
              <div className="mb-4">
                <span className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider block">Gender Cohort Distribution</span>
                <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                  Self-reported gender identification demographics inside the conformed datasets.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-end font-mono text-xs">
                  <div className="space-y-0.5">
                    <span className="text-[9px] font-bold text-[var(--accent)] uppercase block">Male Ratio</span>
                    <span className="text-lg font-black text-white">{analyticsReport.demographics?.gender_distribution?.male_ratio || 0}%</span>
                  </div>
                  <div className="space-y-0.5 text-right">
                    <span className="text-[9px] font-bold text-[var(--accent-purple)] uppercase block">Female Ratio</span>
                    <span className="text-lg font-black text-white">{analyticsReport.demographics?.gender_distribution?.female_ratio || 0}%</span>
                  </div>
                </div>

                <div className="w-full h-3 rounded-full bg-zinc-950 overflow-hidden flex border border-white/[0.03]">
                  <div 
                    style={{ width: `${analyticsReport.demographics?.gender_distribution?.male_ratio || 50}%` }} 
                    className="bg-[var(--accent)] h-full transition-all duration-500"
                  />
                  <div 
                    style={{ width: `${analyticsReport.demographics?.gender_distribution?.female_ratio || 50}%` }} 
                    className="bg-[var(--accent-purple)] h-full transition-all duration-500"
                  />
                </div>

                <div className="flex gap-4 items-center justify-center pt-2">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-[var(--accent)] inline-block" />
                    <span className="text-[9px] font-mono text-[var(--text-secondary)] uppercase">Male</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded bg-[var(--accent-purple)] inline-block" />
                    <span className="text-[9px] font-mono text-[var(--text-secondary)] uppercase">Female</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Disease Prevalence */}
            <div className="panel p-5 bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
              <div className="mb-4">
                <span className="text-[10px] font-bold text-[var(--text-dim)] uppercase tracking-wider block">Clinical Cohort Prevalence Rates</span>
                <p className="text-[9px] text-[var(--text-secondary)] font-mono uppercase mt-1">
                  Percentage of high-risk / disease-detected individuals derived from Silver Parquet aggregates.
                </p>
              </div>

              <div className="space-y-3">
                {[
                  { key: "diabetes", label: "Diabetes Mellitus", color: "bg-[var(--accent)]", val: analyticsReport.prevalence_rates?.diabetes ?? 0 },
                  { key: "heart", label: "Cardiovascular Issues", color: "bg-[var(--accent-purple)]", val: analyticsReport.prevalence_rates?.heart ?? 0 },
                  { key: "liver", label: "Hepatic Dysfunctions", color: "bg-amber-500", val: analyticsReport.prevalence_rates?.liver ?? 0 },
                  { key: "kidney", label: "Renal Failures", color: "bg-cyan-500", val: analyticsReport.prevalence_rates?.kidney ?? 0 },
                  { key: "lungs", label: "Pulmonary Pathologies", color: "bg-[var(--danger)]", val: analyticsReport.prevalence_rates?.lungs ?? 0 }
                ].map((item) => (
                  <div key={item.key} className="space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono uppercase font-bold">
                      <span className="text-white">{item.label}</span>
                      <span className="text-[var(--text-secondary)]">{item.val.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-zinc-950 overflow-hidden border border-white/[0.02]">
                      <div 
                        style={{ width: `${item.val}%` }} 
                        className={`${item.color} h-full rounded-full transition-all duration-500`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ML Model Performance */}
          <div className="panel bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
            <div className="p-4 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Activity size={13} className="text-[var(--success)]" /> ML Model Retraining Accuracies (Gold Layer)
                </h4>
                <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                  Weekly automated PySpark model retraining performance telemetry.
                </p>
              </div>
              <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-zinc-900 border border-white/[0.05] text-[var(--text-secondary)] uppercase">
                5 Models Active
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse" aria-label="ML Models accuracy table">
                <thead className="text-[9px] font-bold uppercase tracking-wider bg-zinc-950/60 text-[var(--text-dim)] border-b border-[var(--border)]">
                  <tr>
                    <th className="px-4 py-3 border-r border-[var(--border)]">Model Identifier</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]">Target Area</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]">Conformed Dataset size</th>
                    <th className="px-4 py-3 border-r border-[var(--border)]">Training Accuracy</th>
                    <th className="px-4 py-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="text-[11px] font-mono">
                  {[
                    { id: "diabetes_model", label: "Diabetes Predictor", disease: "Diabetes Mellitus", size: "253,680 Rows", acc: analyticsReport.model_performance?.diabetes ?? 0.0 },
                    { id: "heart_disease_model", label: "Cardio Disease Predictor", disease: "Cardiovascular disease", size: "253,680 Rows", acc: analyticsReport.model_performance?.heart ?? 0.0 },
                    { id: "kidney_model", label: "Renal failure Predictor", disease: "Chronic kidney disease", size: "15 Rows", acc: analyticsReport.model_performance?.kidney ?? 0.0 },
                    { id: "liver_disease_model", label: "Hepatic Predictor", disease: "Liver disease", size: "30,691 Rows", acc: analyticsReport.model_performance?.liver ?? 0.0 },
                    { id: "lungs_model", label: "Pulmonary Predictor", disease: "Lung disease", size: "309 Rows", acc: analyticsReport.model_performance?.lungs ?? 0.0 }
                  ].map((model) => (
                    <tr key={model.id} className="border-b border-[var(--border)] hover:bg-white/[0.01] transition-colors">
                      <td className="px-4 py-3 border-r border-[var(--border)] text-white font-bold uppercase">{model.label}</td>
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] uppercase">{model.disease}</td>
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">{model.size}</td>
                      <td className="px-4 py-3 border-r border-[var(--border)]">
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-white w-12">{(model.acc * 100).toFixed(1)}%</span>
                          <div className="w-24 h-1.5 rounded-full bg-zinc-950 overflow-hidden border border-white/[0.02] shrink-0">
                            <div 
                              style={{ width: `${model.acc * 100}%` }} 
                              className={`h-full rounded-full transition-all duration-500 ${
                                model.acc >= 0.8 
                                  ? "bg-[var(--success)]" 
                                  : model.acc >= 0.7 
                                  ? "bg-amber-500" 
                                  : "bg-[var(--danger)]"
                              }`}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${
                          model.acc > 0.0 
                            ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                            : "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]"
                        }`}>
                          {model.acc > 0.0 ? "OPTIMIZED" : "DEGRADED"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3.5 bg-white/[0.01] text-center border-t border-[var(--border)]">
              <p className="text-[10px] text-gray-500 italic font-medium">
                Disclaimer: Machine learning predictions are trained on conformed Silver & Gold datasets to assist clinician diagnostics. Model accuracies are evaluated on test sets and should not substitute human clinical expertise.
              </p>
            </div>
          </div>
        </>
      ) : (
        <div className="panel p-6 text-center text-xs text-[var(--text-dim)] font-mono">
          NO REPORT DATA LOADED. PLEASE SELECT "SYNC REPORT".
        </div>
      )}
    </div>
  );
}
