import React from 'react';
import {
  Mic, Sparkles, Loader2, AlertTriangle, CheckCircle2,
  FileText, Save
} from 'lucide-react';

export interface AmbientScribeTabProps {
  transcript: string;
  setTranscript: (text: string) => void;
  scribeNote: any;
  loadingScribe: boolean;
  scribeError: string | null;
  scribeSuccess: string | null;
  onRunScribe: () => void;
  onCommitScribe: () => void;
}

const DEMO_TRANSCRIPT =
  "Doctor: Hi there. Let's review your symptoms today.\n" +
  "Patient: I've been feeling extremely fatigued and thirsty lately. I've also noticed I need to urinate much more frequently.\n" +
  "Doctor: I see. Are you experiencing any blurred vision or numbness in your toes?\n" +
  "Patient: Yes, actually. My toes feel a bit tingly sometimes. Also, my home glucose monitor showed 195 mg/dL this morning.\n" +
  "Doctor: That is elevated. Let's record your blood pressure. It is 145/92 mmHg today, which is also higher than we'd like. I want to start you on Metformin 500mg once daily to manage the glucose levels.";

export const AmbientScribeTab: React.FC<AmbientScribeTabProps> = ({
  transcript,
  setTranscript,
  scribeNote,
  loadingScribe,
  scribeError,
  scribeSuccess,
  onRunScribe,
  onCommitScribe
}) => {
  return (
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
            onClick={() => setTranscript(DEMO_TRANSCRIPT)}
            className="px-3.5 py-2 bg-slate-950 hover:bg-slate-900 border border-slate-850 rounded-xl text-xs font-semibold text-slate-400 transition-colors"
          >
            Load Demo Transcript
          </button>
          <button
            onClick={onRunScribe}
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
                  onClick={onCommitScribe}
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
                <p className="text-xs max-w-[200px]">
                  Enter a consultation transcript and synthesize to generate a structured EHR SOAP draft.
                </p>
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
  );
};
