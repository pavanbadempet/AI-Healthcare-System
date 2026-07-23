import React, { useState } from 'react';
import { 
  Sparkles, 
  X, 
  CheckCircle2, 
  ArrowRight, 
  Stethoscope, 
  Bot, 
  Activity, 
  FileText, 
  ShieldCheck, 
  Zap, 
  BookOpen, 
  Search 
} from 'lucide-react';

interface OnboardingGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OnboardingGuideModal: React.FC<OnboardingGuideModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'clinician' | 'patient' | 'developer'>('clinician');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-3xl w-full overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-6 text-white flex items-center justify-between relative overflow-hidden">
          <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-2xl pointer-events-none" />
          <div className="flex items-center space-x-3 z-10">
            <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
              <Sparkles className="w-6 h-6 text-yellow-300 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight">Zero-Learning-Curve Interactive Guide</h2>
              <p className="text-xs text-blue-100 mt-0.5">Instant 1-Click Navigation & Feature Walkthrough</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors z-10 text-white"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 p-2 gap-2">
          <button
            onClick={() => setActiveTab('clinician')}
            className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === 'clinician'
                ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200 dark:border-slate-700'
                : 'text-slate-600 dark:text-slate-400 hover:bg-white/50 dark:hover:bg-slate-800/50'
            }`}
          >
            <Stethoscope className="w-4 h-4" />
            For Clinicians & Doctors
          </button>
          <button
            onClick={() => setActiveTab('patient')}
            className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === 'patient'
                ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200 dark:border-slate-700'
                : 'text-slate-600 dark:text-slate-400 hover:bg-white/50 dark:hover:bg-slate-800/50'
            }`}
          >
            <Bot className="w-4 h-4" />
            For Patients & Self-Care
          </button>
          <button
            onClick={() => setActiveTab('developer')}
            className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              activeTab === 'developer'
                ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200 dark:border-slate-700'
                : 'text-slate-600 dark:text-slate-400 hover:bg-white/50 dark:hover:bg-slate-800/50'
            }`}
          >
            <Zap className="w-4 h-4" />
            For Developers & Admins
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {activeTab === 'clinician' && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 rounded-xl flex items-start gap-3">
                <Search className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-blue-900 dark:text-blue-200">Global Quick Search (Ctrl + K)</h4>
                  <p className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">
                    Press <kbd className="px-1.5 py-0.5 bg-blue-200 dark:bg-blue-900 rounded font-mono text-[10px]">Ctrl+K</kbd> anywhere to search patients, ICD-10 codes, 3D DICOM scans, or launch governance tools instantly.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5 hover:border-blue-400 transition-colors">
                  <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-xs">
                    <Activity className="w-4 h-4 text-emerald-500" />
                    Pan-Tompkins ECG Analysis
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Auto-detects R-peaks, calculates HRV metrics, and flags QTc prolongation in real-time.
                  </p>
                </div>

                <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5 hover:border-blue-400 transition-colors">
                  <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-xs">
                    <FileText className="w-4 h-4 text-purple-500" />
                    1-Click Biometric Prescriptions
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Sign e-prescriptions on touch/mouse canvas with SHA-256 DEA attestation hash generation.
                  </p>
                </div>

                <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5 hover:border-blue-400 transition-colors">
                  <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-xs">
                    <BookOpen className="w-4 h-4 text-blue-500" />
                    GraphRAG Clinical Terminology
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Queries mapped automatically to SNOMED-CT, RxNorm, and ICD-10 ontologies with CoVe verification.
                  </p>
                </div>

                <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5 hover:border-blue-400 transition-colors">
                  <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-xs">
                    <ShieldCheck className="w-4 h-4 text-amber-500" />
                    NeMo Dosage Safety Guardrails
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Active background inspection of medication dosage bounds & contraindications.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'patient' && (
            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 rounded-xl flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-emerald-900 dark:text-emerald-200 text-xs">100% Plain English AI Assistance</h4>
                  <p className="text-emerald-700 dark:text-emerald-300 mt-0.5">
                    Ask any health question in plain conversational English. The AI breaks down complex medical jargon into easy-to-understand guidance with medical disclaimers.
                  </p>
                </div>
              </div>

              <ul className="space-y-2">
                <li className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg flex items-center justify-between">
                  <span>📱 <strong>ABDM Health ID (ABHA)</strong> — Create or link your 14-digit ABHA ID in 3 steps.</span>
                </li>
                <li className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg flex items-center justify-between">
                  <span>📦 <strong>Home Diagnostic Kits</strong> — Request CGM, ECG, or Spirometer kits delivered to your doorstep.</span>
                </li>
                <li className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg flex items-center justify-between">
                  <span>💳 <strong>Billing & Claims Portal</strong> — View itemized invoices and submit HSA/FSA claims in 1 click.</span>
                </li>
              </ul>
            </div>
          )}

          {activeTab === 'developer' && (
            <div className="space-y-3 text-xs">
              <div className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-[11px] space-y-2">
                <div className="text-slate-400"># Start local zero-config development session</div>
                <div className="text-emerald-400">python scripts/ai_context.py</div>
                <div className="text-blue-400">uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000</div>
                <div className="text-purple-400">npm --prefix frontend run dev</div>
              </div>

              <div className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1">
                <h4 className="font-bold text-slate-900 dark:text-slate-100">Interactive OpenAPI / Swagger Docs</h4>
                <p className="text-slate-500 dark:text-slate-400">
                  Access live self-documenting REST API endpoints at <code className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-blue-600">http://127.0.0.1:8000/docs</code>.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            Zero-Learning-Curve UI • Adaptive SOTA Enabled
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-md transition-all flex items-center gap-1.5"
          >
            Explore Dashboard
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
