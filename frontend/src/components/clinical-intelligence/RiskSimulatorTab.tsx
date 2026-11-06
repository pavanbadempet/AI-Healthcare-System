import React from 'react';
import {
  Sliders, Loader2, TrendingDown, CheckCircle2,
  ShieldAlert, Stethoscope, RefreshCw
} from 'lucide-react';

export interface SimDiabetesState {
  [key: string]: number;
  bmi: number;
  hypertension: number;
  high_chol: number;
  physical_activity: number;
  smoking_history: number;
  general_health: number;
  age: number;
  gender: number;
}

export interface SimHeartState {
  [key: string]: number;
  age: number;
  sex: number;
  cp: number;
  trestbps: number;
  chol: number;
  fbs: number;
  restecg: number;
  thalach: number;
  exang: number;
  oldpeak: number;
  slope: number;
  ca: number;
  thal: number;
}

export interface RiskSimulatorTabProps {
  selectedModel: 'diabetes' | 'heart';
  setSelectedModel: (model: 'diabetes' | 'heart') => void;
  simDiabetes: SimDiabetesState;
  setSimDiabetes: React.Dispatch<React.SetStateAction<SimDiabetesState>>;
  simHeart: SimHeartState;
  setSimHeart: React.Dispatch<React.SetStateAction<SimHeartState>>;
  simResult: any;
  loadingSim: boolean;
  consensus: any;
  loadingConsensus: boolean;
  onRunClinicalConsensus: () => void;
}

export const RiskSimulatorTab: React.FC<RiskSimulatorTabProps> = ({
  selectedModel,
  setSelectedModel,
  simDiabetes,
  setSimDiabetes,
  simHeart,
  setSimHeart,
  simResult,
  loadingSim,
  consensus,
  loadingConsensus,
  onRunClinicalConsensus
}) => {
  return (
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
                  type="range"
                  min="15"
                  max="50"
                  step="0.1"
                  value={simDiabetes.bmi}
                  onChange={(e) => setSimDiabetes((prev) => ({ ...prev, bmi: parseFloat(e.target.value) }))}
                  className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-300">
                  <span>General Health Rating (1: Excellent to 5: Poor)</span>
                  <span className="font-bold text-indigo-400">{simDiabetes.general_health}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={simDiabetes.general_health}
                  onChange={(e) => setSimDiabetes((prev) => ({ ...prev, general_health: parseInt(e.target.value) }))}
                  className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simDiabetes.hypertension === 1}
                    onChange={(e) => setSimDiabetes((prev) => ({ ...prev, hypertension: e.target.checked ? 1 : 0 }))}
                    className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                  />
                  <span className="text-xs font-semibold text-slate-300">Hypertension</span>
                </label>
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simDiabetes.high_chol === 1}
                    onChange={(e) => setSimDiabetes((prev) => ({ ...prev, high_chol: e.target.checked ? 1 : 0 }))}
                    className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                  />
                  <span className="text-xs font-semibold text-slate-300">High Cholesterol</span>
                </label>
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simDiabetes.smoking_history === 1}
                    onChange={(e) => setSimDiabetes((prev) => ({ ...prev, smoking_history: e.target.checked ? 1 : 0 }))}
                    className="rounded border-slate-800 text-indigo-655 focus:ring-indigo-500"
                  />
                  <span className="text-xs font-semibold text-slate-300">Smoking History</span>
                </label>
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simDiabetes.physical_activity === 1}
                    onChange={(e) => setSimDiabetes((prev) => ({ ...prev, physical_activity: e.target.checked ? 1 : 0 }))}
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
                  type="range"
                  min="80"
                  max="200"
                  step="1"
                  value={simHeart.trestbps}
                  onChange={(e) => setSimHeart((prev) => ({ ...prev, trestbps: parseInt(e.target.value) }))}
                  className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-300">
                  <span>Serum Cholesterol (chol)</span>
                  <span className="font-bold text-indigo-400">{simHeart.chol} mg/dL</span>
                </div>
                <input
                  type="range"
                  min="100"
                  max="400"
                  step="1"
                  value={simHeart.chol}
                  onChange={(e) => setSimHeart((prev) => ({ ...prev, chol: parseInt(e.target.value) }))}
                  className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-300">
                  <span>Max Heart Rate (thalach)</span>
                  <span className="font-bold text-indigo-400">{simHeart.thalach} bpm</span>
                </div>
                <input
                  type="range"
                  min="60"
                  max="220"
                  step="1"
                  value={simHeart.thalach}
                  onChange={(e) => setSimHeart((prev) => ({ ...prev, thalach: parseInt(e.target.value) }))}
                  className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simHeart.fbs === 1}
                    onChange={(e) => setSimHeart((prev) => ({ ...prev, fbs: e.target.checked ? 1 : 0 }))}
                    className="rounded border-slate-800 text-indigo-650 focus:ring-indigo-500"
                  />
                  <span className="text-xs font-semibold text-slate-300">Fasting Sugar &gt; 120</span>
                </label>
                <label className="flex items-center gap-3 p-3.5 bg-slate-950/60 border border-slate-850 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simHeart.exang === 1}
                    onChange={(e) => setSimHeart((prev) => ({ ...prev, exang: e.target.checked ? 1 : 0 }))}
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

          {/* AI Healthcare System Security Compliance */}
          <div className="p-3 bg-indigo-500/5 border border-indigo-500/15 rounded-2xl flex items-start gap-2.5 flex-shrink-0">
            <ShieldAlert className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <span className="text-[9px] leading-relaxed text-indigo-300/80 font-mono">
              Counterfactual recourse complies with WHO Clinical Governance and EU AI Act explainability standards.
            </span>
          </div>
        </div>

        {/* Second Opinion Consensus Card */}
        <div className="bg-slate-900/30 border border-slate-900 rounded-3xl p-6 space-y-4 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-900 pb-3">
            <div className="flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-slate-200">AI Diagnostic Consensus</h3>
            </div>
            <button
              onClick={onRunClinicalConsensus}
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
                <span
                  className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                    consensus.consensus_level === 'agreement'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : consensus.consensus_level === 'minor_discrepancy'
                      ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
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
  );
};
