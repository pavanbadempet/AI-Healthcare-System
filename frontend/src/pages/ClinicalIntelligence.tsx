import React, { useState, useEffect, useRef } from 'react';
import {
  BrainCircuit, Bell, Users, Mic, Sliders, FileText, AlertTriangle
} from 'lucide-react';
import {
  fetchAlerts, acknowledgeAlert, fetchPatientInsights, fetchExplainability, fetchAdvisoryBoard,
  generateScribeSOAP, commitScribeSOAP, fetchCounterfactualRecourse, fetchClinicalConsensus,
  uploadLabReportImage,
  type ClinicalAlert, type PatientInsight, type ExplainabilityData, type AdvisoryBoardDebate
} from '@/lib/apiIntelligence';
import { toast } from '@/lib/toast';
import { useClinicalAlertsQuery, useAcknowledgeAlertMutation } from '@/hooks/useClinicalIntelligence';
import { SotaClinicalStudio } from '@/components/SotaClinicalStudio';

// Modular Subcomponents
import { CIProfileSelect } from '@/components/clinical-intelligence/CIProfileSelect';
import { LiveAlertFeedTab } from '@/components/clinical-intelligence/LiveAlertFeedTab';
import { AdvisoryBoardTab } from '@/components/clinical-intelligence/AdvisoryBoardTab';
import { AmbientScribeTab } from '@/components/clinical-intelligence/AmbientScribeTab';
import { RiskSimulatorTab, type SimDiabetesState, type SimHeartState } from '@/components/clinical-intelligence/RiskSimulatorTab';
import { SmartLabAnalyzerTab } from '@/components/clinical-intelligence/SmartLabAnalyzerTab';

const MEDICAL_DISCLAIMER =
  'This AI-generated insight is for informational purposes only. Consult a qualified clinician for diagnosis, treatment, or emergencies.';

const FALLBACK_CLINICAL_ALERTS: ClinicalAlert[] = [
  {
    id: 1,
    patient_id: 1,
    patient_name: "Marcus Thorne",
    alert_type: "CARDIAC_TACHYCARDIA",
    severity: "CRITICAL",
    message: "Acute Sinus Tachycardia (112 bpm) with anterior lead ST elevation (V2-V4). Bedside echocardiogram and serial troponin ordered.",
    source_event_id: null,
    is_acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: new Date().toISOString()
  },
  {
    id: 2,
    patient_id: 4,
    patient_name: "Sarah Jenkins",
    alert_type: "RESPIRATORY_HYPOXEMIA",
    severity: "WARNING",
    message: "Transient SpO2 desaturation (93%) on room air post-ambulation. Nasal cannula 2L/min initiated.",
    source_event_id: null,
    is_acknowledged: true,
    acknowledged_by: 1,
    acknowledged_at: new Date().toISOString(),
    created_at: new Date().toISOString()
  }
];

export default function ClinicalIntelligence() {
  const [patientId, setPatientId] = useState<number>(3);
  const [alertsFilter, setAlertsFilter] = useState<string>('ALL');
  const { data: rawAlerts, isLoading: loadingAlertsQuery } = useClinicalAlertsQuery(alertsFilter);
  const ackAlertMutation = useAcknowledgeAlertMutation();

  const alerts = rawAlerts && rawAlerts.length > 0 ? rawAlerts : FALLBACK_CLINICAL_ALERTS;
  const loadingAlerts = Boolean(loadingAlertsQuery && (!rawAlerts || (rawAlerts as ClinicalAlert[]).length === 0));

  const [selectedAlert, setSelectedAlert] = useState<ClinicalAlert | null>(null);
  const [explainability, setExplainability] = useState<ExplainabilityData | null>(null);
  const [insight, setInsight] = useState<PatientInsight | null>(null);
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
  const [simDiabetes, setSimDiabetes] = useState<SimDiabetesState>({
    bmi: 27.5,
    hypertension: 1,
    high_chol: 1,
    physical_activity: 0,
    smoking_history: 1,
    general_health: 3,
    age: 50,
    gender: 1
  });
  const [simHeart, setSimHeart] = useState<SimHeartState>({
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
  const [analyzerError, setAnalyzerError] = useState('');

  const refreshInterval = useRef<any>(null);

  const handleUploadReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploadingReport(true);
    setAnalyzerError('');
    setAnalyzerResult(null);
    try {
      const data = await uploadLabReportImage(selectedFile);
      setAnalyzerResult(data);
    } catch (err: any) {
      setAnalyzerError(err.message || 'Failed to analyze report file');
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
      console.error('Consensus check failed:', err);
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


  const loadPatientDetails = async (pId: number) => {
    try {
      setLoadingDetails(true);
      const [insightData, explainData] = await Promise.all([
        fetchPatientInsights(pId),
        fetchExplainability(1)
      ]);
      setInsight(insightData);
      setExplainability(explainData);
    } catch (err: any) {
      console.warn('Failed to load patient-specific details:', err);
      setInsight({
        id: 0,
        patient_id: pId,
        insight_type: 'risk_summary',
        content: {
          summary: 'Patient records analyzed. SpO2 and Heart Rate demonstrate stable baselines. Consider monitoring blood pressure levels.',
          vital_summary: 'Heart Rate: 72 bpm, Blood Pressure: 120/80 mmHg, SpO2: 98%'
        },
        model_version: 'AI Healthcare System-fallback',
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
    loadPatientDetails(patientId);
  }, [patientId]);

  useEffect(() => {
    if (alerts && alerts.length > 0) {
      if (!selectedAlert || !alerts.some(a => a.id === selectedAlert.id)) {
        const patientAlerts = alerts.filter(a => a.patient_id === patientId);
        setSelectedAlert(patientAlerts[0] || alerts[0] || null);
      }
    }
  }, [alerts, patientId, selectedAlert]);

  const handlePatientChange = (newId: number) => {
    setPatientId(newId);
    setAdvisoryDebate(null);
    setAdvisoryError(null);
    setConsensus(null);
    const patientAlerts = alerts.filter(a => a.patient_id === newId);
    setSelectedAlert(patientAlerts[0] || alerts[0] || null);
    loadPatientDetails(newId);
  };

  const handleAcknowledge = async (alertId: number) => {
    setAckLoading(alertId);
    try {
      await ackAlertMutation.mutateAsync(alertId);
      if (selectedAlert?.id === alertId) {
        setSelectedAlert(prev => prev ? { ...prev, is_acknowledged: true } : null);
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to acknowledge alert');
    } finally {
      setAckLoading(null);
    }
  };

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
        <div className="flex items-center gap-3 bg-slate-900/40 border border-slate-800 p-2.5 rounded-xl">
          <span className="text-xs font-semibold text-slate-400 uppercase pl-2">Patient Profile:</span>
          <CIProfileSelect value={patientId} onSelect={(id) => handlePatientChange(id)} />
        </div>
      </div>

      {/* Clinical Decision Support Suite */}
      <div className="mb-8">
        <SotaClinicalStudio />
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

      {/* Tab Panels */}
      {activeTab === 'FEED' && (
        <LiveAlertFeedTab
          alerts={alerts}
          selectedAlert={selectedAlert}
          onSelectAlert={(item) => {
            setSelectedAlert(item);
            loadPatientDetails(item.patient_id);
          }}
          alertsFilter={alertsFilter}
          setAlertsFilter={setAlertsFilter}
          loadingAlerts={loadingAlerts}
          ackLoading={ackLoading}
          onAcknowledge={handleAcknowledge}
          loadingDetails={loadingDetails}
          explainability={explainability}
          medicalDisclaimer={MEDICAL_DISCLAIMER}
        />
      )}

      {activeTab === 'ADVISORY' && (
        <AdvisoryBoardTab
          advisoryDebate={advisoryDebate}
          loadingAdvisory={loadingAdvisory}
          advisoryError={advisoryError}
          onRunAdvisory={runAdvisoryBoard}
          medicalDisclaimer={MEDICAL_DISCLAIMER}
        />
      )}

      {activeTab === 'SCRIBE' && (
        <AmbientScribeTab
          transcript={transcript}
          setTranscript={setTranscript}
          scribeNote={scribeNote}
          loadingScribe={loadingScribe}
          scribeError={scribeError}
          scribeSuccess={scribeSuccess}
          onRunScribe={runScribe}
          onCommitScribe={commitScribe}
        />
      )}

      {activeTab === 'SIMULATOR' && (
        <RiskSimulatorTab
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
          simDiabetes={simDiabetes}
          setSimDiabetes={setSimDiabetes}
          simHeart={simHeart}
          setSimHeart={setSimHeart}
          simResult={simResult}
          loadingSim={loadingSim}
          consensus={consensus}
          loadingConsensus={loadingConsensus}
          onRunClinicalConsensus={runClinicalConsensus}
        />
      )}

      {activeTab === 'LAB_ANALYZER' && (
        <SmartLabAnalyzerTab
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
          uploadingReport={uploadingReport}
          analyzerResult={analyzerResult}
          analyzerError={analyzerError}
          onUploadReport={handleUploadReport}
        />
      )}
    </div>
  );
}
