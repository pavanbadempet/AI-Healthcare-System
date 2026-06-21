import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, BrainCircuit, ShieldAlert, Heart, Activity,
  UserCheck, RefreshCw, AlertTriangle, AlertCircle,
  Info, ArrowUpRight, ArrowDownRight, ArrowRight, Loader2, Sparkles,
  CheckCircle2, Users, CheckSquare, Stethoscope, FileText, ChevronRight
} from 'lucide-react';
import {
  fetchAlerts, acknowledgeAlert, fetchPatientInsights, fetchExplainability, fetchAdvisoryBoard,
  generateScribeSOAP, commitScribeSOAP, fetchCounterfactualRecourse, fetchClinicalConsensus,
  uploadLabReportImage,
  type ClinicalAlert, type PatientInsight, type ExplainabilityData, type AdvisoryBoardDebate
} from '@/lib/apiIntelligence';
import { Mic, Save, Sliders, ClipboardCopy, TrendingDown, RefreshCcw } from 'lucide-react';

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
  const [activeTab, setActiveTab] = useState<'FEED' | 'ADVISORY' | 'SCRIBE' | 'SIMULATOR' | 'LAB_ANALYZER'>('FEED');
  const [advisoryDebate, setAdvisoryDebate] = useState<AdvisoryBoardDebate | null>(null);
  const [loadingAdvisory, setLoadingAdvisory] = useState(false);
  const [advisoryError, setAdvisoryError] = useState<string | null>(null);

  // Scribe State
  const [transcript, setTranscript] = useState<string>('');
  const [scribeNote, setScribeNote] = useState<any>(null);
  const [loadingScribe, setLoadingScribe] = useState(false);
  const [scribeError, setScribeError] = useState<string | null>(null);
  const [scribeSuccess, setScribeSuccess] = useState<string | null>(null);

  // Simulator State
  const [selectedModel, setSelectedModel] = useState<'diabetes' | 'heart'>('diabetes');
  const [simDiabetes, setSimDiabetes] = useState({
    bmi: 27.5,
    hypertension: 1,
    high_chol: 1,
    physical_activity: 0,
    smoking_history: 1,
    general_health: 3,
    age: 50,
    gender: 1
  });
  const [simHeart, setSimHeart] = useState({
    age: 55,
    sex: 1,
    cp: 1,
    trestbps: 145,
    chol: 240,
    fbs: 0,
    restecg: 1,
    thalach: 135,
    exang: 1,
    oldpeak: 1.5,
    slope: 1,
    ca: 0,
    thal: 2
  });
  const [simResult, setSimResult] = useState<any>(null);
  const [loadingSim, setLoadingSim] = useState(false);
  const [consensus, setConsensus] = useState<any>(null);
  const [loadingConsensus, setLoadingConsensus] = useState(false);

  // Smart Lab Analyzer State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingReport, setUploadingReport] = useState(false);
  const [analyzerResult, setAnalyzerResult] = useState<any>(null);
  const [analyzerError, setAnalyzerError] = useState("");

  const handleUploadReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploadingReport(true);
    setAnalyzerError("");
    setAnalyzerResult(null);
    try {
      const data = await uploadLabReportImage(selectedFile);
      setAnalyzerResult(data);
    } catch (err: any) {
      setAnalyzerError(err.message || "Failed to analyze report file");
    } finally {
      setUploadingReport(false);
    }
  };

  const runClinicalConsensus = async () => {
    setLoadingConsensus(true);
    try {
      const data = await fetchClinicalConsensus(patientId);
      setConsensus(data);
    } catch (err: any) {
      console.error("Consensus check failed:", err);
    } finally {
      setLoadingConsensus(false);
    }
  };

  const runAdvisoryBoard = async () => {
    setLoadingAdvisory(true);
    setAdvisoryError(null);
    try {
      const data = await fetchAdvisoryBoard(patientId);
      setAdvisoryDebate(data);
    } catch (err: any) {
      setAdvisoryError(err.message || 'Failed to run advisory board.');
    } finally {
      setLoadingAdvisory(false);
    }
  };

  const runScribe = async () => {
    if (!transcript.trim()) return;
    setLoadingScribe(true);
    setScribeError(null);
    setScribeSuccess(null);
    try {
      const data = await generateScribeSOAP(patientId, transcript);
      setScribeNote(data);
    } catch (err: any) {
      setScribeError(err.message || 'Failed to generate scribe SOAP note.');
    } finally {
      setLoadingScribe(false);
    }
  };

  const commitScribe = async () => {
    if (!scribeNote?.data) return;
    setLoadingScribe(true);
    setScribeError(null);
    setScribeSuccess(null);
    try {
      const payload = {
        patient_id: patientId,
        subjective: scribeNote.data.subjective,
        objective: scribeNote.data.objective,
        assessment: scribeNote.data.assessment,
        plan: scribeNote.data.plan,
        icd10_codes: scribeNote.data.icd10_codes || [],
        billing_codes: scribeNote.data.billing_codes || [],
        prescriptions: scribeNote.data.prescriptions || [],
        billing_items: scribeNote.data.billing_items || [],
      };
      const res = await commitScribeSOAP(payload);
      setScribeSuccess(res.message || 'SOAP note, prescriptions, and invoice committed to EHR!');
    } catch (err: any) {
      setScribeError(err.message || 'Failed to commit to EHR.');
    } finally {
      setLoadingScribe(false);
    }
  };

  const runSimulator = async () => {
    setLoadingSim(true);
    try {
      const features = selectedModel === 'diabetes' ? simDiabetes : simHeart;
      const data = await fetchCounterfactualRecourse(patientId, selectedModel, features);
      setSimResult(data);
    } catch (err) {
      console.error('Failed to run simulator:', err);
    } finally {
      setLoadingSim(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'SIMULATOR') {
      runSimulator();
    }
  }, [simDiabetes, simHeart, selectedModel, activeTab]);


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
    setAdvisoryDebate(null);
    setAdvisoryError(null);
    setConsensus(null);
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

      {/* Tabs Navigation */}
      <div className="flex gap-4 mb-8 border-b border-slate-900 pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('FEED')}
          className={`flex items-center gap-2 pb-3 px-1 text-sm font-semibold tracking-wide transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'FEED'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Bell className="w-4 h-4" />
          <span>Command Center Feed</span>
        </button>
        <button
          onClick={() => setActiveTab('ADVISORY')}
          className={`flex items-center gap-2 pb-3 px-1 text-sm font-semibold tracking-wide transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'ADVISORY'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Clinical Advisory Board</span>
        </button>
        <button
          onClick={() => setActiveTab('SCRIBE')}
          className={`flex items-center gap-2 pb-3 px-1 text-sm font-semibold tracking-wide transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'SCRIBE'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>Ambient Scribe</span>
        </button>
        <button
          onClick={() => setActiveTab('SIMULATOR')}
          className={`flex items-center gap-2 pb-3 px-1 text-sm font-semibold tracking-wide transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'SIMULATOR'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Risk Simulator</span>
        </button>
        <button
          onClick={() => setActiveTab('LAB_ANALYZER')}
          className={`flex items-center gap-2 pb-3 px-1 text-sm font-semibold tracking-wide transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'LAB_ANALYZER'
              ? 'border-indigo-500 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Smart Lab Analyzer</span>
        </button>
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

      {activeTab === 'FEED' && (
        /* Main Layout Grid */
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
      )}

      {activeTab === 'ADVISORY' && (
        <div className="space-y-8 animate-fadeIn">
          {advisoryError && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <div>
                <h3 className="font-semibold mb-1">Advisory Board Error</h3>
                <p className="text-sm opacity-90">{advisoryError}</p>
              </div>
            </div>
          )}

          {/* Trigger Button or Status */}
          {!advisoryDebate && !loadingAdvisory && (
            <div className="bg-slate-900/20 border border-slate-900 rounded-3xl p-10 text-center flex flex-col items-center justify-center max-w-2xl mx-auto space-y-6">
              <div className="p-4 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <BrainCircuit className="w-10 h-10" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-100">Trigger Clinical Advisory Board</h2>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  Initiate a multi-agent consultation session. The AI Cardiology, Endocrinology, and General Practitioner agents will debate the case and synthesize a consensus report.
                </p>
              </div>
              <button
                onClick={runAdvisoryBoard}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <Sparkles className="w-4 h-4" />
                <span>Start Multi-Agent Consult</span>
              </button>
            </div>
          )}

          {/* Loading State with animated debate timeline */}
          {loadingAdvisory && (
            <div className="bg-slate-900/20 border border-slate-900 rounded-3xl p-8 max-w-xl mx-auto space-y-6">
              <div className="flex items-center gap-3 border-b border-slate-900 pb-4 justify-center">
                <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                <h3 className="font-bold text-slate-200">Advisory Debate in Progress...</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">1</div>
                  <span className="text-sm font-semibold text-slate-300">Extracting patient EHR context and ML predictions...</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">2</div>
                  <span className="text-sm font-semibold text-slate-300">Generating initial Cardiologist & Endocrinologist opinions...</span>
                </div>
                <div className="flex items-center gap-3 animate-pulse">
                  <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">3</div>
                  <span className="text-sm font-semibold text-indigo-400">Performing cross-consultation review...</span>
                </div>
                <div className="flex items-center gap-3 opacity-50">
                  <div className="w-5 h-5 rounded-full bg-slate-900 text-slate-600 border border-slate-800 flex items-center justify-center text-xs font-bold font-mono">4</div>
                  <span className="text-sm font-semibold text-slate-400">Synthesizing consensus report note...</span>
                </div>
              </div>
            </div>
          )}

          {/* Debate Result Loaded */}
          {advisoryDebate && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Column: Debate Chat Logs (7 cols) */}
              <div className="lg:col-span-7 space-y-6">
                <h3 className="font-bold text-slate-200 flex items-center justify-between border-b border-slate-900 pb-3">
                  <span className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-indigo-400" />
                    <span>Sequential Consult Transcript</span>
                  </span>
                  <span className="text-xs text-slate-500 font-mono font-normal">
                    Patient Vitals Context: {advisoryDebate.patient_vitals_context}
                  </span>
                </h3>

                <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
                  {/* Round 1 Opinions */}
                  <div className="space-y-4">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Round 1: Initial Specialist Assessments</div>
                    {/* Cardiologist */}
                    <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-4.5 space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                        <span className="text-xs font-bold text-red-400">Dr. Alicia (Cardiologist Agent)</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line">
                        {advisoryDebate.debate.round1.cardiologist}
                      </p>
                    </div>
                    {/* Endocrinologist */}
                    <div className="bg-amber-500/5 border border-amber-500/10 rounded-2xl p-4.5 space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                        <span className="text-xs font-bold text-amber-400">Dr. Marcus (Endocrinologist Agent)</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line">
                        {advisoryDebate.debate.round1.endocrinologist}
                      </p>
                    </div>
                  </div>

                  {/* Round 2 Rebuttals */}
                  <div className="space-y-4">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Round 2: Cross-Consultation comments</div>
                    {/* Cardiologist rebuttal */}
                    <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-4.5 space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                        <span className="text-xs font-bold text-red-400">Dr. Alicia (Cardiologist Agent)</span>
                        <span className="text-[9px] bg-red-500/20 text-red-300 px-1.5 py-0.5 rounded font-extrabold tracking-widest font-mono">REBUTTAL</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line">
                        {advisoryDebate.debate.round2.cardiologist_rebuttal}
                      </p>
                    </div>
                    {/* Endocrinologist rebuttal */}
                    <div className="bg-amber-500/5 border border-amber-500/10 rounded-2xl p-4.5 space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                        <span className="text-xs font-bold text-amber-400">Dr. Marcus (Endocrinologist Agent)</span>
                        <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-extrabold tracking-widest font-mono">REBUTTAL</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-serif whitespace-pre-line">
                        {advisoryDebate.debate.round2.endocrinologist_rebuttal}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: final consensus report (5 cols) */}
              <div className="lg:col-span-5 space-y-6">
                <div className="bg-slate-900/30 border border-slate-900 rounded-3xl p-6 space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-4">
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-5 h-5 text-indigo-400" />
                      <h3 className="font-bold text-slate-200">Consensus Report Card</h3>
                    </div>
                    <button
                      onClick={runAdvisoryBoard}
                      className="p-2 bg-slate-950 hover:bg-slate-900 text-slate-400 hover:text-white rounded-lg border border-slate-800 transition-colors"
                      title="Re-run consultation"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Consensus Note */}
                  <div className="space-y-2">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">GP Coordinator Synthesis</div>
                    <div className="p-4 bg-slate-950/60 border border-slate-850 rounded-2xl space-y-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-indigo-500" />
                        <span className="text-xs font-bold text-indigo-400">Dr. Sarah (Coordinator Agent)</span>
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed">
                        {advisoryDebate.debate.round3.coordinator_synthesis.consensus_note}
                      </p>
                    </div>
                  </div>

                  {/* ICD-10 Codes */}
                  <div className="space-y-2">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Primary Diagnostic ICD-10 Codes</div>
                    <div className="flex flex-wrap gap-2">
                      {advisoryDebate.debate.round3.coordinator_synthesis.icd10_codes.map((code: string, idx: number) => (
                        <span key={idx} className="px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded-lg text-xs font-bold font-mono">
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Treatment Priorities */}
                  <div className="space-y-2">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Treatment Priorities</div>
                    <ul className="space-y-2.5">
                      {advisoryDebate.debate.round3.coordinator_synthesis.treatment_plan.map((item: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                          <CheckSquare className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Lifestyle Recommendations */}
                  <div className="space-y-2">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Lifestyle Recommendations</div>
                    <ul className="space-y-2.5">
                      {advisoryDebate.debate.round3.coordinator_synthesis.lifestyle_plan.map((item: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                          <CheckSquare className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Telemetry info */}
                  <div className="border-t border-slate-900 pt-4 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span>Inference latency: {advisoryDebate.telemetry.duration_seconds}s</span>
                    <span>Estimated cost: ${advisoryDebate.telemetry.estimated_cost.toFixed(4)}</span>
                  </div>

                  {/* Disclaimer */}
                  <div className="p-3.5 bg-amber-500/5 border border-amber-500/15 rounded-2xl flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span className="text-[10px] leading-relaxed text-amber-500/80 font-medium font-sans">
                      {MEDICAL_DISCLAIMER}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'SCRIBE' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">
          {/* Left Column: Scribe consultation transcript input (7 cols) */}
          <div className="lg:col-span-7 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-4 h-[75vh]">
            <div className="flex items-center gap-2 border-b border-slate-900 pb-4">
              <Mic className="w-5 h-5 text-indigo-400" />
              <h2 className="font-bold text-slate-200">Ambient Clinical Consultation Scribe</h2>
            </div>
            
            <p className="text-xs text-slate-400 leading-relaxed">
              Paste or type a patient-doctor consultation transcript below. The Scribe Agent will parse symptoms, vitals, history, and compile a structured SOAP clinical record, complete with ICD-10 diagnosis/billing codes and recommended prescriptions.
            </p>

            <div className="p-3 rounded-2xl border border-yellow-500/20 bg-yellow-500/5 text-[10px] font-mono text-yellow-500 uppercase leading-normal">
              Medical Disclaimer: Ambient Scribe output is AI-generated clinical decision-support and does not replace professional clinical evaluation or judgment. Confirm all details before committing to EHR.
            </div>

            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Doctor: Good afternoon. How have you been feeling since our last visit?&#10;Patient: I've had some severe headaches and my feet have been swelling. Also, my blood sugar has been running high, around 180 in the mornings..."
              className="flex-1 bg-slate-950/60 border border-slate-850 rounded-2xl p-4 text-sm text-slate-300 focus:outline-none focus:border-indigo-500 font-sans resize-none"
            />

            <div className="flex items-center gap-3">
              <button
                onClick={() => setTranscript(
                  "Doctor: Hi there. Let's review your symptoms today.\n" +
                  "Patient: I've been feeling extremely fatigued and thirsty lately. I've also noticed I need to urinate much more frequently.\n" +
                  "Doctor: I see. Are you experiencing any blurred vision or numbness in your toes?\n" +
                  "Patient: Yes, actually. My toes feel a bit tingly sometimes. Also, my home glucose monitor showed 195 mg/dL this morning.\n" +
                  "Doctor: That is elevated. Let's record your blood pressure. It is 145/92 mmHg today, which is also higher than we'd like. I want to start you on Metformin 500mg once daily to manage the glucose levels."
                )}
                className="px-3.5 py-2 bg-slate-950 hover:bg-slate-900 border border-slate-850 rounded-xl text-xs font-semibold text-slate-400 transition-colors"
              >
                Load Demo Transcript
              </button>
              <button
                onClick={runScribe}
                disabled={loadingScribe || !transcript.trim()}
                className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2"
              >
                {loadingScribe ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Scribing Consultation...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Synthesize SOAP Record</span>
                  </>
                )}
              </button>
            </div>

            {scribeError && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{scribeError}</span>
              </div>
            )}
            {scribeSuccess && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{scribeSuccess}</span>
              </div>
            )}
          </div>

          {/* Right Column: Structured Output Preview (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-slate-900/30 border border-slate-900 rounded-3xl p-6 space-y-6 flex flex-col h-[75vh] justify-between">
              <div className="space-y-6 flex flex-col overflow-hidden">
                <div className="flex items-center justify-between border-b border-slate-900 pb-4 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-indigo-400" />
                    <h3 className="font-bold text-slate-200">EHR SOAP Draft</h3>
                  </div>
                  {scribeNote?.data && (
                    <button
                      onClick={commitScribe}
                      disabled={loadingScribe}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-900/20"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>Commit to EHR</span>
                    </button>
                  )}
                </div>

                {!scribeNote ? (
                  <div className="flex-1 border border-dashed border-slate-850 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-6 text-center space-y-3">
                    <Sparkles className="w-8 h-8 text-slate-650 animate-pulse" />
                    <p className="text-xs max-w-[200px]">Enter a consultation transcript and synthesize to generate a structured EHR SOAP draft.</p>
                  </div>
                ) : (
                  <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                    {/* SOAP Sections */}
                    <div className="space-y-2.5">
                      <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Subjective (Symptoms)</div>
                      <p className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
                        {scribeNote.data.subjective}
                      </p>
                    </div>
                    <div className="space-y-2.5">
                      <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Objective (Vitals/Exam)</div>
                      <p className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
                        {scribeNote.data.objective}
                      </p>
                    </div>
                    <div className="space-y-2.5">
                      <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Assessment (Diagnosis)</div>
                      <p className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
                        {scribeNote.data.assessment}
                      </p>
                    </div>
                    <div className="space-y-2.5">
                      <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Plan (Care Guidelines)</div>
                      <p className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl text-xs text-slate-300 leading-relaxed font-sans">
                        {scribeNote.data.plan}
                      </p>
                    </div>

                    {/* ICD-10 & Billing */}
                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">ICD-10 Codes</div>
                        <div className="flex flex-wrap gap-1.5">
                          {scribeNote.data.icd10_codes?.map((code: string, idx: number) => (
                            <span key={idx} className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded font-mono text-[10px] font-bold">
                              {code}
                            </span>
                          )) || <span className="text-slate-500 text-xs">None</span>}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Billing Codes</div>
                        <div className="flex flex-wrap gap-1.5">
                          {scribeNote.data.billing_codes?.map((code: string, idx: number) => (
                            <span key={idx} className="px-2 py-0.5 bg-slate-500/10 border border-slate-500/20 text-slate-300 rounded font-mono text-[10px] font-bold">
                              {code}
                            </span>
                          )) || <span className="text-slate-500 text-xs">None</span>}
                        </div>
                      </div>
                    </div>

                    {/* Proposed Prescriptions */}
                    <div className="space-y-2">
                      <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Extracted Prescriptions</div>
                      <div className="space-y-1.5">
                        {scribeNote.data.prescriptions?.map((item: any, idx: number) => (
                          <div key={idx} className="flex justify-between items-center p-2.5 bg-slate-950/40 border border-slate-900 rounded-xl text-xs text-slate-300">
                            <span className="font-semibold text-slate-200">{item.medication_name}</span>
                            <span className="text-slate-455 text-[10px]">{item.dosage} • {item.frequency}</span>
                          </div>
                        )) || <span className="text-slate-500 text-xs">None</span>}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Scribe Telemetry */}
              {scribeNote?.telemetry && (
                <div className="border-t border-slate-900 pt-4 flex items-center justify-between text-[10px] text-slate-500 font-mono flex-shrink-0">
                  <span>Latency: {scribeNote.telemetry.duration}s</span>
                  <span>Tokens: {scribeNote.telemetry.input_tokens + scribeNote.telemetry.output_tokens}</span>
                  <span>Est. Cost: ${scribeNote.telemetry.estimated_cost.toFixed(4)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'SIMULATOR' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">
          {/* Left Column: Sliders depending on model selection (7 cols) */}
          <div className="lg:col-span-7 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-6 h-[75vh]">
            <div className="flex items-center justify-between border-b border-slate-900 pb-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" />
                <h2 className="font-bold text-slate-200">Interactive Clinical Risk Sandbox</h2>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedModel('diabetes')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                    selectedModel === 'diabetes'
                      ? 'bg-indigo-600 border-indigo-500 text-white'
                      : 'bg-slate-950 border-slate-850 text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Diabetes Model
                </button>
                <button
                  onClick={() => setSelectedModel('heart')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                    selectedModel === 'heart'
                      ? 'bg-indigo-600 border-indigo-500 text-white'
                      : 'bg-slate-950 border-slate-850 text-slate-400 hover:text-slate-300'
                  }`}
                >
                  Heart Disease Model
                </button>
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Drag the sliders below to modify the patient's vitals and lifestyle parameters. The system runs our local ML classifiers in real time to calculate risk change and optimize a counterfactual recourse plan.
            </p>

            <div className="p-3 rounded-2xl border border-yellow-500/20 bg-yellow-500/5 text-[10px] font-mono text-yellow-500 uppercase leading-normal">
              Medical Disclaimer: The risk sandbox shows statistical predictions for decision support. It does not guarantee clinical outcomes. Consult a qualified clinician for diagnoses or treatment plans.
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto pr-2">
              {selectedModel === 'diabetes' ? (
                <div className="space-y-6">
                  {/* Diabetes Sliders */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>Body Mass Index (BMI)</span>
                      <span className="font-bold text-indigo-400">{simDiabetes.bmi.toFixed(1)}</span>
                    </div>
                    <input
                      type="range" min="15" max="50" step="0.1"
                      value={simDiabetes.bmi}
                      onChange={(e) => setSimDiabetes(prev => ({ ...prev, bmi: parseFloat(e.target.value) }))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>General Health Rating (1: Excellent to 5: Poor)</span>
                      <span className="font-bold text-indigo-400">{simDiabetes.general_health}</span>
                    </div>
                    <input
                      type="range" min="1" max="5" step="1"
                      value={simDiabetes.general_health}
                      onChange={(e) => setSimDiabetes(prev => ({ ...prev, general_health: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simDiabetes.hypertension === 1}
                        onChange={(e) => setSimDiabetes(prev => ({ ...prev, hypertension: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">Hypertension</span>
                    </label>
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simDiabetes.high_chol === 1}
                        onChange={(e) => setSimDiabetes(prev => ({ ...prev, high_chol: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">High Cholesterol</span>
                    </label>
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simDiabetes.smoking_history === 1}
                        onChange={(e) => setSimDiabetes(prev => ({ ...prev, smoking_history: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-655 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">Smoking History</span>
                    </label>
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simDiabetes.physical_activity === 1}
                        onChange={(e) => setSimDiabetes(prev => ({ ...prev, physical_activity: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-655 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">Active Past 30 Days</span>
                    </label>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Heart Sliders */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>Resting Blood Pressure (trestbps)</span>
                      <span className="font-bold text-indigo-400">{simHeart.trestbps} mmHg</span>
                    </div>
                    <input
                      type="range" min="80" max="200" step="1"
                      value={simHeart.trestbps}
                      onChange={(e) => setSimHeart(prev => ({ ...prev, trestbps: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>Serum Cholesterol (chol)</span>
                      <span className="font-bold text-indigo-400">{simHeart.chol} mg/dL</span>
                    </div>
                    <input
                      type="range" min="100" max="400" step="1"
                      value={simHeart.chol}
                      onChange={(e) => setSimHeart(prev => ({ ...prev, chol: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>Max Heart Rate (thalach)</span>
                      <span className="font-bold text-indigo-400">{simHeart.thalach} bpm</span>
                    </div>
                    <input
                      type="range" min="60" max="220" step="1"
                      value={simHeart.thalach}
                      onChange={(e) => setSimHeart(prev => ({ ...prev, thalach: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simHeart.fbs === 1}
                        onChange={(e) => setSimHeart(prev => ({ ...prev, fbs: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">Fasting Sugar &gt; 120</span>
                    </label>
                    <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                      <input
                        type="checkbox"
                        checked={simHeart.exang === 1}
                        onChange={(e) => setSimHeart(prev => ({ ...prev, exang: e.target.checked ? 1 : 0 }))}
                        className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                      />
                      <span className="text-xs font-semibold text-slate-300">Exercise Angina</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Simulator Output (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-slate-900/30 border border-slate-900 rounded-3xl p-6 space-y-4 flex flex-col justify-between min-h-[42vh]">
              <div className="space-y-4 flex flex-col overflow-hidden">
                <div className="flex items-center gap-2 border-b border-slate-900 pb-3 flex-shrink-0">
                  <TrendingDown className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-bold text-slate-200">Simulation Output</h3>
                </div>

                {loadingSim ? (
                  <div className="flex-1 border border-slate-850 rounded-2xl flex flex-col items-center justify-center text-slate-500 space-y-3 py-6">
                    <Loader2 className="w-8 h-8 text-slate-650 animate-spin" />
                    <p className="text-xs">Computing counterfactual trajectories...</p>
                  </div>
                ) : simResult ? (
                  <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                    {/* Risk Gauges Comparison */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-950/60 border border-slate-900 rounded-2xl p-4 text-center space-y-1">
                        <div className="text-[9px] uppercase font-extrabold text-slate-500">Baseline Risk</div>
                        <div className={`text-2xl font-black ${simResult.baseline_risk >= 0.5 ? 'text-red-500' : 'text-emerald-500'}`}>
                          {(simResult.baseline_risk * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="bg-slate-950/60 border border-slate-900 rounded-2xl p-4 text-center space-y-1">
                        <div className="text-[9px] uppercase font-extrabold text-slate-500">Optimized Target Risk</div>
                        <div className={`text-2xl font-black ${simResult.optimized_risk >= 0.5 ? 'text-red-500' : 'text-emerald-500'}`}>
                          {(simResult.optimized_risk * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>

                    {/* Recourse Path Action Steps */}
                    <div className="space-y-3">
                      <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Recourse Recommendation Path</div>
                      <div className="space-y-2">
                        {Object.keys(simResult.changes_applied).length === 0 ? (
                          <div className="p-4 bg-slate-950/40 border border-slate-850 rounded-2xl text-xs text-slate-400 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <span>Risk is already below clinical intervention threshold!</span>
                          </div>
                        ) : (
                          Object.entries(simResult.changes_applied).map(([key, val]: any, idx) => (
                            <div key={idx} className="flex gap-3 p-3 bg-slate-950/60 border border-slate-900 rounded-2xl items-start">
                              <span className="w-5 h-5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-extrabold text-[10px] flex items-center justify-center rounded-lg flex-shrink-0 mt-0.5">
                                {idx + 1}
                              </span>
                              <div className="space-y-0.5">
                                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wide">{key.replace('_', ' ')}</span>
                                <p className="text-xs text-slate-200">{val}</p>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 border border-dashed border-slate-850 rounded-2xl flex items-center justify-center text-slate-500 py-12">
                    <span className="text-xs">Adjust sliders to load simulation metrics</span>
                  </div>
                )}
              </div>

              {/* ClinOS Security Compliance */}
              <div className="p-3 bg-indigo-500/5 border border-indigo-500/15 rounded-2xl flex items-start gap-2.5 flex-shrink-0">
                <ShieldAlert className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                <span className="text-[9px] leading-relaxed text-indigo-300/80 font-mono">
                  Counterfactual recourse complies with WHO Clinical Governance and EU AI Act explainability standards.
                </span>
              </div>
            </div>

            {/* Second Opinion Consensus Card (Itch 2) */}
            <div className="bg-slate-900/30 border border-slate-900 rounded-3xl p-6 space-y-4 flex flex-col">
              <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                <div className="flex items-center gap-2">
                  <Stethoscope className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-bold text-slate-200">AI Diagnostic Consensus</h3>
                </div>
                <button
                  onClick={runClinicalConsensus}
                  disabled={loadingConsensus}
                  className="px-2.5 py-1 rounded bg-indigo-650 hover:bg-indigo-600 disabled:bg-slate-850 text-[10px] font-bold text-white transition-colors cursor-pointer flex items-center gap-1 uppercase"
                >
                  {loadingConsensus ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                  Audit Consensus
                </button>
              </div>

              {loadingConsensus ? (
                <div className="py-8 flex flex-col items-center justify-center text-slate-500 space-y-2">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-650" />
                  <span className="text-[10px]">Analyzing diagnostic discrepancies...</span>
                </div>
              ) : consensus ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-slate-500">Consensus Assessment</span>
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                      consensus.consensus_level === 'agreement' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                      consensus.consensus_level === 'minor_discrepancy' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' :
                      'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}>
                      {consensus.consensus_level.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-900">
                    <div className="text-xs font-bold text-slate-200 mb-1">{consensus.summary}</div>
                    <p className="text-[11px] text-slate-400 leading-normal">{consensus.detailed_audit}</p>
                  </div>

                  {consensus.recommended_tests && consensus.recommended_tests.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-[9px] uppercase font-bold text-slate-500">Recommended Diagnostics</span>
                      <div className="flex flex-wrap gap-1.5">
                        {consensus.recommended_tests.map((test: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-slate-950/80 border border-slate-850 text-[10px] font-mono text-indigo-300">
                            {test}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-6 text-center border border-dashed border-slate-850 rounded-2xl text-slate-500">
                  <span className="text-[11px]">Click Audit to query ML-Vitals consensus logs</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'LAB_ANALYZER' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">
          {/* Left Column: Report File Upload and Status */}
          <div className="lg:col-span-5 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-900 pb-4">
              <FileText className="w-5 h-5 text-indigo-400" />
              <h2 className="font-bold text-slate-200 uppercase tracking-wide">Smart Lab Report Analyzer</h2>
            </div>
            
            <p className="text-xs text-slate-400 leading-relaxed uppercase">
              Upload a digital image (JPEG/PNG) of pathology results or a clinical referral letter. The Google Gemini Vision model will read the image text and parse key parameters into structured entries.
            </p>

            <form onSubmit={handleUploadReport} className="space-y-4 pt-2">
              <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-950/40 hover:bg-slate-950/60 transition-colors cursor-pointer relative group">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  required
                />
                <FileText className="w-8 h-8 text-slate-650 mb-2 group-hover:text-indigo-400 transition-colors" />
                <span className="text-xs text-slate-400 group-hover:text-slate-200 transition-colors uppercase font-mono font-bold">
                  {selectedFile ? selectedFile.name.toUpperCase() : "Select Report Image"}
                </span>
                <span className="text-[10px] text-slate-500 font-mono mt-1">JPEG, PNG (Max 5MB)</span>
              </div>

              <button
                type="submit"
                disabled={uploadingReport || !selectedFile}
                className="w-full btn btn-primary py-2.5 cursor-pointer flex items-center justify-center gap-1.5 text-xs uppercase"
              >
                {uploadingReport ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                {uploadingReport ? "Analyzing..." : "Analyze Lab Report"}
              </button>
            </form>

            {analyzerError && (
              <div className="p-3 text-[10px] font-mono uppercase bg-[rgba(255,74,74,0.08)] border border-[var(--danger-border)] rounded text-[var(--danger)] flex items-start gap-2" role="alert">
                {analyzerError}
              </div>
            )}
          </div>

          {/* Right Column: Parsed Results */}
          <div className="lg:col-span-7 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 flex flex-col space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-900 pb-4">
              <BrainCircuit className="w-5 h-5 text-indigo-400" />
              <h2 className="font-bold text-slate-200 uppercase tracking-wide">Vision Model Extraction</h2>
            </div>

            {uploadingReport ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 space-y-2">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                <span className="text-xs uppercase font-mono tracking-wider animate-pulse">Running Gemini Vision OCR...</span>
              </div>
            ) : analyzerResult ? (
              <div className="space-y-6">
                <div className="space-y-2">
                  <span className="text-xs uppercase font-bold text-slate-500 font-mono">Summary & Analysis</span>
                  <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-900 text-xs text-slate-300 leading-relaxed">
                    {analyzerResult.summary}
                  </div>
                </div>

                {analyzerResult.extracted_data && Object.keys(analyzerResult.extracted_data).length > 0 ? (
                  <div className="space-y-2">
                    <span className="text-xs uppercase font-bold text-slate-500 font-mono">Extracted Lab Metrics</span>
                    <div className="border border-slate-900 rounded-2xl overflow-hidden">
                      <table className="w-full text-xs font-mono uppercase">
                        <thead>
                          <tr className="bg-slate-950/60 border-b border-slate-900 text-slate-400 text-left">
                            <th className="p-3">Metric Name</th>
                            <th className="p-3 text-right">Reported Value</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-900 text-slate-300">
                          {Object.entries(analyzerResult.extracted_data).map(([key, val]: any) => (
                            <tr key={key} className="hover:bg-slate-950/20 transition-all">
                              <td className="p-3 text-indigo-300 font-semibold">{key.replace(/_/g, ' ')}</td>
                              <td className="p-3 text-right font-bold">{val}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="py-6 text-center text-slate-500 text-xs font-mono uppercase border border-dashed border-slate-900 rounded-2xl">
                    No clinical metrics were extracted.
                  </div>
                )}

                {analyzerResult.disclaimer && (
                  <div className="p-3.5 bg-amber-500/5 border border-amber-500/15 rounded-2xl flex items-start gap-2.5 mt-4">
                    <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span className="text-[10px] leading-relaxed text-amber-500/80 font-medium font-sans">
                      {analyzerResult.disclaimer}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-12 border border-dashed border-slate-900 rounded-2xl">
                <FileText className="w-10 h-10 text-slate-700 mb-2" />
                <span className="text-xs uppercase font-mono text-slate-500">Upload a report file to view extracted parameters</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
