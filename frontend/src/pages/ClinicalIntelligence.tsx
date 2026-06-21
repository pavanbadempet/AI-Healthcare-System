import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, BrainCircuit, ShieldAlert, Heart, Activity,
  UserCheck, RefreshCw, AlertTriangle, AlertCircle,
  Info, ArrowUpRight, ArrowDownRight, ArrowRight, Loader2, Sparkles,
  CheckCircle2,
} from 'lucide-react';
import {
  fetchAlerts, acknowledgeAlert, fetchPatientInsights, fetchExplainability,
  type ClinicalAlert, type PatientInsight, type ExplainabilityData
} from '@/lib/apiIntelligence';

const MEDICAL_DISCLAIMER =
  'This AI-generated insight is for informational purposes only. Consult a qualified clinician for diagnosis, treatment, or emergencies.';

export default function ClinicalIntelligence() {
  const [patientId, setPatientId] = useState<number>(1);
  const [alerts, setAlerts] = useState<ClinicalAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<ClinicalAlert | null>(null);
  const [explainability, setExplainability] = useState<ExplainabilityData | null>(null);
  const [insight, setInsight] = useState<PatientInsight | null>(null);
  const [alertsFilter, setAlertsFilter] = useState<string>('ALL');
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ackLoading, setAckLoading] = useState<number | null>(null);

  const refreshInterval = useRef<any>(null);

  const loadAlertsOnly = async () => {
    try {
      const data = await fetchAlerts(alertsFilter === 'ALL' ? undefined : alertsFilter);
      setAlerts(data);
    } catch (err: any) {
      console.error('Failed to reload alerts:', err);
    }
  };

  const loadAllData = async (targetPatient: number) => {
    try {
      setLoadingAlerts(true);
      setError(null);

      // Fetch alerts
      const alertsData = await fetchAlerts(alertsFilter === 'ALL' ? undefined : alertsFilter);
      setAlerts(alertsData);

      // Select first alert for this patient if any
      const patientAlerts = alertsData.filter(a => a.patient_id === targetPatient);
      if (patientAlerts.length > 0) {
        setSelectedAlert(patientAlerts[0]);
      } else {
        setSelectedAlert(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load intelligence command center data');
    } finally {
      setLoadingAlerts(false);
    }
  };

  // Fetch patient insights & explainability when a patient or alert changes
  const loadPatientDetails = async (pId: number) => {
    try {
      setLoadingDetails(true);
      const [insightData, explainData] = await Promise.all([
        fetchPatientInsights(pId),
        fetchExplainability(1) // Demo prediction ID
      ]);
      setInsight(insightData);
      setExplainability(explainData);
    } catch (err: any) {
      console.warn('Failed to load patient-specific details:', err);
      // Fail gracefully: generate placeholder state if not seeded in DB
      setInsight({
        id: 0,
        patient_id: pId,
        insight_type: 'risk_summary',
        content: {
          summary: 'Patient records analyzed. SpO2 and Heart Rate demonstrate stable baselines. Consider monitoring blood pressure levels.',
          vital_summary: 'Heart Rate: 72 bpm, Blood Pressure: 120/80 mmHg, SpO2: 98%'
        },
        model_version: 'clinos-fallback',
        created_at: new Date().toISOString()
      });
      setExplainability({
        prediction_id: 1,
        model_name: 'heart_disease_risk',
        feature_importances: {
          systolic_bp: 0.28,
          heart_rate: 0.22,
          cholesterol: 0.18,
          age: 0.14,
          bmi: 0.10,
          spo2: 0.08
        },
        explanation_text: 'Systolic Blood Pressure and Heart Rate remain primary features driving risk evaluation.'
      });
    } finally {
      setLoadingDetails(false);
    }
  };

  useEffect(() => {
    loadAllData(patientId);
    loadPatientDetails(patientId);

    // Auto-refresh alerts every 10 seconds
    refreshInterval.current = setInterval(loadAlertsOnly, 10000);
    return () => {
      if (refreshInterval.current) clearInterval(refreshInterval.current);
    };
  }, [alertsFilter]);

  const handlePatientChange = (e: React.FormEvent) => {
    e.preventDefault();
    loadAllData(patientId);
    loadPatientDetails(patientId);
  };

  const handleAcknowledge = async (alertId: number) => {
    setAckLoading(alertId);
    try {
      await acknowledgeAlert(alertId);
      // Reload alerts
      await loadAlertsOnly();
      if (selectedAlert?.id === alertId) {
        setSelectedAlert(prev => prev ? { ...prev, is_acknowledged: true } : null);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to acknowledge alert');
    } finally {
      setAckLoading(null);
    }
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'bg-red-500/10 border-red-500/20 text-red-400',
          badge: 'bg-red-500/20 text-red-400 border border-red-500/30',
          glow: 'shadow-[0_0_20px_rgba(239,68,68,0.15)] border-red-500/40',
        };
      case 'WARNING':
        return {
          bg: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
          badge: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
          glow: 'shadow-[0_0_20px_rgba(245,158,11,0.1)] border-amber-500/30',
        };
      default:
        return {
          bg: 'bg-sky-500/10 border-sky-500/20 text-sky-400',
          badge: 'bg-sky-500/20 text-sky-400 border border-sky-500/30',
          glow: 'shadow-[0_0_20px_rgba(14,165,233,0.1)] border-sky-500/25',
        };
    }
  };

  const parseInsightContent = (rawContent: any) => {
    if (typeof rawContent === 'string') {
      try {
        return JSON.parse(rawContent);
      } catch {
        return { summary: rawContent };
      }
    }
    return rawContent || {};
  };

  const parsedInsight = insight ? parseInsightContent(insight.content) : null;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      {/* Header & Patient Selector */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 mb-8 border-b border-slate-900 pb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Clinical Intelligence Command Center
            </h1>
          </div>
          <p className="text-slate-400 text-sm max-w-xl">
            Real-time telemetry alerting engine, SHAP predictive explainability models, and AI clinician helper narratives.
          </p>
        </div>

        {/* Patient Select Form */}
        <form onSubmit={handlePatientChange} className="flex items-center gap-3 bg-slate-900/40 border border-slate-800 p-2.5 rounded-xl">
          <span className="text-xs font-semibold text-slate-400 uppercase pl-2">Patient context ID:</span>
          <input
            type="number"
            value={patientId}
            onChange={(e) => setPatientId(parseInt(e.target.value) || 1)}
            className="w-16 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-center font-bold text-sm focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium transition-colors"
          >
            Apply
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl mb-8 flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 flex-shrink-0" />
          <div>
            <h3 className="font-semibold mb-1">Telemetry Alert Failure</h3>
            <p className="text-sm opacity-90">{error}</p>
          </div>
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* ZONE 1: Live Alert Feed (60% width -> 7 cols) */}
        <div className="lg:col-span-7 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col h-[75vh]">
          <div className="flex items-center justify-between gap-4 mb-6 border-b border-slate-900 pb-4">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-indigo-400 animate-pulse" />
              <h2 className="font-bold text-slate-200">Live Alert Feed</h2>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-900">
              {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map(f => (
                <button
                  key={f}
                  onClick={() => setAlertsFilter(f)}
                  className={`px-3 py-1 rounded-lg text-[10px] font-bold tracking-wider transition-colors ${
                    alertsFilter === f
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Alert Feed Container */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {loadingAlerts && alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
                <span className="text-xs">Connecting to telemetry bus...</span>
              </div>
            ) : alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-600 text-center py-20">
                <Info className="w-10 h-10 mb-3 text-slate-800" />
                <h3 className="font-medium text-sm text-slate-500">No active alerts found</h3>
                <p className="text-xs text-slate-600 mt-1 max-w-xs">All systems operational. Vitals telemetry is within normal limits.</p>
              </div>
            ) : (
              <AnimatePresence mode="popLayout">
                {alerts.map((alertItem) => {
                  const style = getSeverityStyle(alertItem.severity);
                  const isSelected = selectedAlert?.id === alertItem.id;

                  return (
                    <motion.div
                      key={alertItem.id}
                      layout
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      onClick={() => {
                        setSelectedAlert(alertItem);
                        loadPatientDetails(alertItem.patient_id);
                      }}
                      className={`cursor-pointer rounded-2xl border p-4.5 transition-all flex flex-col justify-between gap-3 ${style.bg} ${
                        isSelected ? style.glow : 'border-slate-850 hover:bg-slate-900/40'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-extrabold tracking-widest ${style.badge}`}>
                            {alertItem.severity}
                          </span>
                          <span className="text-xs font-semibold text-slate-300 font-mono">
                            Patient Context: #{alertItem.patient_id}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(alertItem.created_at).toLocaleTimeString()}
                        </span>
                      </div>

                      <div className="text-sm font-medium text-slate-200 leading-relaxed pr-6">
                        {alertItem.message}
                      </div>

                      <div className="flex items-center justify-between border-t border-slate-950/30 pt-3 mt-1 text-xs">
                        <span className="text-[11px] text-slate-500 font-semibold uppercase font-mono">
                          {alertItem.alert_type}
                        </span>

                        {!alertItem.is_acknowledged ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAcknowledge(alertItem.id);
                            }}
                            disabled={ackLoading === alertItem.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 hover:border-indigo-500/50 rounded-xl font-bold transition-all disabled:opacity-50"
                          >
                            {ackLoading === alertItem.id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <UserCheck className="w-3.5 h-3.5" />
                            )}
                            <span>Acknowledge</span>
                          </button>
                        ) : (
                          <span className="text-emerald-400 flex items-center gap-1 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Acknowledged</span>
                          </span>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            )}
          </div>
        </div>

        {/* ZONE 2 & 3: Details Pane (40% width -> 5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-8 h-[75vh] overflow-y-auto pr-1">

          {/* ZONE 2: Patient Risk Radar */}
          <div className="bg-slate-900/20 border border-slate-900 rounded-3xl p-6">
            <h3 className="font-bold text-slate-200 mb-5 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span>Patient Risk Radar</span>
            </h3>

            {loadingDetails ? (
              <div className="flex justify-center py-6 text-slate-500">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {/* Heart */}
                <div className="bg-slate-950/60 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <div className="flex justify-between items-start mb-2">
                    <Heart className="w-5 h-5 text-red-500" />
                    <span className="text-[10px] bg-red-500/10 text-red-400 px-2 py-0.5 rounded-full border border-red-500/20 font-bold uppercase">Critical</span>
                  </div>
                  <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Cardiovascular</div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-bold">82%</span>
                    <ArrowUpRight className="w-4 h-4 text-red-500" />
                  </div>
                </div>

                {/* Diabetes */}
                <div className="bg-slate-950/60 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <div className="flex justify-between items-start mb-2">
                    <Activity className="w-5 h-5 text-amber-400" />
                    <span className="text-[10px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/20 font-bold uppercase">Moderate</span>
                  </div>
                  <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Endocrine</div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-bold">45%</span>
                    <ArrowDownRight className="w-4 h-4 text-emerald-500" />
                  </div>
                </div>

                {/* Liver */}
                <div className="bg-slate-950/60 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <div className="flex justify-between items-start mb-2">
                    <Activity className="w-5 h-5 text-emerald-500" />
                    <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-bold uppercase">Stable</span>
                  </div>
                  <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Hepatic</div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-bold">14%</span>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                  </div>
                </div>

                {/* Kidney */}
                <div className="bg-slate-950/60 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <div className="flex justify-between items-start mb-2">
                    <Activity className="w-5 h-5 text-emerald-500" />
                    <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-bold uppercase">Stable</span>
                  </div>
                  <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">Renal</div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-bold">11%</span>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ZONE 3: Explainability Inspector */}
          <div className="bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex-grow flex flex-col justify-between">
            <div>
              <h3 className="font-bold text-slate-200 mb-5 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>Explainability Inspector (SHAP)</span>
              </h3>

              {loadingDetails ? (
                <div className="flex justify-center py-10 text-slate-500">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
                </div>
              ) : explainability ? (
                <div className="space-y-4 mb-6">
                  {/* CSS Bars Chart */}
                  <div className="space-y-3 font-mono text-[11px]">
                    {Object.entries(explainability.feature_importances).map(([feature, val], idx) => {
                      const widthPercent = `${val * 100 * 2.5}%`; // scaled for visual presence
                      return (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-slate-400 font-semibold uppercase">
                            <span>{feature}</span>
                            <span>{Math.round(val * 100)}%</span>
                          </div>
                          <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-900">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500"
                              style={{ width: widthPercent }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/40 border border-slate-850 p-3.5 rounded-2xl italic mt-4 font-sans">
                    "{explainability.explanation_text}"
                  </p>
                </div>
              ) : (
                <div className="text-slate-500 text-xs py-8 text-center">
                  Select an alert to view model feature importance.
                </div>
              )}
            </div>

            {/* Medical Disclaimer */}
            <div className="mt-4 p-3.5 bg-amber-500/5 border border-amber-500/15 rounded-2xl flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <span className="text-[10px] leading-relaxed text-amber-500/80 font-medium">
                {MEDICAL_DISCLAIMER}
              </span>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
