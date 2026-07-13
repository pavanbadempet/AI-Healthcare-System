/**
 * AnalyticsPanel – Medallion Gold Layer Insights tab for the Admin page.
 * Extracted from Admin.tsx for maintainability.
 */
import { useState } from "react";
import { Activity, Sparkles, RefreshCw, ShieldAlert, Loader2, BarChart2, ShieldCheck, Database, Trash } from "lucide-react";
import { 
  getAnalyticsReport, 
  getAttributionDriftReport, 
  getSemanticCacheStats,
  clearSemanticCache,
  getAIFunctionRegistry,
  getModelCards,
  type AnalyticsReport, 
  type AttributionDriftReport,
  type SemanticCacheStats,
  type AIFunctionRegistryResponse,
  type ModelCardsResponse
} from "@/lib/api";

export default function AnalyticsPanel() {
  const [analyticsReport, setAnalyticsReport] = useState<AnalyticsReport | null>(null);
  const [driftReport, setDriftReport] = useState<AttributionDriftReport | null>(null);
  const [cacheStats, setCacheStats] = useState<SemanticCacheStats | null>(null);
  const [aiFunctions, setAiFunctions] = useState<AIFunctionRegistryResponse | null>(null);
  const [modelCards, setModelCards] = useState<ModelCardsResponse | null>(null);
  const [activeGovernanceTab, setActiveGovernanceTab] = useState<"functions" | "models">("functions");
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState("");

  const fetchAnalyticsReport = () => {
    setAnalyticsLoading(true);
    setAnalyticsError("");
    Promise.all([
      getAnalyticsReport(),
      getAttributionDriftReport(),
      getSemanticCacheStats(),
      getAIFunctionRegistry(),
      getModelCards()
    ])
      .then(([analyticsData, driftData, cacheData, aiFuncs, mCards]) => {
        setAnalyticsReport(analyticsData);
        setDriftReport(driftData);
        setCacheStats(cacheData.stats);
        setAiFunctions(aiFuncs);
        setModelCards(mCards);
      })

      .catch((err) => {
        console.error("Failed to load analytics reports", err);
        setAnalyticsError(err.message || "Failed to load report data.");
      })
      .finally(() => setAnalyticsLoading(false));
  };

  const handleClearCache = async () => {
    if (!window.confirm("Are you sure you want to flush the LLM Semantic Cache? All cached narratives will be evicted.")) return;
    try {
      await clearSemanticCache();
      alert("LLM Semantic Cache cleared successfully!");
      const cacheData = await getSemanticCacheStats();
      setCacheStats(cacheData.stats);
    } catch (err: any) {
      alert("Failed to clear cache: " + err.message);
    }
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

          {/* SHAP Feature Attribution Drift Monitoring */}
          <div className="panel bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
            <div className="p-4 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart2 size={13} className="text-[var(--accent)]" /> SHAP Feature Attribution Drift Monitoring
                </h4>
                <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                  Wasserstein & Cosine distance tracking of production SHAP values vs baseline.
                </p>
              </div>
              <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-zinc-900 border border-white/[0.05] text-[var(--text-secondary)] uppercase">
                Active Drift Audits
              </span>
            </div>

            <div className="p-4 space-y-6">
              {driftReport ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {Object.entries(driftReport).map(([modelKey, modelReport]) => {
                    const getStatusBadge = (status: string) => {
                      if (status.includes("Low")) {
                        return "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]";
                      }
                      if (status.includes("Moderate") || status.includes("Warning")) {
                        return "bg-amber-500/10 text-amber-500 border-amber-500/30";
                      }
                      return "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]";
                    };

                    const modelLabel = modelKey.charAt(0).toUpperCase() + modelKey.slice(1) + " Predictor";

                    return (
                      <div key={modelKey} className="border border-[var(--border)] rounded p-4 bg-zinc-950/20 space-y-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-xs font-bold text-white uppercase">{modelLabel}</span>
                            <span className="block text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                              Sample Count: {modelReport.sample_count} | Drift Score: {modelReport.drift_score.toFixed(4)}
                            </span>
                          </div>
                          <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase border ${getStatusBadge(modelReport.status)}`}>
                            {modelReport.status}
                          </span>
                        </div>

                        {modelReport.production_relative_attributions && modelReport.sample_count > 0 ? (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 pt-2 border-t border-[var(--border)]/40">
                            {Object.entries(modelReport.baseline_relative_attributions)
                              .slice(0, 6) // show top 6 features to avoid layout bloat
                              .map(([feature, baselineVal]) => {
                                const prodVal = modelReport.production_relative_attributions[feature] ?? 0;
                                return (
                                  <div key={feature} className="space-y-1 py-1">
                                    <div className="flex justify-between text-[9px] font-mono uppercase">
                                      <span className="text-[var(--text-secondary)] font-bold">{feature}</span>
                                      <span className="text-[var(--text-dim)]">
                                        Base: {(baselineVal * 100).toFixed(1)}% | Prod: {(prodVal * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <div className="w-full h-1 bg-zinc-900 rounded overflow-hidden flex">
                                        <div 
                                          style={{ width: `${baselineVal * 100}%` }} 
                                          className="bg-blue-500/60 h-full"
                                          title="Baseline"
                                        />
                                        <div 
                                          style={{ width: `${prodVal * 100}%` }} 
                                          className="bg-[var(--accent)] h-full border-l border-black/50"
                                          title="Production"
                                        />
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                        ) : (
                          <p className="text-center font-mono text-[9px] text-[var(--text-dim)] uppercase py-2">
                            {modelReport.message || "No production predictions logged yet for this model."}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-center font-mono text-[10px] text-[var(--text-dim)] uppercase py-4">No attribution drift data available.</p>
              )}
            </div>
          </div>

          {/* LLM Semantic Cache Telemetry & Management */}
          <div className="panel bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
            <div className="p-4 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between items-center">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Database size={13} className="text-purple-400" /> LLM Semantic Cache Management
                </h4>
                <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                  Audit cached narratives and flush database to evict stale entries.
                </p>
              </div>
              
              <button
                onClick={handleClearCache}
                disabled={!cacheStats || cacheStats.size === 0}
                className="btn-clinical text-xs py-1 px-2.5 bg-red-950/20 text-red-400 border border-red-500/20 hover:bg-red-900/20 flex items-center gap-1.5 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <Trash size={11} /> Flush Cache
              </button>
            </div>

            <div className="p-4 space-y-4">
              {cacheStats ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left Column: Metrics */}
                  <div className="lg:col-span-1 bg-zinc-950/40 border border-[var(--border)] rounded p-4 flex flex-col justify-between font-mono text-[10px] uppercase">
                    <div className="space-y-3">
                      <div>
                        <span className="text-[var(--text-dim)] font-bold block mb-0.5">Total Cached Prompts</span>
                        <span className="text-lg font-black text-white">{cacheStats.size}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <span className="text-[var(--text-dim)] font-bold block mb-0.5">Cache Hits</span>
                          <span className="text-sm font-bold text-[var(--success)]">{cacheStats.hits}</span>
                        </div>
                        <div>
                          <span className="text-[var(--text-dim)] font-bold block mb-0.5">Cache Misses</span>
                          <span className="text-sm font-bold text-[var(--text-secondary)]">{cacheStats.misses}</span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-[var(--border)]/40 mt-4">
                      <span className="text-[var(--text-dim)] font-bold block mb-1">Hit Rate Efficiency</span>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-bold text-white">
                          {cacheStats.hits + cacheStats.misses > 0
                            ? `${((cacheStats.hits / (cacheStats.hits + cacheStats.misses)) * 100).toFixed(1)}%`
                            : "0.0%"}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-zinc-900 rounded overflow-hidden">
                        <div
                          style={{
                            width: `${
                              cacheStats.hits + cacheStats.misses > 0
                                ? (cacheStats.hits / (cacheStats.hits + cacheStats.misses)) * 100
                                : 0
                            }%`,
                          }}
                          className="bg-purple-500 h-full rounded-full transition-all duration-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Cached Queries List */}
                  <div className="lg:col-span-2 space-y-2">
                    <span className="text-[9px] font-bold text-[var(--text-dim)] uppercase tracking-wider block">Cached Entry Audits (Last 5)</span>
                    {cacheStats.entries.length > 0 ? (
                      <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                        {cacheStats.entries.slice(-5).map((entry, idx) => (
                          <div
                            key={idx}
                            className="bg-zinc-950/20 border border-[var(--border)] rounded p-2 flex justify-between items-center text-[9px] font-mono uppercase"
                          >
                            <span className="text-white truncate max-w-[280px]" title={entry.query}>
                              "{entry.query}"
                            </span>
                            <span className="text-[var(--text-dim)] shrink-0 border border-white/[0.03] px-1 py-0.5 rounded bg-zinc-950/30">
                              len: {entry.response_length} chars
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="panel p-6 text-center text-[9px] font-mono text-[var(--text-dim)] uppercase border-dashed border-[var(--border)]">
                        No entries cached yet. Run LLM queries to build cache telemetry.
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-center font-mono text-[10px] text-[var(--text-dim)] uppercase py-4">No semantic cache telemetry loaded.</p>
              )}
            </div>
          </div>

          {/* Clinical AI Governance Registry */}
          <div className="panel bg-[rgba(24,24,27,0.4)] border border-[var(--border)] rounded">
            <div className="p-4 border-b border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex flex-col md:flex-row md:justify-between md:items-center gap-3">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck size={13} className="text-emerald-400" /> Clinical AI Governance Registry
                </h4>
                <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase mt-0.5">
                  FDA CDS, WHO AI & EU AI Act Intended-Use Evidence Artifacts
                </p>
              </div>

              {/* Tab Selector */}
              <div className="flex bg-zinc-950/60 p-0.5 rounded border border-[var(--border)] text-[9px] font-mono uppercase">
                <button
                  onClick={() => setActiveGovernanceTab("functions")}
                  className={`px-3 py-1 rounded transition-colors duration-200 cursor-pointer ${
                    activeGovernanceTab === "functions" ? "bg-[var(--accent)] text-black font-bold" : "text-[var(--text-dim)] hover:text-white"
                  }`}
                >
                  AI Functions ({aiFunctions?.functions.length || 0})
                </button>
                <button
                  onClick={() => setActiveGovernanceTab("models")}
                  className={`px-3 py-1 rounded transition-colors duration-200 cursor-pointer ${
                    activeGovernanceTab === "models" ? "bg-[var(--accent)] text-black font-bold" : "text-[var(--text-dim)] hover:text-white"
                  }`}
                >
                  Model & Dataset Cards ({modelCards?.model_cards.length || 0})
                </button>
              </div>
            </div>

            <div className="p-4">
              {activeGovernanceTab === "functions" ? (
                aiFunctions && aiFunctions.functions.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {aiFunctions.functions.map((func) => (
                      <div
                        key={func.id}

                        className="bg-zinc-950/20 border border-[var(--border)] rounded p-4 space-y-3 font-mono text-[9px] uppercase"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-[var(--text-dim)] block text-[8px]">Function ID: {func.id}</span>
                            <h5 className="text-white text-xs font-bold font-sans tracking-wide normal-case mt-0.5">{func.name}</h5>
                          </div>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                              func.risk_category.toLowerCase().includes("high")
                                ? "bg-red-950/30 text-red-400 border border-red-500/20"
                                : func.risk_category.toLowerCase().includes("medium") || func.risk_category.toLowerCase().includes("review")
                                ? "bg-yellow-950/30 text-yellow-400 border border-yellow-500/20"
                                : "bg-emerald-950/30 text-emerald-400 border border-emerald-500/20"
                            }`}
                          >
                            {func.risk_category}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[8px]">
                          <div>
                            <span className="text-[var(--text-dim)] block">Module Location</span>
                            <span className="text-white select-all block truncate" title={func.module}>{func.module}</span>
                          </div>
                          <div>
                            <span className="text-[var(--text-dim)] block">Audience Scope</span>
                            <span className="text-white">{func.audience.join(" / ")}</span>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-[var(--border)]/40 space-y-1.5">
                          <span className="text-[var(--text-dim)] block text-[8px]">Endpoints</span>
                          <div className="flex flex-wrap gap-1">
                            {func.endpoints.map((ep, idx) => (
                              <span key={idx} className="bg-zinc-900 border border-[var(--border)] text-white px-1.5 py-0.5 rounded font-mono text-[8px] select-all">
                                {ep}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="pt-2 border-t border-[var(--border)]/40 flex flex-wrap gap-1.5">
                          {func.clinical_safety_required && (
                            <span className="bg-emerald-950/20 text-emerald-400 border border-emerald-500/10 px-1 py-0.5 rounded text-[7px]" title="Clinical Safety Verification Required">
                              🏥 Safety Gate
                            </span>
                          )}
                          {func.medical_disclaimer_required && (
                            <span className="bg-purple-950/20 text-purple-400 border border-purple-500/10 px-1 py-0.5 rounded text-[7px]" title="Disclaimer Required">
                              ⚖️ Disclaimer
                            </span>
                          )}
                          {func.human_review_required && (
                            <span className="bg-blue-950/20 text-blue-400 border border-blue-500/10 px-1 py-0.5 rounded text-[7px]" title="Human-in-the-loop Review Required">
                              👤 Human-in-loop
                            </span>
                          )}
                          {func.uses_ai_provider && (
                            <span className="bg-orange-950/20 text-orange-400 border border-orange-500/10 px-1 py-0.5 rounded text-[7px]" title={`Runs via LLM Provider boundary: ${func.provider_boundary}`}>
                              🤖 {func.provider_boundary}
                            </span>
                          )}
                        </div>

                        {func.notes && (
                          <div className="pt-2 border-t border-[var(--border)]/40 bg-zinc-950/30 p-2 rounded text-[8px] leading-relaxed text-[var(--text-secondary)] normal-case font-sans">
                            <strong>Governance Note:</strong> {func.notes}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center font-mono text-[10px] text-[var(--text-dim)] uppercase py-4">No AI functions registered.</p>
                )
              ) : (
                modelCards && modelCards.model_cards.length > 0 ? (
                  <div className="space-y-4">
                    {modelCards.model_cards.map((model) => {
                      const dataset = modelCards.dataset_cards.find((d) => d.id === model.dataset_card_id);
                      return (
                        <div
                          key={model.id}
                          className="bg-zinc-950/20 border border-[var(--border)] rounded p-4 space-y-4 font-mono text-[9px] uppercase"
                        >
                          {/* Header */}
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2">
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="text-[var(--text-dim)] text-[8px]">Model ID: {model.id}</span>
                                {model.artifact_exists ? (
                                  <span className="bg-emerald-950/30 text-emerald-400 border border-emerald-500/20 px-1 rounded text-[7px] font-bold">
                                    Active: {(model.artifact_size_bytes / (1024 * 1024)).toFixed(2)} MB
                                  </span>
                                ) : (
                                  <span className="bg-red-950/30 text-red-400 border border-red-500/20 px-1 rounded text-[7px] font-bold">
                                    Missing Artifact
                                  </span>
                                )}
                              </div>
                              <h5 className="text-white text-xs font-bold font-sans tracking-wide normal-case mt-0.5">{model.name}</h5>
                            </div>
                            <div className="flex flex-wrap gap-1 text-[8px]">
                              <span className="bg-zinc-900 border border-[var(--border)] text-[var(--text-secondary)] px-1.5 py-0.5 rounded">
                                {model.model_family}
                              </span>
                              <span className="bg-zinc-900 border border-[var(--border)] text-[var(--text-secondary)] px-1.5 py-0.5 rounded">
                                Category: {model.clinical_use_category}
                              </span>
                            </div>
                          </div>

                          {/* Body Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-[var(--border)]/40">
                            {/* Left Column: Intended Use, Limits */}
                            <div className="space-y-3">
                              <div>
                                <span className="text-[var(--text-dim)] block text-[8px]">Intended Clinical Use</span>
                                <p className="text-white normal-case font-sans text-[9px] mt-0.5 leading-relaxed">{model.intended_use}</p>
                              </div>
                              <div>
                                <span className="text-[var(--text-dim)] block text-[8px]">Known Limitations / Boundary conditions</span>
                                <ul className="list-disc pl-4 text-[var(--text-secondary)] normal-case font-sans text-[8px] space-y-1 mt-1 leading-relaxed">
                                  {model.limitations.map((lim, idx) => (
                                    <li key={idx}>{lim}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>

                            {/* Right Column: Training Dataset metadata */}
                            <div className="bg-zinc-950/30 p-3 rounded border border-[var(--border)]/50 space-y-2.5">
                              <div className="flex justify-between items-center">
                                <span className="text-white text-[9px] font-bold">Training Dataset Card</span>
                                {dataset?.contains_production_patient_data ? (
                                  <span className="bg-amber-950/30 text-amber-400 border border-amber-500/20 px-1 rounded text-[7px]">
                                    Contains Prod Data
                                  </span>
                                ) : (
                                  <span className="bg-zinc-900 border border-[var(--border)] text-[var(--text-dim)] px-1 rounded text-[7px]">
                                    De-identified / Public
                                  </span>
                                )}
                              </div>

                              {dataset ? (
                                <div className="space-y-2">
                                  <div>
                                    <span className="text-[var(--text-dim)] block text-[8px]">Name</span>
                                    <span className="text-white font-sans normal-case text-[9px]">{dataset.name}</span>
                                  </div>
                                  <div className="grid grid-cols-2 gap-1.5 text-[8px]">
                                    <div>
                                      <span className="text-[var(--text-dim)] block">Source / Publisher</span>
                                      <span className="text-white">{dataset.source}</span>
                                    </div>
                                    <div>
                                      <span className="text-[var(--text-dim)] block">Local File</span>
                                      <span className="text-white font-mono select-all truncate block" title={dataset.local_artifact}>
                                        {dataset.local_artifact}
                                      </span>
                                    </div>
                                  </div>
                                  <div>
                                    <span className="text-[var(--text-dim)] block text-[8px]">Dataset Limitations</span>
                                    <ul className="list-disc pl-3 text-[var(--text-secondary)] normal-case font-sans text-[7px] space-y-0.5 leading-relaxed mt-0.5">
                                      {dataset.known_limitations.map((lim, idx) => (
                                        <li key={idx}>{lim}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                              ) : (
                                <p className="text-[8px] text-[var(--text-dim)] uppercase">Dataset card metadata not found ({model.dataset_card_id}).</p>
                              )}
                            </div>
                          </div>

                          {/* Footer Info */}
                          <div className="pt-2 border-t border-[var(--border)]/40 flex flex-wrap gap-2 text-[8px] text-[var(--text-dim)]">
                            <div>
                              <span>Target Users: </span>
                              <span className="text-white">{model.target_users.join(" & ")}</span>
                            </div>
                            <span className="text-[var(--border)]">•</span>
                            <div>
                              <span>Feature Dimension Count: </span>
                              <span className="text-white">{model.feature_count} Inputs</span>
                            </div>
                            <span className="text-[var(--border)]">•</span>
                            <div>
                              <span>Outputs: </span>
                              <span className="text-white normal-case">{model.output}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-center font-mono text-[10px] text-[var(--text-dim)] uppercase py-4">No model cards loaded.</p>
                )
              )}
            </div>

            {modelCards?.privacy_note && (
              <div className="p-3 border-t border-[var(--border)] bg-zinc-950/20 text-center font-mono text-[8px] text-[var(--text-dim)] uppercase tracking-wider">
                🔒 Privacy Statement: {modelCards.privacy_note}
              </div>
            )}
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
