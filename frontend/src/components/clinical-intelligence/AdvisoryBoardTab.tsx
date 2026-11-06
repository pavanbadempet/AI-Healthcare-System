import React from 'react';
import {
  BrainCircuit, Sparkles, Loader2, Users, Stethoscope,
  RefreshCw, CheckSquare, AlertCircle, AlertTriangle
} from 'lucide-react';
import { AdvisoryBoardDebate } from '@/lib/apiIntelligence';

const DEFAULT_DISCLAIMER =
  'This AI-generated insight is for informational purposes only. Consult a qualified clinician for diagnosis, treatment, or emergencies.';

export interface AdvisoryBoardTabProps {
  advisoryDebate: AdvisoryBoardDebate | null;
  loadingAdvisory: boolean;
  advisoryError: string | null;
  onRunAdvisory: () => void;
  medicalDisclaimer?: string;
}

export const AdvisoryBoardTab: React.FC<AdvisoryBoardTabProps> = ({
  advisoryDebate,
  loadingAdvisory,
  advisoryError,
  onRunAdvisory,
  medicalDisclaimer = DEFAULT_DISCLAIMER
}) => {
  return (
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
            onClick={onRunAdvisory}
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
              <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">
                1
              </div>
              <span className="text-sm font-semibold text-slate-300">Extracting patient EHR context and ML predictions...</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">
                2
              </div>
              <span className="text-sm font-semibold text-slate-300">Generating initial Cardiologist & Endocrinologist opinions...</span>
            </div>
            <div className="flex items-center gap-3 animate-pulse">
              <div className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-xs font-bold font-mono">
                3
              </div>
              <span className="text-sm font-semibold text-indigo-400">Performing cross-consultation review...</span>
            </div>
            <div className="flex items-center gap-3 opacity-50">
              <div className="w-5 h-5 rounded-full bg-slate-900 text-slate-600 border border-slate-800 flex items-center justify-center text-xs font-bold font-mono">
                4
              </div>
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
                  onClick={onRunAdvisory}
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
                  {medicalDisclaimer}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
